"""Delete only verified obsolete Phase 3 Bitable archive tables."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = Path(__file__).resolve().parent
for path in (BACKEND_ROOT, SCRIPT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from reconcile_phase3_single_submission_base import _load_env, _load_lark_client
from services.fde_phase3_archive_cleanup import (
    ArchiveCleanup,
    ArchiveCleanupSafetyError,
    AutomationInspection,
)
from services.fde_phase3_two_stage_migration import (
    TwoStageMigration,
    TwoStageMigrationSafetyError,
)


CONFIRMATION = "FDE_PHASE3_DELETE_ARCHIVES"
DEFAULT_TABLE_CONFIRMATION = "FDE_PHASE3_DELETE_DEFAULT_TABLE"
AUTOMATION_STATE_VERIFIED_NONE = "verified-none"


class FeishuArchiveCleanupClient:
    """Narrow Bitable metadata adapter used only by the cleanup command."""

    def __init__(self, lark_client: Any, base_token: str, *, automation_state: str | None) -> None:
        self._lark = lark_client
        self._base_token = base_token
        self._automation_state = automation_state

    def list_tables(self) -> list[dict[str, Any]]:
        return self._lark.list_tables()

    def list_views(self, table_id: str) -> list[dict[str, Any]]:
        response = self._lark.get(self._url(f"/tables/{table_id}/views?page_size=100"))
        return list(self._data(response, "list views").get("items") or [])

    def list_fields(self, table_id: str) -> list[dict[str, Any]]:
        response = self._lark.get(self._url(f"/tables/{table_id}/fields?page_size=100"))
        return list(self._data(response, "list fields").get("items") or [])

    def get_form_metadata(self, table_id: str, form_id: str) -> dict[str, Any]:
        response = self._lark.get(self._url(f"/tables/{table_id}/forms/{form_id}"))
        return dict(self._data(response, "get Form metadata").get("form") or {})

    def inspect_automation(self, table_id: str) -> AutomationInspection:
        del table_id
        # Feishu does not expose this Base-level binding through the reusable client.
        # An explicit UI verification is therefore required instead of assuming none.
        return AutomationInspection(
            checked=self._automation_state == AUTOMATION_STATE_VERIFIED_NONE,
            active_binding_names=(),
        )

    def delete_table(self, table_id: str) -> None:
        request = getattr(self._lark, "_request", None)
        if not callable(request):
            raise RuntimeError("configured Lark client does not support DELETE metadata requests")
        response = request("DELETE", self._url(f"/tables/{table_id}"))
        if response.get("code") != 0:
            raise RuntimeError(f"delete table failed: {response.get('msg', 'unknown error')}")

    def _url(self, suffix: str) -> str:
        return f"{self._lark.LARK_BASE}/bitable/v1/apps/{self._base_token}{suffix}"

    @staticmethod
    def _data(response: dict[str, Any], action: str) -> dict[str, Any]:
        if response.get("code") != 0:
            raise RuntimeError(f"{action} failed: {response.get('msg', 'unknown error')}")
        data = response.get("data")
        if not isinstance(data, dict):
            raise RuntimeError(f"{action} response did not include data")
        return data


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-token", default=os.environ.get("FDE_PHASE3_BASE_TOKEN"))
    parser.add_argument(
        "--secret-file",
        default=str(Path.home() / ".claude" / ".cache" / ".fde_api_secrets.env"),
    )
    parser.add_argument("--apply", action="store_true", help="apply one verified deletion action")
    parser.add_argument(
        "--delete-default-table",
        action="store_true",
        help=(
            "delete only the verified empty default table; requires a distinct "
            f"confirmation {DEFAULT_TABLE_CONFIRMATION}"
        ),
    )
    parser.add_argument(
        "--confirm",
        help=f"required with --apply: {CONFIRMATION}",
    )
    parser.add_argument(
        "--automation-state",
        help=(
            "required with --apply after the Feishu UI confirms no legacy binding: "
            f"{AUTOMATION_STATE_VERIFIED_NONE}"
        ),
    )
    for action in parser._actions:
        if action.dest == "delete_default_table":
            action.help = argparse.SUPPRESS
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not isinstance(args.base_token, str) or not args.base_token.strip():
        raise SystemExit("--base-token or FDE_PHASE3_BASE_TOKEN is required")
    delete_default_table = bool(getattr(args, "delete_default_table", False))
    if delete_default_table:
        raise SystemExit(
            "--delete-default-table is disabled; preserve existing records"
        )
    if delete_default_table:
        if not args.apply:
            raise SystemExit("--delete-default-table requires --apply")
        if args.confirm != DEFAULT_TABLE_CONFIRMATION:
            raise SystemExit(
                f"--delete-default-table requires --confirm {DEFAULT_TABLE_CONFIRMATION}"
            )
        if args.automation_state != AUTOMATION_STATE_VERIFIED_NONE:
            raise SystemExit(
                f"--apply requires --automation-state {AUTOMATION_STATE_VERIFIED_NONE}"
            )
        return
    if args.apply and args.confirm != CONFIRMATION:
        raise SystemExit(f"--apply requires --confirm {CONFIRMATION}")
    if args.apply and args.automation_state != AUTOMATION_STATE_VERIFIED_NONE:
        raise SystemExit(
            f"--apply requires --automation-state {AUTOMATION_STATE_VERIFIED_NONE}"
        )


def _plan_output(cleanup: ArchiveCleanup) -> dict[str, object]:
    plan = cleanup.plan()
    return {
        "mode": "dry_run",
        "delete_table_names": list(plan.deletable_table_names),
        "remaining_table_names": list(plan.remaining_table_names),
    }


def main() -> int:
    args = _args()
    validate_args(args)
    _load_env(Path(args.secret_file))
    client = FeishuArchiveCleanupClient(
        _load_lark_client(args.base_token),
        args.base_token,
        automation_state=args.automation_state,
    )
    try:
        if args.delete_default_table:
            receipt = TwoStageMigration(client).delete_default_table(confirmed=True)
            print(
                json.dumps(
                    {
                        "mode": "applied",
                        "deleted_table_name": receipt.deleted_table_name,
                        "remaining_table_names": list(receipt.remaining_table_names),
                    },
                    ensure_ascii=False,
                )
            )
            return 0
        cleanup = ArchiveCleanup(client)
        if not args.apply:
            print(json.dumps(_plan_output(cleanup), ensure_ascii=False))
            return 0
        receipt = cleanup.apply(confirmed=True)
    except (ArchiveCleanupSafetyError, TwoStageMigrationSafetyError) as exc:
        print(json.dumps({"mode": "blocked", "reason": str(exc)}, ensure_ascii=False))
        return 2

    print(
        json.dumps(
            {
                "mode": "applied",
                "deleted_table_names": list(receipt.deleted_table_names),
                "remaining_table_names": list(receipt.remaining_table_names),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

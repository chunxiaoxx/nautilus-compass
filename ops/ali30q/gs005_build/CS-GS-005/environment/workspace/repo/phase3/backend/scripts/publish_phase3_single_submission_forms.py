"""Configure and publish the two Phase 3 native Form views."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (BACKEND_ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from reconcile_phase3_single_submission_base import _load_env, _load_lark_client
from services.fde_phase3_single_submission_forms import FormPublisher


CONFIRMATION = "FDE_PHASE3_SINGLE_SUBMISSION"


class FeishuFormClient:
    """Narrow adapter for supported Bitable Form metadata APIs."""

    def __init__(self, lark_client: Any, base_token: str) -> None:
        self._lark = lark_client
        self._base_token = base_token

    def list_tables(self) -> list[dict[str, Any]]:
        return self._lark.list_tables()

    def list_fields(self, table_id: str) -> list[dict[str, Any]]:
        return self._lark.list_fields(table_id)

    def list_views(self, table_id: str) -> list[dict[str, Any]]:
        return list(self._data(self._lark.get(self._url(f"/tables/{table_id}/views?page_size=100")), "list views").get("items") or [])

    def get_form_metadata(self, table_id: str, form_id: str) -> dict[str, Any]:
        return dict(
            self._data(
                self._lark.get(self._url(f"/tables/{table_id}/forms/{form_id}")),
                "get Form metadata",
            ).get("form")
            or {}
        )

    def list_form_fields(self, table_id: str, form_id: str) -> list[dict[str, Any]]:
        return list(
            self._data(
                self._lark.get(
                    self._url(f"/tables/{table_id}/forms/{form_id}/fields?page_size=100")
                ),
                "list Form questions",
            ).get("items")
            or []
        )

    def patch_form_metadata(
        self,
        table_id: str,
        form_id: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        return dict(
            self._patch(
                f"/tables/{table_id}/forms/{form_id}", body, "patch Form metadata"
            ).get("form")
            or {}
        )

    def patch_form_field(
        self,
        table_id: str,
        form_id: str,
        field_id: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        return dict(
            self._patch(
                f"/tables/{table_id}/forms/{form_id}/fields/{field_id}",
                body,
                "patch Form question",
            ).get("field")
            or {}
        )

    def _patch(self, suffix: str, body: dict[str, Any], action: str) -> dict[str, Any]:
        request = getattr(self._lark, "_request", None)
        if not callable(request):
            raise RuntimeError("configured Lark client does not support PATCH Form requests")
        return self._data(request("PATCH", self._url(suffix), body=body), action)

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
    parser.add_argument("--apply", action="store_true", help="apply approved Form presentation")
    parser.add_argument(
        "--retire-legacy",
        action="store_true",
        help="unshare the three older public Forms after publication succeeds",
    )
    parser.add_argument(
        "--reconfigure-public",
        action="store_true",
        help="temporarily unshare, update, read back, and republish changed public Forms",
    )
    parser.add_argument("--confirm", help=f"required with --apply: {CONFIRMATION}")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not isinstance(args.base_token, str) or not args.base_token.strip():
        raise SystemExit("--base-token or FDE_PHASE3_BASE_TOKEN is required")
    if args.apply and args.confirm != CONFIRMATION:
        raise SystemExit(f"--apply requires --confirm {CONFIRMATION}")
    if getattr(args, "reconfigure_public", False) and not args.apply:
        raise SystemExit("--reconfigure-public requires --apply")


def _plan_output(
    publisher: FormPublisher,
    *,
    retire_legacy: bool,
    reconfigure_public: bool,
) -> dict[str, Any]:
    plan = publisher.reconfiguration_plan() if reconfigure_public else publisher.plan()
    return {
        "mode": "dry_run",
        "field_updates": [patch.field_name for patch in plan.field_patches],
        "forms_to_publish": [patch.form_name for patch in plan.metadata_patches],
        "legacy_forms_to_retire": retire_legacy,
        "reconfigure_public": reconfigure_public,
    }


def main() -> int:
    args = _args()
    validate_args(args)
    _load_env(Path(args.secret_file))
    publisher = FormPublisher(FeishuFormClient(_load_lark_client(args.base_token), args.base_token))
    if not args.apply:
        print(
            json.dumps(
                _plan_output(
                    publisher,
                    retire_legacy=args.retire_legacy,
                    reconfigure_public=args.reconfigure_public,
                ),
                ensure_ascii=False,
            )
        )
        return 0

    receipt = (
        publisher.reconfigure_public_forms(confirmed=True)
        if args.reconfigure_public
        else publisher.publish(confirmed=True)
    )
    retired = publisher.retire_legacy_forms(confirmed=True) if args.retire_legacy else ()
    print(
        json.dumps(
            {
                "mode": "applied",
                "published_forms": [
                    {"name": form.form_name, "shared_url": form.shared_url}
                    for form in receipt.forms
                ],
                "retired_forms": [form.form_name for form in retired],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Provision the approved Phase 3 2026-07-22 public intake structure.

The command defaults to a schema-only dry run. It never creates business
records, synchronizes a buyer Sheet, or enables V5/Compass exports.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.fde_phase3_20260722_provisioning import BitableProvisioner


CONFIRMATION = "FDE_PHASE3_20260722"


def _load_env(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _load_lark_client(base_token: str) -> Any:
    scripts_dir = Path.home() / ".agents" / "skills" / "ecc-shared" / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from bitable_v2.lark_client import LarkHttpClient  # noqa: PLC0415

    app_id = os.environ.get("FEISHU_APP_ID") or os.environ.get("LARK_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET") or os.environ.get("LARK_APP_SECRET")
    if not app_id or not app_secret:
        raise RuntimeError("missing Feishu application credentials")
    return LarkHttpClient(app_id=app_id, app_secret=app_secret, base_token=base_token)


class FeishuBitableClient:
    """Small adapter limited to schema and native Form-view endpoints."""

    def __init__(self, lark_client: Any, base_token: str) -> None:
        self._lark = lark_client
        self._base_token = base_token

    def list_tables(self) -> list[dict[str, Any]]:
        return self._lark.list_tables()

    def list_fields(self, table_id: str) -> list[dict[str, Any]]:
        return self._lark.list_fields(table_id)

    def list_views(self, table_id: str) -> list[dict[str, Any]]:
        response = self._lark.get(
            f"{self._lark.LARK_BASE}/bitable/v1/apps/{self._base_token}"
            f"/tables/{table_id}/views?page_size=100"
        )
        self._assert_ok(response, "list views")
        return response.get("data", {}).get("items", [])

    def create_table(self, name: str, fields: list[dict[str, Any]]) -> dict[str, Any]:
        response = self._lark.post(
            f"{self._lark.LARK_BASE}/bitable/v1/apps/{self._base_token}/tables",
            body={"table": {"name": name, "fields": fields}},
        )
        self._assert_ok(response, "create table")
        data = response.get("data", {})
        table = data.get("table", data)
        if not table.get("table_id"):
            raise RuntimeError("create table response did not include table_id")
        return table

    def create_form_view(self, table_id: str, view_name: str) -> dict[str, Any]:
        response = self._lark.post(
            f"{self._lark.LARK_BASE}/bitable/v1/apps/{self._base_token}"
            f"/tables/{table_id}/views",
            body={"view_name": view_name, "view_type": "form"},
        )
        self._assert_ok(response, "create Form view")
        view = response.get("data", {}).get("view", {})
        if not view.get("view_id"):
            raise RuntimeError("create Form view response did not include view_id")
        return view

    @staticmethod
    def _assert_ok(response: dict[str, Any], action: str) -> None:
        if response.get("code") != 0:
            raise RuntimeError(f"{action} failed: {response.get('msg', 'unknown error')}")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-token", default=os.environ.get("FDE_PHASE3_BASE_TOKEN"))
    parser.add_argument(
        "--secret-file",
        default=str(Path.home() / ".claude" / ".cache" / ".fde_api_secrets.env"),
    )
    parser.add_argument("--apply", action="store_true", help="create missing tables and Form views")
    parser.add_argument("--confirm", help=f"required with --apply: {CONFIRMATION}")
    return parser.parse_args()


def main() -> int:
    args = _args()
    if not args.base_token:
        raise SystemExit("--base-token or FDE_PHASE3_BASE_TOKEN is required")
    if args.apply and args.confirm != CONFIRMATION:
        raise SystemExit(f"--apply requires --confirm {CONFIRMATION}")

    _load_env(Path(args.secret_file))
    client = FeishuBitableClient(_load_lark_client(args.base_token), args.base_token)
    provisioner = BitableProvisioner(client)
    if not args.apply:
        plan = provisioner.plan()
        print(
            json.dumps(
                {
                    "mode": "dry_run",
                    "create_tables": plan.create_table_names,
                    "create_form_views": plan.create_form_names,
                },
                ensure_ascii=False,
            )
        )
        return 0

    receipt = provisioner.apply(confirmed=True)
    print(
        json.dumps(
            {
                "mode": "applied",
                "created_tables": receipt.created_table_names,
                "created_form_views": receipt.created_form_names,
                "verified_tables": receipt.table_names,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

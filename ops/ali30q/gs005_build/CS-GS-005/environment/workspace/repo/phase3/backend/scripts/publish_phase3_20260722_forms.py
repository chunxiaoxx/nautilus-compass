"""Publish the approved Phase 3 native Form views through Feishu's Form API.

Default mode is read-only. Apply mode changes Form metadata and Form-question
presentation only; it never accesses the records endpoint.
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

from services.fde_phase3_20260722_form_publishing import FormPublisher
from services.fde_phase3_20260722_provisioning import expected_public_form_names

from provision_phase3_20260722_bitable import _load_env, _load_lark_client


CONFIRMATION = "FDE_PHASE3_20260722"


class FeishuFormClient:
    """Narrow adapter for supported Bitable Form API endpoints only."""

    def __init__(self, lark_client: Any, base_token: str) -> None:
        self._lark = lark_client
        self._base_token = base_token

    def _url(self, suffix: str) -> str:
        return f"{self._lark.LARK_BASE}/bitable/v1/apps/{self._base_token}{suffix}"

    @staticmethod
    def _assert_ok(response: dict[str, Any], action: str) -> dict[str, Any]:
        if response.get("code") != 0:
            raise RuntimeError(f"{action} failed: {response.get('msg', 'unknown error')}")
        return response.get("data", {})

    def _patch(self, suffix: str, body: dict[str, Any], action: str) -> dict[str, Any]:
        # Keep authentication, retries, and secret masking in ecc-shared's client.
        response = self._lark._request("PATCH", self._url(suffix), body=body)
        return self._assert_ok(response, action)

    def list_tables(self) -> list[dict[str, Any]]:
        return self._lark.list_tables()

    def list_fields(self, table_id: str) -> list[dict[str, Any]]:
        return self._lark.list_fields(table_id)

    def list_views(self, table_id: str) -> list[dict[str, Any]]:
        data = self._assert_ok(
            self._lark.get(self._url(f"/tables/{table_id}/views?page_size=100")),
            "list views",
        )
        return data.get("items", [])

    def get_form_metadata(self, table_id: str, form_id: str) -> dict[str, Any]:
        data = self._assert_ok(
            self._lark.get(self._url(f"/tables/{table_id}/forms/{form_id}")),
            "get Form metadata",
        )
        return data.get("form", {})

    def list_form_fields(self, table_id: str, form_id: str) -> list[dict[str, Any]]:
        data = self._assert_ok(
            self._lark.get(
                self._url(f"/tables/{table_id}/forms/{form_id}/fields?page_size=100")
            ),
            "list Form fields",
        )
        return data.get("items", [])

    def patch_form_metadata(
        self, table_id: str, form_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        data = self._patch(f"/tables/{table_id}/forms/{form_id}", body, "patch Form metadata")
        return data.get("form", {})

    def patch_form_field(
        self, table_id: str, form_id: str, field_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        data = self._patch(
            f"/tables/{table_id}/forms/{form_id}/fields/{field_id}",
            body,
            "patch Form field",
        )
        return data.get("field", {})


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-token", default=os.environ.get("FDE_PHASE3_BASE_TOKEN"))
    parser.add_argument(
        "--secret-file",
        default=str(Path.home() / ".claude" / ".cache" / ".fde_api_secrets.env"),
    )
    parser.add_argument("--apply", action="store_true", help="apply Form presentation and sharing")
    parser.add_argument("--retire-obsolete", action="store_true")
    parser.add_argument("--confirm", help=f"required with --apply: {CONFIRMATION}")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.base_token:
        raise SystemExit("--base-token or FDE_PHASE3_BASE_TOKEN is required")
    if args.apply and args.confirm != CONFIRMATION:
        raise SystemExit(f"--apply requires --confirm {CONFIRMATION}")


def _plan_payload(publisher: FormPublisher, *, retire_obsolete: bool) -> dict[str, Any]:
    plan = publisher.plan()
    return {
        "mode": "dry_run",
        "field_updates": [
            {"form_field": patch.field_name, "form_id": patch.form_id}
            for patch in plan.field_patches
        ],
        "forms_to_publish": [patch.form_name for patch in plan.metadata_patches],
        "obsolete_forms_to_retire": [
            "第三期题目与交互成果提交",
            "第三期专家申请与豆包开通",
        ]
        if retire_obsolete
        else [],
    }


def main() -> int:
    args = _args()
    validate_args(args)

    _load_env(Path(args.secret_file))
    publisher = FormPublisher(FeishuFormClient(_load_lark_client(args.base_token), args.base_token))
    if not args.apply:
        print(json.dumps(_plan_payload(publisher, retire_obsolete=args.retire_obsolete), ensure_ascii=False))
        return 0

    receipt = publisher.publish(confirmed=True)
    retired = publisher.retire_obsolete_forms(confirmed=True) if args.retire_obsolete else ()
    print(
        json.dumps(
            {
                "mode": "applied",
                "published_forms": [
                    {"name": item.form_name, "shared_url": item.shared_url} for item in receipt.forms
                ],
                "retired_forms": [item.form_name for item in retired],
                "verified_form_names": expected_public_form_names(),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

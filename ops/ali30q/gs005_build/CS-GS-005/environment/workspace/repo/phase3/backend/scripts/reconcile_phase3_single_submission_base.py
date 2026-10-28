"""Create and verify the Phase 3 canonical Bitable metadata contract."""
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

from services.fde_phase3_single_submission_provisioning import BitableReconciler
from services.fde_phase3_two_stage_migration import TwoStageMigration
from services.fde_phase3_two_stage_schema import (
    canonical_tables as two_stage_canonical_tables,
)


CONFIRMATION = "FDE_PHASE3_SINGLE_SUBMISSION"
TWO_STAGE_CONFIRMATION = "FDE_PHASE3_ACTIVATE_TWO_STAGE"


def _load_env(path: Path) -> None:
    if not path.is_file():
        raise RuntimeError(f"credential file does not exist: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
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


class FeishuSchemaClient:
    """Small adapter restricted to Bitable metadata endpoints."""

    def __init__(self, lark_client: Any, base_token: str) -> None:
        self._lark = lark_client
        self._base_token = base_token

    def list_tables(self) -> list[dict[str, Any]]:
        return self._lark.list_tables()

    def list_fields(self, table_id: str) -> list[dict[str, Any]]:
        return self._lark.list_fields(table_id)

    def list_views(self, table_id: str) -> list[dict[str, Any]]:
        response = self._lark.get(self._url(f"/tables/{table_id}/views?page_size=100"))
        return list(self._data(response, "list views").get("items") or [])

    def create_table(self, name: str, fields: list[dict[str, Any]]) -> dict[str, Any]:
        response = self._lark.post(
            self._url("/tables"),
            body={"table": {"name": name, "fields": fields}},
        )
        table_id = self._data(response, "create table").get("table_id")
        if not isinstance(table_id, str) or not table_id.strip():
            raise RuntimeError("create table response did not include table_id")
        return {"table_id": table_id, "name": name}

    def create_field(
        self,
        table_id: str,
        field: dict[str, Any] | None = None,
        *,
        field_name: str | None = None,
        field_type: int | None = None,
        options: tuple[str, ...] = (),
        link_target: str | None = None,
    ) -> dict[str, Any]:
        if field is not None and field_name is not None:
            raise TypeError("provide either a field payload or two-stage field arguments")
        if field is None:
            if not field_name or field_type is None:
                raise TypeError("field_name and field_type are required")
            field = {"field_name": field_name, "type": field_type}
            if link_target is not None:
                if link_target == "self":
                    target_table_id = table_id
                else:
                    targets = [
                        table
                        for table in self.list_tables()
                        if table.get("name") == link_target
                    ]
                    if len(targets) != 1:
                        raise RuntimeError(
                            f"link target table is not unique: {link_target}"
                        )
                    target_table_id = str(targets[0]["table_id"])
                field["property"] = {
                    "multiple": False,
                    "table_id": target_table_id,
                }
            elif options:
                field["property"] = {
                    "options": [{"name": option} for option in options]
                }
        response = self._lark.post(
            self._url(f"/tables/{table_id}/fields"),
            body=field,
        )
        created = self._data(response, "create field").get("field")
        if not isinstance(created, dict) or not isinstance(created.get("field_name"), str):
            raise RuntimeError("create field response did not include field metadata")
        return created

    def create_link_field(
        self,
        table_id: str,
        name: str,
        target_table_id: str,
    ) -> dict[str, Any]:
        response = self._lark.post(
            self._url(f"/tables/{table_id}/fields"),
            body={
                "field_name": name,
                "type": 18,
                "property": {"multiple": False, "table_id": target_table_id},
            },
        )
        field = self._data(response, "create link field").get("field")
        if not isinstance(field, dict) or field.get("field_name") != name:
            raise RuntimeError("create link field response did not include the expected field")
        return field

    def update_field_options(
        self,
        table_id: str,
        *,
        field_id: str,
        field_name: str,
        field_type: int,
        options: tuple[str, ...],
    ) -> None:
        response = self._lark.put(
            self._url(f"/tables/{table_id}/fields/{field_id}"),
            body={
                "field_name": field_name,
                "type": field_type,
                "property": {
                    "options": [{"name": option} for option in options]
                },
            },
        )
        field = self._data(response, "update field options").get("field")
        if not isinstance(field, dict) or field.get("field_id") != field_id:
            raise RuntimeError(
                "update field options response did not include the expected field"
            )

    def create_form_view(self, table_id: str, view_name: str) -> dict[str, Any]:
        response = self._lark.post(
            self._url(f"/tables/{table_id}/views"),
            body={"view_name": view_name, "view_type": "form"},
        )
        view = self._data(response, "create Form view").get("view")
        if not isinstance(view, dict) or not isinstance(view.get("view_id"), str):
            raise RuntimeError("create Form view response did not include view_id")
        return view

    def rename_table(self, table_id: str, name: str) -> dict[str, Any]:
        request = getattr(self._lark, "_request", None)
        if not callable(request):
            raise RuntimeError("configured Lark client does not support PATCH metadata requests")
        response = request("PATCH", self._url(f"/tables/{table_id}"), body={"name": name})
        self._data(response, "rename table")
        return {"table_id": table_id, "name": name}

    def get_form_metadata(self, table_id: str, form_id: str) -> dict[str, Any]:
        response = self._lark.get(
            self._url(f"/tables/{table_id}/forms/{form_id}")
        )
        data = self._data(response, "get form metadata")
        form = data.get("form", data)
        if not isinstance(form, dict):
            raise RuntimeError("get form metadata response did not include form metadata")
        return form

    def set_form_shared(
        self,
        table_id: str,
        form_id: str,
        shared: bool,
    ) -> None:
        request = getattr(self._lark, "_request", None)
        if not callable(request):
            raise RuntimeError(
                "configured Lark client does not support PATCH metadata requests"
            )
        response = request(
            "PATCH",
            self._url(f"/tables/{table_id}/forms/{form_id}"),
            body={"shared": shared},
        )
        self._data(response, "update form sharing")

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
    parser.add_argument("--apply", action="store_true", help="apply approved metadata changes")
    parser.add_argument("--confirm", help=f"required with --apply: {CONFIRMATION}")
    parser.add_argument(
        "--activate-two-stage",
        action="store_true",
        help=(
            "activate the separated question and interaction tables; "
            f"requires --apply --confirm {TWO_STAGE_CONFIRMATION}"
        ),
    )
    parser.add_argument(
        "--archive-legacy",
        action="store_true",
        help="rename legacy tables after legacy Forms are retired",
    )
    parser.add_argument(
        "--legacy-forms-retired",
        action="store_true",
        help="acknowledge that legacy public Forms have been retired",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not isinstance(args.base_token, str) or not args.base_token.strip():
        raise SystemExit("--base-token or FDE_PHASE3_BASE_TOKEN is required")
    activate_two_stage = bool(getattr(args, "activate_two_stage", False))
    expected_confirmation = (
        TWO_STAGE_CONFIRMATION if activate_two_stage else CONFIRMATION
    )
    if args.apply and args.confirm != expected_confirmation:
        raise SystemExit(f"--apply requires --confirm {expected_confirmation}")
    if activate_two_stage and getattr(args, "archive_legacy", False):
        raise SystemExit("--activate-two-stage cannot be combined with --archive-legacy")
    if args.archive_legacy and not args.apply:
        raise SystemExit("--archive-legacy requires --apply")
    if args.archive_legacy and not args.legacy_forms_retired:
        raise SystemExit("--archive-legacy requires --legacy-forms-retired")


def _plan_output(plan: Any) -> dict[str, Any]:
    return {
        "create_tables": plan.create_table_names,
        "create_fields": [
            {"table": field.table_name, "field": field.field.name}
            for field in plan.create_initial_fields
        ],
        "create_link_fields": [
            {
                "table": link.table_name,
                "field": link.field_name,
                "target_table": link.target_table_name,
            }
            for link in plan.create_link_fields
        ],
        "create_form_views": plan.create_form_names,
        "archive_tables_after_form_retirement": plan.archive_table_names,
    }


def _two_stage_plan_output(plan: Any) -> dict[str, Any]:
    return {
        "mode": "two_stage_dry_run",
        "canonical_tables": plan.canonical_table_names,
        "rename_tables": [
            {"from": source, "to": target}
            for source, target in plan.renamed_tables
        ],
        "create_fields": [
            {"table": table_name, "fields": fields}
            for table_name, fields in plan.added_fields.items()
            if fields
        ],
        "update_fields": [
            {"table": table_name, "fields": fields}
            for table_name, fields in plan.updated_fields.items()
            if fields
        ],
        "forms_to_close": [
            {"table": table_name, "form_id": form_id}
            for table_name, form_id in plan.forms_to_close
        ],
    }


def _two_stage_receipt_output(receipt: Any) -> dict[str, Any]:
    return {
        "mode": "two_stage_activated",
        "canonical_tables": receipt.canonical_table_names,
        "renamed_tables": [
            {"from": source, "to": target}
            for source, target in receipt.renamed_tables
        ],
        "added_fields": receipt.added_fields,
        "updated_fields": receipt.updated_fields,
        "read_back": receipt.read_back,
    }


def main() -> int:
    args = _args()
    validate_args(args)
    _load_env(Path(args.secret_file))
    client = FeishuSchemaClient(_load_lark_client(args.base_token), args.base_token)

    if args.activate_two_stage:
        migration = TwoStageMigration(client)
        specs = two_stage_canonical_tables()
        if not args.apply:
            output = _two_stage_plan_output(
                migration.plan_activation(canonical_tables=specs)
            )
        else:
            output = _two_stage_receipt_output(
                migration.activate(canonical_tables=specs, confirmed=True)
            )
        print(json.dumps(output, ensure_ascii=False))
        return 0

    reconciler = BitableReconciler(client)

    if not args.apply:
        print(json.dumps({"mode": "dry_run", **_plan_output(reconciler.plan())}, ensure_ascii=False))
        return 0

    receipt = reconciler.apply(confirmed=True)
    output: dict[str, Any] = {
        "mode": "applied",
        "created_tables": receipt.created_table_names,
        "created_fields": [
            {"table": field.table_name, "field": field.field.name}
            for field in receipt.created_initial_fields
        ],
        "created_link_fields": [
            {"table": link.table_name, "field": link.field_name}
            for link in receipt.created_link_fields
        ],
        "created_form_views": receipt.created_form_names,
    }
    if args.archive_legacy:
        archived = reconciler.archive_legacy_tables(
            confirmed=True,
            legacy_forms_retired=True,
        )
        output["archived_tables"] = archived.archived_table_names
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

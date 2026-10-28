from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from services.fde_phase3_archive_cleanup import AutomationInspection
from services.fde_phase3_two_stage_migration import (
    DEFAULT_TABLE_NAME,
    DEFAULT_TABLE_FIELD_SIGNATURE,
    QUESTION_ARCHIVE_NAME,
    RESULT_ARCHIVE_NAME,
    TwoStageMigration,
    TwoStageMigrationSafetyError,
)
from services.fde_phase3_two_stage_schema import canonical_tables


SUPPORT_TABLES = (
    "第三期专家",
    "第三期审核与反馈",
    "第三期导出与回执",
)


class FakeMigrationClient:
    def __init__(
        self,
        table_names: tuple[str, ...],
        *,
        fields_by_name: dict[str, tuple[tuple[str, int], ...]] | None = None,
        options_by_name: dict[str, dict[str, tuple[str, ...]]] | None = None,
        shared_form_names: frozenset[str] = frozenset(),
        automation_by_name: dict[str, AutomationInspection] | None = None,
    ) -> None:
        self._tables = [
            {"table_id": f"tbl_{index}", "name": name}
            for index, name in enumerate(table_names, start=1)
        ]
        self._fields_by_name = fields_by_name or {}
        self._options_by_name = options_by_name or {}
        self._link_targets_by_name: dict[str, dict[str, str]] = {}
        self._shared_form_ids = {
            str(table["table_id"])
            for table in self._tables
            if table["name"] in shared_form_names
        }
        self._automation_by_name = automation_by_name or {}
        self.deleted_table_ids: list[str] = []
        self.renamed_tables: list[tuple[str, str]] = []
        self.created_fields: list[tuple[str, str]] = []
        self.updated_fields: list[tuple[str, str]] = []
        self.sharing_updates: list[tuple[str, str, bool]] = []
        self.record_methods_called = False

    def list_tables(self) -> list[dict[str, str]]:
        return list(self._tables)

    def list_fields(self, table_id: str) -> list[dict[str, object]]:
        table_name = self._table_name(table_id)
        fields = self._fields_by_name.get(table_name, ())
        result = []
        table_options = self._options_by_name.get(table_name, {})
        for index, (name, field_type) in enumerate(fields, start=1):
            field: dict[str, object] = {
                "field_id": f"fld_{index}",
                "field_name": name,
                "type": field_type,
            }
            if name in table_options:
                field["property"] = {
                    "options": [
                        {"name": option} for option in table_options[name]
                    ]
                }
            target_id = self._link_targets_by_name.get(table_name, {}).get(name)
            if target_id is not None:
                field["property"] = {
                    "multiple": False,
                    "table_id": target_id,
                }
            result.append(field)
        return result

    def list_views(self, table_id: str) -> list[dict[str, str]]:
        if table_id in self._shared_form_ids:
            return [{"view_id": f"vew_{table_id}", "view_type": "form"}]
        return []

    def get_form_metadata(self, table_id: str, form_id: str) -> dict[str, bool]:
        assert form_id == f"vew_{table_id}"
        return {"shared": table_id in self._shared_form_ids}

    def inspect_automation(self, table_id: str) -> AutomationInspection:
        return self._automation_by_name.get(
            self._table_name(table_id),
            AutomationInspection(checked=True, active_binding_names=()),
        )

    def delete_table(self, table_id: str) -> None:
        self.deleted_table_ids.append(table_id)
        self._tables = [table for table in self._tables if table["table_id"] != table_id]

    def rename_table(self, table_id: str, new_name: str) -> None:
        old_name = self._table_name(table_id)
        self.renamed_tables.append((old_name, new_name))
        for table in self._tables:
            if table["table_id"] == table_id:
                table["name"] = new_name
        if old_name in self._fields_by_name:
            self._fields_by_name[new_name] = self._fields_by_name.pop(old_name)
        if old_name in self._options_by_name:
            self._options_by_name[new_name] = self._options_by_name.pop(old_name)
        if old_name in self._link_targets_by_name:
            self._link_targets_by_name[new_name] = self._link_targets_by_name.pop(old_name)

    def create_field(
        self,
        table_id: str,
        *,
        field_name: str,
        field_type: int,
        options: tuple[str, ...],
        link_target: str | None,
    ) -> None:
        table_name = self._table_name(table_id)
        current = self._fields_by_name.get(table_name, ())
        self._fields_by_name[table_name] = current + ((field_name, field_type),)
        if options:
            self._options_by_name.setdefault(table_name, {})[field_name] = options
        if link_target:
            target_name = table_name if link_target == "self" else link_target
            target_id = next(
                str(table["table_id"])
                for table in self._tables
                if table["name"] == target_name
            )
            self._link_targets_by_name.setdefault(table_name, {})[
                field_name
            ] = target_id
        self.created_fields.append((table_name, field_name))

    def update_field_options(
        self,
        table_id: str,
        *,
        field_id: str,
        field_name: str,
        field_type: int,
        options: tuple[str, ...],
    ) -> None:
        table_name = self._table_name(table_id)
        self._options_by_name.setdefault(table_name, {})[field_name] = options
        self.updated_fields.append((table_name, field_name))

    def set_form_shared(self, table_id: str, form_id: str, shared: bool) -> None:
        table_name = self._table_name(table_id)
        self.sharing_updates.append((table_name, form_id, shared))
        if not shared:
            self._shared_form_ids.discard(table_id)

    def _table_name(self, table_id: str) -> str:
        for table in self._tables:
            if table["table_id"] == table_id:
                return str(table["name"])
        raise AssertionError(f"unknown table: {table_id}")


def _table_names(*extra: str) -> tuple[str, ...]:
    return SUPPORT_TABLES + (DEFAULT_TABLE_NAME, QUESTION_ARCHIVE_NAME, RESULT_ARCHIVE_NAME) + extra


def _default_fields() -> dict[str, tuple[tuple[str, int], ...]]:
    return {DEFAULT_TABLE_NAME: DEFAULT_TABLE_FIELD_SIGNATURE}


def test_inventory_preserves_default_table_and_reuses_archives() -> None:
    client = FakeMigrationClient(_table_names(), fields_by_name=_default_fields())

    inventory = TwoStageMigration(client).inventory()

    assert inventory.default_table_deletable is False
    assert inventory.reusable_archive_names == (QUESTION_ARCHIVE_NAME, RESULT_ARCHIVE_NAME)
    assert inventory.table_names == tuple(sorted(_table_names()))
    assert client.deleted_table_ids == []
    assert client.record_methods_called is False


def test_inventory_rejects_default_table_schema_drift() -> None:
    client = FakeMigrationClient(
        _table_names(),
        fields_by_name={DEFAULT_TABLE_NAME: (("文本", 1),)},
    )

    with pytest.raises(TwoStageMigrationSafetyError, match="default table schema"):
        TwoStageMigration(client).inventory()

    assert client.deleted_table_ids == []


def test_inventory_rejects_shared_or_automated_default_table() -> None:
    shared_client = FakeMigrationClient(
        _table_names(),
        fields_by_name=_default_fields(),
        shared_form_names=frozenset({DEFAULT_TABLE_NAME}),
    )
    with pytest.raises(TwoStageMigrationSafetyError, match="shared Form"):
        TwoStageMigration(shared_client).inventory()

    automated_client = FakeMigrationClient(
        _table_names(),
        fields_by_name=_default_fields(),
        automation_by_name={
            DEFAULT_TABLE_NAME: AutomationInspection(
                checked=True,
                active_binding_names=("default-table-automation",),
            )
        },
    )
    with pytest.raises(TwoStageMigrationSafetyError, match="active automation"):
        TwoStageMigration(automated_client).inventory()


def test_default_table_deletion_is_disabled_even_with_confirmation() -> None:
    client = FakeMigrationClient(_table_names(), fields_by_name=_default_fields())
    migration = TwoStageMigration(client)

    with pytest.raises(TwoStageMigrationSafetyError, match="disabled"):
        migration.delete_default_table(confirmed=False)
    with pytest.raises(TwoStageMigrationSafetyError, match="disabled"):
        migration.delete_default_table(confirmed=True)
    assert client.deleted_table_ids == []


def test_inventory_requires_support_tables_and_both_reuse_candidates() -> None:
    missing_support = tuple(name for name in _table_names() if name != "第三期审核与反馈")
    with pytest.raises(TwoStageMigrationSafetyError, match="support table"):
        TwoStageMigration(
            FakeMigrationClient(missing_support, fields_by_name=_default_fields())
        ).inventory()

    missing_archive = tuple(name for name in _table_names() if name != RESULT_ARCHIVE_NAME)
    with pytest.raises(TwoStageMigrationSafetyError, match="reuse candidate"):
        TwoStageMigration(
            FakeMigrationClient(missing_archive, fields_by_name=_default_fields())
        ).inventory()


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "prune_phase3_archives.py"


def _load_cleanup_cli():
    module_name = "phase3_two_stage_cleanup_cli_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_cli_exposes_no_default_table_deletion_mode() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        cwd=SCRIPT_PATH.parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--delete-default-table" not in result.stdout
    assert "FDE_PHASE3_DELETE_DEFAULT_TABLE" not in result.stdout

    module = _load_cleanup_cli()
    with pytest.raises(SystemExit, match="disabled"):
        module.validate_args(
            argparse.Namespace(
                base_token="base-safe",
                secret_file="unused",
                automation_state="verified-none",
                apply=True,
                confirm="FDE_PHASE3_DELETE_ARCHIVES",
                delete_default_table=True,
            )
        )


def test_activation_requires_confirmation_and_never_deletes_tables() -> None:
    client = FakeMigrationClient(_table_names(), fields_by_name=_default_fields())
    migration = TwoStageMigration(client)

    with pytest.raises(TwoStageMigrationSafetyError, match="activation confirmation"):
        migration.activate(canonical_tables=canonical_tables(), confirmed=False)

    assert client.deleted_table_ids == []
    assert client.renamed_tables == []


def test_activation_reuses_archives_adds_missing_fields_and_reads_back() -> None:
    client = FakeMigrationClient(
        _table_names("第三期任务与交互提交"),
        fields_by_name=_default_fields(),
        shared_form_names=frozenset({QUESTION_ARCHIVE_NAME, RESULT_ARCHIVE_NAME}),
    )

    receipt = TwoStageMigration(client).activate(
        canonical_tables=canonical_tables(),
        confirmed=True,
    )

    assert (QUESTION_ARCHIVE_NAME, "第三期题目预审") in client.renamed_tables
    assert (RESULT_ARCHIVE_NAME, "第三期交互成果") in client.renamed_tables
    assert ("第三期任务与交互提交", "归档_20260729_第三期任务与交互提交") in client.renamed_tables
    assert client.deleted_table_ids == []
    assert set(receipt.canonical_table_names) == {
        "第三期专家",
        "第三期题目预审",
        "第三期交互成果",
        "第三期审核与反馈",
        "第三期导出与回执",
    }
    assert "逐轮评价JSON" in receipt.added_fields["第三期交互成果"]
    assert "飞书open_id" in receipt.added_fields["第三期专家"]
    assert all(shared is False for _, _, shared in client.sharing_updates)
    assert receipt.read_back is True


def test_activation_stops_when_form_share_update_cannot_be_read_back() -> None:
    class NonPersistingFormClient(FakeMigrationClient):
        def set_form_shared(self, table_id: str, form_id: str, shared: bool) -> None:
            self.sharing_updates.append((self._table_name(table_id), form_id, shared))

    client = NonPersistingFormClient(
        _table_names("第三期任务与交互提交"),
        fields_by_name=_default_fields(),
        shared_form_names=frozenset({QUESTION_ARCHIVE_NAME}),
    )

    with pytest.raises(TwoStageMigrationSafetyError, match="sharing read-back"):
        TwoStageMigration(client).activate(
            canonical_tables=canonical_tables(),
            confirmed=True,
        )

    assert client.sharing_updates
    assert client.renamed_tables == []
    assert client.deleted_table_ids == []


def test_activation_repairs_option_drift_and_closes_archived_forms() -> None:
    fields = _default_fields()
    fields["第三期审核与反馈"] = (
        ("审核编号", 1),
        ("审核来源", 3),
        ("P0状态", 3),
    )
    client = FakeMigrationClient(
        _table_names("第三期任务与交互提交", "归档_20260723_第三期专家信息"),
        fields_by_name=fields,
        options_by_name={
            "第三期审核与反馈": {
                "审核来源": ("自动QC", "甲方反馈", "系统"),
                "P0状态": ("待运行", "建议进入甲方队列", "需返修", "阻断"),
            }
        },
        shared_form_names=frozenset({"归档_20260723_第三期专家信息"}),
    )
    migration = TwoStageMigration(client)

    plan = migration.plan_activation(canonical_tables=canonical_tables())

    assert plan.updated_fields["第三期审核与反馈"] == ("审核来源", "P0状态")
    assert {
        table_name for table_name, _ in plan.forms_to_close
    } == {"归档_20260723_第三期专家信息"}

    receipt = migration.activate(canonical_tables=canonical_tables(), confirmed=True)

    assert receipt.updated_fields["第三期审核与反馈"] == ("审核来源", "P0状态")
    assert client.updated_fields == [
        ("第三期审核与反馈", "审核来源"),
        ("第三期审核与反馈", "P0状态"),
    ]
    assert client._shared_form_ids == set()
    assert receipt.read_back is True

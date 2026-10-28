from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from services.fde_phase3_archive_cleanup import (
    ARCHIVE_PREFIX,
    CANONICAL_TABLE_NAMES,
    ArchiveCleanup,
    ArchiveCleanupSafetyError,
    AutomationInspection,
)


class FakeArchiveClient:
    def __init__(
        self,
        table_names: tuple[str, ...],
        *,
        shared_form_tables: frozenset[str] = frozenset(),
        automation_by_name: dict[str, AutomationInspection] | None = None,
    ) -> None:
        self._tables = [
            {"table_id": f"tbl_{index}", "name": name}
            for index, name in enumerate(table_names, start=1)
        ]
        self._shared_form_tables = shared_form_tables
        self._automation_by_name = automation_by_name or {}
        self.deleted_table_ids: list[str] = []
        self.list_table_calls = 0

    def list_tables(self) -> list[dict[str, str]]:
        self.list_table_calls += 1
        return list(self._tables)

    def list_views(self, table_id: str) -> list[dict[str, str]]:
        table_name = self._table_name(table_id)
        if table_name in self._shared_form_tables:
            return [{"view_id": f"vew_{table_id}", "view_type": "form"}]
        return []

    def get_form_metadata(self, table_id: str, form_id: str) -> dict[str, bool]:
        assert form_id == f"vew_{table_id}"
        return {"shared": self._table_name(table_id) in self._shared_form_tables}

    def inspect_automation(self, table_id: str) -> AutomationInspection:
        return self._automation_by_name.get(
            self._table_name(table_id),
            AutomationInspection(checked=True, active_binding_names=()),
        )

    def delete_table(self, table_id: str) -> None:
        self.deleted_table_ids.append(table_id)
        self._tables = [table for table in self._tables if table["table_id"] != table_id]

    def _table_name(self, table_id: str) -> str:
        for table in self._tables:
            if table["table_id"] == table_id:
                return table["name"]
        raise AssertionError(f"unknown table {table_id}")


def _tables(*archive_names: str) -> tuple[str, ...]:
    return tuple(sorted(CANONICAL_TABLE_NAMES)) + archive_names


def test_cleanup_plan_selects_only_archived_tables_and_never_deletes_in_dry_run() -> None:
    archive_names = (
        f"{ARCHIVE_PREFIX}外部题目提交",
        f"{ARCHIVE_PREFIX}专家申请",
    )
    client = FakeArchiveClient(_tables(*archive_names))

    plan = ArchiveCleanup(client).plan()

    assert plan.deletable_table_names == archive_names
    assert plan.remaining_table_names == tuple(sorted(CANONICAL_TABLE_NAMES))
    assert client.deleted_table_ids == []


def test_cleanup_refuses_missing_canonical_or_unexpected_tables() -> None:
    missing_canonical = tuple(sorted(CANONICAL_TABLE_NAMES - {"第三期专家"}))
    with pytest.raises(ArchiveCleanupSafetyError, match="canonical"):
        ArchiveCleanup(FakeArchiveClient(missing_canonical)).plan()

    with pytest.raises(ArchiveCleanupSafetyError, match="unexpected"):
        ArchiveCleanup(FakeArchiveClient(_tables("临时任务表"))).plan()


def test_cleanup_refuses_archive_with_a_shared_form() -> None:
    archive_name = f"{ARCHIVE_PREFIX}第三期题目预审"
    client = FakeArchiveClient(
        _tables(archive_name),
        shared_form_tables=frozenset({archive_name}),
    )

    with pytest.raises(ArchiveCleanupSafetyError, match="shared Form"):
        ArchiveCleanup(client).plan()

    assert client.deleted_table_ids == []


@pytest.mark.parametrize(
    "inspection, message",
    [
        (AutomationInspection(checked=False, active_binding_names=()), "automation inspection"),
        (AutomationInspection(checked=True, active_binding_names=("legacy-runner",)), "active automation"),
    ],
)
def test_cleanup_refuses_unverified_or_active_automation(
    inspection: AutomationInspection,
    message: str,
) -> None:
    archive_name = f"{ARCHIVE_PREFIX}交互尝试"
    client = FakeArchiveClient(
        _tables(archive_name),
        automation_by_name={archive_name: inspection},
    )

    with pytest.raises(ArchiveCleanupSafetyError, match=message):
        ArchiveCleanup(client).plan()

    assert client.deleted_table_ids == []


def test_cleanup_apply_requires_confirmation_and_readbacks_after_each_delete() -> None:
    archive_names = (
        f"{ARCHIVE_PREFIX}外部题目提交",
        f"{ARCHIVE_PREFIX}专家申请",
    )
    client = FakeArchiveClient(_tables(*archive_names))
    cleanup = ArchiveCleanup(client)

    with pytest.raises(ArchiveCleanupSafetyError, match="confirmation"):
        cleanup.apply(confirmed=False)
    assert client.deleted_table_ids == []

    receipt = cleanup.apply(confirmed=True)

    assert receipt.deleted_table_names == archive_names
    assert receipt.remaining_table_names == tuple(sorted(CANONICAL_TABLE_NAMES))
    assert len(client.deleted_table_ids) == len(archive_names)
    assert client.list_table_calls >= 1 + (2 * len(archive_names))


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "prune_phase3_archives.py"


def _load_cli_module():
    module_name = "phase3_archive_cleanup_cli_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_cleanup_cli_defaults_to_dry_run_and_requires_explicit_delete_confirmation() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        cwd=SCRIPT_PATH.parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--apply" in result.stdout
    assert "FDE_PHASE3_DELETE_ARCHIVES" in result.stdout
    assert "--automation-state" in result.stdout
    assert "--delete-default-table" not in result.stdout

    module = _load_cli_module()
    with pytest.raises(SystemExit, match="FDE_PHASE3_DELETE_ARCHIVES"):
        module.validate_args(
            argparse.Namespace(
                base_token="base-safe",
                secret_file="unused",
                automation_state="verified-none",
                apply=True,
                confirm="wrong",
            )
        )
    with pytest.raises(SystemExit, match="automation-state"):
        module.validate_args(
            argparse.Namespace(
                base_token="base-safe",
                secret_file="unused",
                automation_state=None,
                apply=True,
                confirm="FDE_PHASE3_DELETE_ARCHIVES",
            )
        )
    module.validate_args(
        argparse.Namespace(
            base_token="base-safe",
            secret_file="unused",
            automation_state=None,
            apply=False,
            confirm=None,
        )
    )

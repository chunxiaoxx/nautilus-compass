"""Fail-closed removal of obsolete Phase 3 Bitable tables.

Only metadata is inspected. The planner never reads records, attachments, or
Form responses, and its public result contains table names only.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol


ARCHIVE_PREFIX = "归档_20260723_"
CANONICAL_TABLE_NAMES = frozenset(
    {
        "第三期专家",
        "第三期任务与交互提交",
        "第三期审核与反馈",
        "第三期导出与回执",
    }
)


class ArchiveCleanupSafetyError(ValueError):
    """Raised before an archive cleanup can mutate a remote Base."""


@dataclass(frozen=True)
class AutomationInspection:
    """A metadata-only assertion about one table's automation bindings."""

    checked: bool
    active_binding_names: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.checked, bool):
            raise ValueError("automation inspection checked must be a boolean")
        if any(not isinstance(name, str) or not name.strip() for name in self.active_binding_names):
            raise ValueError("automation binding names must be non-empty strings")


class ArchiveCleanupClient(Protocol):
    """Only the metadata operations required by the cleanup state machine."""

    def list_tables(self) -> Sequence[Mapping[str, object]]: ...

    def list_views(self, table_id: str) -> Sequence[Mapping[str, object]]: ...

    def get_form_metadata(self, table_id: str, form_id: str) -> Mapping[str, object]: ...

    def inspect_automation(self, table_id: str) -> AutomationInspection: ...

    def delete_table(self, table_id: str) -> None: ...


@dataclass(frozen=True)
class ArchiveCleanupPlan:
    """Safe dry-run output. It deliberately does not retain table identities."""

    deletable_table_names: tuple[str, ...]
    remaining_table_names: tuple[str, ...]


@dataclass(frozen=True)
class ArchiveCleanupReceipt:
    """Safe post-operation output, with names but no records or identifiers."""

    deleted_table_names: tuple[str, ...]
    remaining_table_names: tuple[str, ...]


@dataclass(frozen=True)
class _Table:
    table_id: str
    name: str


class ArchiveCleanup:
    """Delete only verified obsolete tables, with a read-back after every delete."""

    def __init__(self, client: ArchiveCleanupClient) -> None:
        self._client = client

    def plan(self) -> ArchiveCleanupPlan:
        tables = self._load_tables()
        self._assert_expected_table_set(tables)
        archived = tuple(table for table in tables if table.name.startswith(ARCHIVE_PREFIX))
        for table in archived:
            self._assert_table_dependencies_clear(table)
        return ArchiveCleanupPlan(
            deletable_table_names=tuple(table.name for table in archived),
            remaining_table_names=tuple(sorted(CANONICAL_TABLE_NAMES)),
        )

    def apply(self, *, confirmed: bool) -> ArchiveCleanupReceipt:
        if confirmed is not True:
            raise ArchiveCleanupSafetyError("explicit cleanup confirmation is required")

        plan = self.plan()
        expected_names = set(CANONICAL_TABLE_NAMES) | set(plan.deletable_table_names)
        for table_name in plan.deletable_table_names:
            current = self._table_lookup(self._load_tables())
            if set(current) != expected_names or table_name not in current:
                raise ArchiveCleanupSafetyError("table set changed before deletion")
            target = current[table_name]
            self._assert_table_dependencies_clear(target)
            self._client.delete_table(target.table_id)
            expected_names.remove(table_name)
            after = self._table_lookup(self._load_tables())
            if set(after) != expected_names:
                raise ArchiveCleanupSafetyError("unexpected table set after deletion")

        if expected_names != set(CANONICAL_TABLE_NAMES):
            raise ArchiveCleanupSafetyError("cleanup did not end at the canonical table set")
        return ArchiveCleanupReceipt(
            deleted_table_names=plan.deletable_table_names,
            remaining_table_names=tuple(sorted(expected_names)),
        )

    def _load_tables(self) -> tuple[_Table, ...]:
        raw_tables = self._client.list_tables()
        if isinstance(raw_tables, (str, bytes)) or not isinstance(raw_tables, Sequence):
            raise ArchiveCleanupSafetyError("table metadata must be a sequence")

        tables: list[_Table] = []
        seen_ids: set[str] = set()
        seen_names: set[str] = set()
        for raw_table in raw_tables:
            if not isinstance(raw_table, Mapping):
                raise ArchiveCleanupSafetyError("table metadata must contain mappings")
            table_id = self._compact_string(raw_table.get("table_id"), "table identity")
            name = self._compact_string(raw_table.get("name"), "table name")
            if table_id in seen_ids or name in seen_names:
                raise ArchiveCleanupSafetyError("duplicate table metadata")
            seen_ids.add(table_id)
            seen_names.add(name)
            tables.append(_Table(table_id=table_id, name=name))
        return tuple(tables)

    def _assert_expected_table_set(self, tables: tuple[_Table, ...]) -> None:
        names = {table.name for table in tables}
        missing = CANONICAL_TABLE_NAMES - names
        if missing:
            raise ArchiveCleanupSafetyError("canonical table set is incomplete")
        unexpected = names - CANONICAL_TABLE_NAMES - {
            name for name in names if name.startswith(ARCHIVE_PREFIX)
        }
        if unexpected:
            raise ArchiveCleanupSafetyError("unexpected non-archive table is present")

    def _assert_table_dependencies_clear(self, table: _Table) -> None:
        self._assert_no_shared_form(table)
        inspection = self._client.inspect_automation(table.table_id)
        if not isinstance(inspection, AutomationInspection):
            raise ArchiveCleanupSafetyError("automation inspection is unavailable")
        if not inspection.checked:
            raise ArchiveCleanupSafetyError("automation inspection is not verified")
        if inspection.active_binding_names:
            raise ArchiveCleanupSafetyError("active automation binding blocks deletion")

    def _assert_no_shared_form(self, table: _Table) -> None:
        raw_views = self._client.list_views(table.table_id)
        if isinstance(raw_views, (str, bytes)) or not isinstance(raw_views, Sequence):
            raise ArchiveCleanupSafetyError("view metadata must be a sequence")
        for raw_view in raw_views:
            if not isinstance(raw_view, Mapping):
                raise ArchiveCleanupSafetyError("view metadata must contain mappings")
            view_type = raw_view.get("view_type")
            if not isinstance(view_type, str):
                raise ArchiveCleanupSafetyError("view type is missing")
            if view_type.casefold() != "form":
                continue
            form_id = self._compact_string(raw_view.get("view_id"), "Form identity")
            metadata = self._client.get_form_metadata(table.table_id, form_id)
            if not isinstance(metadata, Mapping) or not isinstance(metadata.get("shared"), bool):
                raise ArchiveCleanupSafetyError("Form metadata is incomplete")
            if metadata["shared"]:
                raise ArchiveCleanupSafetyError("shared Form blocks deletion")

    @staticmethod
    def _table_lookup(tables: tuple[_Table, ...]) -> dict[str, _Table]:
        return {table.name: table for table in tables}

    @staticmethod
    def _compact_string(value: object, label: str) -> str:
        if not isinstance(value, str) or not value or value != value.strip():
            raise ArchiveCleanupSafetyError(f"{label} must be a non-empty compact string")
        return value

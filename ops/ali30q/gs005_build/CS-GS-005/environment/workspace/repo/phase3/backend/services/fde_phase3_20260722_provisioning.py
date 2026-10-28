"""Idempotent provisioning for the verified Phase 3 public intake schema."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from services.fde_phase3_20260722_schema import PUBLIC_FORM_NAMES, TableSpec, public_form_tables


class ProvisionConfirmationError(ValueError):
    """Raised when a caller attempts a remote write without confirmation."""


class SchemaDriftError(ValueError):
    """Raised when an existing source table has an unexpected schema."""


class BitableClient(Protocol):
    def list_tables(self) -> list[dict[str, Any]]: ...

    def list_fields(self, table_id: str) -> list[dict[str, Any]]: ...

    def list_views(self, table_id: str) -> list[dict[str, Any]]: ...

    def create_table(self, name: str, fields: list[dict[str, Any]]) -> dict[str, Any]: ...

    def create_form_view(self, table_id: str, view_name: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ProvisionPlan:
    create_table_names: tuple[str, ...]
    create_form_names: tuple[str, ...]


@dataclass(frozen=True)
class ProvisionReceipt:
    created_table_names: tuple[str, ...]
    created_form_names: tuple[str, ...]
    table_names: tuple[str, ...]


class BitableProvisioner:
    """Creates only missing approved source tables and native Form views."""

    def __init__(self, client: BitableClient) -> None:
        self._client = client

    @staticmethod
    def _source_tables() -> tuple[TableSpec, ...]:
        return public_form_tables()

    @staticmethod
    def _table_lookup(tables: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {str(table["name"]): table for table in tables}

    @staticmethod
    def _expected_schema(table: TableSpec) -> tuple[tuple[str, int], ...]:
        return tuple((field.name, field.field_type) for field in table.fields)

    def _assert_schema_matches(self, table: TableSpec, existing: dict[str, Any]) -> None:
        fields = self._client.list_fields(str(existing["table_id"]))
        actual = tuple((str(field.get("field_name")), int(field.get("type"))) for field in fields)
        expected = self._expected_schema(table)
        if actual != expected:
            raise SchemaDriftError(
                f"table {table.name} schema differs from the approved 20260722 contract"
            )

    def plan(self) -> ProvisionPlan:
        tables = self._table_lookup(self._client.list_tables())
        missing_tables = []
        missing_forms = []
        for table in self._source_tables():
            existing = tables.get(table.name)
            if existing is None:
                missing_tables.append(table.name)
                missing_forms.append(table.form_name)
                continue
            self._assert_schema_matches(table, existing)
            views = self._client.list_views(str(existing["table_id"]))
            if not any(view.get("view_name") == table.form_name for view in views):
                missing_forms.append(table.form_name)
        return ProvisionPlan(tuple(missing_tables), tuple(missing_forms))

    def apply(self, *, confirmed: bool) -> ProvisionReceipt:
        if not confirmed:
            raise ProvisionConfirmationError("remote provisioning requires explicit confirmation")

        initial_plan = self.plan()
        tables = self._table_lookup(self._client.list_tables())
        created_tables: list[str] = []
        for table in self._source_tables():
            if table.name in tables:
                continue
            created = self._client.create_table(table.name, table.feishu_fields())
            tables[table.name] = created
            created_tables.append(table.name)

        created_forms: list[str] = []
        for table in self._source_tables():
            target = tables[table.name]
            views = self._client.list_views(str(target["table_id"]))
            if any(view.get("view_name") == table.form_name for view in views):
                continue
            self._client.create_form_view(str(target["table_id"]), table.form_name)
            created_forms.append(table.form_name)

        final_plan = self.plan()
        if final_plan.create_table_names or final_plan.create_form_names:
            raise RuntimeError("provisioning read-back is incomplete")
        return ProvisionReceipt(
            created_table_names=tuple(created_tables),
            created_form_names=tuple(created_forms),
            table_names=tuple(table.name for table in self._source_tables()),
        )


def expected_public_form_names() -> tuple[str, ...]:
    return PUBLIC_FORM_NAMES

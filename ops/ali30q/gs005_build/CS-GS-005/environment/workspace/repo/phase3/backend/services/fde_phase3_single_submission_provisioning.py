"""Guarded, metadata-only provisioning for the Phase 3 canonical Base.

The reconciler creates the approved schema and native Form views, then reads
back only table, field, and view metadata.  It never accesses Bitable records.
Legacy tables are rename-only and may be archived only after the caller proves
that legacy public Forms have been retired.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from services.fde_phase3_single_submission_schema import FieldSpec, TableSpec, canonical_tables


ARCHIVE_PREFIX = "归档_20260723_"
LEGACY_TABLE_NAMES = (
    "外部题目提交",
    "任务",
    "交互尝试",
    "审核",
    "导出与回执",
    "专家申请",
    "第三期专家信息",
    "第三期题目预审",
    "第三期交互成果",
)


class ProvisionConfirmationError(ValueError):
    """Raised when a remote schema mutation lacks explicit confirmation."""


class SchemaDriftError(ValueError):
    """Raised when canonical metadata differs from the approved contract."""


class LegacyArchiveSafetyError(ValueError):
    """Raised before a legacy table can be renamed while its Form is public."""


class BitableSchemaClient(Protocol):
    """The only metadata operations needed by the reconciler."""

    def list_tables(self) -> list[dict[str, Any]]: ...

    def list_fields(self, table_id: str) -> list[dict[str, Any]]: ...

    def list_views(self, table_id: str) -> list[dict[str, Any]]: ...

    def create_table(self, name: str, fields: list[dict[str, Any]]) -> dict[str, Any]: ...

    def create_field(self, table_id: str, field: dict[str, Any]) -> dict[str, Any]: ...

    def create_link_field(
        self, table_id: str, name: str, target_table_id: str
    ) -> dict[str, Any]: ...

    def create_form_view(self, table_id: str, view_name: str) -> dict[str, Any]: ...

    def rename_table(self, table_id: str, name: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class LinkFieldPlan:
    table_name: str
    field_name: str
    target_table_name: str


@dataclass(frozen=True)
class InitialFieldPlan:
    table_name: str
    field: FieldSpec


@dataclass(frozen=True)
class ReconciliationPlan:
    create_table_names: tuple[str, ...]
    create_initial_fields: tuple[InitialFieldPlan, ...]
    create_link_fields: tuple[LinkFieldPlan, ...]
    create_form_names: tuple[str, ...]
    archive_table_names: tuple[str, ...]


@dataclass(frozen=True)
class ReconciliationReceipt:
    created_table_names: tuple[str, ...]
    created_initial_fields: tuple[InitialFieldPlan, ...]
    created_link_fields: tuple[LinkFieldPlan, ...]
    created_form_names: tuple[str, ...]
    archived_table_names: tuple[str, ...]


class BitableReconciler:
    """Idempotent creator for canonical tables and native Form views."""

    def __init__(self, client: BitableSchemaClient) -> None:
        self._client = client

    @staticmethod
    def _table_lookup(tables: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        lookup: dict[str, dict[str, Any]] = {}
        for table in tables:
            name = table.get("name")
            table_id = table.get("table_id")
            if not isinstance(name, str) or not name.strip():
                raise SchemaDriftError("table name is missing")
            if not isinstance(table_id, str) or not table_id.strip():
                raise SchemaDriftError(f"table identity is missing: {name}")
            if name in lookup:
                raise SchemaDriftError(f"duplicate table name: {name}")
            lookup[name] = table
        return lookup

    @staticmethod
    def _field_lookup(fields: list[dict[str, Any]], table_name: str) -> dict[str, dict[str, Any]]:
        lookup: dict[str, dict[str, Any]] = {}
        for field in fields:
            name = field.get("field_name")
            if not isinstance(name, str) or not name.strip():
                raise SchemaDriftError(f"field name is missing in table {table_name}")
            if name in lookup:
                raise SchemaDriftError(f"duplicate field name in {table_name}: {name}")
            lookup[name] = field
        return lookup

    @staticmethod
    def _link_target_name(table: TableSpec, field: FieldSpec) -> str:
        if field.link_target == "self":
            return table.name
        if not field.link_target:
            raise ValueError(f"field {field.name} is not a link field")
        return field.link_target

    @staticmethod
    def _forms_missing(table: TableSpec, views: list[dict[str, Any]]) -> bool:
        if not table.form_name:
            return False
        matches = [
            view
            for view in views
            if view.get("view_name") == table.form_name and view.get("view_type") == "form"
        ]
        if len(matches) > 1:
            raise SchemaDriftError(f"ambiguous native Form view: {table.form_name}")
        return not matches

    def plan(self) -> ReconciliationPlan:
        tables = self._table_lookup(self._client.list_tables())
        create_tables: list[str] = []
        create_initial_fields: list[InitialFieldPlan] = []
        create_links: list[LinkFieldPlan] = []
        create_forms: list[str] = []

        for table in canonical_tables():
            existing = tables.get(table.name)
            if existing is None:
                create_tables.append(table.name)
                create_links.extend(self._link_plan_for_table(table))
                if table.form_name:
                    create_forms.append(table.form_name)
                continue

            fields = self._field_lookup(
                self._client.list_fields(str(existing["table_id"])), table.name
            )
            self._assert_initial_fields(table, fields, allow_missing=True)
            create_initial_fields.extend(self._missing_initial_fields(table, fields))
            create_links.extend(self._missing_link_fields(table, fields, tables))
            if table.form_name and self._forms_missing(
                table, self._client.list_views(str(existing["table_id"]))
            ):
                create_forms.append(table.form_name)

        archive_names = tuple(name for name in LEGACY_TABLE_NAMES if name in tables)
        return ReconciliationPlan(
            create_table_names=tuple(create_tables),
            create_initial_fields=tuple(create_initial_fields),
            create_link_fields=tuple(create_links),
            create_form_names=tuple(create_forms),
            archive_table_names=archive_names,
        )

    def apply(self, *, confirmed: bool) -> ReconciliationReceipt:
        """Create missing canonical metadata; legacy tables remain untouched."""
        if not confirmed:
            raise ProvisionConfirmationError("remote provisioning requires explicit confirmation")

        self.plan()
        tables = self._table_lookup(self._client.list_tables())
        created_tables: list[str] = []
        for table in canonical_tables():
            if table.name in tables:
                continue
            created = self._client.create_table(
                table.name,
                [field.feishu_field() for field in table.initial_fields],
            )
            table_id = created.get("table_id")
            if not isinstance(table_id, str) or not table_id.strip():
                raise RuntimeError(f"create table did not return an identity: {table.name}")
            tables[table.name] = {"table_id": table_id, "name": table.name}
            created_tables.append(table.name)

        created_initial_fields = self._create_missing_initial_fields(tables)
        created_links = self._create_missing_link_fields(tables)
        self._assert_canonical_schema(tables)

        created_forms: list[str] = []
        for table in canonical_tables():
            if not table.form_name:
                continue
            table_id = str(tables[table.name]["table_id"])
            if self._forms_missing(table, self._client.list_views(table_id)):
                created = self._client.create_form_view(table_id, table.form_name)
                if not isinstance(created.get("view_id"), str) or not created["view_id"].strip():
                    raise RuntimeError(f"create Form view did not return an identity: {table.form_name}")
                created_forms.append(table.form_name)

        self._assert_canonical_schema(self._table_lookup(self._client.list_tables()))
        self._assert_form_views(self._table_lookup(self._client.list_tables()))
        return ReconciliationReceipt(
            created_table_names=tuple(created_tables),
            created_initial_fields=tuple(created_initial_fields),
            created_link_fields=tuple(created_links),
            created_form_names=tuple(created_forms),
            archived_table_names=(),
        )

    def archive_legacy_tables(
        self,
        *,
        confirmed: bool,
        legacy_forms_retired: bool,
    ) -> ReconciliationReceipt:
        """Rename old tables only after the caller has retired legacy public Forms."""
        if not confirmed:
            raise ProvisionConfirmationError("legacy archive requires explicit confirmation")
        if not legacy_forms_retired:
            raise LegacyArchiveSafetyError("legacy Forms must be retired before legacy tables are archived")

        tables = self._table_lookup(self._client.list_tables())
        self._assert_canonical_schema(tables)
        self._assert_form_views(tables)

        archived: list[str] = []
        for legacy_name in LEGACY_TABLE_NAMES:
            table = tables.get(legacy_name)
            if table is None:
                continue
            archived_name = ARCHIVE_PREFIX + legacy_name
            if archived_name in tables:
                raise SchemaDriftError(f"archive destination already exists: {archived_name}")
            self._client.rename_table(str(table["table_id"]), archived_name)
            archived.append(legacy_name)
            tables.pop(legacy_name)
            tables[archived_name] = {"table_id": table["table_id"], "name": archived_name}

        final_tables = self._table_lookup(self._client.list_tables())
        self._assert_canonical_schema(final_tables)
        self._assert_form_views(final_tables)
        if any(name in final_tables for name in archived):
            raise RuntimeError("legacy table archive read-back is incomplete")
        return ReconciliationReceipt((), (), (), (), tuple(archived))

    def _assert_canonical_schema(self, tables: dict[str, dict[str, Any]]) -> None:
        for table in canonical_tables():
            existing = tables.get(table.name)
            if existing is None:
                raise SchemaDriftError(f"canonical table missing: {table.name}")
            fields = self._field_lookup(
                self._client.list_fields(str(existing["table_id"])), table.name
            )
            self._assert_initial_fields(table, fields)
            missing_links = self._missing_link_fields(table, fields, tables)
            if missing_links:
                names = ", ".join(plan.field_name for plan in missing_links)
                raise SchemaDriftError(f"canonical link fields missing: {table.name}/{names}")

    def _assert_form_views(self, tables: dict[str, dict[str, Any]]) -> None:
        for table in canonical_tables():
            if table.form_name and self._forms_missing(
                table, self._client.list_views(str(tables[table.name]["table_id"]))
            ):
                raise SchemaDriftError(f"native Form view missing: {table.form_name}")

    def _assert_initial_fields(
        self,
        table: TableSpec,
        fields: dict[str, dict[str, Any]],
        *,
        allow_missing: bool = False,
    ) -> None:
        expected_names = {field.name for field in table.initial_fields}
        actual_names = set(fields)
        unknown = actual_names - expected_names - {
            field.name for field in table.fields if field.link_target
        }
        missing = expected_names - actual_names
        if unknown or (missing and not allow_missing):
            raise SchemaDriftError(
                f"table {table.name} schema differs: missing={sorted(missing)} unknown={sorted(unknown)}"
            )
        for field in table.initial_fields:
            actual = fields.get(field.name)
            if actual is None:
                continue
            if actual.get("type") != field.field_type:
                raise SchemaDriftError(
                    f"table {table.name} schema differs: field type {field.name}"
                )
            if field.options:
                actual_options = tuple(
                    option.get("name")
                    for option in (actual.get("property") or {}).get("options") or []
                )
                if actual_options != field.options:
                    raise SchemaDriftError(
                        f"table {table.name} schema differs: field options {field.name}"
                    )

    @staticmethod
    def _missing_initial_fields(
        table: TableSpec,
        fields: dict[str, dict[str, Any]],
    ) -> list[InitialFieldPlan]:
        return [
            InitialFieldPlan(table.name, field)
            for field in table.initial_fields
            if field.name not in fields
        ]

    def _create_missing_initial_fields(
        self,
        tables: dict[str, dict[str, Any]],
    ) -> list[InitialFieldPlan]:
        created: list[InitialFieldPlan] = []
        for table in canonical_tables():
            table_id = str(tables[table.name]["table_id"])
            fields = self._field_lookup(self._client.list_fields(table_id), table.name)
            self._assert_initial_fields(table, fields, allow_missing=True)
            for plan in self._missing_initial_fields(table, fields):
                created_field = self._client.create_field(
                    table_id,
                    plan.field.feishu_field(),
                )
                if created_field.get("field_name") != plan.field.name:
                    raise RuntimeError(
                        f"create field returned wrong name: {table.name}/{plan.field.name}"
                    )
                fields[plan.field.name] = created_field
                created.append(plan)
        return created

    def _missing_link_fields(
        self,
        table: TableSpec,
        fields: dict[str, dict[str, Any]],
        tables: dict[str, dict[str, Any]],
    ) -> list[LinkFieldPlan]:
        missing: list[LinkFieldPlan] = []
        for plan in self._link_plan_for_table(table):
            actual = fields.get(plan.field_name)
            if actual is None:
                missing.append(plan)
                continue
            target = tables.get(plan.target_table_name)
            if target is None:
                raise SchemaDriftError(f"link target table missing: {plan.target_table_name}")
            property_data = actual.get("property") or {}
            if (
                actual.get("type") != 18
                or property_data.get("multiple") is not False
                or property_data.get("table_id") != target.get("table_id")
            ):
                raise SchemaDriftError(
                    f"table {table.name} schema differs: link field {plan.field_name}"
                )
        return missing

    def _create_missing_link_fields(
        self,
        tables: dict[str, dict[str, Any]],
    ) -> list[LinkFieldPlan]:
        created: list[LinkFieldPlan] = []
        for table in canonical_tables():
            table_id = str(tables[table.name]["table_id"])
            fields = self._field_lookup(self._client.list_fields(table_id), table.name)
            self._assert_initial_fields(table, fields)
            for link in self._missing_link_fields(table, fields, tables):
                target_id = str(tables[link.target_table_name]["table_id"])
                created_field = self._client.create_link_field(
                    table_id, link.field_name, target_id
                )
                if created_field.get("field_name") != link.field_name:
                    raise RuntimeError(f"create link field returned wrong name: {link.field_name}")
                created.append(link)
                fields[link.field_name] = created_field
        return created

    def _link_plan_for_table(self, table: TableSpec) -> list[LinkFieldPlan]:
        return [
            LinkFieldPlan(table.name, field.name, self._link_target_name(table, field))
            for field in table.fields
            if field.link_target
        ]

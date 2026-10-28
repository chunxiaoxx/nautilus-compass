"""Metadata-only safety gate for the Phase 3 two-stage Base migration."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from services.fde_phase3_archive_cleanup import AutomationInspection
from services.fde_phase3_two_stage_schema import TwoStageTableSpec


DEFAULT_TABLE_NAME = "数据表"
DEFAULT_TABLE_FIELD_SIGNATURE = (
    ("文本", 1),
    ("单选", 3),
    ("日期", 5),
    ("附件", 17),
)
QUESTION_ARCHIVE_NAME = "归档_20260723_第三期题目预审"
RESULT_ARCHIVE_NAME = "归档_20260723_第三期交互成果"
UNIFIED_TABLE_NAME = "第三期任务与交互提交"
UNIFIED_ARCHIVE_NAME = "归档_20260729_第三期任务与交互提交"
REQUIRED_SUPPORT_TABLES = frozenset(
    {"第三期专家", "第三期审核与反馈", "第三期导出与回执"}
)


class TwoStageMigrationSafetyError(ValueError):
    """Raised before a two-stage migration can mutate remote Base metadata."""


class TwoStageMigrationClient(Protocol):
    """The strictly metadata-only client surface used before migration."""

    def list_tables(self) -> Sequence[Mapping[str, object]]: ...

    def list_fields(self, table_id: str) -> Sequence[Mapping[str, object]]: ...

    def list_views(self, table_id: str) -> Sequence[Mapping[str, object]]: ...

    def get_form_metadata(self, table_id: str, form_id: str) -> Mapping[str, object]: ...

    def inspect_automation(self, table_id: str) -> AutomationInspection: ...

    def delete_table(self, table_id: str) -> None: ...

    def rename_table(self, table_id: str, new_name: str) -> None: ...

    def create_field(
        self,
        table_id: str,
        *,
        field_name: str,
        field_type: int,
        options: tuple[str, ...],
        link_target: str | None,
    ) -> None: ...

    def update_field_options(
        self,
        table_id: str,
        *,
        field_id: str,
        field_name: str,
        field_type: int,
        options: tuple[str, ...],
    ) -> None: ...

    def set_form_shared(self, table_id: str, form_id: str, shared: bool) -> None: ...


@dataclass(frozen=True)
class TwoStageMigrationInventory:
    """Safe inventory result containing names only, never table identifiers."""

    table_names: tuple[str, ...]
    reusable_archive_names: tuple[str, ...]
    default_table_deletable: bool


@dataclass(frozen=True)
class DefaultTableDeletionReceipt:
    """Read-back receipt for the explicitly authorized default-table deletion."""

    deleted_table_name: str
    remaining_table_names: tuple[str, ...]


@dataclass(frozen=True)
class TwoStageActivationPlan:
    """Read-only description of every metadata change required for activation."""

    canonical_table_names: tuple[str, ...]
    renamed_tables: tuple[tuple[str, str], ...]
    added_fields: Mapping[str, tuple[str, ...]]
    updated_fields: Mapping[str, tuple[str, ...]]
    forms_to_close: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class TwoStageActivationReceipt:
    """Read-back receipt for the non-destructive two-stage activation."""

    canonical_table_names: tuple[str, ...]
    renamed_tables: tuple[tuple[str, str], ...]
    added_fields: Mapping[str, tuple[str, ...]]
    updated_fields: Mapping[str, tuple[str, ...]]
    read_back: bool


@dataclass(frozen=True)
class _Table:
    table_id: str
    name: str


class TwoStageMigration:
    """Inventory reusable schema and delete only the verified default table."""

    def __init__(self, client: TwoStageMigrationClient) -> None:
        self._client = client

    def inventory(self) -> TwoStageMigrationInventory:
        tables = self._load_tables()
        table_by_name = {table.name: table for table in tables}
        self._assert_support_tables(table_by_name)
        self._assert_reuse_candidates(table_by_name)
        default_table = table_by_name.get(DEFAULT_TABLE_NAME)
        if default_table is None:
            raise TwoStageMigrationSafetyError("default table is missing")
        self._assert_default_table_is_safe(default_table)
        return TwoStageMigrationInventory(
            table_names=tuple(sorted(table_by_name)),
            reusable_archive_names=(QUESTION_ARCHIVE_NAME, RESULT_ARCHIVE_NAME),
            default_table_deletable=False,
        )

    def plan_activation(
        self,
        *,
        canonical_tables: Sequence[TwoStageTableSpec],
    ) -> TwoStageActivationPlan:
        """Build the two-stage activation plan without issuing remote writes."""

        specs = tuple(canonical_tables)
        if not specs or any(not isinstance(spec, TwoStageTableSpec) for spec in specs):
            raise TwoStageMigrationSafetyError("canonical table specs are invalid")
        expected_names = tuple(spec.name for spec in specs)
        if len(set(expected_names)) != len(expected_names):
            raise TwoStageMigrationSafetyError("canonical table specs contain duplicates")

        current_tables = {table.name: table for table in self._load_tables()}
        self._assert_support_tables(current_tables)
        simulated_tables = dict(current_tables)
        renamed: list[tuple[str, str]] = []

        for archive_name, target_name in (
            (QUESTION_ARCHIVE_NAME, "第三期题目预审"),
            (RESULT_ARCHIVE_NAME, "第三期交互成果"),
        ):
            if target_name in simulated_tables and archive_name in simulated_tables:
                raise TwoStageMigrationSafetyError(
                    f"both active and archived tables exist: {target_name}"
                )
            if target_name in simulated_tables:
                continue
            source = simulated_tables.get(archive_name)
            if source is None:
                raise TwoStageMigrationSafetyError(
                    f"required reuse candidate is missing: {archive_name}"
                )
            renamed.append((archive_name, target_name))
            simulated_tables.pop(archive_name)
            simulated_tables[target_name] = _Table(
                table_id=source.table_id,
                name=target_name,
            )

        if UNIFIED_TABLE_NAME in simulated_tables:
            if UNIFIED_ARCHIVE_NAME in simulated_tables:
                raise TwoStageMigrationSafetyError("unified archive name already exists")
            source = simulated_tables.pop(UNIFIED_TABLE_NAME)
            renamed.append((UNIFIED_TABLE_NAME, UNIFIED_ARCHIVE_NAME))
            simulated_tables[UNIFIED_ARCHIVE_NAME] = _Table(
                table_id=source.table_id,
                name=UNIFIED_ARCHIVE_NAME,
            )

        if not set(expected_names).issubset(simulated_tables):
            raise TwoStageMigrationSafetyError(
                "canonical tables are missing after planned rename"
            )

        added_fields: dict[str, tuple[str, ...]] = {}
        updated_fields: dict[str, tuple[str, ...]] = {}
        for spec in specs:
            table = simulated_tables[spec.name]
            existing = self._field_lookup(table.table_id)
            added: list[str] = []
            updated: list[str] = []
            for field in spec.fields:
                actual = existing.get(field.name)
                if actual is None:
                    added.append(field.name)
                    continue
                options_match = self._assert_field_shape(
                    table_name=spec.name,
                    field=field,
                    actual=actual,
                    tables=simulated_tables,
                    allow_option_drift=True,
                )
                if not options_match:
                    updated.append(field.name)
            added_fields[spec.name] = tuple(added)
            updated_fields[spec.name] = tuple(updated)

        forms_to_close: list[tuple[str, str]] = []
        for table in current_tables.values():
            if not (
                table.name.startswith("归档_")
                or table.name
                in {"第三期题目预审", "第三期交互成果", UNIFIED_TABLE_NAME}
            ):
                continue
            forms_to_close.extend(
                (table.name, form_id)
                for form_id in self._shared_form_ids(table)
            )

        return TwoStageActivationPlan(
            canonical_table_names=tuple(sorted(expected_names)),
            renamed_tables=tuple(renamed),
            added_fields=added_fields,
            updated_fields=updated_fields,
            forms_to_close=tuple(forms_to_close),
        )

    def activate(
        self,
        *,
        canonical_tables: Sequence[TwoStageTableSpec],
        confirmed: bool,
    ) -> TwoStageActivationReceipt:
        """Activate archived two-stage tables without deleting any table or record."""

        if confirmed is not True:
            raise TwoStageMigrationSafetyError(
                "explicit activation confirmation is required"
            )
        specs = tuple(canonical_tables)
        if not specs or any(not isinstance(spec, TwoStageTableSpec) for spec in specs):
            raise TwoStageMigrationSafetyError("canonical table specs are invalid")
        expected_names = tuple(spec.name for spec in specs)
        if len(set(expected_names)) != len(expected_names):
            raise TwoStageMigrationSafetyError("canonical table specs contain duplicates")

        renamed: list[tuple[str, str]] = []
        tables = {table.name: table for table in self._load_tables()}
        self._assert_support_tables(tables)
        self._activate_archive(
            tables,
            archive_name=QUESTION_ARCHIVE_NAME,
            target_name="第三期题目预审",
            renamed=renamed,
        )
        tables = {table.name: table for table in self._load_tables()}
        self._activate_archive(
            tables,
            archive_name=RESULT_ARCHIVE_NAME,
            target_name="第三期交互成果",
            renamed=renamed,
        )
        tables = {table.name: table for table in self._load_tables()}
        if UNIFIED_TABLE_NAME in tables:
            if UNIFIED_ARCHIVE_NAME in tables:
                raise TwoStageMigrationSafetyError("unified archive name already exists")
            source = tables[UNIFIED_TABLE_NAME]
            self._set_forms_private(source)
            self._client.rename_table(source.table_id, UNIFIED_ARCHIVE_NAME)
            renamed.append((UNIFIED_TABLE_NAME, UNIFIED_ARCHIVE_NAME))

        tables = {table.name: table for table in self._load_tables()}
        if not set(expected_names).issubset(tables):
            raise TwoStageMigrationSafetyError("canonical tables are missing after rename")

        added_fields: dict[str, tuple[str, ...]] = {}
        updated_fields: dict[str, tuple[str, ...]] = {}
        for spec in specs:
            table = tables[spec.name]
            existing = self._field_lookup(table.table_id)
            added: list[str] = []
            updated: list[str] = []
            for field in spec.fields:
                actual = existing.get(field.name)
                if actual is not None:
                    options_match = self._assert_field_shape(
                        table_name=spec.name,
                        field=field,
                        actual=actual,
                        tables=tables,
                        allow_option_drift=True,
                    )
                    if not options_match:
                        field_id = self._compact(
                            actual.get("field_id"),
                            "field identity",
                        )
                        self._client.update_field_options(
                            table.table_id,
                            field_id=field_id,
                            field_name=field.name,
                            field_type=field.field_type,
                            options=field.options,
                        )
                        updated.append(field.name)
                    continue
                self._client.create_field(
                    table.table_id,
                    field_name=field.name,
                    field_type=field.field_type,
                    options=field.options,
                    link_target=field.link_target,
                )
                added.append(field.name)
            added_fields[spec.name] = tuple(added)
            updated_fields[spec.name] = tuple(updated)
            if spec.name in {"第三期题目预审", "第三期交互成果"}:
                self._set_forms_private(table)

        tables = {table.name: table for table in self._load_tables()}
        for table in tables.values():
            if table.name.startswith("归档_"):
                self._set_forms_private(table)

        read_back_tables = {table.name: table for table in self._load_tables()}
        if not set(expected_names).issubset(read_back_tables):
            raise TwoStageMigrationSafetyError("canonical table read-back failed")
        for spec in specs:
            actual_fields = self._field_lookup(
                read_back_tables[spec.name].table_id
            )
            for field in spec.fields:
                actual = actual_fields.get(field.name)
                if actual is None:
                    raise TwoStageMigrationSafetyError(
                        f"{spec.name} field read-back failed: {field.name}"
                    )
                self._assert_field_shape(
                    table_name=spec.name,
                    field=field,
                    actual=actual,
                    tables=read_back_tables,
                    allow_option_drift=False,
                )
        for table in read_back_tables.values():
            if (
                table.name.startswith("归档_")
                or table.name in {"第三期题目预审", "第三期交互成果"}
            ) and self._shared_form_ids(table):
                raise TwoStageMigrationSafetyError(
                    f"Form sharing read-back failed: {table.name}"
                )
        return TwoStageActivationReceipt(
            canonical_table_names=tuple(sorted(expected_names)),
            renamed_tables=tuple(renamed),
            added_fields=added_fields,
            updated_fields=updated_fields,
            read_back=True,
        )

    def delete_default_table(self, *, confirmed: bool) -> DefaultTableDeletionReceipt:
        raise TwoStageMigrationSafetyError(
            "default table deletion is disabled; preserve existing records"
        )

    def _load_tables(self) -> tuple[_Table, ...]:
        raw_tables = self._client.list_tables()
        if isinstance(raw_tables, (str, bytes)) or not isinstance(raw_tables, Sequence):
            raise TwoStageMigrationSafetyError("table metadata must be a sequence")
        tables: list[_Table] = []
        seen_ids: set[str] = set()
        seen_names: set[str] = set()
        for raw_table in raw_tables:
            if not isinstance(raw_table, Mapping):
                raise TwoStageMigrationSafetyError("table metadata must contain mappings")
            table_id = self._compact(raw_table.get("table_id"), "table identity")
            name = self._compact(raw_table.get("name"), "table name")
            if table_id in seen_ids or name in seen_names:
                raise TwoStageMigrationSafetyError("duplicate table metadata")
            seen_ids.add(table_id)
            seen_names.add(name)
            tables.append(_Table(table_id=table_id, name=name))
        return tuple(tables)

    def _assert_support_tables(self, tables: Mapping[str, _Table]) -> None:
        missing = REQUIRED_SUPPORT_TABLES - set(tables)
        if missing:
            raise TwoStageMigrationSafetyError("required support table is missing")

    def _assert_reuse_candidates(self, tables: Mapping[str, _Table]) -> None:
        missing = {QUESTION_ARCHIVE_NAME, RESULT_ARCHIVE_NAME} - set(tables)
        if missing:
            raise TwoStageMigrationSafetyError("required reuse candidate is missing")

    def _assert_default_table_is_safe(self, table: _Table) -> None:
        fields = self._field_signature(table.table_id)
        if fields != DEFAULT_TABLE_FIELD_SIGNATURE:
            raise TwoStageMigrationSafetyError("default table schema differs")
        self._assert_no_shared_form(table)
        inspection = self._client.inspect_automation(table.table_id)
        if not isinstance(inspection, AutomationInspection) or not inspection.checked:
            raise TwoStageMigrationSafetyError("automation inspection is not verified")
        if inspection.active_binding_names:
            raise TwoStageMigrationSafetyError("active automation blocks default deletion")

    def _activate_archive(
        self,
        tables: Mapping[str, _Table],
        *,
        archive_name: str,
        target_name: str,
        renamed: list[tuple[str, str]],
    ) -> None:
        if target_name in tables and archive_name in tables:
            raise TwoStageMigrationSafetyError(
                f"both active and archived tables exist: {target_name}"
            )
        if target_name in tables:
            return
        source = tables.get(archive_name)
        if source is None:
            raise TwoStageMigrationSafetyError(
                f"required reuse candidate is missing: {archive_name}"
            )
        self._set_forms_private(source)
        self._client.rename_table(source.table_id, target_name)
        renamed.append((archive_name, target_name))

    def _shared_form_ids(self, table: _Table) -> tuple[str, ...]:
        raw_views = self._client.list_views(table.table_id)
        if isinstance(raw_views, (str, bytes)) or not isinstance(raw_views, Sequence):
            raise TwoStageMigrationSafetyError("view metadata must be a sequence")
        shared_form_ids: list[str] = []
        for raw_view in raw_views:
            if not isinstance(raw_view, Mapping):
                raise TwoStageMigrationSafetyError("view metadata must contain mappings")
            if raw_view.get("view_type") != "form":
                continue
            form_id = self._compact(raw_view.get("view_id"), "Form identity")
            metadata = self._client.get_form_metadata(table.table_id, form_id)
            if not isinstance(metadata, Mapping) or not isinstance(
                metadata.get("shared"), bool
            ):
                raise TwoStageMigrationSafetyError("Form metadata is incomplete")
            if metadata["shared"]:
                shared_form_ids.append(form_id)
        return tuple(shared_form_ids)

    def _set_forms_private(self, table: _Table) -> None:
        for form_id in self._shared_form_ids(table):
            self._client.set_form_shared(table.table_id, form_id, False)
            metadata = self._client.get_form_metadata(table.table_id, form_id)
            if not isinstance(metadata, Mapping) or metadata.get("shared") is not False:
                raise TwoStageMigrationSafetyError(
                    "Form sharing read-back failed"
                )

    def _field_lookup(self, table_id: str) -> dict[str, Mapping[str, object]]:
        raw_fields = self._client.list_fields(table_id)
        if isinstance(raw_fields, (str, bytes)) or not isinstance(raw_fields, Sequence):
            raise TwoStageMigrationSafetyError("field metadata must be a sequence")
        fields: dict[str, Mapping[str, object]] = {}
        for raw_field in raw_fields:
            if not isinstance(raw_field, Mapping):
                raise TwoStageMigrationSafetyError("field metadata must contain mappings")
            name = self._compact(raw_field.get("field_name"), "field name")
            if name in fields:
                raise TwoStageMigrationSafetyError("duplicate field metadata")
            field_type = raw_field.get("type")
            if isinstance(field_type, bool) or not isinstance(field_type, int):
                raise TwoStageMigrationSafetyError("field type must be an integer")
            fields[name] = raw_field
        return fields

    def _field_signature(self, table_id: str) -> tuple[tuple[str, int], ...]:
        return tuple(
            (name, int(field["type"]))
            for name, field in self._field_lookup(table_id).items()
        )

    def _assert_field_shape(
        self,
        *,
        table_name: str,
        field: Any,
        actual: Mapping[str, object],
        tables: Mapping[str, _Table],
        allow_option_drift: bool,
    ) -> bool:
        if actual.get("type") != field.field_type:
            raise TwoStageMigrationSafetyError(
                f"{table_name} field type differs: {field.name}"
            )
        if field.link_target:
            target_name = table_name if field.link_target == "self" else field.link_target
            target = tables.get(target_name)
            property_data = actual.get("property")
            if (
                target is None
                or not isinstance(property_data, Mapping)
                or property_data.get("table_id") != target.table_id
                or property_data.get("multiple") is not False
            ):
                raise TwoStageMigrationSafetyError(
                    f"{table_name} link field differs: {field.name}"
                )
        if not field.options:
            return True
        actual_options = self._field_options(actual, table_name, field.name)
        if actual_options != field.options and not allow_option_drift:
            raise TwoStageMigrationSafetyError(
                f"{table_name} field options differ: {field.name}"
            )
        return actual_options == field.options

    def _field_options(
        self,
        actual: Mapping[str, object],
        table_name: str,
        field_name: str,
    ) -> tuple[str, ...]:
        property_data = actual.get("property")
        if not isinstance(property_data, Mapping):
            raise TwoStageMigrationSafetyError(
                f"{table_name} field options are missing: {field_name}"
            )
        raw_options = property_data.get("options")
        if isinstance(raw_options, (str, bytes)) or not isinstance(raw_options, Sequence):
            raise TwoStageMigrationSafetyError(
                f"{table_name} field options are invalid: {field_name}"
            )
        options: list[str] = []
        for raw_option in raw_options:
            if not isinstance(raw_option, Mapping):
                raise TwoStageMigrationSafetyError(
                    f"{table_name} field option is invalid: {field_name}"
                )
            options.append(self._compact(raw_option.get("name"), "field option"))
        return tuple(options)

    def _assert_no_shared_form(self, table: _Table) -> None:
        raw_views = self._client.list_views(table.table_id)
        if isinstance(raw_views, (str, bytes)) or not isinstance(raw_views, Sequence):
            raise TwoStageMigrationSafetyError("view metadata must be a sequence")
        for raw_view in raw_views:
            if not isinstance(raw_view, Mapping):
                raise TwoStageMigrationSafetyError("view metadata must contain mappings")
            if raw_view.get("view_type") != "form":
                continue
            form_id = self._compact(raw_view.get("view_id"), "Form identity")
            metadata = self._client.get_form_metadata(table.table_id, form_id)
            if not isinstance(metadata, Mapping) or not isinstance(metadata.get("shared"), bool):
                raise TwoStageMigrationSafetyError("Form metadata is incomplete")
            if metadata["shared"]:
                raise TwoStageMigrationSafetyError("shared Form blocks default deletion")

    @staticmethod
    def _compact(value: object, label: str) -> str:
        if not isinstance(value, str) or not value or value != value.strip():
            raise TwoStageMigrationSafetyError(f"{label} must be a non-empty compact string")
        return value

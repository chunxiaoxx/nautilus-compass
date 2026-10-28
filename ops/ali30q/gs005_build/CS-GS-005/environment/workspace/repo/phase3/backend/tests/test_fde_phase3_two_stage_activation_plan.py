from __future__ import annotations

from services.fde_phase3_two_stage_migration import (
    QUESTION_ARCHIVE_NAME,
    RESULT_ARCHIVE_NAME,
    UNIFIED_ARCHIVE_NAME,
    UNIFIED_TABLE_NAME,
    TwoStageMigration,
)
from services.fde_phase3_two_stage_schema import canonical_tables


class ReadOnlyPlanClient:
    def __init__(self) -> None:
        names = (
            "第三期专家",
            "第三期审核与反馈",
            "第三期导出与回执",
            QUESTION_ARCHIVE_NAME,
            RESULT_ARCHIVE_NAME,
            UNIFIED_TABLE_NAME,
        )
        self.tables = [
            {"table_id": f"tbl_{index}", "name": name}
            for index, name in enumerate(names, start=1)
        ]
        self.mutations: list[tuple[object, ...]] = []

    def list_tables(self):
        return [dict(table) for table in self.tables]

    def list_fields(self, table_id):
        return []

    def list_views(self, table_id):
        table_name = next(
            table["name"] for table in self.tables if table["table_id"] == table_id
        )
        if table_name in {
            QUESTION_ARCHIVE_NAME,
            RESULT_ARCHIVE_NAME,
            UNIFIED_TABLE_NAME,
        }:
            return [
                {
                    "view_id": f"form_{table_id}",
                    "view_name": f"{table_name}旧表单",
                    "view_type": "form",
                }
            ]
        return []

    def get_form_metadata(self, table_id, form_id):
        return {"form_id": form_id, "shared": True}

    def rename_table(self, table_id, new_name):
        self.mutations.append(("rename", table_id, new_name))

    def create_field(
        self,
        table_id,
        *,
        field_name,
        field_type,
        options,
        link_target,
    ):
        self.mutations.append(("field", table_id, field_name))

    def set_form_shared(self, table_id, form_id, shared):
        self.mutations.append(("form", table_id, form_id, shared))


def test_two_stage_activation_plan_is_complete_and_read_only() -> None:
    client = ReadOnlyPlanClient()

    plan = TwoStageMigration(client).plan_activation(
        canonical_tables=canonical_tables()
    )

    assert plan.renamed_tables == (
        (QUESTION_ARCHIVE_NAME, "第三期题目预审"),
        (RESULT_ARCHIVE_NAME, "第三期交互成果"),
        (UNIFIED_TABLE_NAME, UNIFIED_ARCHIVE_NAME),
    )
    assert set(plan.added_fields) == {
        "第三期专家",
        "第三期题目预审",
        "第三期交互成果",
        "第三期审核与反馈",
        "第三期导出与回执",
    }
    assert {table_name for table_name, _ in plan.forms_to_close} == {
        QUESTION_ARCHIVE_NAME,
        RESULT_ARCHIVE_NAME,
        UNIFIED_TABLE_NAME,
    }
    assert all(plan.added_fields[table.name] for table in canonical_tables())
    assert client.mutations == []

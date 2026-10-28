from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.fde_phase3_single_submission_provisioning import (
    BitableReconciler,
    LegacyArchiveSafetyError,
    ProvisionConfirmationError,
    SchemaDriftError,
)
from services.fde_phase3_single_submission_schema import (
    CANONICAL_TABLE_NAMES,
    EXPERT_FORM_NAME,
    TASK_FORM_NAME,
)


class FakeBitableClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, object | None]] = []
        self.tables = [
            {"table_id": "tbl_legacy_expert", "name": "第三期专家信息"},
            {"table_id": "tbl_legacy_task", "name": "第三期题目预审"},
            {"table_id": "tbl_legacy_result", "name": "第三期交互成果"},
        ]
        self.fields = {table["table_id"]: [] for table in self.tables}
        self.views = {table["table_id"]: [] for table in self.tables}
        self._next_table = 1
        self._next_field = 1
        self._next_view = 1

    def list_tables(self):
        self.calls.append(("GET", "/tables", None))
        return [dict(table) for table in self.tables]

    def list_fields(self, table_id):
        self.calls.append(("GET", f"/tables/{table_id}/fields", None))
        return [dict(field) for field in self.fields[table_id]]

    def list_views(self, table_id):
        self.calls.append(("GET", f"/tables/{table_id}/views", None))
        return [dict(view) for view in self.views[table_id]]

    def create_table(self, name, fields):
        self.calls.append(("POST", "/tables", {"name": name, "fields": fields}))
        table_id = f"tbl_canonical_{self._next_table}"
        self._next_table += 1
        self.tables.append({"table_id": table_id, "name": name})
        self.fields[table_id] = [self._field(field) for field in fields]
        self.views[table_id] = []
        return {"table_id": table_id, "name": name}

    def create_link_field(self, table_id, name, target_table_id):
        body = {
            "field_name": name,
            "type": 18,
            "property": {"multiple": False, "table_id": target_table_id},
        }
        self.calls.append(("POST", f"/tables/{table_id}/fields", body))
        field = self._field(body)
        self.fields[table_id].append(field)
        return field

    def create_field(self, table_id, field):
        self.calls.append(("POST", f"/tables/{table_id}/fields", dict(field)))
        created = self._field(field)
        self.fields[table_id].append(created)
        return created

    def create_form_view(self, table_id, view_name):
        self.calls.append(("POST", f"/tables/{table_id}/views", {"view_name": view_name}))
        view = {
            "view_id": f"vew_{self._next_view}",
            "view_name": view_name,
            "view_type": "form",
        }
        self._next_view += 1
        self.views[table_id].append(view)
        return dict(view)

    def rename_table(self, table_id, name):
        self.calls.append(("PATCH", f"/tables/{table_id}", {"name": name}))
        for table in self.tables:
            if table["table_id"] == table_id:
                table["name"] = name
                return dict(table)
        raise KeyError(table_id)

    def _field(self, raw):
        field = dict(raw)
        field.setdefault("field_id", f"fld_{self._next_field}")
        self._next_field += 1
        return field


def test_plan_is_read_only_and_never_queries_business_records() -> None:
    client = FakeBitableClient()
    reconciler = BitableReconciler(client)

    plan = reconciler.plan()

    assert plan.create_table_names == CANONICAL_TABLE_NAMES
    assert plan.create_form_names == (EXPERT_FORM_NAME, TASK_FORM_NAME)
    assert plan.archive_table_names == (
        "第三期专家信息",
        "第三期题目预审",
        "第三期交互成果",
    )
    assert not any(method != "GET" for method, _, _ in client.calls)
    assert all("/records" not in path for _, path, _ in client.calls)


def test_apply_requires_explicit_confirmation_before_any_remote_mutation() -> None:
    client = FakeBitableClient()
    reconciler = BitableReconciler(client)

    with pytest.raises(ProvisionConfirmationError):
        reconciler.apply(confirmed=False)

    assert not any(method != "GET" for method, _, _ in client.calls)


def test_apply_creates_canonical_tables_links_and_forms_before_any_archive() -> None:
    client = FakeBitableClient()
    reconciler = BitableReconciler(client)

    receipt = reconciler.apply(confirmed=True)

    assert receipt.created_table_names == CANONICAL_TABLE_NAMES
    assert receipt.created_form_names == (EXPERT_FORM_NAME, TASK_FORM_NAME)
    assert receipt.archived_table_names == ()
    assert [table["name"] for table in client.tables[:3]] == [
        "第三期专家信息",
        "第三期题目预审",
        "第三期交互成果",
    ]
    write_methods = [method for method, _, _ in client.calls if method != "GET"]
    assert write_methods[:4] == ["POST", "POST", "POST", "POST"]
    assert "PATCH" not in write_methods
    assert all("/records" not in path for _, path, _ in client.calls)

    tables = {table["name"]: table["table_id"] for table in client.tables}
    task_fields = {field["field_name"]: field for field in client.fields[tables["第三期任务与交互提交"]]}
    review_fields = {field["field_name"]: field for field in client.fields[tables["第三期审核与反馈"]]}
    assert task_fields["专家关联"]["property"] == {
        "multiple": False,
        "table_id": tables["第三期专家"],
    }
    assert task_fields["revision_of"]["property"] == {
        "multiple": False,
        "table_id": tables["第三期任务与交互提交"],
    }
    assert review_fields["提交关联"]["property"]["table_id"] == tables["第三期任务与交互提交"]


def test_legacy_archive_requires_retired_forms_and_uses_rename_only() -> None:
    client = FakeBitableClient()
    reconciler = BitableReconciler(client)
    reconciler.apply(confirmed=True)

    with pytest.raises(LegacyArchiveSafetyError, match="legacy Forms"):
        reconciler.archive_legacy_tables(confirmed=True, legacy_forms_retired=False)

    receipt = reconciler.archive_legacy_tables(confirmed=True, legacy_forms_retired=True)

    assert receipt.archived_table_names == (
        "第三期专家信息",
        "第三期题目预审",
        "第三期交互成果",
    )
    renamed = [table["name"] for table in client.tables[:3]]
    assert all(name.startswith("归档_20260723_") for name in renamed)
    assert all(method != "DELETE" for method, _, _ in client.calls)
    assert all("/records" not in path for _, path, _ in client.calls)


def test_readback_rejects_canonical_field_drift() -> None:
    client = FakeBitableClient()
    reconciler = BitableReconciler(client)
    reconciler.apply(confirmed=True)

    task = next(table for table in client.tables if table["name"] == "第三期任务与交互提交")
    client.fields[task["table_id"]][0]["type"] = 2

    with pytest.raises(SchemaDriftError, match="schema differs"):
        reconciler.plan()


def test_reconciler_adds_only_missing_approved_fields_to_existing_canonical_table() -> None:
    client = FakeBitableClient()
    reconciler = BitableReconciler(client)
    reconciler.apply(confirmed=True)

    task = next(table for table in client.tables if table["name"] == "第三期任务与交互提交")
    client.fields[task["table_id"]] = [
        field
        for field in client.fields[task["table_id"]]
        if field["field_name"]
        not in {"工作流配置", "返修关联码", "返修码状态", "返修码到期时间"}
    ]
    client.calls.clear()

    plan = reconciler.plan()

    assert tuple((item.table_name, item.field.name) for item in plan.create_initial_fields) == (
        ("第三期任务与交互提交", "工作流配置"),
        ("第三期任务与交互提交", "返修关联码"),
        ("第三期任务与交互提交", "返修码状态"),
        ("第三期任务与交互提交", "返修码到期时间"),
    )
    assert not any(method != "GET" for method, _, _ in client.calls)

    receipt = reconciler.apply(confirmed=True)

    assert tuple((item.table_name, item.field.name) for item in receipt.created_initial_fields) == (
        ("第三期任务与交互提交", "工作流配置"),
        ("第三期任务与交互提交", "返修关联码"),
        ("第三期任务与交互提交", "返修码状态"),
        ("第三期任务与交互提交", "返修码到期时间"),
    )
    fields = {field["field_name"]: field for field in client.fields[task["table_id"]]}
    assert fields["工作流配置"]["property"]["options"] == [
        {"name": "phase3_interactive"}
    ]
    assert fields["返修关联码"]["type"] == 1
    assert fields["返修码状态"]["property"]["options"] == [
        {"name": "未发放"},
        {"name": "可用"},
        {"name": "已使用"},
        {"name": "已过期"},
    ]
    assert fields["返修码到期时间"]["type"] == 5
    assert all("/records" not in path for _, path, _ in client.calls)


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "reconcile_phase3_single_submission_base.py"
)


def load_reconcile_cli_module():
    module_name = "phase3_single_submission_reconcile_cli_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_reconcile_cli_requires_exact_confirmation_and_exposes_no_record_mode() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        cwd=SCRIPT_PATH.parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--apply" in result.stdout
    assert "--confirm" in result.stdout
    assert "records" not in result.stdout.lower()

    module = load_reconcile_cli_module()
    invalid = argparse.Namespace(
        base_token="base-safe",
        secret_file="unused",
        apply=True,
        confirm="wrong",
        archive_legacy=False,
        legacy_forms_retired=False,
    )
    with pytest.raises(SystemExit, match="FDE_PHASE3_SINGLE_SUBMISSION"):
        module.validate_args(invalid)


def test_reconcile_cli_requires_separate_confirmation_for_two_stage_activation() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        cwd=SCRIPT_PATH.parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--activate-two-stage" in result.stdout
    assert "FDE_PHASE3_ACTIVATE_TWO_STAGE" in result.stdout

    module = load_reconcile_cli_module()
    invalid = argparse.Namespace(
        base_token="base-safe",
        secret_file="unused",
        apply=True,
        confirm="FDE_PHASE3_SINGLE_SUBMISSION",
        archive_legacy=False,
        legacy_forms_retired=False,
        activate_two_stage=True,
    )
    with pytest.raises(SystemExit, match="FDE_PHASE3_ACTIVATE_TWO_STAGE"):
        module.validate_args(invalid)


def test_feishu_adapter_uses_metadata_only_endpoints_and_rename_patch() -> None:
    module = load_reconcile_cli_module()

    class FakeLark:
        LARK_BASE = "https://open.feishu.cn/open-apis"

        def __init__(self):
            self.calls = []

        def list_tables(self):
            self.calls.append(("GET", "/tables", None))
            return [{"table_id": "tbl_expert", "name": "第三期专家"}]

        def list_fields(self, table_id):
            self.calls.append(("GET", f"/tables/{table_id}/fields", None))
            return []

        def get(self, url):
            self.calls.append(("GET", url, None))
            if "/forms/" in url:
                return {
                    "code": 0,
                    "data": {"form": {"form_id": "vew_form", "shared": True}},
                }
            return {"code": 0, "data": {"items": []}}

        def post(self, url, body):
            self.calls.append(("POST", url, body))
            if url.endswith("/tables"):
                return {"code": 0, "data": {"table_id": "tbl_created"}}
            if url.endswith("/fields"):
                return {"code": 0, "data": {"field": {"field_name": body["field_name"]}}}
            return {"code": 0, "data": {"view": {"view_id": "vew_created"}}}

        def _request(self, method, url, body):
            self.calls.append((method, url, body))
            if "/forms/" in url:
                return {
                    "code": 0,
                    "data": {"form": {"form_id": "vew_form", "shared": body["shared"]}},
                }
            return {"code": 0, "data": {"name": body["name"]}}

    lark = FakeLark()
    client = module.FeishuSchemaClient(lark, "base-safe")

    assert client.create_table("第三期专家", [{"field_name": "专家编号", "type": 1}]) == {
        "table_id": "tbl_created",
        "name": "第三期专家",
    }
    client.create_field("tbl_task", {"field_name": "返修关联码", "type": 1})
    client.create_link_field("tbl_task", "专家关联", "tbl_expert")
    client.create_form_view("tbl_task", "第三期任务与交互提交（正式）")
    client.rename_table("tbl_legacy", "归档_20260723_第三期题目预审")

    paths = [path for _, path, _ in lark.calls]
    assert all("/records" not in path for path in paths)
    assert any(method == "PATCH" and body == {"name": "归档_20260723_第三期题目预审"} for method, _, body in lark.calls)


def test_feishu_adapter_supports_two_stage_fields_and_form_share_readback() -> None:
    module = load_reconcile_cli_module()

    class FakeLark:
        LARK_BASE = "https://open.feishu.cn/open-apis"

        def __init__(self):
            self.calls = []

        def list_tables(self):
            self.calls.append(("GET", "/tables", None))
            return [{"table_id": "tbl_expert", "name": "第三期专家"}]

        def list_fields(self, table_id):
            self.calls.append(("GET", f"/tables/{table_id}/fields", None))
            return []

        def get(self, url):
            self.calls.append(("GET", url, None))
            return {
                "code": 0,
                "data": {"form": {"form_id": "vew_form", "shared": True}},
            }

        def post(self, url, body):
            self.calls.append(("POST", url, body))
            return {
                "code": 0,
                "data": {"field": {"field_name": body["field_name"], **body}},
            }

        def put(self, url, body):
            self.calls.append(("PUT", url, body))
            return {
                "code": 0,
                "data": {"field": {"field_id": "fld_review", **body}},
            }

        def _request(self, method, url, body):
            self.calls.append((method, url, body))
            return {
                "code": 0,
                "data": {"form": {"form_id": "vew_form", "shared": body["shared"]}},
            }

    lark = FakeLark()
    client = module.FeishuSchemaClient(lark, "base-safe")

    client.create_field(
        "tbl_question",
        field_name="运营锁题决定",
        field_type=3,
        options=("开放交互", "退回补充", "异常升级"),
        link_target=None,
    )
    client.create_field(
        "tbl_question",
        field_name="专家关联",
        field_type=18,
        options=(),
        link_target="第三期专家",
    )
    client.create_field(
        "tbl_question",
        field_name="revision_of",
        field_type=18,
        options=(),
        link_target="self",
    )
    client.update_field_options(
        "tbl_review",
        field_id="fld_review",
        field_name="审核来源",
        field_type=3,
        options=("题目自动QC", "交互自动QC", "甲方反馈", "系统"),
    )
    assert client.get_form_metadata("tbl_question", "vew_form")["shared"] is True
    client.set_form_shared("tbl_question", "vew_form", False)

    assert (
        "POST",
        "https://open.feishu.cn/open-apis/bitable/v1/apps/base-safe/tables/tbl_question/fields",
        {
            "field_name": "运营锁题决定",
            "type": 3,
            "property": {
                "options": [
                    {"name": "开放交互"},
                    {"name": "退回补充"},
                    {"name": "异常升级"},
                ]
            },
        },
    ) in lark.calls
    assert (
        "PUT",
        "https://open.feishu.cn/open-apis/bitable/v1/apps/base-safe/tables/tbl_review/fields/fld_review",
        {
            "field_name": "审核来源",
            "type": 3,
            "property": {
                "options": [
                    {"name": "题目自动QC"},
                    {"name": "交互自动QC"},
                    {"name": "甲方反馈"},
                    {"name": "系统"},
                ]
            },
        },
    ) in lark.calls
    assert (
        "POST",
        "https://open.feishu.cn/open-apis/bitable/v1/apps/base-safe/tables/tbl_question/fields",
        {
            "field_name": "revision_of",
            "type": 18,
            "property": {"multiple": False, "table_id": "tbl_question"},
        },
    ) in lark.calls
    assert (
        "POST",
        "https://open.feishu.cn/open-apis/bitable/v1/apps/base-safe/tables/tbl_question/fields",
        {
            "field_name": "专家关联",
            "type": 18,
            "property": {"multiple": False, "table_id": "tbl_expert"},
        },
    ) in lark.calls
    assert (
        "PATCH",
        "https://open.feishu.cn/open-apis/bitable/v1/apps/base-safe/tables/tbl_question/forms/vew_form",
        {"shared": False},
    ) in lark.calls
    assert all("/records" not in path for _, path, _ in lark.calls)


@pytest.mark.parametrize("apply", [False, True])
def test_reconcile_cli_routes_two_stage_plan_and_apply_without_single_table_flow(
    monkeypatch,
    capsys,
    apply: bool,
) -> None:
    module = load_reconcile_cli_module()
    calls: list[tuple[str, object]] = []
    args = argparse.Namespace(
        base_token="base-safe",
        secret_file="unused",
        apply=apply,
        confirm=("FDE_PHASE3_ACTIVATE_TWO_STAGE" if apply else None),
        archive_legacy=False,
        legacy_forms_retired=False,
        activate_two_stage=True,
    )

    class FakeMigration:
        def __init__(self, client):
            calls.append(("client", client))

        def plan_activation(self, *, canonical_tables):
            calls.append(("plan", canonical_tables))
            return SimpleNamespace(
                canonical_table_names=("第三期专家", "第三期题目预审"),
                renamed_tables=(("归档题目", "第三期题目预审"),),
                added_fields={"第三期题目预审": ("题目编号",)},
                updated_fields={"第三期审核与反馈": ("审核来源",)},
                forms_to_close=(("归档题目", "form_1"),),
            )

        def activate(self, *, canonical_tables, confirmed):
            calls.append(("activate", (canonical_tables, confirmed)))
            return SimpleNamespace(
                canonical_table_names=("第三期专家", "第三期题目预审"),
                renamed_tables=(("归档题目", "第三期题目预审"),),
                added_fields={"第三期题目预审": ("题目编号",)},
                updated_fields={"第三期审核与反馈": ("审核来源",)},
                read_back=True,
            )

    sentinel_client = object()
    monkeypatch.setattr(module, "_args", lambda: args)
    monkeypatch.setattr(module, "_load_env", lambda _path: None)
    monkeypatch.setattr(module, "_load_lark_client", lambda _token: object())
    monkeypatch.setattr(
        module,
        "FeishuSchemaClient",
        lambda _lark, _token: sentinel_client,
    )
    monkeypatch.setattr(module, "TwoStageMigration", FakeMigration)
    monkeypatch.setattr(module, "two_stage_canonical_tables", lambda: ("spec",))

    assert module.main() == 0
    output = json.loads(capsys.readouterr().out)

    if apply:
        assert output["mode"] == "two_stage_activated"
        assert output["read_back"] is True
        assert output["updated_fields"] == {
            "第三期审核与反馈": ["审核来源"]
        }
        assert ("activate", (("spec",), True)) in calls
        assert not any(name == "plan" for name, _ in calls)
    else:
        assert output["mode"] == "two_stage_dry_run"
        assert output["forms_to_close"] == [
            {"table": "归档题目", "form_id": "form_1"}
        ]
        assert output["update_fields"] == [
            {"table": "第三期审核与反馈", "fields": ["审核来源"]}
        ]
        assert ("plan", ("spec",)) in calls
        assert not any(name == "activate" for name, _ in calls)

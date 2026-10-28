import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

from services.fde_phase3_20260722_schema import (
    EXPERT_EDUCATION_OPTIONS,
    EXPERT_SCHOOL_TIER_OPTIONS,
    INTERACTION_RESULT_PUBLIC_FIELDS,
    PHASE3_PRIMARY_CATEGORY_OPTIONS,
    PUBLIC_FORM_NAMES,
    TASK_PRESCREEN_PUBLIC_FIELDS,
    expert_info_table,
    interaction_result_table,
    task_prescreen_table,
)
from services.fde_phase3_20260722_provisioning import (
    BitableProvisioner,
    ProvisionConfirmationError,
)
from services.fde_phase3_20260722_form_publishing import (
    FormPublishConfirmationError,
    FormPublisher,
    public_form_configurations,
)
from services.fde_phase3_20260722_schema import public_form_tables


def test_expert_info_form_matches_verified_ten_field_contract():
    assert expert_info_table().public_field_names == (
        "姓名",
        "豆包UID",
        "最高学历",
        "毕业院校",
        "专业",
        "学校层次",
        "工作领域",
        "工作年限",
        "行业证书认证（文字描述）",
        "每日作业时长",
    )
    assert EXPERT_EDUCATION_OPTIONS == ("本科", "硕士", "博士", "其他")
    assert EXPERT_SCHOOL_TIER_OPTIONS == (
        "C9",
        "985",
        "211",
        "双一流",
        "其它院校",
        "海外院校",
    )


def test_task_prescreen_uses_only_verified_buyer_fields_and_primary_categories():
    assert task_prescreen_table().public_field_names == (
        "UID",
        "题目",
        "题目领域一级目录",
        "题目领域二级目录",
        "相关附件",
        "附件来源",
        "后续交互思路",
    )
    assert TASK_PRESCREEN_PUBLIC_FIELDS == task_prescreen_table().public_field_names
    assert len(PHASE3_PRIMARY_CATEGORY_OPTIONS) == 15
    assert "科技软件与 AI 工作流" in PHASE3_PRIMARY_CATEGORY_OPTIONS
    assert "题目领域三级目录" not in TASK_PRESCREEN_PUBLIC_FIELDS


def test_interaction_result_is_uid_plus_only_the_five_verified_completion_fields():
    assert interaction_result_table().public_field_names == (
        "UID",
        "姓名",
        "豆包UID",
        "对话图片",
        "轨迹链接",
        "日志ID",
    )
    assert INTERACTION_RESULT_PUBLIC_FIELDS == interaction_result_table().public_field_names


def test_public_forms_do_not_expose_internal_review_or_export_fields():
    public_names = set(
        expert_info_table().public_field_names
        + task_prescreen_table().public_field_names
        + interaction_result_table().public_field_names
    )
    assert public_names.isdisjoint(
        {
            "P0状态",
            "质检状态",
            "质检意见",
            "verdict",
            "revision_of",
            "导出状态",
            "compass_receipt_hash",
        }
    )
    assert PUBLIC_FORM_NAMES == (
        "第三期专家信息采集",
        "第三期题目预审提交",
        "第三期交互成果补充",
    )


class FakeBitableClient:
    def __init__(self):
        self.calls = []
        self.tables = [
            {"table_id": "tbl_tasks", "name": "任务"},
            {"table_id": "tbl_attempts", "name": "交互尝试"},
        ]
        self.fields = {"tbl_tasks": [], "tbl_attempts": []}
        self.views = {"tbl_tasks": [], "tbl_attempts": []}

    def list_tables(self):
        self.calls.append(("GET", "/tables"))
        return list(self.tables)

    def list_fields(self, table_id):
        self.calls.append(("GET", f"/tables/{table_id}/fields"))
        return list(self.fields[table_id])

    def list_views(self, table_id):
        self.calls.append(("GET", f"/tables/{table_id}/views"))
        return list(self.views[table_id])

    def create_table(self, name, fields):
        self.calls.append(("POST", "/tables"))
        table_id = f"tbl_{len(self.tables)}"
        self.tables.append({"table_id": table_id, "name": name})
        self.fields[table_id] = [
            {"field_name": field["field_name"], "type": field["type"]}
            for field in fields
        ]
        self.views[table_id] = []
        return {"table_id": table_id, "name": name}

    def create_form_view(self, table_id, view_name):
        self.calls.append(("POST", f"/tables/{table_id}/views"))
        view = {"view_id": f"view_{len(self.views[table_id])}", "view_name": view_name}
        self.views[table_id].append(view)
        return view


def test_provisioner_is_dry_run_until_explicit_confirmation():
    client = FakeBitableClient()
    provisioner = BitableProvisioner(client)

    plan = provisioner.plan()

    assert plan.create_table_names == ("第三期专家信息", "第三期题目预审", "第三期交互成果")
    assert plan.create_form_names == PUBLIC_FORM_NAMES
    assert not any(method == "POST" for method, _ in client.calls)

    with __import__("pytest").raises(ProvisionConfirmationError):
        provisioner.apply(confirmed=False)


def test_provisioner_creates_only_schema_and_form_view_resources_then_reads_them_back():
    client = FakeBitableClient()
    provisioner = BitableProvisioner(client)

    receipt = provisioner.apply(confirmed=True)

    assert receipt.created_table_names == ("第三期专家信息", "第三期题目预审", "第三期交互成果")
    assert receipt.created_form_names == PUBLIC_FORM_NAMES
    assert any(method == "POST" and path == "/tables" for method, path in client.calls)
    assert any(method == "POST" and path.endswith("/views") for method, path in client.calls)
    assert all("/records" not in path for _, path in client.calls)


def test_provisioner_script_starts_from_the_backend_working_directory():
    script = Path(__file__).parents[1] / "scripts" / "provision_phase3_20260722_bitable.py"

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=Path(__file__).parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--apply" in result.stdout


class FakeFormClient:
    def __init__(self):
        self.calls = []
        self.tables = []
        self.fields = {}
        self.views = {}
        self.form_metadata = {}
        self.form_fields = {}

        for index, table_spec in enumerate(public_form_tables(), start=1):
            table_id = f"tbl_public_{index}"
            form_id = f"vew_public_{index}"
            self.tables.append({"table_id": table_id, "name": table_spec.name})
            self.fields[table_id] = [
                {
                    "field_id": f"fld_{index}_{field_index}",
                    "field_name": field.name,
                    "type": field.field_type,
                }
                for field_index, field in enumerate(table_spec.fields, start=1)
            ]
            self.views[table_id] = [
                {"view_id": form_id, "view_name": table_spec.form_name, "view_type": "form"}
            ]
            key = (table_id, form_id)
            self.form_metadata[key] = {
                "name": table_spec.form_name,
                "description": None,
                "shared": False,
                "shared_limit": None,
                "submit_limit_once": False,
                "shared_url": None,
            }
            self.form_fields[key] = {
                field["field_id"]: {
                    "field_id": field["field_id"],
                    "title": field["field_name"],
                    "description": None,
                    "required": False,
                    "visible": True,
                }
                for field in self.fields[table_id]
            }

        self._add_legacy_form(
            table_id="tbl_legacy_task",
            table_name="外部题目提交",
            form_id="vew_legacy_task",
            form_name="第三期题目与交互成果提交",
        )
        self._add_legacy_form(
            table_id="tbl_legacy_expert",
            table_name="专家申请",
            form_id="vew_legacy_expert",
            form_name="第三期专家申请与豆包开通",
        )

    def _add_legacy_form(self, *, table_id, table_name, form_id, form_name):
        self.tables.append({"table_id": table_id, "name": table_name})
        self.fields[table_id] = []
        self.views[table_id] = [{"view_id": form_id, "view_name": form_name, "view_type": "form"}]
        self.form_metadata[(table_id, form_id)] = {
            "name": form_name,
            "description": None,
            "shared": True,
            "shared_limit": "anyone_editable",
            "submit_limit_once": False,
            "shared_url": f"https://share.example/{form_id}",
        }
        self.form_fields[(table_id, form_id)] = {}

    def list_tables(self):
        self.calls.append(("GET", "/tables", None))
        return list(self.tables)

    def list_fields(self, table_id):
        self.calls.append(("GET", f"/tables/{table_id}/fields", None))
        return [dict(item) for item in self.fields[table_id]]

    def list_views(self, table_id):
        self.calls.append(("GET", f"/tables/{table_id}/views", None))
        return [dict(item) for item in self.views[table_id]]

    def get_form_metadata(self, table_id, form_id):
        self.calls.append(("GET", f"/tables/{table_id}/forms/{form_id}", None))
        return dict(self.form_metadata[(table_id, form_id)])

    def list_form_fields(self, table_id, form_id):
        self.calls.append(("GET", f"/tables/{table_id}/forms/{form_id}/fields", None))
        return [dict(item) for item in self.form_fields[(table_id, form_id)].values()]

    def patch_form_metadata(self, table_id, form_id, body):
        self.calls.append(("PATCH", f"/tables/{table_id}/forms/{form_id}", dict(body)))
        metadata = self.form_metadata[(table_id, form_id)]
        metadata.update(body)
        if metadata.get("shared"):
            metadata["shared_url"] = f"https://share.example/{form_id}"
        return dict(metadata)

    def patch_form_field(self, table_id, form_id, field_id, body):
        self.calls.append(
            ("PATCH", f"/tables/{table_id}/forms/{form_id}/fields/{field_id}", dict(body))
        )
        field = self.form_fields[(table_id, form_id)][field_id]
        field.update(body)
        return dict(field)


def test_public_form_configuration_only_exposes_verified_external_fields():
    configs = public_form_configurations()

    assert tuple(config.table_name for config in configs) == (
        "第三期专家信息",
        "第三期题目预审",
        "第三期交互成果",
    )
    assert all(config.shared_limit == "anyone_editable" for config in configs)
    assert all(not config.submit_limit_once for config in configs)
    for config, table_spec in zip(configs, public_form_tables(), strict=True):
        visible = tuple(field.name for field in config.fields if field.visible)
        hidden = tuple(field.name for field in config.fields if not field.visible)
        assert visible == table_spec.public_field_names
        assert set(hidden) == {field.name for field in table_spec.fields if not field.public}


def test_form_publisher_requires_confirmation_before_remote_writes():
    client = FakeFormClient()
    publisher = FormPublisher(client)

    with __import__("pytest").raises(FormPublishConfirmationError):
        publisher.publish(confirmed=False)

    assert not any(method == "PATCH" for method, _, _ in client.calls)


def test_form_publisher_hides_internal_fields_before_opening_public_share():
    client = FakeFormClient()
    publisher = FormPublisher(client)

    receipt = publisher.publish(confirmed=True)

    assert tuple(item.form_name for item in receipt.forms) == PUBLIC_FORM_NAMES
    assert all(item.shared_url.startswith("https://share.example/") for item in receipt.forms)
    patch_calls = [call for call in client.calls if call[0] == "PATCH"]
    metadata_indexes = [
        index
        for index, (_, path, body) in enumerate(patch_calls)
        if path.count("/") == 4 and body.get("shared") is True
    ]
    hidden_field_indexes = [
        index
        for index, (_, path, body) in enumerate(patch_calls)
        if "/fields/" in path and body == {"visible": False}
    ]
    assert metadata_indexes
    assert hidden_field_indexes
    assert max(hidden_field_indexes) < min(metadata_indexes)
    assert all("/records" not in path for _, path, _ in client.calls)


def test_legacy_forms_are_retired_only_after_new_public_forms_verify():
    client = FakeFormClient()
    publisher = FormPublisher(client)

    publisher.publish(confirmed=True)
    retired = publisher.retire_obsolete_forms(confirmed=True)

    assert tuple(item.form_name for item in retired) == (
        "第三期题目与交互成果提交",
        "第三期专家申请与豆包开通",
    )
    assert all(not item.shared for item in retired)
    retirement_patches = [
        body
        for method, path, body in client.calls
        if method == "PATCH"
        and path in {
            "/tables/tbl_legacy_task/forms/vew_legacy_task",
            "/tables/tbl_legacy_expert/forms/vew_legacy_expert",
        }
    ]
    assert retirement_patches == [{"shared": False}, {"shared": False}]
    assert all("/records" not in path for _, path, _ in client.calls)


def test_form_publish_script_allows_retirement_preview_without_apply(monkeypatch):
    script = Path(__file__).parents[1] / "scripts" / "publish_phase3_20260722_forms.py"
    monkeypatch.syspath_prepend(str(script.parent))
    spec = importlib.util.spec_from_file_location("phase3_form_publish_script", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    args = argparse.Namespace(
        base_token="base-token",
        secret_file="unused",
        apply=False,
        retire_obsolete=True,
        confirm=None,
    )

    module.validate_args(args)

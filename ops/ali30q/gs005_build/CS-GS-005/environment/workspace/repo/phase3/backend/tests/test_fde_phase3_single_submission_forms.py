from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from services.fde_phase3_single_submission_forms import (
    ExpertFormProbe,
    FormPublicationSafetyError,
    FormPublishConfirmationError,
    FormPublisher,
    public_form_configurations,
)
from services.fde_phase3_single_submission_schema import (
    EXPERT_FORM_NAME,
    TASK_FORM_NAME,
    canonical_tables,
)


class FakeFormClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []
        self.tables: list[dict] = []
        self.fields: dict[str, list[dict]] = {}
        self.views: dict[str, list[dict]] = {}
        self.form_metadata: dict[tuple[str, str], dict] = {}
        self.form_fields: dict[tuple[str, str], dict[str, dict]] = {}

        for index, table_spec in enumerate(canonical_tables(), start=1):
            table_id = f"tbl_canonical_{index}"
            self.tables.append({"table_id": table_id, "name": table_spec.name})
            self.fields[table_id] = [
                {
                    "field_id": f"fld_{index}_{field_index}",
                    "field_name": field.name,
                    "type": field.field_type,
                }
                for field_index, field in enumerate(table_spec.fields, start=1)
            ]
            self.views[table_id] = []
            if table_spec.form_name:
                form_id = f"vew_canonical_{index}"
                self.views[table_id].append(
                    {
                        "view_id": form_id,
                        "view_name": table_spec.form_name,
                        "view_type": "form",
                    }
                )
                key = (table_id, form_id)
                self.form_metadata[key] = {
                    "name": table_spec.form_name,
                    "description": "",
                    "shared": False,
                    "shared_limit": "off",
                    "submit_limit_once": True,
                    "shared_url": "",
                }
                self.form_fields[key] = {
                    field["field_id"]: {
                        "field_id": field["field_id"],
                        "title": field["field_name"],
                        "description": "",
                        "required": False,
                        "visible": True,
                    }
                    for field in self.fields[table_id]
                }

        self._add_legacy_form(
            "tbl_legacy_expert",
            "第三期专家信息",
            "vew_legacy_expert",
            "第三期专家信息采集",
        )
        self._add_legacy_form(
            "tbl_legacy_task",
            "第三期题目预审",
            "vew_legacy_task",
            "第三期题目预审提交",
        )
        self._add_legacy_form(
            "tbl_legacy_result",
            "第三期交互成果",
            "vew_legacy_result",
            "第三期交互成果补充",
        )

    def _add_legacy_form(self, table_id, table_name, form_id, form_name) -> None:
        self.tables.append({"table_id": table_id, "name": table_name})
        self.fields[table_id] = []
        self.views[table_id] = [
            {"view_id": form_id, "view_name": form_name, "view_type": "form"}
        ]
        self.form_metadata[(table_id, form_id)] = {
            "name": form_name,
            "description": "",
            "shared": True,
            "shared_limit": "anyone_editable",
            "submit_limit_once": False,
            "shared_url": f"https://share.example/{form_id}",
        }
        self.form_fields[(table_id, form_id)] = {}

    def list_tables(self):
        self.calls.append(("GET", "/tables", None))
        return [dict(table) for table in self.tables]

    def list_fields(self, table_id):
        self.calls.append(("GET", f"/tables/{table_id}/fields", None))
        return [dict(field) for field in self.fields[table_id]]

    def list_views(self, table_id):
        self.calls.append(("GET", f"/tables/{table_id}/views", None))
        return [dict(view) for view in self.views[table_id]]

    def get_form_metadata(self, table_id, form_id):
        self.calls.append(("GET", f"/tables/{table_id}/forms/{form_id}", None))
        return dict(self.form_metadata[(table_id, form_id)])

    def list_form_fields(self, table_id, form_id):
        self.calls.append(("GET", f"/tables/{table_id}/forms/{form_id}/fields", None))
        return [dict(field) for field in self.form_fields[(table_id, form_id)].values()]

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


def test_two_public_form_contracts_keep_complete_submission_but_hide_internal_columns() -> None:
    configs = public_form_configurations()
    tables = {table.name: table for table in canonical_tables()}

    assert tuple(config.table_name for config in configs) == (
        "第三期专家",
        "第三期任务与交互提交",
    )
    assert all(config.shared_limit == "anyone_editable" for config in configs)
    assert all(config.submit_limit_once is False for config in configs)
    assert "至少 6 轮" in configs[1].description
    assert "豆包办公任务" in configs[1].description
    repair_reference = next(field for field in configs[1].fields if field.name == "返修关联码")
    assert repair_reference.visible is True
    assert repair_reference.required is False
    assert "一次性" in repair_reference.description
    assert "未过期" in repair_reference.description
    assert "返修" in repair_reference.description
    for config in configs:
        table = tables[config.table_name]
        visible = tuple(field.name for field in config.fields if field.visible)
        hidden = tuple(field.name for field in config.fields if not field.visible)
        assert visible == table.public_field_names
        assert set(hidden) == {field.name for field in table.fields if not field.public}


def test_hidden_form_questions_use_the_minimal_supported_patch_body() -> None:
    expert_config = public_form_configurations()[0]
    hidden_field = next(field for field in expert_config.fields if not field.visible)

    assert FormPublisher._field_body(hidden_field) == {"visible": False}


def test_form_publisher_requires_confirmation_before_mutating_remote_forms() -> None:
    client = FakeFormClient()
    publisher = FormPublisher(client)

    with pytest.raises(FormPublishConfirmationError):
        publisher.publish(confirmed=False)

    assert not any(method == "PATCH" for method, _, _ in client.calls)


def test_form_publisher_hides_internal_fields_before_public_share() -> None:
    client = FakeFormClient()
    publisher = FormPublisher(client)

    receipt = publisher.publish(confirmed=True)

    assert tuple(form.form_name for form in receipt.forms) == (
        "第三期专家信息采集（正式）",
        "第三期任务与交互提交（正式）",
    )
    assert all(form.shared_url.startswith("https://share.example/") for form in receipt.forms)

    patch_calls = [call for call in client.calls if call[0] == "PATCH"]
    metadata_share_indexes = [
        index
        for index, (_, path, body) in enumerate(patch_calls)
        if "/forms/" in path and "/fields/" not in path and body.get("shared") is True
    ]
    field_patch_indexes = [
        index for index, (_, path, _) in enumerate(patch_calls) if "/fields/" in path
    ]
    assert metadata_share_indexes
    assert field_patch_indexes
    assert max(field_patch_indexes) < min(metadata_share_indexes)

    canonical_tables_by_name = {table["name"]: table for table in client.tables}
    for config in public_form_configurations():
        table_id = canonical_tables_by_name[config.table_name]["table_id"]
        form_id = next(
            view["view_id"]
            for view in client.views[table_id]
            if view["view_name"] == config.form_name
        )
        table_fields = {field["field_name"]: field for field in client.fields[table_id]}
        form_fields = client.form_fields[(table_id, form_id)]
        for config_field in config.fields:
            form_field = form_fields[table_fields[config_field.name]["field_id"]]
            assert form_field["visible"] is config_field.visible
            if config_field.visible:
                assert form_field["required"] is config_field.required
            else:
                assert form_field["required"] is False


def test_legacy_forms_can_be_retired_only_after_new_forms_are_verified_public() -> None:
    client = FakeFormClient()
    publisher = FormPublisher(client)

    with pytest.raises(Exception, match="publication"):
        publisher.retire_legacy_forms(confirmed=True)

    publisher.publish(confirmed=True)
    retired = publisher.retire_legacy_forms(confirmed=True)

    assert tuple(item.form_name for item in retired) == (
        "第三期专家信息采集",
        "第三期题目预审提交",
        "第三期交互成果补充",
    )
    assert all(item.shared is False for item in retired)
    assert all(
        metadata["shared"] is False
        for (table_id, _), metadata in client.form_metadata.items()
        if table_id.startswith("tbl_legacy")
    )


def test_publisher_refuses_to_change_a_public_form_with_unverified_fields() -> None:
    client = FakeFormClient()
    table_id = "tbl_canonical_1"
    form_id = "vew_canonical_1"
    client.form_metadata[(table_id, form_id)]["shared"] = True
    publisher = FormPublisher(client)

    with pytest.raises(FormPublicationSafetyError, match="requires field changes"):
        publisher.plan()

    assert not any(method == "PATCH" for method, _, _ in client.calls)


def test_publisher_reconfigures_a_public_form_only_via_private_field_update_window() -> None:
    client = FakeFormClient()
    publisher = FormPublisher(client)
    publisher.publish(confirmed=True)

    task_table_id = "tbl_canonical_2"
    task_form_id = "vew_canonical_2"
    uid_field_id = next(
        field["field_id"]
        for field in client.fields[task_table_id]
        if field["field_name"] == "UID"
    )
    client.form_fields[(task_table_id, task_form_id)][uid_field_id]["description"] = "stale"
    client.calls.clear()

    receipt = publisher.reconfigure_public_forms(confirmed=True)

    assert tuple(form.form_name for form in receipt.forms) == (
        "第三期专家信息采集（正式）",
        "第三期任务与交互提交（正式）",
    )
    patch_calls = [call for call in client.calls if call[0] == "PATCH"]
    private_index = next(
        index
        for index, (_, path, body) in enumerate(patch_calls)
        if path.endswith(f"/forms/{task_form_id}") and body == {"shared": False}
    )
    field_index = next(
        index for index, (_, path, _) in enumerate(patch_calls) if "/fields/" in path
    )
    public_index = max(
        index
        for index, (_, path, body) in enumerate(patch_calls)
        if path.endswith(f"/forms/{task_form_id}") and body.get("shared") is True
    )
    assert private_index < field_index < public_index
    assert client.form_metadata[(task_table_id, task_form_id)]["shared"] is True


def test_publisher_can_pause_only_the_task_form_before_schema_maintenance() -> None:
    client = FakeFormClient()
    publisher = FormPublisher(client)
    publisher.publish(confirmed=True)
    client.calls.clear()

    paused = publisher.pause_public_forms(
        confirmed=True,
        form_names=(TASK_FORM_NAME,),
    )

    assert tuple(item.form_name for item in paused) == (TASK_FORM_NAME,)
    task_metadata = client.form_metadata[("tbl_canonical_2", "vew_canonical_2")]
    expert_metadata = client.form_metadata[("tbl_canonical_1", "vew_canonical_1")]
    assert task_metadata["shared"] is False
    assert expert_metadata["shared"] is True
    patch_calls = [call for call in client.calls if call[0] == "PATCH"]
    assert patch_calls == [
        ("PATCH", "/tables/tbl_canonical_2/forms/vew_canonical_2", {"shared": False})
    ]


def test_expert_form_probe_reads_only_expert_form_metadata() -> None:
    client = FakeFormClient()
    publisher = FormPublisher(client)
    publisher.publish(confirmed=True)
    client.calls.clear()

    probe = publisher.probe_expert_form()

    assert probe.form_name == EXPERT_FORM_NAME
    assert probe.shared is True
    assert probe.shared_limit == "anyone_editable"
    assert probe.submit_limit_once is False
    assert probe.question_count == len(public_form_configurations()[0].fields)
    assert probe.visible_question_count == len(canonical_tables()[0].public_field_names)
    assert not hasattr(probe, "shared_url")
    assert all("tbl_canonical_2" not in path for _, path, _ in client.calls)
    assert all("/records" not in path for _, path, _ in client.calls)


def test_expert_form_refresh_uses_a_private_window_without_task_calls() -> None:
    client = FakeFormClient()
    publisher = FormPublisher(client)
    publisher.publish(confirmed=True)
    expert_table_id = "tbl_canonical_1"
    expert_form_id = "vew_canonical_1"
    name_field_id = next(
        field["field_id"]
        for field in client.fields[expert_table_id]
        if field["field_name"] == "姓名"
    )
    client.form_fields[(expert_table_id, expert_form_id)][name_field_id]["description"] = "stale"
    client.calls.clear()

    receipt = publisher.refresh_expert_form(confirmed=True)

    assert receipt.form_name == EXPERT_FORM_NAME
    assert receipt.shared is True
    patch_calls = [call for call in client.calls if call[0] == "PATCH"]
    private_index = next(
        index
        for index, (_, path, body) in enumerate(patch_calls)
        if path.endswith(f"/forms/{expert_form_id}") and body == {"shared": False}
    )
    field_index = next(
        index for index, (_, path, _) in enumerate(patch_calls) if "/fields/" in path
    )
    public_index = max(
        index
        for index, (_, path, body) in enumerate(patch_calls)
        if path.endswith(f"/forms/{expert_form_id}") and body.get("shared") is True
    )
    assert private_index < field_index < public_index
    assert all("tbl_canonical_2" not in path for _, path, _ in client.calls)
    assert all("/records" not in path for _, path, _ in client.calls)


def test_expert_form_refresh_requires_confirmation_without_patching() -> None:
    client = FakeFormClient()
    publisher = FormPublisher(client)

    with pytest.raises(FormPublishConfirmationError, match="expert Form refresh"):
        publisher.refresh_expert_form(confirmed=False)

    assert not any(method == "PATCH" for method, _, _ in client.calls)


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "publish_phase3_single_submission_forms.py"
)


def load_form_publish_cli_module():
    module_name = "phase3_single_submission_publish_forms_cli_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_form_publish_cli_requires_exact_confirmation_without_record_options() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        cwd=SCRIPT_PATH.parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--apply" in result.stdout
    assert "--retire-legacy" in result.stdout
    assert "--reconfigure-public" in result.stdout
    assert "records" not in result.stdout.lower()

    module = load_form_publish_cli_module()
    invalid = argparse.Namespace(
        base_token="base-safe",
        secret_file="unused",
        apply=True,
        retire_legacy=False,
        confirm="wrong",
    )
    with pytest.raises(SystemExit, match="FDE_PHASE3_SINGLE_SUBMISSION"):
        module.validate_args(invalid)

    dry_run = argparse.Namespace(
        base_token="base-safe",
        secret_file="unused",
        apply=False,
        retire_legacy=True,
        confirm=None,
        reconfigure_public=False,
    )
    module.validate_args(dry_run)

    reconfigure = argparse.Namespace(
        base_token="base-safe",
        secret_file="unused",
        apply=True,
        retire_legacy=False,
        reconfigure_public=True,
        confirm="FDE_PHASE3_SINGLE_SUBMISSION",
    )
    module.validate_args(reconfigure)


def test_feishu_form_adapter_uses_only_form_metadata_and_question_endpoints() -> None:
    module = load_form_publish_cli_module()

    class FakeLark:
        LARK_BASE = "https://open.feishu.cn/open-apis"

        def __init__(self):
            self.calls = []

        def list_tables(self):
            self.calls.append(("GET", "/tables", None))
            return []

        def list_fields(self, table_id):
            self.calls.append(("GET", f"/tables/{table_id}/fields", None))
            return []

        def get(self, url):
            self.calls.append(("GET", url, None))
            if "/forms/" in url and url.endswith("/fields?page_size=100"):
                return {"code": 0, "data": {"items": []}}
            if "/forms/" in url:
                return {"code": 0, "data": {"form": {"shared": False}}}
            return {"code": 0, "data": {"items": []}}

        def _request(self, method, url, body):
            self.calls.append((method, url, body))
            if "/fields/" in url:
                return {"code": 0, "data": {"field": body}}
            return {"code": 0, "data": {"form": body}}

    lark = FakeLark()
    client = module.FeishuFormClient(lark, "base-safe")
    client.patch_form_metadata("tbl_task", "vew_form", {"shared": True})
    client.patch_form_field("tbl_task", "vew_form", "fld_uid", {"visible": True})

    paths = [path for _, path, _ in lark.calls]
    assert all("/records" not in path for path in paths)
    assert any(method == "PATCH" and "/forms/vew_form" in path for method, path, _ in lark.calls)


EXPERT_RECOVERY_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "refresh_phase3_expert_form.py"
)


def load_expert_form_recovery_cli_module():
    module_name = "phase3_expert_form_recovery_cli_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, EXPERT_RECOVERY_SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_expert_form_cli_is_scoped_to_sanitized_probe_or_confirmed_refresh() -> None:
    result = subprocess.run(
        [sys.executable, str(EXPERT_RECOVERY_SCRIPT_PATH), "--help"],
        cwd=EXPERT_RECOVERY_SCRIPT_PATH.parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--probe" in result.stdout
    assert "--apply" in result.stdout
    assert "--confirm" in result.stdout
    assert "--target" not in result.stdout
    assert "records" not in result.stdout.lower()
    assert "browser acceptance" in result.stdout.lower()

    module = load_expert_form_recovery_cli_module()
    invalid = argparse.Namespace(
        base_token="base-safe",
        secret_file="unused",
        apply=True,
        probe=False,
        confirm="wrong",
    )
    with pytest.raises(SystemExit, match="FDE_PHASE3_EXPERT_FORM_REFRESH"):
        module.validate_args(invalid)

    probe = module.probe_output(
        ExpertFormProbe(
            form_name=EXPERT_FORM_NAME,
            shared=True,
            shared_limit="anyone_editable",
            submit_limit_once=False,
            question_count=16,
            visible_question_count=10,
        )
    )
    assert probe == {
        "form_name": EXPERT_FORM_NAME,
        "shared": True,
        "shared_limit": "anyone_editable",
        "submit_limit_once": False,
        "question_count": 16,
        "visible_question_count": 10,
    }
    assert all("url" not in key and "id" not in key for key in probe)
    assert "/records" not in EXPERT_RECOVERY_SCRIPT_PATH.read_text(encoding="utf-8")

    operation = module.result_output(
        ExpertFormProbe(
            form_name=EXPERT_FORM_NAME,
            shared=True,
            shared_limit="anyone_editable",
            submit_limit_once=False,
            question_count=16,
            visible_question_count=10,
        ),
        metadata_refreshed=False,
    )
    assert operation["mode"] == "metadata_probe"
    assert operation["external_fillability"] == "unverified"
    assert operation["form"] == probe

"""飞书字段 schema 层的契约测试：纯文本提取/字段映射/任务线归一化/分页读取。"""
from services.fde_task_form_schema import (
    plain_text,
    normalize_task_line,
    map_fields,
    resolve_expert_identities,
    claim_agent_id,
    display_expert,
    normalize_uid,
    read_bitable_rows,
)


def test_plain_text_richtext_array_and_scalar():
    assert plain_text(None) == ""
    assert plain_text("  abc  ") == "  abc  "
    assert plain_text([{"text": "一"}, {"text": "二"}, {"no": "3"}, 1, {"text": ""}]) == "一二"


def test_normalize_task_line_handles_rgdk_variants():
    assert normalize_task_line("2·教案") == "2"
    assert normalize_task_line("1·出题") == "1"
    assert normalize_task_line("3·评测") == "3"
    assert normalize_task_line("二") == "2"
    assert normalize_task_line("第三类-基准样例") == "3"
    assert normalize_task_line("第2类") == "2"


def test_map_fields_extracts_unicode_fields_to_std_keys():
    row = map_fields(
        {
            "task_uid": "u_001",
            "业务线": "2",
            "一级类目": "Cat",
            "三级领域": "Domain",
            "L级": "L2",
            "指派专家": "专家A",
            "验收标准": "标准",
            "标题": "测试标题",
            "提交内容": "稿件",
        },
        {
            "task_uid": "task_uid",
            "业务线": "line",
            "一级类目": "category",
            "三级领域": "domain",
            "L级": "level",
            "指派专家": "assignee",
            "验收标准": "acceptance",
            "标题": "title",
            "提交内容": "submission",
        },
    )
    assert row["task_uid"] == "u_001"
    assert row["line"] == "2"
    assert row["assignee"] == "专家A"
    assert row["submission"] == "稿件"


def test_normalize_uid_trims_and_normalizes_empty():
    assert normalize_uid({"task_uid": "  a1 "}) == "a1"
    assert normalize_uid({"task_uid": None}) == ""
    assert normalize_uid({}) == ""


def test_read_bitable_rows_follows_pagination_token():
    calls = []

    def fake(method: str, url: str, token: str | None = None, body: dict | None = None):
        calls.append(url)
        if "page_token=" not in url:
            return {"data": {"items": [{"record_id": "r1"}], "has_more": True, "page_token": "p2"}}
        if "page_token=p2" in url:
            return {"data": {"items": [{"record_id": "r2"}], "has_more": False, "page_token": ""}}
        return {"data": {"items": [], "has_more": False, "page_token": ""}}

    rows = read_bitable_rows(fake, "tok", "app", "tbl", "http://feishu")
    assert rows == [{"record_id": "r1"}, {"record_id": "r2"}]
    assert len(calls) == 2
    assert "page_token=" not in calls[0]
    assert "page_token=p2" in calls[1]


def test_resolve_expert_identities_prefers_expert_id_open_id_assignee():
    row = {"expert_id": "ext-001", "open_id": "open-001", "assignee": "legacy"}
    assert resolve_expert_identities(row) == ("ext-001", "expert_id")

    row = {"expert_id": "", "open_id": "open-001", "assignee": "legacy"}
    assert resolve_expert_identities(row) == ("open-001", "open_id")

    row = {"expert_id": None, "assignee": "legacy"}
    assert resolve_expert_identities(row) == ("legacy", "assignee")


def test_claim_and_display_expert_normalize_identity_source():
    row = {"expert_id": "", "open_id": "open@nautilus.io", "assignee": "legacy"}
    assert claim_agent_id(row) == "expert:open@nautilus.io"
    assert display_expert(row) == "open@nautilus.io"

    row = {"assignee": "legacy"}
    assert claim_agent_id(row) == "expert:legacy"
    assert display_expert(row) == "legacy"

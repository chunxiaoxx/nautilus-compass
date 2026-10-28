"""飞书字段映射与任务表单 schema 的统一适配层。

目标: 把派活表/提交表/交付表的字段散落映射集中到一个模块,
同时保留历史行为不变。
"""

from __future__ import annotations

import re
from typing import Any, Mapping


CN_DIGIT = {"一": "1", "二": "2", "三": "3"}


def plain_text(v: Any) -> str:
    """飞书 richtext list 或标量转纯文本.

    运行时容错：None -> "", 列表项缺 text -> 跳过, 非 dict -> 空字符串.
    """
    if isinstance(v, list):
        return "".join(seg.get("text", "") for seg in v if isinstance(seg, Mapping) and "text" in seg)
    if v is None:
        return ""
    return str(v)


def normalize_task_line(raw: Any) -> str:
    """RGDK 业务线标准化(1/2/3).

    支持数字、中文数字、以及常见描述性表述:
    - 2·教案
    - 第二类-知识教案
    - 第3类
    """
    s = str(raw or "").strip()
    if not s:
        return ""

    head = s.split("·")[0].strip()
    if head in ("1", "2", "3"):
        return head
    if head in CN_DIGIT:
        return CN_DIGIT[head]

    m = re.search(r"[123]", s)
    if m:
        return m.group(0)

    for cn, line_no in CN_DIGIT.items():
        if cn in s:
            return line_no
    return s


def map_fields(row: Mapping[str, Any], field_map: Mapping[str, str]) -> dict[str, str]:
    """按映射把飞书字段转为引擎内标准字段.

    field_map: {feishu_field_name -> std_field_name}
    """
    return {std: plain_text(row.get(feishu)) for feishu, std in field_map.items()}


def _text(row: Mapping[str, Any], key: str) -> str:
    """Read a single field as plain text."""
    return plain_text(row.get(key)).strip()


def resolve_expert_identities(row: Mapping[str, Any]) -> tuple[str, str]:
    """Resolve expert identity for claim/report/delivery (优先 expert_id，次 open_id，最后 assignee).

    Returns:
        (identity_value, source_key) 其中 source_key ∈ {"expert_id","open_id","assignee",""}
    """
    expert_id = _text(row, "expert_id")
    if expert_id:
        return expert_id, "expert_id"

    open_id = _text(row, "open_id")
    if open_id:
        return open_id, "open_id"

    assignee = _text(row, "assignee")
    if assignee:
        return assignee, "assignee"
    return "", ""


def claim_agent_id(row: Mapping[str, Any]) -> str:
    """Return dispatch claim token (e.g. expert:<id> or expert:<name>).

    For historical compatibility, if no id field is available, fallback to assignee
    (legacy S1/S2 rows).
    """
    identity, _ = resolve_expert_identities(row)
    return f"expert:{identity}" if identity else ""


def display_expert(row: Mapping[str, Any]) -> str:
    """Return the best human-display expert label for payloads/settlement."""
    identity, _ = resolve_expert_identities(row)
    return identity


def normalize_uid(row: Mapping[str, Any]) -> str:
    """统一 task_uid 提取与去空格.

    空 uid 会返回空串; 上游负责幂等过滤。
    """
    return plain_text(row.get("task_uid")).strip()


def read_bitable_rows(
    fetch_page,
    token: str,
    app_token: str,
    table_id: str,
    base_url: str,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    """读取一张飞书表全部记录(含分页)."""
    out: list[dict[str, Any]] = []
    page_token = ""
    while True:
        url = (
            f"{base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size={page_size}"
            + (f"&page_token={page_token}" if page_token else "")
        )
        payload = fetch_page("GET", url, token=token)
        data = (payload.get("data") or {}) if isinstance(payload, Mapping) else {}
        out.extend(data.get("items") or [])

        page_token = str(data.get("page_token") or "")
        if not data.get("has_more") or not page_token:
            return out


ASSIGNMENT_FIELDS: dict[str, str] = {
    "task_uid": "task_uid",
    "标题": "title",
    "业务线": "line",
    "一级类目": "category",
    "三级领域": "domain",
    "L级": "level",
    # 兼容新表单：前端可下沉到 expert_id/open_id，后端保持 assignee 向后兼容。
    "expert_id": "expert_id",
    "open_id": "open_id",
    "Expert ID": "expert_id",
    "专家ID": "expert_id",
    "指派专家": "assignee",
    "验收标准": "acceptance",
}


SUBMISSION_FIELDS: dict[str, str] = {
    "task_uid": "task_uid",
    "业务线": "line",
    "L级": "level",
    "expert_id": "expert_id",
    "open_id": "open_id",
    "Expert ID": "expert_id",
    "专家ID": "expert_id",
    "指派专家": "assignee",
    "验收标准": "acceptance",
    "标题": "title",
    "提交内容": "submission",
}


DELIVERY_FIELDS: dict[str, str] = {
    "task_uid": "task_uid",
    "业务线": "line",
    "L级": "level",
    "expert_id": "expert_id",
    "open_id": "open_id",
    "Expert ID": "expert_id",
    "专家ID": "expert_id",
    "指派专家": "assignee",
    "验收标准": "acceptance",
    "一级类目": "category",
    "三级领域": "domain",
    "标题": "title",
    "提交内容": "submission",
    "工时": "hours",
}

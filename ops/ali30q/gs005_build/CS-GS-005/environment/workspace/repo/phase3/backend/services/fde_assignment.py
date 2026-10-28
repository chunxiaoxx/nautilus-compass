"""S1 派活+验收标准 · human-author 路径纯编排核心.

turf:平台 own 派活决策;飞书读写=effect runner(vendored compass client);
引擎=现成 fde_dispatch API(零改动)。
🔴 human 任务不停留 open(kairos +20s 抢单实证)→ sync 必须 dispatch+具名 claim 背靠背。
"""
from __future__ import annotations

import json
from typing import Callable, Iterable

from services.fde_task_form_schema import claim_agent_id, resolve_expert_identities

REQUIRED = ("task_uid", "title", "assignee", "acceptance")


def _emit_attention(attention_fn, **payload: object) -> None:
    if attention_fn is None:
        return
    try:
        attention_fn(payload)
    except Exception:
        pass


def build_assignment_dispatch(row: dict) -> dict | None:
    """飞书派活行 → POST /dispatch body。缺 task_uid/assignee/acceptance 任一 = 不派(None)。

    验收标准(acceptance)是 S1 的第一痛点——没有它专家盲写,强制必填。
    富 spec 打包进 description JSON(dispatch 只持久化 3 字段·schema 实证)。
    """
    assignee, assignee_source = resolve_expert_identities(row)
    assignee = assignee.strip()
    if not assignee:
        return None
    if not str(row.get("task_uid") or "").strip() or not str(row.get("title") or "").strip() \
       or not str(row.get("acceptance") or "").strip():
        return None
    spec = {
        "producer": "human",
        "assignee": assignee,
        "assignee_source": assignee_source or "assignee",
        "line": str(row.get("line") or ""),
        "category": str(row.get("category") or ""),
        "domain": str(row.get("domain") or ""),
        "level": str(row.get("level") or ""),
        "acceptance": str(row["acceptance"]),
    }
    return {
        "task_uid": str(row["task_uid"]).strip(),
        "title": str(row["title"]).strip(),
        "description": json.dumps(spec, ensure_ascii=False),
    }


def sync_assignments(
    source,
    dispatch_fn: Callable[[dict], object],
    claim_fn: Callable[[str, str], object],
    already_assigned: Iterable[str] | None = None,
    attention_fn: Callable[[dict], None] | None = None,
) -> dict:
    """读派活表 → 去重 → dispatch+具名 claim 背靠背 → 汇总。fail-soft 单行不拖批。

    Returns {"assigned": [...], "skipped": [...], "lost_to_agent": [...], "failed": [...]}
    """
    seen = set(already_assigned or ())
    assigned, skipped, lost, failed = [], [], [], []
    for row in source.read_assignment_rows():
        body = build_assignment_dispatch(row)
        uid = (row.get("task_uid") or "").strip() or None
        if body is None or body["task_uid"] in seen:
            code = "s1_invalid_row" if body is None else "s1_duplicate_assigned"
            if uid:
                _emit_attention(
                    attention_fn,
                    stage="s1",
                    code=code,
                    task_uid=uid,
                    severity="warning",
                    title="S1 派发未生效",
                    detail=("未构建成功：acceptance 为空或字段缺失"
                            if body is None else "任务重复：已在已派发集合"),
                    context={"task_uid": uid, "stage": "s1"},
                )
            skipped.append(uid)
            continue
        uid = body["task_uid"]
        expert = claim_agent_id(row)
        if not expert:
            _emit_attention(
                attention_fn,
                stage="s1",
                code="s1_no_identity",
                task_uid=uid,
                severity="warning",
                title="S1 缺失专家身份",
                detail="S1 行无法解析 expert_id/open_id/assignee，无法 claim。请补充身份字段",
                context={"row": {"task_uid": uid, "line": row.get("line", ""), "title": row.get("title", "")},
                         "available_fields": list(row.keys())},
            )
            skipped.append(uid)
            continue
        try:
            dispatch_fn(body)
        except Exception:
            _emit_attention(
                attention_fn,
                stage="s1",
                code="s1_dispatch_error",
                task_uid=uid,
                severity="error",
                title="S1 dispatch 调用失败",
                detail="派单接口调用异常，请确认平台 key/网络/平台状态",
                context={"task_uid": uid, "dispatch_body": body},
            )
            failed.append(uid)
            continue
        try:
            claim_fn(uid, expert)
        except Exception:
            _emit_attention(
                attention_fn,
                stage="s1",
                code="s1_claim_conflict",
                task_uid=uid,
                severity="warning",
                title="S1 claim 失败",
                detail="任务被其他 agent 抢占或 claim API 异常",
                context={"task_uid": uid, "expert": expert},
            )
            lost.append(uid)
            seen.add(uid)
            continue
        assigned.append(uid)
        seen.add(uid)
    return {"assigned": assigned, "skipped": skipped,
            "lost_to_agent": lost, "failed": failed}

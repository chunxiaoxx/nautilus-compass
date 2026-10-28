"""W6 RSI soul 半边 · grounding 暴露端纯核.

跨 fde_verdicts 行展平打回项(pass is False)→ 可检索 grounding feed,每条带
reason 原文 + 已有结构键。纯派生·只读·fail-soft·**无语义检索**(compass bge-m3 turf)、
**无注入**(V5 producer turf)。复活 design_20260605 指的"死记录":verdict items[].reason。

resurrects the per-item fail-reason — the content-level RSI signal that V5 agent-fitness
(scalar pass率) and compass PoI (score) both discard.
"""
from __future__ import annotations

from typing import Iterable, Optional


def extract_grounding(
    verdict_rows: Iterable[dict],
    *,
    source: Optional[str] = None,
    veto_only: bool = False,
    since: Optional[str] = None,   # ISO8601 字符串·按 created_at 字典序比较
    limit: Optional[int] = None,
) -> list[dict]:
    """展平 verdict 行的打回 items(pass is False)成 grounding 记录列表.

    一条打回 item = ``it.get("pass") is False``(缺/None 不算失败·fail-soft)。
    veto_only=True 只留硬约束(veto)规则。返回纯 JSON-able dict 列表。
    """
    out: list[dict] = []
    for v in verdict_rows:
        if not isinstance(v, dict):
            continue
        if source is not None and v.get("source") != source:
            continue
        created = v.get("created_at")
        if since is not None and created is not None and created < since:
            continue
        items = v.get("items")
        if not isinstance(items, list):
            continue
        for it in items:
            if not isinstance(it, dict):
                continue
            if it.get("pass") is not False:        # 只打回项
                continue
            veto = bool(it.get("veto"))
            if veto_only and not veto:
                continue
            out.append({
                "reason": it.get("reason", ""),
                "task_uid": v.get("task_uid"),
                "checklist_uid": v.get("checklist_uid"),
                "item_id": it.get("id"),
                "veto": veto,
                "source": v.get("source"),
                "score": v.get("score"),
                "created_at": created,
            })
    if limit is not None:
        out = out[:limit]
    return out

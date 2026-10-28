"""Org OS · outcome 写回端点(断奶第一刀,U13 · 2026-09-25)。

- POST /api/platform/org/outcomes/writeback   批量写回 proposal_outcomes(幂等行级)
  鉴权 require_platform_key;输入=数据包(pre/post 快照 + items[ticket/fix_commit/...])
  逻辑:短 ticket(前缀)→ platform_improvement_proposals 完整 UUID 展开(全表含 pending,
  唯一前缀才认);已存在行跳过;外键不存在的记入 misaligned 不硬填(禁补估)。
  响应含行级回读对账(V-Sign 不变量②:inserted/skipped/misaligned/table_total)。
  表无 ORM model(裸 SQL 建表先例),本路由同用 text() 裸 SQL。
  键形:post_snapshot.source_letter(对齐 W41 55 行先例 2026-09-25,判分 SQL 按此键读)。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text

from utils.database import get_db
from utils.platform_auth import require_platform_key

router = APIRouter(prefix="/api/platform/org/outcomes", tags=["Org Outcomes Writeback"])


class WritebackItem(BaseModel):
    ticket: str
    fix_commit: str | None = None
    cluster: str | None = None
    batch: str | None = None
    note: str | None = None
    source: str | None = None


class WritebackPack(BaseModel):
    pack_id: str
    graded_by: str = "external-writeback"
    pre_snapshot: dict
    post_snapshot: dict
    items: list[WritebackItem]


def _expand_tickets(db, tickets: list[str]) -> tuple[dict[str, str], list[str]]:
    """短前缀 → 完整提案 UUID(全表含 pending;唯一匹配才认,歧义/无则 missing)。"""
    rows = db.execute(text("SELECT id FROM platform_improvement_proposals")).fetchall()
    by_prefix: dict[str, list[str]] = {}
    for (full,) in rows:
        by_prefix.setdefault(full[:8], []).append(full)
    id_map: dict[str, str] = {}
    missing: list[str] = []
    for t in tickets:
        exact = [c for c in by_prefix.get(t[:8], []) if c.startswith(t)]
        if len(exact) == 1:
            id_map[t] = exact[0]
        else:
            missing.append(t)
    return id_map, missing


@router.post("/writeback")
def writeback_outcomes(pack: WritebackPack, db=Depends(get_db),
                       _=Depends(require_platform_key)):
    tickets = [it.ticket for it in pack.items]
    id_map, missing = _expand_tickets(db, tickets)
    inserted = skipped = 0
    now = datetime.now(timezone.utc)
    for it in pack.items:
        pid = id_map.get(it.ticket)
        if not pid:
            continue
        if db.execute(text("SELECT 1 FROM proposal_outcomes WHERE proposal_id=:p"),
                      {"p": pid}).fetchone():
            skipped += 1
            continue
        post = {**pack.post_snapshot,
                "batch": it.batch, "fix_commit": it.fix_commit,
                "cluster": it.cluster, "note": it.note, "source_letter": it.source}
        db.execute(text(
            "INSERT INTO proposal_outcomes (proposal_id, pre_snapshot, post_snapshot, "
            "composite_delta, no_revert, graded_at, graded_by) "
            "VALUES (:p, CAST(:pre AS jsonb), CAST(:post AS jsonb), NULL, NULL, :t, :g)"),
            {"p": pid, "pre": json.dumps(pack.pre_snapshot, ensure_ascii=False),
             "post": json.dumps(post, ensure_ascii=False), "t": now, "g": pack.graded_by})
        inserted += 1
    db.commit()
    total = db.execute(text("SELECT COUNT(*) FROM proposal_outcomes")).fetchone()[0]
    return {"success": True, "data": {
        "pack_id": pack.pack_id, "inserted": inserted, "skipped": skipped,
        "misaligned": missing, "table_total": total}}

"""W6 RSI soul 半边 · grounding 暴露 API · GET /api/platform/fde/grounding.

只读暴露 fde_verdicts 打回项的避坑 reason feed,供 compass 摄入 bge-m3 语料库。
薄壳 = 查 FdeVerdict 行 → services.fde_grounding.extract_grounding → envelope。
**无语义检索/排序**(compass turf)·**无注入**(V5 turf)。镜像 fde_verdict.py 约定。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from utils.database import get_db
from models.fde_verdict import FdeVerdict
from services.fde_grounding import extract_grounding

router = APIRouter(prefix="/api/platform/fde", tags=["FDE Grounding (RSI)"])


@router.get("/grounding")
def get_grounding(
    source: str | None = None,
    veto_only: bool = False,
    since: str | None = None,
    limit: int | None = None,
    db=Depends(get_db),
):
    """跨题暴露打回项 grounding feed(只读派生)."""
    rows = (
        db.query(FdeVerdict)
        .order_by(FdeVerdict.created_at.desc(), FdeVerdict.id.desc())
        .all()
    )
    feed = extract_grounding(
        [r.to_dict() for r in rows],
        source=source, veto_only=veto_only, since=since, limit=limit,
    )
    return {"success": True, "data": feed, "error": None}

"""FDE human attention queue API.

Provides an explicit operator handoff surface for key failures. Endpoints:

- GET /api/platform/fde/attention: inspect pending/resolved attention records
- POST /api/platform/fde/attention: create an attention record (ops quick create)
- POST /api/platform/fde/attention/{attention_id}/resolve: record operator action
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from utils.database import get_db
from models.fde_attention import FdeAttention

router = APIRouter(prefix="/api/platform/fde", tags=["FDE Attention Queue"])
logger = logging.getLogger(__name__)


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _err(msg: str, status: int = 400):
    return JSONResponse(status_code=status,
                        content={"success": False, "data": None, "error": msg})


def _safe_json(v):
    return v if isinstance(v, (dict, list)) else {}


def _default_actions(stage: str, code: str) -> list[str]:
    if stage == "s1":
        if code in {"s1_no_identity", "s1_invalid_row"}:
            return ["manual_fix_identity", "skip_row", "keep_pending"]
        if code in {"s1_dispatch_error", "s1_claim_conflict", "s1_claim_lost"}:
            return ["rerun_s1_runner", "manual_fix_feishu_row", "ignore"]
        return ["manual_fix", "ignore"]
    if stage == "s2":
        if code in {"s2_empty_submission"}:
            return ["提醒专家补填提交内容", "rerun_s2_runner", "ignore"]
        return ["rerun_s2_runner", "排查QC异常", "ignore"]
    if stage == "s3":
        if code in {"s3_verdict_missing"}:
            return ["retry外部验收", "rerun_s3_runner", "ignore"]
        return ["rerun_s3_runner", "人工终止交付", "ignore"]
    return ["ignore"]


@router.get("/attention")
def list_attention(
    status: str = None,
    stage: str = None,
    task_uid: str = None,
    db=Depends(get_db),
):
    """List queued attention records for monitoring + manual selection."""
    q = db.query(FdeAttention)
    if status is not None:
        q = q.filter_by(status=str(status))
    if stage is not None:
        q = q.filter_by(stage=str(stage))
    if task_uid is not None:
        q = q.filter_by(task_uid=str(task_uid))

    rows = q.order_by(FdeAttention.created_at.desc()).all()
    items = []
    for row in rows:
        d = row.to_dict()
        d["suggested_actions"] = d.get("suggested_actions") or _default_actions(
            d["stage"], d["code"]
        )
        items.append(d)

    return _ok({
        "items": items,
        "summary": {
            "count": len(items),
            "pending": sum(1 for i in items if i["status"] == "pending"),
        },
    })


@router.post("/attention")
def create_attention(body: dict, db=Depends(get_db)):
    """Create a new manual attention row."""
    if not body.get("stage") or not body.get("code") or not body.get("title"):
        return _err("stage / code / title are required")
    stage = str(body["stage"]).strip()
    code = str(body["code"]).strip()
    if stage not in {"s1", "s2", "s3"}:
        return _err("stage must be one of s1, s2, s3")

    rec = FdeAttention(
        task_uid=(str(body.get("task_uid")).strip() or None),
        stage=stage,
        code=code,
        severity=str(body.get("severity") or "warning"),
        title=str(body["title"]),
        detail=str(body.get("detail") or ""),
        suggested_actions=_safe_json(body.get("suggested_actions")) or
        _default_actions(stage, code),
        context=_safe_json(body.get("context")),
    )
    db.add(rec)
    try:
        db.commit()
        db.refresh(rec)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("create attention failed: %s", str(exc)[:200])
        return _err("attention persistence failed", status=500)
    return _ok(rec.to_dict())


@router.post("/attention/{attention_id}/resolve")
def resolve_attention(attention_id: int, body: dict, db=Depends(get_db)):
    """Resolve one attention row with an operator choice."""
    row = db.query(FdeAttention).filter_by(id=int(attention_id)).first()
    if row is None:
        return _err("attention not found", status=404)

    status = str((body or {}).get("status") or "resolved").strip()
    if status not in {"resolved", "in_progress", "ignored"}:
        return _err("status must be one of resolved, in_progress, ignored")

    row.status = status
    row.resolution = str((body or {}).get("resolution") or "")
    row.resolution_note = str((body or {}).get("resolution_note") or "")
    row.resolved_by = str((body or {}).get("resolved_by") or "web")
    from datetime import datetime
    row.resolved_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(row)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("resolve attention failed: %s", str(exc)[:200])
        return _err("attention resolve failed", status=500)
    return _ok(row.to_dict())

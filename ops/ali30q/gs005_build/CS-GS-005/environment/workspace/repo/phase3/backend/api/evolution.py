"""
Evolution Ledger API — 查看平台进化历史和待发 NAU 奖励。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
import logging

from utils.database import get_db
from services.evolution_ledger import get_ledger_summary

router = APIRouter(prefix="/api/platform/evolution", tags=["Platform Evolution"])
logger = logging.getLogger(__name__)


def _ok(data): return {"success": True, "data": data, "error": None}
def _err(msg): return {"success": False, "data": None, "error": msg}


def _q(db, sql, params=None):
    try:
        return db.execute(text(sql), params or {})
    except Exception as exc:
        try: db.rollback()
        except Exception: pass
        raise exc


@router.get("")
def get_evolution_summary(db=Depends(get_db)):
    """进化账本摘要：总进化次数、NAU 分发总量、最新版本。"""
    try:
        return _ok(get_ledger_summary(db))
    except Exception as e:
        logger.error(f"get_evolution_summary: {e}")
        return _err(str(e))


@router.get("/history")
def get_evolution_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),
):
    """完整进化历史列表（按版本倒序）。"""
    try:
        rows = _q(db,
            "SELECT id, version_str, minor_version, change_type, "
            "       metric_delta, nau_rewarded, status, created_at "
            "FROM platform_evolution_log "
            "ORDER BY minor_version DESC LIMIT :limit OFFSET :offset",
            {"limit": limit, "offset": offset}
        ).fetchall()
        return _ok({
            "count": len(rows),
            "history": [{
                "id": r.id,
                "version": r.version_str,
                "change_type": r.change_type,
                "metric_delta": float(r.metric_delta or 0),
                "nau_rewarded": float(r.nau_rewarded or 0),
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            } for r in rows],
        })
    except Exception as e:
        logger.error(f"get_evolution_history: {e}")
        return _err(str(e))


@router.get("/pending-rewards")
def get_pending_rewards(
    agent_id: int = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
):
    """查看待发 NAU 奖励（按 agent 或全部）。"""
    try:
        conds = ["status='pending'"]
        params = {"limit": limit}
        if agent_id:
            conds.append("agent_id=:agent_id")
            params["agent_id"] = agent_id
        where = " AND ".join(conds)
        rows = _q(db,
            f"SELECT id, agent_id, amount, reason, source_id, created_at "
            f"FROM pending_nau_rewards WHERE {where} "
            f"ORDER BY created_at DESC LIMIT :limit",
            params
        ).fetchall()
        total = _q(db, "SELECT COALESCE(SUM(amount),0) FROM pending_nau_rewards WHERE status='pending'").scalar() or 0
        return _ok({
            "count": len(rows),
            "total_pending_nau": float(total),
            "rewards": [{
                "id": r.id,
                "agent_id": r.agent_id,
                "amount": float(r.amount),
                "reason": r.reason,
                "source_id": r.source_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            } for r in rows],
        })
    except Exception as e:
        logger.error(f"get_pending_rewards: {e}")
        return _err(str(e))

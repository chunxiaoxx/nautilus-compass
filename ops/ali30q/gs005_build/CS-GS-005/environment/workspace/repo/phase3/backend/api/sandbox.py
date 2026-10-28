"""
Sandbox API — 只读端点，查看实验状态和结果。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
import logging, json

from utils.database import get_db

router = APIRouter(prefix="/api/platform/sandbox", tags=["Platform Sandbox"])
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
def list_experiments(
    status: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """返回所有 A/B 实验列表。"""
    try:
        conds = ["1=1"]
        params = {"limit": limit}
        if status:
            conds.append("status=:status")
            params["status"] = status
        where = " AND ".join(conds)
        rows = _q(db,
            f"SELECT id, proposal_id, status, sandbox_traffic_pct, "
            f"       observation_hours, ends_at, created_at, finalized_at, sandbox_metrics "
            f"FROM sandbox_experiments WHERE {where} "
            f"ORDER BY created_at DESC LIMIT :limit",
            params
        ).fetchall()
        return _ok({"count": len(rows), "experiments": [{
            "id": r.id,
            "proposal_id": r.proposal_id,
            "status": r.status,
            "traffic_pct": r.sandbox_traffic_pct,
            "observation_hours": r.observation_hours,
            "ends_at": r.ends_at.isoformat() if r.ends_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "finalized_at": r.finalized_at.isoformat() if r.finalized_at else None,
            "metrics": r.sandbox_metrics if isinstance(r.sandbox_metrics, dict) else json.loads(r.sandbox_metrics or "{}"),
        } for r in rows]})
    except Exception as e:
        logger.error(f"list_experiments: {e}")
        return _err(str(e))


@router.get("/{exp_id}")
def get_experiment(exp_id: str, db=Depends(get_db)):
    """单个实验详情。"""
    try:
        row = _q(db,
            "SELECT * FROM sandbox_experiments WHERE id=:id",
            {"id": exp_id}
        ).fetchone()
        if not row:
            return _err("Experiment not found")
        return _ok({
            "id": row.id,
            "proposal_id": row.proposal_id,
            "proposed_change": row.proposed_change if isinstance(row.proposed_change, dict) else json.loads(row.proposed_change or "{}"),
            "status": row.status,
            "traffic_pct": row.sandbox_traffic_pct,
            "observation_hours": row.observation_hours,
            "ends_at": row.ends_at.isoformat() if row.ends_at else None,
            "baseline_metrics": row.baseline_metrics if isinstance(row.baseline_metrics, dict) else json.loads(row.baseline_metrics or "{}"),
            "sandbox_metrics": row.sandbox_metrics if isinstance(row.sandbox_metrics, dict) else json.loads(row.sandbox_metrics or "{}"),
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "finalized_at": row.finalized_at.isoformat() if row.finalized_at else None,
        })
    except Exception as e:
        logger.error(f"get_experiment: {e}")
        return _err(str(e))

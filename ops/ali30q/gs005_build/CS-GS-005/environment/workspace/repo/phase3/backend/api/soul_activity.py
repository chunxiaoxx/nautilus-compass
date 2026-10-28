"""Soul/platform activity API (W2.1 可感知) · GET /api/platform/soul/activity.

Read-only surface of what the platform is actually DOING — recent engine cycles
(ship activity) + FDE verdicts (external buyer acceptance) + a 成绩 summary. This
is the "可感知" half of the 4-way coupling: it makes the soul's work visible
without touching the self-referential internal economy.

DELIBERATELY does NOT read pending_nau_rewards / votes (anchor #3 · those are the
self-referential signals the benchmark pivot moved away from). Each table query
is fail-soft: a missing table yields an empty section, never a 500.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from utils.database import get_db

router = APIRouter(prefix="/api/platform/soul", tags=["Soul Activity"])
logger = logging.getLogger(__name__)


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _safe_rows(db, sql: str, params: dict) -> list:
    """Run a read-only SELECT · return [] on any error (e.g. table absent)."""
    try:
        return db.execute(text(sql), params).fetchall()
    except Exception as exc:  # noqa: BLE001 — fail-soft · never 500 the dashboard
        try:
            db.rollback()
        except Exception:
            pass
        logger.debug("soul/activity query skipped: %s", str(exc)[:120])
        return []


@router.get("/activity")
def soul_activity(limit: int = Query(20, ge=1, le=100), db=Depends(get_db)):
    """Recent engine cycles + FDE verdicts + a 成绩 summary. Read-only."""
    cycle_rows = _safe_rows(
        db,
        "SELECT cycle_id, goal_source, ship_status, git_sha, created_at "
        "FROM engine_cycle_outcomes ORDER BY created_at DESC LIMIT :lim",
        {"lim": limit},
    )
    recent_cycles = [
        {
            "cycle_id": r[0],
            "goal_source": r[1],
            "ship_status": r[2],
            "git_sha": r[3],
            "created_at": str(r[4]) if r[4] is not None else None,
        }
        for r in cycle_rows
    ]

    verdict_rows = _safe_rows(
        db,
        "SELECT verdict_id, task_uid, source, overall_pass, veto_failed, score, created_at "
        "FROM fde_verdicts ORDER BY created_at DESC LIMIT :lim",
        {"lim": limit},
    )
    fde_verdicts = [
        {
            "verdict_id": r[0],
            "task_uid": r[1],
            "source": r[2],
            "overall_pass": bool(r[3]),
            "veto_failed": bool(r[4]),
            "score": r[5],
            "created_at": str(r[6]) if r[6] is not None else None,
        }
        for r in verdict_rows
    ]

    summary = {
        "cycles_total": len(recent_cycles),
        "ships_success": sum(1 for c in recent_cycles if c["ship_status"] == "success"),
        "verdicts_total": len(fde_verdicts),
        "verdicts_passed": sum(1 for v in fde_verdicts if v["overall_pass"]),
    }

    return _ok({
        "recent_cycles": recent_cycles,
        "fde_verdicts": fde_verdicts,
        "summary": summary,
    })

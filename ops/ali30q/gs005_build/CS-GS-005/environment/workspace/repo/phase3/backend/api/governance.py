"""
Governance API — Agent Parliament endpoints.

External agents can participate in platform governance:
  POST /api/governance/propose  — submit improvement proposals (senator+)
  POST /api/governance/review   — peer review tasks (citizen+)
  GET  /api/governance/parliament — parliament summary
  GET  /api/governance/tier/{agent_id} — check governance tier
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from utils.database import get_db

router = APIRouter(prefix="/api/governance", tags=["Governance"])
logger = logging.getLogger(__name__)


def _ok(data): return {"success": True, "data": data, "error": None}
def _err(msg): return {"success": False, "data": None, "error": msg}


@router.get("/parliament")
def parliament_summary(db: Session = Depends(get_db)):
    """Get current governance state: tier distribution, proposals, votes."""
    try:
        from services.agent_parliament import get_parliament_summary
        return _ok(get_parliament_summary(db))
    except Exception as e:
        return _err(str(e))


@router.get("/tier/{agent_id}")
def agent_tier(agent_id: int, db: Session = Depends(get_db)):
    """Check an agent's governance tier."""
    try:
        from services.agent_parliament import get_governance_tier
        return _ok(get_governance_tier(db, agent_id))
    except Exception as e:
        return _err(str(e))


@router.post("/propose")
def submit_proposal(body: dict, db: Session = Depends(get_db)):
    """External agent submits a platform improvement proposal. Requires senator tier."""
    try:
        from services.agent_parliament import submit_external_proposal
        agent_id = body.get("agent_id")
        if not agent_id:
            return _err("agent_id required")
        result = submit_external_proposal(
            db, agent_id,
            root_cause=body.get("root_cause", ""),
            proposed_change=body.get("proposed_change", {}),
            expected_impact=body.get("expected_impact", ""),
            rollback_plan=body.get("rollback_plan", "Revert and monitor 24h"),
        )
        return _ok(result) if result.get("success") else _err(result.get("error"))
    except Exception as e:
        return _err(str(e))


@router.post("/review")
def peer_review(body: dict, db: Session = Depends(get_db)):
    """Agent reviews another agent's completed task. Requires citizen tier."""
    try:
        from services.agent_parliament import submit_peer_review
        result = submit_peer_review(
            db,
            reviewer_id=body.get("reviewer_id"),
            task_id=body.get("task_id"),
            score=float(body.get("score", 3.0)),
            feedback=body.get("feedback", ""),
        )
        return _ok(result) if result.get("success") else _err(result.get("error"))
    except Exception as e:
        return _err(str(e))

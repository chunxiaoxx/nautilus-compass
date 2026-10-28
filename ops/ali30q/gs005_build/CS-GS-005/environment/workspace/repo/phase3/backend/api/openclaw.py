"""
OpenClaw Protocol API — External agent lifecycle endpoints.

Exposes the full OpenClaw workflow:
  POST /api/openclaw/onboard       — Register an external agent
  POST /api/openclaw/heartbeat     — Send heartbeat (keep alive)
  POST /api/openclaw/work-cycle    — Execute one work cycle (claim→execute→submit)
  GET  /api/openclaw/tasks         — Browse available tasks
  GET  /api/openclaw/leaderboard   — PoW leaderboard
  POST /api/openclaw/callback      — Register callback URL for task push
  GET  /api/openclaw/status/{id}   — Agent status + PoW score
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from models.database import Agent, APIKey
from utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------- Auth helper ----------

def _get_agent_by_key(api_key: str, db: Session) -> Agent:
    """Resolve API key to Agent, raise 401 if invalid."""
    key_row = db.query(APIKey).filter(APIKey.key == api_key, APIKey.is_active == True).first()
    if not key_row:
        raise HTTPException(401, "Invalid or expired API key")
    agent = db.query(Agent).filter(Agent.agent_id == key_row.agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found for this API key")
    return agent


# ---------- Request models ----------

class OnboardRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    capabilities: list[str] = Field(default=["general_computation"])
    callback_url: Optional[str] = None
    description: Optional[str] = None


class CallbackRequest(BaseModel):
    callback_url: str


# ---------- Endpoints ----------

@router.post("/onboard")
async def onboard_agent(body: OnboardRequest, db: Session = Depends(get_db)):
    """
    Register a new external agent via OpenClaw protocol.

    Returns agent_id, api_key, wallet_address, and available tasks.
    """
    from services.openclaw_protocol import get_openclaw_protocol

    protocol = get_openclaw_protocol()
    result = await protocol.onboard_agent(
        agent_data={
            "name": body.name,
            "capabilities": body.capabilities,
            "callback_url": body.callback_url,
            "description": body.description or f"OpenClaw agent: {body.name}",
        },
        db=db,
    )

    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Onboarding failed"))

    return result


@router.post("/heartbeat")
async def agent_heartbeat(
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: Session = Depends(get_db),
):
    """
    Send heartbeat. Keeps agent alive and prevents coma/death.

    Must be called at least every 15 minutes.
    """
    agent = _get_agent_by_key(x_agent_key, db)

    from services.openclaw_protocol import get_openclaw_protocol
    protocol = get_openclaw_protocol()
    protocol._heartbeats[agent.agent_id] = __import__("datetime").datetime.utcnow()

    # Return available task count as hint
    # 2026-10-09 修:原数 AcademicTask(老学术市场残骸)恒 0 → kairos 长期"看不见任务";
    # 真任务源=platform_bounties(status=open AND assigned_to=本 agent),双形态兼容(整数 id/名字串)。
    pending_count = db.execute(text(
        "SELECT count(*) FROM platform_bounties "
        "WHERE status='open' AND assigned_to IS NOT NULL "
        "AND (assigned_to=:aid OR lower(assigned_to)=lower(:aname))"),
        {"aid": str(agent.agent_id), "aname": agent.name or ""}).scalar() or 0

    return {
        "success": True,
        "data": {
            "agent_id": agent.agent_id,
            "status": "alive",
            "pending_tasks": pending_count,
            "message": "Heartbeat recorded" + (
                f" — {pending_count} tasks waiting!" if pending_count > 0 else ""
            ),
        },
    }


@router.post("/work-cycle")
async def agent_work_cycle(
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: Session = Depends(get_db),
):
    """
    Execute one complete work cycle:
    1. Record heartbeat
    2. Find and claim best matching task
    3. Execute task
    4. Submit result
    5. Calculate PoW score
    6. Return summary with next available tasks

    This is the core loop for autonomous agents.
    """
    agent = _get_agent_by_key(x_agent_key, db)

    from services.openclaw_protocol import get_openclaw_protocol
    protocol = get_openclaw_protocol()
    result = await protocol.agent_work_cycle(agent.agent_id, db)

    return result


@router.get("/tasks")
async def browse_tasks(
    type: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Browse available tasks. No auth required — tasks are public.

    Filter by type: general_computation, jc_constitutive, curve_fitting, etc.
    """
    from models.database import AcademicTask

    query = db.query(AcademicTask).filter(AcademicTask.status.in_(["pending", "open"]))
    if type:
        query = query.filter(AcademicTask.task_type == type)

    # Priority: bounty > platform_meta > regular > self-improvement
    from sqlalchemy import case
    priority = case(
        (AcademicTask.task_id.startswith("bounty_"), 0),
        (AcademicTask.task_type == "platform_meta", 1),
        (AcademicTask.task_id.startswith("self_"), 3),
        (AcademicTask.task_id.startswith("explore_"), 3),
        else_=2,
    )
    tasks = query.order_by(priority, AcademicTask.token_reward.desc().nullslast(), AcademicTask.created_at.desc()).limit(min(limit, 50)).all()

    return {
        "success": True,
        "data": {
            "tasks": [
                {
                    "task_id": t.task_id,
                    "title": t.title,
                    "description": (t.description or "")[:2000],
                    "task_type": t.task_type,
                    "token_reward": t.token_reward,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "is_bounty": t.task_id.startswith("bounty_"),
                    "is_self_improvement": t.task_id.startswith("self_"),
                }
                for t in tasks
            ],
            "total": len(tasks),
        },
    }


@router.get("/leaderboard")
async def get_leaderboard(db: Session = Depends(get_db)):
    """PoW leaderboard — all agents ranked by work contribution."""
    from services.openclaw_protocol import get_openclaw_protocol
    protocol = get_openclaw_protocol()
    board = await protocol.get_leaderboard(db)
    return {"success": True, "data": {"leaderboard": board}}


@router.post("/callback")
async def register_callback(
    body: CallbackRequest,
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: Session = Depends(get_db),
):
    """
    Register a callback URL for receiving task push notifications.

    When new tasks are published, the platform will POST to this URL.
    """
    agent = _get_agent_by_key(x_agent_key, db)

    from services.openclaw_protocol import get_openclaw_protocol
    protocol = get_openclaw_protocol()
    protocol._callbacks[agent.agent_id] = body.callback_url

    return {
        "success": True,
        "data": {
            "agent_id": agent.agent_id,
            "callback_url": body.callback_url,
            "message": "Callback registered. You will receive task notifications.",
        },
    }


@router.get("/status/{agent_id}")
async def agent_status(agent_id: int, db: Session = Depends(get_db)):
    """Get agent status including PoW score, heartbeat, and stats."""
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")

    from services.openclaw_protocol import get_openclaw_protocol
    protocol = get_openclaw_protocol()

    pow_data = await protocol.calculate_pow(agent_id, db)

    return {
        "success": True,
        "data": {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "is_online": protocol._is_online(agent_id),
            "is_active": agent.is_active,
            "agent_status": getattr(agent, "agent_status", "unknown"),
            "completed_tasks": agent.completed_tasks or 0,
            "failed_tasks": getattr(agent, "failed_tasks", 0) or 0,
            "reputation": agent.reputation or 100,
            "pow": pow_data.get("data", {}),
            "has_callback": agent_id in protocol._callbacks,
        },
    }


@router.post("/maintenance/fix-agents")
async def maintenance_fix_agents(
    secret: str,
    db: Session = Depends(get_db),
):
    """
    One-time maintenance: fix agents with stale/unmatched capabilities
    and reset stuck failed tasks.

    Requires ?secret=<ADMIN_SECRET> query param.
    """
    import os
    admin_secret = os.getenv("ADMIN_SECRET", "")
    if not admin_secret or secret != admin_secret:
        raise HTTPException(403, "Forbidden")

    import json
    from models.database import AcademicTask

    # 1. Fix agents whose only capability has zero pending tasks
    agents = db.query(Agent).filter(Agent.owner == "openclaw").all()
    fixed_agents = []
    valid_types = {
        r[0] for r in db.query(AcademicTask.task_type).filter(
            AcademicTask.status == "pending"
        ).distinct().all()
    }
    # If no pending tasks exist, use the full known set
    if not valid_types:
        valid_types = {"general_computation", "statistical_analysis", "jc_constitutive",
                       "code_generation", "data_analysis"}

    for ag in agents:
        try:
            caps = json.loads(ag.specialties or "[]")
        except Exception:
            caps = []
        if caps and not any(c in valid_types for c in caps):
            ag.specialties = json.dumps(["general_computation"])
            fixed_agents.append({"id": ag.agent_id, "name": ag.name, "old_caps": caps})

    # 2. Reset recently-failed tasks (failed within last 24h) back to pending
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(hours=24)
    failed_tasks = (
        db.query(AcademicTask)
        .filter(
            AcademicTask.status == "failed",
            AcademicTask.updated_at >= cutoff,
        )
        .all()
    )
    reset_tasks = []
    for t in failed_tasks:
        t.status = "pending"
        t.user_id = None
        t.result_error = None
        reset_tasks.append(t.task_id)

    db.commit()

    return {
        "success": True,
        "data": {
            "agents_fixed": len(fixed_agents),
            "agents": fixed_agents,
            "tasks_reset": len(reset_tasks),
            "task_ids": reset_tasks[:20],
        },
    }

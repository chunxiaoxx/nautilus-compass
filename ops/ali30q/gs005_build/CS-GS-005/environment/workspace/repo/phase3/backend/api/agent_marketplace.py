"""
Agent Marketplace API - External agents browse, claim, submit, and earn.

This is the public-facing marketplace that lets external agents (e.g. OpenClaw)
participate in the Nautilus ecosystem: discover tasks, claim them, submit results,
review peers, and track earnings.

Authentication: X-Agent-Key header mapped to api_keys table.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import os
import json
import secrets

from models.database import Agent, APIKey, AcademicTask
from utils.database import get_db
from utils.auth import generate_api_key

router = APIRouter()
logger = logging.getLogger(__name__)

TESTING = os.getenv("TESTING", "false").lower() == "true"
limiter = Limiter(key_func=get_remote_address, enabled=not TESTING)

# Default reward points by task type
TASK_TYPE_REWARDS: Dict[str, int] = {
    "jc_constitutive": 500,
    "thmc_coupling": 800,
    "curve_fitting": 300,
    "ode_simulation": 400,
    "pde_simulation": 600,
    "monte_carlo": 500,
    "statistical_analysis": 350,
    "ml_training": 700,
    "data_visualization": 200,
    "physics_simulation": 500,
    "general_computation": 250,
}

CLAIM_TIME_LIMIT_SECONDS = 3600  # 1 hour


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class MarketTaskItem(BaseModel):
    task_id: str
    title: str
    description: str
    task_type: str
    reward_points: int
    estimated_time: str
    status: str
    created_at: str


class MarketTaskListResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
    error: Optional[str] = None


class ClaimResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
    error: Optional[str] = None


class SubmitRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=500000)
    output: str = Field(..., max_length=500000)
    metrics: Optional[Dict[str, Any]] = Field(
        None, description="Result metrics, e.g. {r_squared: 0.98}"
    )


class ReviewRequest(BaseModel):
    passed: bool
    reason: str = Field(..., min_length=1, max_length=5000)
    suggested_fixes: Optional[str] = Field(None, max_length=10000)


class AgentRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    capabilities: Optional[List[str]] = None
    api_endpoint: Optional[str] = Field(None, max_length=500)


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

def _get_agent_by_key(
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: Session = Depends(get_db),
) -> Agent:
    """Resolve X-Agent-Key header to an Agent row."""
    api_key_row = (
        db.query(APIKey)
        .filter(APIKey.key == x_agent_key, APIKey.is_active == True)
        .first()
    )
    if not api_key_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_API_KEY",
                    "message": "Invalid or inactive API key / API Key 无效或已停用",
                }
            },
        )
    agent = db.query(Agent).filter(Agent.agent_id == api_key_row.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "AGENT_NOT_FOUND",
                    "message": "Agent associated with this key not found / 未找到关联的 Agent",
                }
            },
        )
    # Touch last_used_at
    api_key_row.last_used_at = datetime.utcnow()
    db.commit()
    return agent


def _reward_points_for(task_type: str) -> int:
    """Return reward points for a task type."""
    return TASK_TYPE_REWARDS.get(task_type, 250)


def _estimated_time_for(task_type: str) -> str:
    """Return human-readable estimated time."""
    estimates: Dict[str, str] = {
        "jc_constitutive": "30-60 min",
        "thmc_coupling": "45-90 min",
        "curve_fitting": "15-30 min",
        "ml_training": "30-60 min",
        "pde_simulation": "30-60 min",
    }
    return estimates.get(task_type, "15-45 min")


# ---------------------------------------------------------------------------
# 1. GET /tasks - Browse available tasks
# ---------------------------------------------------------------------------

@router.get("/bounties")
async def list_bounties(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """公开 bounty 清单(SPA useBounties 数据源 · R3 补缺 2026-10-09)。
    读 platform_bounties(DMAS 正本),映射 SPA Bounty 字段。status 过滤页面侧做。"""
    rows = db.execute(text(
        "SELECT bounty_id, title, status, reward_nau, assigned_to, claimed_by, "
        "score, posted_at FROM platform_bounties "
        "ORDER BY posted_at DESC LIMIT :lim"),
        {"lim": limit}).fetchall()
    return {"bounties": [
        {"id": r[0], "title": r[1], "status": r[2], "reward": int(r[3] or 0),
         "reward_unit": "NAU", "assignee": r[4] or r[5],
         "score_overall": float(r[6]) if r[6] is not None else None,
         "created_at": r[7].isoformat() if r[7] else None}
        for r in rows]}


@router.get("/tasks")
@limiter.limit("60/minute")
async def browse_tasks(
    request: Request,
    type: Optional[str] = Query(None, description="Filter by task_type"),
    min_reward: Optional[int] = Query(None, ge=0, description="Minimum reward points"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Browse available (unclaimed) tasks in the marketplace.

    Returns tasks with status='pending' and no assigned agent.
    Supports filtering by task type and minimum reward.
    """
    query = db.query(AcademicTask).filter(
        AcademicTask.status == "pending",
        AcademicTask.user_id == None,  # noqa: E711 - unclaimed
    )

    # 2026-10-10 换源:AcademicTask 老市场已空,列表改读 platform_bounties 真单(DMAS 正本);
    # 老 AcademicTask 查询保留为 legacy 附加(历史任务仍可见)。
    bounty_rows = db.execute(text(
        "SELECT bounty_id, title, description, COALESCE(task_type,'general'), "
        "reward_nau, 'open' AS status, posted_at FROM platform_bounties "
        "WHERE status='open' AND claimed_by IS NULL "
        "ORDER BY posted_at DESC LIMIT 100")).fetchall()
    bounty_items: List[MarketTaskItem] = [
        MarketTaskItem(
            task_id=r[0], title=(r[1] or "")[:200],
            description=(r[2] or "")[:500], task_type=r[3],
            reward_points=int(r[4] or 0), estimated_time="",
            status=r[5],
            created_at=r[6].isoformat() if r[6] else "",
        ) for r in bounty_rows
    ]

    if type:
        query = query.filter(AcademicTask.task_type == type)

    # We filter by reward in-memory since reward_points is computed
    all_rows = query.order_by(AcademicTask.created_at.desc()).all()

    items: List[MarketTaskItem] = list(bounty_items)  # bounty 真单在前
    for row in all_rows:
        rp = _reward_points_for(row.task_type)
        if min_reward is not None and rp < min_reward:
            continue
        items.append(MarketTaskItem(
            task_id=row.task_id,
            title=row.title,
            description=row.description[:500],
            task_type=row.task_type,
            reward_points=rp,
            estimated_time=_estimated_time_for(row.task_type),
            status=row.status,
            created_at=row.created_at.isoformat() if row.created_at else "",
        ))

    total = len(items)
    start = (page - 1) * limit
    page_items = items[start : start + limit]

    return {
        "success": True,
        "data": {
            "tasks": [i.model_dump() for i in page_items],
            "total": total,
            "page": page,
            "limit": limit,
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# 2. POST /tasks/{task_id}/claim - Claim a task
# ---------------------------------------------------------------------------

@router.post("/tasks/{task_id}/claim")
@limiter.limit("20/minute")
async def claim_task(
    request: Request,
    task_id: str,
    agent: Agent = Depends(_get_agent_by_key),
    db: Session = Depends(get_db),
):
    """
    Claim a pending task. Sets the agent as the assignee.

    The agent must complete the task within 1 hour.
    """
    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task '{task_id}' not found / 任务未找到",
                }
            },
        )

    if task.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "TASK_NOT_AVAILABLE",
                    "message": f"Task is '{task.status}', not claimable / 任务状态为 '{task.status}'，无法领取",
                }
            },
        )

    if task.user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "TASK_ALREADY_CLAIMED",
                    "message": "Task already claimed by another agent / 任务已被其他 Agent 领取",
                }
            },
        )

    # Assign
    task.user_id = agent.id
    task.status = "processing"
    task.updated_at = datetime.utcnow()
    db.commit()

    deadline = datetime.utcnow() + timedelta(seconds=CLAIM_TIME_LIMIT_SECONDS)
    logger.info(
        "Agent %s (id=%s) claimed task %s", agent.name, agent.agent_id, task_id
    )

    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "status": "processing",
            "agent_id": agent.agent_id,
            "deadline": deadline.isoformat(),
            "time_limit_seconds": CLAIM_TIME_LIMIT_SECONDS,
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# 3. POST /tasks/{task_id}/submit - Submit result
# ---------------------------------------------------------------------------

@router.post("/tasks/{task_id}/submit")
@limiter.limit("10/minute")
async def submit_result(
    request: Request,
    task_id: str,
    body: SubmitRequest,
    agent: Agent = Depends(_get_agent_by_key),
    db: Session = Depends(get_db),
):
    """
    Submit task result. Validates ownership, runs Raid audit, awards points.
    """
    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task '{task_id}' not found / 任务未找到",
                }
            },
        )

    # Verify this agent owns the claim
    if task.user_id != agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "NOT_TASK_OWNER",
                    "message": "You did not claim this task / 你未领取此任务",
                }
            },
        )

    if task.status not in ("processing",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_STATUS",
                    "message": f"Task status '{task.status}' does not accept submissions / 当前状态不接受提交",
                }
            },
        )

    # Persist result
    task.result_code = body.code
    task.result_output = body.output
    if body.metrics:
        # Store metrics in parameters field as JSON
        existing_params = {}
        if task.parameters:
            try:
                existing_params = json.loads(task.parameters)
            except (json.JSONDecodeError, TypeError):
                existing_params = {}
        existing_params["submission_metrics"] = body.metrics
        task.parameters = json.dumps(existing_params)

    # Run Raid audit (non-blocking best-effort)
    audit_passed = True
    audit_reason = ""
    try:
        from services.rehoboam import get_rehoboam
        rehoboam = get_rehoboam()
        audit_result = await rehoboam.verify_task_result(task_id)
        if audit_result and not audit_result.get("passed", True):
            audit_passed = False
            audit_reason = audit_result.get("reason", "Audit flagged")
    except Exception as e:
        logger.warning("Raid audit skipped for %s: %s", task_id, e)

    if audit_passed:
        task.status = "completed"
        task.audit_status = "passed"
        reward_pts = _reward_points_for(task.task_type)
        # Award points to agent
        agent.completed_tasks = (agent.completed_tasks or 0) + 1
        agent.total_earnings = (agent.total_earnings or 0) + reward_pts
        if agent.current_tasks and agent.current_tasks > 0:
            agent.current_tasks -= 1

        # Update survival scores (PoW integration)
        try:
            from services.survival_service import SurvivalService
            task_duration = (datetime.utcnow() - (task.created_at or datetime.utcnow())).total_seconds()
            SurvivalService.update_scores_on_task_completion(
                db=db,
                agent_id=agent.agent_id,
                task_reward=float(reward_pts),
                task_duration_seconds=task_duration,
                published_duration_seconds=3600.0,
                task_rating=None,
            )
            SurvivalService.record_income(
                db=db,
                agent_id=agent.agent_id,
                amount=reward_pts,
                category="task_reward",
                task_id=task_id,
            )
            logger.info("Survival scores updated for agent %s on task %s", agent.agent_id, task_id)
        except Exception as surv_err:
            db.rollback()
            logger.warning("Survival update failed for agent: %s", surv_err)
    else:
        task.status = "failed"
        task.audit_status = "flagged"
        task.audit_reason = audit_reason
        reward_pts = 0

    task.updated_at = datetime.utcnow()
    db.commit()

    # Evolution Pulse: emit task lifecycle event (activates capability_evolution + reputation)
    try:
        import asyncio
        from services.event_bus import emit, Events
        event_type = Events.TASK_COMPLETED if audit_passed else Events.TASK_FAILED
        asyncio.ensure_future(emit(event_type, {
            "task_id": task_id,
            "agent_id": agent.agent_id,
            "task_type": task.task_type,
            "success": audit_passed,
            "reward_points": reward_pts,
        }))
    except Exception:
        pass  # event emission must never block task submission

    logger.info(
        "Agent %s submitted task %s: audit=%s reward=%d",
        agent.agent_id, task_id, "passed" if audit_passed else "flagged", reward_pts,
    )

    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "status": task.status,
            "audit": task.audit_status,
            "reward_points": reward_pts,
        },
        "error": None if audit_passed else audit_reason,
    }


# ---------------------------------------------------------------------------
# 4. POST /tasks/{task_id}/review - Peer review
# ---------------------------------------------------------------------------

@router.post("/tasks/{task_id}/review")
@limiter.limit("20/minute")
async def review_task(
    request: Request,
    task_id: str,
    body: ReviewRequest,
    agent: Agent = Depends(_get_agent_by_key),
    db: Session = Depends(get_db),
):
    """
    Submit a peer review for a completed task. Reviewer earns review points.
    """
    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task '{task_id}' not found / 任务未找到",
                }
            },
        )

    # Reviews allowed on completed tasks awaiting peer review
    if task.status not in ("completed",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "NOT_REVIEWABLE",
                    "message": f"Task status '{task.status}' is not reviewable / 任务当前不可评审",
                }
            },
        )

    # Cannot review own work
    if task.user_id == agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "SELF_REVIEW_FORBIDDEN",
                    "message": "Cannot review your own task / 不能评审自己的任务",
                }
            },
        )

    # Store review in audit fields
    review_data = {
        "reviewer_agent_id": agent.agent_id,
        "passed": body.passed,
        "reason": body.reason,
        "suggested_fixes": body.suggested_fixes,
        "reviewed_at": datetime.utcnow().isoformat(),
    }
    task.audit_reason = json.dumps(review_data)
    task.audit_status = "peer_reviewed"
    task.updated_at = datetime.utcnow()

    # Award reviewer points
    review_points = 50
    agent.total_earnings = (agent.total_earnings or 0) + review_points
    db.commit()

    logger.info(
        "Agent %s reviewed task %s: passed=%s", agent.agent_id, task_id, body.passed
    )

    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "review_points_earned": review_points,
            "review_passed": body.passed,
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# 5. GET /me - Agent profile
# ---------------------------------------------------------------------------

@router.get("/me")
@limiter.limit("60/minute")
async def agent_profile(
    request: Request,
    agent: Agent = Depends(_get_agent_by_key),
    db: Session = Depends(get_db),
):
    """
    Get the authenticated agent's profile and earnings summary.
    """
    total_tasks = (agent.completed_tasks or 0) + (agent.failed_tasks or 0)
    success_rate = (
        round((agent.completed_tasks or 0) / total_tasks * 100, 1)
        if total_tasks > 0 else 0.0
    )

    # Compute rank by total_earnings
    rank = (
        db.query(func.count(Agent.id))
        .filter(Agent.total_earnings > (agent.total_earnings or 0))
        .scalar() or 0
    ) + 1

    return {
        "success": True,
        "data": {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "description": agent.description,
            "reputation": agent.reputation,
            "total_points": agent.total_earnings or 0,
            "completed_tasks": agent.completed_tasks or 0,
            "failed_tasks": agent.failed_tasks or 0,
            "current_tasks": agent.current_tasks or 0,
            "success_rate": success_rate,
            "rank": rank,
            "created_at": agent.created_at.isoformat() if agent.created_at else "",
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# 6. GET /leaderboard - Top agents
# ---------------------------------------------------------------------------

@router.get("/leaderboard")
@limiter.limit("30/minute")
async def leaderboard(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get leaderboard of top agents ranked by total points (earnings).
    """
    agents = (
        db.query(Agent)
        .order_by(Agent.total_earnings.desc())
        .limit(limit)
        .all()
    )

    entries = []
    for rank_idx, a in enumerate(agents, start=1):
        total = (a.completed_tasks or 0) + (a.failed_tasks or 0)
        entries.append({
            "rank": rank_idx,
            "agent_id": a.agent_id,
            "name": a.name,
            "total_points": a.total_earnings or 0,
            "completed_tasks": a.completed_tasks or 0,
            "success_rate": round((a.completed_tasks or 0) / total * 100, 1) if total > 0 else 0.0,
            "reputation": a.reputation,
        })

    return {
        "success": True,
        "data": {"leaderboard": entries, "total": len(entries)},
        "error": None,
    }


# ---------------------------------------------------------------------------
# 7. POST /register - Self-registration
# ---------------------------------------------------------------------------

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register_agent(
    request: Request,
    body: AgentRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new external agent. Returns agent_id + API key.

    New agents receive 500 initial points and 7-day newcomer protection.
    """
    # Generate a unique agent_id (max existing + 1)
    max_id = db.query(func.max(Agent.agent_id)).scalar() or 0
    new_agent_id = max_id + 1

    # Generate a placeholder owner address for external agents
    owner_address = f"0x{'0' * 32}{new_agent_id:08x}"

    specialties_json = json.dumps(body.capabilities) if body.capabilities else None

    agent = Agent(
        agent_id=new_agent_id,
        owner=owner_address,
        name=body.name,
        description=f"External agent. Endpoint: {body.api_endpoint or 'N/A'}",
        reputation=100,
        specialties=specialties_json,
        current_tasks=0,
        completed_tasks=0,
        failed_tasks=0,
        total_earnings=500,  # Initial 500 points
        created_at=datetime.utcnow(),
    )
    db.add(agent)
    db.flush()  # get agent.id populated

    # Create API key
    api_key_value = generate_api_key()
    api_key_row = APIKey(
        key=api_key_value,
        agent_id=new_agent_id,
        name=f"{body.name} marketplace key",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(api_key_row)
    db.commit()

    logger.info(
        "New marketplace agent registered: id=%d name=%s", new_agent_id, body.name
    )

    return {
        "success": True,
        "data": {
            "agent_id": new_agent_id,
            "name": body.name,
            "api_key": api_key_value,
            "initial_points": 500,
            "protection_days": 7,
            "protection_expires": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "message": "Welcome to Nautilus! / 欢迎加入 Nautilus!",
        },
        "error": None,
    }

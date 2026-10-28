"""
A2A Gateway — standard A2A protocol inbound endpoint.
External agents send A2A messages → mapped to Nautilus internal APIs.

Phase 3.2 of the Nautilus strategic plan.
"""
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

_ALLOWED_TASK_TYPES = {"general_computation", "research_synthesis", "code_generation", "arc_puzzle", "agent_bounty", "data_analysis"}

def _safe_task_type(val) -> str:
    if isinstance(val, str) and val in _ALLOWED_TASK_TYPES:
        return val
    return "general_computation"

def _safe_reward(val) -> float:
    try:
        r = float(val) if val is not None else 10.0
        return max(1.0, min(r, 500.0))  # clamp 1-500 NAU
    except (ValueError, TypeError):
        return 10.0


class A2AMessage(BaseModel):
    """Standard A2A protocol message."""
    sender: str                     # sender agent name or URL (max 200 chars)
    sender_url: Optional[str] = None  # sender's .well-known/agent.json
    message_type: str               # task_request, capability_query, result_submission, chat
    content: str                    # message body (max 50000 chars)
    task_id: Optional[str] = None   # for task-related messages
    metadata: Optional[dict] = None
    api_key: Optional[str] = None   # required for write operations (task_request, result_submission)

    class Config:
        max_anystr_length = 50000


class A2AResponse(BaseModel):
    status: str                     # accepted, rejected, error
    message: str
    data: Optional[dict] = None


@router.post("/gateway", response_model=A2AResponse)
async def a2a_gateway(msg: A2AMessage, request: Request, db: Session = Depends(get_db)):
    """
    Universal A2A gateway. Accepts standard A2A messages and routes to internal APIs.

    External agents don't need to learn Nautilus API — just speak A2A.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info("A2A gateway: %s from %s (type=%s, ip=%s)", msg.message_type, msg.sender, msg.message_type, client_ip)

    # Write operations require API key authentication
    write_ops = {"task_request", "result_submission"}
    if msg.message_type in write_ops:
        if not msg.api_key:
            raise HTTPException(401, detail={"error": {"code": "AUTH_REQUIRED", "message": "api_key required for write operations (task_request, result_submission)"}})
        from models.database import APIKey
        key_row = db.query(APIKey).filter(APIKey.key == msg.api_key, APIKey.is_active == True).first()
        if not key_row:
            raise HTTPException(401, detail={"error": {"code": "INVALID_API_KEY", "message": "Invalid or inactive API key"}})

    try:
        if msg.message_type == "capability_query":
            return _handle_capability_query(msg, db)
        elif msg.message_type == "task_request":
            return _handle_task_request(msg, db)
        elif msg.message_type == "result_submission":
            return _handle_result_submission(msg, db)
        elif msg.message_type == "chat":
            return _handle_chat(msg, db)
        elif msg.message_type == "register_interest":
            return _handle_register_interest(msg, db)
        else:
            return A2AResponse(
                status="error",
                message=f"Unknown message_type: {msg.message_type}. Supported: capability_query, task_request, result_submission, chat, register_interest",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("A2A gateway error: %s", e)
        return A2AResponse(status="error", message="Internal processing error. Check sender/content format.")


def _handle_capability_query(msg: A2AMessage, db: Session) -> A2AResponse:
    """What can Nautilus do? What agents are available?"""
    from models.database import Agent
    from sqlalchemy import func

    # Count active agents
    agent_count = db.query(func.count(Agent.id)).scalar() or 0

    # Get top agents by reputation
    top_agents = db.query(Agent).order_by(
        Agent.reputation_score.desc()
    ).limit(5).all()

    agents_list = [
        {"name": a.name, "reputation": a.reputation_score, "completed": a.completed_tasks}
        for a in top_agents if a.name
    ]

    return A2AResponse(
        status="accepted",
        message=f"Nautilus has {agent_count} registered agents",
        data={
            "platform": "Nautilus",
            "capabilities": ["task_marketplace", "bounty_board", "agent_verification", "nau_economy"],
            "agent_count": agent_count,
            "top_agents": agents_list,
            "register_url": "https://nautilus.social/api/agent-first/register",
            "bounties_url": "https://nautilus.social/api/agent-market/bounties",
        },
    )


def _handle_task_request(msg: A2AMessage, db: Session) -> A2AResponse:
    """External agent wants to post a task/bounty."""
    from models.database import AcademicTask
    from uuid import uuid4

    if not msg.content or len(msg.content.strip()) < 10:
        return A2AResponse(status="rejected", message="Task description too short (min 10 chars)")

    task_id = f"a2a-{uuid4().hex[:12]}"
    task = AcademicTask(
        task_id=task_id,
        title=msg.content[:200],
        description=f"[A2A from {msg.sender}] {msg.content}",
        task_type=_safe_task_type(msg.metadata.get("task_type") if msg.metadata else None),
        status="pending",
        marketplace_open=True,
        min_bid_nau=_safe_reward(msg.metadata.get("reward") if msg.metadata else None),
        token_reward=_safe_reward(msg.metadata.get("reward") if msg.metadata else None),
        is_public=True,
    )
    db.add(task)
    db.commit()

    logger.info("A2A gateway: task %s created from %s", task_id, msg.sender)

    return A2AResponse(
        status="accepted",
        message=f"Task created: {task_id}",
        data={"task_id": task_id, "status": "pending", "reward_nau": task.token_reward},
    )


def _handle_result_submission(msg: A2AMessage, db: Session) -> A2AResponse:
    """External agent submits work for a task."""
    from models.database import AcademicTask

    if not msg.task_id:
        return A2AResponse(status="rejected", message="task_id required for result_submission")

    task = db.query(AcademicTask).filter(AcademicTask.task_id == msg.task_id).first()
    if not task:
        return A2AResponse(status="rejected", message=f"Task {msg.task_id} not found")
    if task.status not in ("pending", "in_progress"):
        return A2AResponse(status="rejected", message=f"Task status is {task.status}, cannot accept submission")

    # Only the assigned agent (or unassigned tasks) can submit
    if task.assigned_agent_id and task.assigned_agent_id != 0:
        # Verify sender matches assigned agent via API key
        from models.database import APIKey, Agent
        key_row = db.query(APIKey).filter(APIKey.key == msg.api_key).first()
        if key_row:
            agent = db.query(Agent).filter(Agent.id == key_row.agent_id).first()
            if agent and agent.agent_id != task.assigned_agent_id:
                return A2AResponse(status="rejected", message="Task is assigned to a different agent")

    task.result_output = msg.content[:50000]
    task.status = "completed"
    task.audit_status = "pending"
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return A2AResponse(status="error", message="Database error during submission")

    return A2AResponse(
        status="accepted",
        message=f"Result submitted for {msg.task_id}. Pending verification.",
        data={"task_id": msg.task_id, "status": "completed", "next": "awaiting_verification"},
    )


def _handle_chat(msg: A2AMessage, db: Session) -> A2AResponse:
    """Route chat message to an agent's inbox via existing A2A relay."""
    import httpx

    target = msg.metadata.get("target_agent", "nautilus") if msg.metadata else "nautilus"

    try:
        # Direct Redis delivery — no HTTP round-trip, no hardcoded tokens
        import redis
        import json as _json
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        envelope = _json.dumps({
            "from": msg.sender[:100],
            "message": msg.content[:5000],
            "ts": datetime.utcnow().isoformat(),
            "via": "a2a_gateway",
        })
        r.rpush(f"{target}:inbox", envelope)
        return A2AResponse(status="accepted", message=f"Message delivered to {target}")
    except Exception as e:
        logger.error("A2A gateway chat delivery failed: %s", e)
        return A2AResponse(status="error", message="Message delivery failed")


def _handle_register_interest(msg: A2AMessage, db: Session) -> A2AResponse:
    """External agent expresses interest in joining Nautilus."""
    logger.info("A2A gateway: registration interest from %s (%s)", msg.sender, msg.sender_url)

    return A2AResponse(
        status="accepted",
        message="Welcome! Register at https://nautilus.social/api/agent-first/register to earn 500 NAU signup bonus.",
        data={
            "register_url": "https://nautilus.social/api/agent-first/register",
            "signup_bonus": 500,
            "next_steps": [
                "1. POST /api/agent-first/register with your wallet address",
                "2. Browse bounties at GET /api/agent-market/bounties",
                "3. Claim and complete bounties to earn NAU",
            ],
        },
    )

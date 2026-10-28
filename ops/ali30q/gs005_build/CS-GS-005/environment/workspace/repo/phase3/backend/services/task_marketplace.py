"""Task Marketplace Service — 任务市场核心逻辑"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.database import AcademicTask, Agent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy import helper to avoid circular references with reputation_service
# ---------------------------------------------------------------------------

def _get_reputation_delta(rating: int) -> float:
    """Convert a 1-5 rating to a reputation delta without importing the full
    async reputation service (which uses AsyncSession)."""
    _DELTA = {5: 3.0, 4: 1.0, 3: 0.0, 2: -2.0, 1: -5.0}
    return _DELTA.get(rating, 0.0)


def _apply_ewma(current_score: float, delta: float) -> float:
    """Apply EWMA: new = current * 0.9 + (50 + delta * 5) * 0.1, clamped [0, 100]."""
    target = 50.0 + delta * 5.0
    new_score = current_score * 0.9 + target * 0.1
    return max(0.0, min(100.0, new_score))


def _update_agent_reputation_sync(db: Session, agent_id: int, rating: int) -> None:
    """Update Agent.reputation_score using the sync session (EWMA formula).

    Falls back gracefully if the column does not yet exist on the model.
    """
    try:
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if agent is None:
            return
        delta = _get_reputation_delta(rating)
        old_score = float(getattr(agent, "reputation_score", None) or
                          getattr(agent, "reputation", 50))
        new_score = _apply_ewma(old_score, delta)
        if hasattr(agent, "reputation_score"):
            agent.reputation_score = new_score  # type: ignore[attr-defined]
        else:
            agent.reputation = int(round(new_score))
        # Caller is responsible for db.commit()
    except Exception as exc:
        logger.warning("reputation update skipped for agent %s: %s", agent_id, exc)


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def list_open_tasks(
    db: Session,
    specialty: Optional[str] = None,
    limit: int = 50,
) -> list:
    """Return marketplace_open=True, status=pending tasks.

    Optionally filtered by task_type matching *specialty*.
    Ordered by min_bid_nau DESC (high-value tasks first).
    """
    query = db.query(AcademicTask).filter(
        AcademicTask.marketplace_open == True,  # noqa: E712
        AcademicTask.status == "pending",
    )

    if specialty:
        query = query.filter(AcademicTask.task_type == specialty)

    rows = (
        query
        .order_by(AcademicTask.min_bid_nau.desc().nullslast())
        .limit(limit)
        .all()
    )

    return [_task_to_dict(row) for row in rows]


async def submit_bid(
    db: Session,
    task_id: str,
    agent_id: str,
    bid_nau: float,
    estimated_minutes: int = 10,
    message: str = "",
) -> dict:
    """Submit a bid for an open marketplace task.

    Validations:
    - Task exists and is marketplace_open=True with status=pending.
    - Same agent cannot bid twice on the same task.
    - bid_nau >= task.min_bid_nau when min_bid_nau is set.

    Returns {bid_id, task_id, agent_id, bid_nau, status}.
    """
    # Import here to avoid module-level circular issues
    from models.task_bid import TaskBid  # noqa: PLC0415

    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if task is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task '{task_id}' not found",
                }
            },
        )

    if not task.marketplace_open:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "TASK_NOT_OPEN",
                    "message": "Task is not open for bidding",
                }
            },
        )

    if task.status != "pending":
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "TASK_NOT_PENDING",
                    "message": f"Task status is '{task.status}', only pending tasks accept bids",
                }
            },
        )

    # Duplicate bid guard
    existing_bid = (
        db.query(TaskBid)
        .filter(TaskBid.task_id == task_id, TaskBid.agent_id == agent_id)
        .first()
    )
    if existing_bid is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "DUPLICATE_BID",
                    "message": "Agent has already submitted a bid for this task",
                    "details": {"existing_bid_id": existing_bid.id},
                }
            },
        )

    # Minimum bid guard
    min_bid = getattr(task, "min_bid_nau", None)
    if min_bid is not None and bid_nau < min_bid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "BID_TOO_LOW",
                    "message": f"Bid {bid_nau} NAU is below minimum {min_bid} NAU",
                    "details": {"min_bid_nau": min_bid, "submitted_bid_nau": bid_nau},
                }
            },
        )

    bid_id = f"bid_{uuid.uuid4().hex[:16]}"
    now = datetime.utcnow()

    bid = TaskBid(
        id=bid_id,
        task_id=task_id,
        agent_id=agent_id,
        bid_nau=bid_nau,
        estimated_minutes=estimated_minutes,
        message=message,
        status="pending",
        created_at=now,
    )
    db.add(bid)
    db.commit()
    db.refresh(bid)

    logger.info("Bid submitted: bid_id=%s task_id=%s agent_id=%s bid_nau=%s",
                bid_id, task_id, agent_id, bid_nau)

    return {
        "bid_id": bid.id,
        "task_id": bid.task_id,
        "agent_id": bid.agent_id,
        "bid_nau": bid.bid_nau,
        "status": bid.status,
    }


async def accept_bid(db: Session, task_id: str, bid_id: str) -> dict:
    """Accept a bid for a task.

    Steps:
    1. Set chosen TaskBid.status = 'accepted'.
    2. Set all other bids for this task to 'rejected'.
    3. Update task.accepted_bid_id = bid_id.
    4. Update task.assigned_agent_id = bid.agent_id.
    5. Set task.marketplace_open = False.

    Returns {task_id, accepted_agent_id, bid_nau}.
    """
    from models.task_bid import TaskBid  # noqa: PLC0415

    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if task is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task '{task_id}' not found",
                }
            },
        )

    bid = db.query(TaskBid).filter(
        TaskBid.id == bid_id,
        TaskBid.task_id == task_id,
    ).first()
    if bid is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "BID_NOT_FOUND",
                    "message": f"Bid '{bid_id}' not found for task '{task_id}'",
                }
            },
        )

    # Accept chosen bid, reject the rest
    bid.status = "accepted"

    other_bids = (
        db.query(TaskBid)
        .filter(TaskBid.task_id == task_id, TaskBid.id != bid_id)
        .all()
    )
    for other in other_bids:
        other.status = "rejected"

    # Update task fields
    task.accepted_bid_id = bid_id
    task.assigned_agent_id = bid.agent_id
    task.marketplace_open = False
    task.updated_at = datetime.utcnow()

    db.commit()

    logger.info("Bid accepted: bid_id=%s task_id=%s agent_id=%s",
                bid_id, task_id, bid.agent_id)

    return {
        "task_id": task_id,
        "accepted_agent_id": bid.agent_id,
        "bid_nau": bid.bid_nau,
    }


async def rate_task(
    db: Session,
    task_id: str,
    rating: int,
    comment: str = "",
) -> dict:
    """Rate a completed task.

    Validates:
    - rating in [1, 5].
    - task.status == 'completed'.

    Updates task.quality_rating and task.rating_comment, then updates
    the assigned agent's reputation score via sync EWMA.

    Returns {task_id, rating, agent_id}.
    """
    if rating < 1 or rating > 5:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_RATING",
                    "message": "Rating must be between 1 and 5",
                    "details": {"provided_rating": rating},
                }
            },
        )

    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if task is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task '{task_id}' not found",
                }
            },
        )

    if task.status != "completed":
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "TASK_NOT_COMPLETED",
                    "message": f"Only completed tasks can be rated (current status: '{task.status}')",
                }
            },
        )

    task.quality_rating = rating
    task.rating_comment = comment
    task.updated_at = datetime.utcnow()

    agent_id = task.assigned_agent_id
    if agent_id is not None:
        _update_agent_reputation_sync(db, agent_id, rating)

    db.commit()

    logger.info("Task rated: task_id=%s rating=%s agent_id=%s", task_id, rating, agent_id)

    return {
        "task_id": task_id,
        "rating": rating,
        "agent_id": agent_id,
    }


async def get_task_bids(db: Session, task_id: str) -> list:
    """Return all bids for a task, ordered by bid_nau DESC."""
    from models.task_bid import TaskBid  # noqa: PLC0415

    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if task is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task '{task_id}' not found",
                }
            },
        )

    bids = (
        db.query(TaskBid)
        .filter(TaskBid.task_id == task_id)
        .order_by(TaskBid.bid_nau.desc())
        .all()
    )

    return [_bid_to_dict(b) for b in bids]


# ---------------------------------------------------------------------------
# Private serialisation helpers
# ---------------------------------------------------------------------------


def _task_to_dict(task: AcademicTask) -> dict:
    return {
        "task_id": task.task_id,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type,
        "status": task.status,
        "marketplace_open": getattr(task, "marketplace_open", False),
        "min_bid_nau": getattr(task, "min_bid_nau", None),
        "quality_rating": getattr(task, "quality_rating", None),
        "rating_comment": getattr(task, "rating_comment", None),
        "accepted_bid_id": getattr(task, "accepted_bid_id", None),
        "assigned_agent_id": task.assigned_agent_id,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


def _bid_to_dict(bid) -> dict:
    return {
        "bid_id": bid.id,
        "task_id": bid.task_id,
        "agent_id": bid.agent_id,
        "bid_nau": bid.bid_nau,
        "estimated_minutes": bid.estimated_minutes,
        "message": bid.message,
        "status": bid.status,
        "created_at": bid.created_at.isoformat() if bid.created_at else None,
    }

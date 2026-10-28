"""Raid consensus execution API endpoints."""
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from models.raid import RaidExecution, RaidVote
from services.raid_engine import RaidEngine, RaidLevel, RaidResult
from utils.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

TESTING = os.getenv("TESTING", "false").lower() == "true"
limiter = Limiter(key_func=get_remote_address, enabled=not TESTING)


# ------------------------------------------------------------------
# Request / Response schemas
# ------------------------------------------------------------------

class RaidExecuteRequest(BaseModel):
    """Request body for starting a Raid execution."""
    description: str = Field(..., min_length=1, max_length=10000)
    level: int = Field(2, description="Raid level: 1, 2, 3, or 5")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class RaidExecutionResponse(BaseModel):
    """Envelope response for a single execution."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RaidListResponse(BaseModel):
    """Paginated list of executions."""
    success: bool
    data: List[Dict[str, Any]]
    meta: Dict[str, Any]
    error: Optional[str] = None


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.post("/execute", response_model=RaidExecutionResponse)
@limiter.limit("10/minute")
async def execute_raid(
    request: Request,
    body: RaidExecuteRequest,
    db: Session = Depends(get_db),
) -> RaidExecutionResponse:
    """Start a new Raid consensus execution.

    Supported levels:
    - **1**: Single execution + self-review
    - **2**: Execute -> Review -> Improve (up to 3 rounds)
    - **3**: 3 parallel executions + majority vote
    - **5**: 5 expert reviews with 4/5 consensus threshold
    """
    valid_levels = {1, 2, 3, 5}
    if body.level not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_RAID_LEVEL",
                    "message": f"Raid level must be one of {sorted(valid_levels)}",
                }
            },
        )

    try:
        engine = RaidEngine(db)
        result: RaidResult = await engine.execute(
            task_description=body.description,
            level=RaidLevel(body.level),
            context=body.context,
        )
        return RaidExecutionResponse(
            success=True,
            data=result.model_dump(),
        )
    except Exception as e:
        logger.exception("Raid execution failed")
        return RaidExecutionResponse(success=False, error=str(e))


@router.get("/{execution_id}", response_model=RaidExecutionResponse)
@limiter.limit("30/minute")
async def get_raid_execution(
    request: Request,
    execution_id: str,
    db: Session = Depends(get_db),
) -> RaidExecutionResponse:
    """Retrieve status and result of a Raid execution."""
    record = (
        db.query(RaidExecution)
        .filter(RaidExecution.execution_id == execution_id)
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "EXECUTION_NOT_FOUND",
                    "message": f"No execution found with id '{execution_id}'",
                }
            },
        )

    votes = (
        db.query(RaidVote)
        .filter(RaidVote.execution_id == execution_id)
        .order_by(RaidVote.round_number, RaidVote.id)
        .all()
    )

    return RaidExecutionResponse(
        success=True,
        data={
            "execution_id": record.execution_id,
            "raid_level": record.raid_level,
            "status": record.status,
            "output": record.final_output,
            "consensus_score": record.consensus_score,
            "rounds": record.rounds_completed,
            "num_agents": record.num_agents,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "votes": [
                {
                    "role": v.agent_role,
                    "round_number": v.round_number,
                    "approved": v.approved,
                    "quality_score": v.quality_score,
                    "feedback": v.feedback,
                }
                for v in votes
            ],
        },
    )


@router.get("/", response_model=RaidListResponse)
@limiter.limit("30/minute")
async def list_raid_executions(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
) -> RaidListResponse:
    """List past Raid executions with pagination."""
    query = db.query(RaidExecution)
    if status:
        query = query.filter(RaidExecution.status == status)

    total = query.count()
    records = (
        query.order_by(RaidExecution.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return RaidListResponse(
        success=True,
        data=[
            {
                "execution_id": r.execution_id,
                "raid_level": r.raid_level,
                "status": r.status,
                "consensus_score": r.consensus_score,
                "rounds": r.rounds_completed,
                "num_agents": r.num_agents,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in records
        ],
        meta={"page": page, "limit": limit, "total": total},
    )

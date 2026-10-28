"""
A2A (Agent-to-Agent) API endpoints.

Routes:
  POST /api/a2a/spawn           — Split a task into subtasks
  GET  /api/a2a/status/{task_id} — Get subtask status
  POST /api/a2a/aggregate/{task_id} — Force aggregate results
  POST /api/a2a/work            — Worker: claim and execute one subtask
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.database import Agent, APIKey
from utils.database import get_db
from services.a2a_protocol import get_a2a_coordinator, get_a2a_worker
import os

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Auth helper — verify API key and return the owning Agent
# ---------------------------------------------------------------------------

def _get_agent_from_api_key(
    x_api_key: str,
    db: Session,
) -> Agent:
    """Validate x-api-key header and return the associated Agent."""
    prefix = os.getenv("API_KEY_PREFIX", "nau_")
    if not x_api_key or not x_api_key.startswith(prefix):
        raise HTTPException(status_code=401, detail="Invalid API key format")

    api_key_obj = db.query(APIKey).filter(APIKey.key == x_api_key).first()
    if api_key_obj is None or not api_key_obj.is_active:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    agent = db.query(Agent).filter(Agent.agent_id == api_key_obj.agent_id).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class SpawnRequest(BaseModel):
    task_id: str = Field(..., description="Parent task ID to split")
    num_workers: int = Field(
        ...,
        ge=2,
        le=8,
        description="Number of worker subtasks to create (2–8)",
    )


class SpawnResponse(BaseModel):
    success: bool
    data: dict
    error: str | None = None


class StatusResponse(BaseModel):
    success: bool
    data: dict
    error: str | None = None


class AggregateResponse(BaseModel):
    success: bool
    data: dict
    error: str | None = None


class WorkResponse(BaseModel):
    success: bool
    data: dict
    error: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/a2a/spawn",
    response_model=SpawnResponse,
    summary="Spawn A2A subtasks",
    description=(
        "Split a coordinator task into *num_workers* parallel worker subtasks. "
        "Requires a valid agent API key in the `x-api-key` header."
    ),
    tags=["A2A Protocol"],
)
async def spawn_subtasks(
    body: SpawnRequest,
    x_api_key: str = Header(..., alias="x-api-key"),
    db: Session = Depends(get_db),
) -> SpawnResponse:
    agent = _get_agent_from_api_key(x_api_key, db)

    coordinator = get_a2a_coordinator()
    try:
        subtask_ids = await coordinator.spawn_subtasks(
            task_id=body.task_id,
            num_workers=body.num_workers,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("spawn_subtasks failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error during subtask spawn")

    logger.info(
        "Agent %d spawned %d subtasks for task '%s'.",
        agent.agent_id, len(subtask_ids), body.task_id,
    )

    return SpawnResponse(
        success=True,
        data={
            "coordinator_task_id": body.task_id,
            "subtask_ids": subtask_ids,
            "num_workers": body.num_workers,
        },
    )


@router.get(
    "/a2a/status/{task_id}",
    response_model=StatusResponse,
    summary="Get A2A subtask status",
    description="Return completion stats and per-subtask results for a coordinator task.",
    tags=["A2A Protocol"],
)
def get_status(
    task_id: str,
    db: Session = Depends(get_db),
) -> StatusResponse:
    coordinator = get_a2a_coordinator()
    try:
        status_data = coordinator.get_subtask_status(
            parent_task_id=task_id,
            db=db,
        )
    except Exception as exc:
        logger.error("get_status failed for task '%s': %s", task_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error fetching status")

    return StatusResponse(success=True, data=status_data)


@router.post(
    "/a2a/aggregate/{task_id}",
    response_model=AggregateResponse,
    summary="Force aggregate A2A results",
    description=(
        "Aggregate all subtask results into the parent task. "
        "Call this endpoint after a timeout or when all workers have finished. "
        "Requires a valid agent API key in the `x-api-key` header."
    ),
    tags=["A2A Protocol"],
)
async def aggregate_results(
    task_id: str,
    x_api_key: str = Header(..., alias="x-api-key"),
    db: Session = Depends(get_db),
) -> AggregateResponse:
    _get_agent_from_api_key(x_api_key, db)

    coordinator = get_a2a_coordinator()
    try:
        result = await coordinator.aggregate_results(
            task_id=task_id,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(
            "aggregate_results failed for task '%s': %s", task_id, exc, exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal error during aggregation")

    return AggregateResponse(success=True, data=result)


@router.post(
    "/a2a/work",
    response_model=WorkResponse,
    summary="Worker: claim one subtask (dispatch-only)",
    description=(
        "Claim one pending A2A worker subtask and receive its payload. "
        "The platform does NOT execute the task — the registered agent runs it "
        "in its own loop and reports back via POST /a2a/work/{task_id}/result "
        "(旧版内置 Haiku 代执行已于 2026-08-27 移除,对齐 §0-ARCH 派单模式). "
        "Requires a valid agent API key in the `x-api-key` header."
    ),
    tags=["A2A Protocol"],
)
async def claim_work(
    x_api_key: str = Header(..., alias="x-api-key"),
    db: Session = Depends(get_db),
) -> WorkResponse:
    agent = _get_agent_from_api_key(x_api_key, db)

    worker = get_a2a_worker()
    try:
        result = await worker.claim(
            worker_agent_id=agent.agent_id,
            db=db,
        )
    except Exception as exc:
        logger.error(
            "claim_work failed for agent %d: %s",
            agent.agent_id, exc, exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal error during claim")

    return WorkResponse(success=True, data=result)


@router.post(
    "/a2a/work/{task_id}/result",
    response_model=WorkResponse,
    summary="Worker: submit execution result",
    description=(
        "Report the outcome of a claimed subtask. Only the claiming agent may "
        "submit. `success=true` requires `result`; `success=false` accepts `error`."
    ),
    tags=["A2A Protocol"],
)
async def submit_work_result(
    task_id: str,
    body: dict,
    x_api_key: str = Header(..., alias="x-api-key"),
    db: Session = Depends(get_db),
) -> WorkResponse:
    agent = _get_agent_from_api_key(x_api_key, db)
    success = bool(body.get("success"))
    result = body.get("result")
    error = body.get("error")
    if success and not result:
        raise HTTPException(status_code=400, detail="result is required when success=true")

    worker = get_a2a_worker()
    out = worker.submit_result(
        task_id=task_id,
        worker_agent_id=agent.agent_id,
        success=success,
        result=result,
        error=error,
        db=db,
    )
    status_code = out.pop("status_code", None)
    if status_code is not None:
        raise HTTPException(status_code=status_code, detail=out.get("error"))
    return WorkResponse(success=True, data=out)

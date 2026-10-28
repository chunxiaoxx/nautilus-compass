"""
Simulation Task API - Brain-Body bridge for embodied AI training.

Accepts simulation tasks from robotics/AV companies:
- Physics simulation scenarios
- Sensor data generation
- Motion planning evaluation
- Sim2Real transfer data

Follows the same async dispatch pattern as academic_tasks.py, routing
work to the CodeExecutor with physics-specific templates.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address
import asyncio
import uuid
import json
import logging
import os

from models.database import SimulationTask as SimulationTaskModel
from utils.database import get_db, get_db_context

router = APIRouter()
logger = logging.getLogger(__name__)

# Concurrency limit: at most 3 simulation tasks dispatched in parallel
_task_semaphore = asyncio.Semaphore(3)

TESTING = os.getenv("TESTING", "false").lower() == "true"
limiter = Limiter(key_func=get_remote_address, enabled=not TESTING)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SimulationType(str, Enum):
    """Supported simulation types for brain-body training."""
    PHYSICS_SIM = "physics_simulation"
    MOTION_PLANNING = "motion_planning"
    SENSOR_SIM = "sensor_simulation"
    SCENARIO_GEN = "scenario_generation"
    COLLISION_CHECK = "collision_detection"
    DYNAMICS_SIM = "dynamics_simulation"
    ENVIRONMENT_SIM = "environment_simulation"


class SimulationStatus(str, Enum):
    """Simulation task lifecycle status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class CreateSimulationRequest(BaseModel):
    """Request to submit a new simulation task."""
    title: str = Field(..., min_length=1, max_length=200)
    simulation_type: SimulationType
    description: str = Field(..., min_length=1, max_length=5000)
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Physics params, initial conditions, solver settings",
    )
    num_episodes: int = Field(default=1, ge=1, le=1000)
    time_steps: int = Field(default=100, ge=10, le=100000)
    output_format: str = Field(
        default="json",
        description="Desired output format: json, csv, or numpy",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Double pendulum chaos simulation",
                "simulation_type": "physics_simulation",
                "description": (
                    "Simulate a double pendulum with m1=m2=1kg, l1=l2=1m. "
                    "Initial angles: theta1=120deg, theta2=-10deg. "
                    "Output position traces for 20 seconds."
                ),
                "parameters": {
                    "m1": 1.0,
                    "m2": 1.0,
                    "l1": 1.0,
                    "l2": 1.0,
                    "theta1_deg": 120.0,
                    "theta2_deg": -10.0,
                    "gravity": 9.81,
                },
                "num_episodes": 1,
                "time_steps": 2000,
                "output_format": "json",
            }
        }


class SimulationResult(BaseModel):
    """Result from an executed simulation task."""
    code: Optional[str] = Field(None, description="Generated Python code")
    output: Optional[str] = Field(None, description="Stdout from execution")
    plots: Optional[List[str]] = Field(
        None, description="Base64-encoded plot images",
    )
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time: Optional[float] = Field(
        None, description="Wall-clock execution time in seconds",
    )


class SimulationTaskResponse(BaseModel):
    """Single simulation task."""
    task_id: str
    title: str
    description: str
    simulation_type: str
    status: str
    num_episodes: int
    time_steps: int
    output_format: str
    created_at: str
    updated_at: str
    parameters: Optional[Dict[str, Any]] = None
    result: Optional[SimulationResult] = None


class SimulationTaskListResponse(BaseModel):
    """Paginated list of simulation tasks."""
    tasks: List[SimulationTaskResponse]
    total: int
    page: int
    limit: int


class BatchSimulationRequest(BaseModel):
    """Submit multiple simulation scenarios in one call."""
    scenarios: List[CreateSimulationRequest] = Field(
        ..., min_length=1, max_length=50,
    )


class BatchSimulationResponse(BaseModel):
    """Response for a batch submission."""
    submitted: int
    task_ids: List[str]


class SimulationCapability(BaseModel):
    """Description of a supported simulation capability."""
    simulation_type: str
    description: str
    required_packages: List[str]
    default_parameters: Dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _model_to_response(row: SimulationTaskModel) -> SimulationTaskResponse:
    """Convert a DB row to the API response model."""
    parameters: Optional[Dict[str, Any]] = None
    if row.parameters:
        try:
            parameters = json.loads(row.parameters)
        except (json.JSONDecodeError, TypeError):
            parameters = None

    result: Optional[SimulationResult] = None
    if (row.result_code is not None
            or row.result_output is not None
            or row.result_error is not None):
        plots: Optional[List[str]] = None
        if row.result_plots:
            try:
                plots = json.loads(row.result_plots)
            except (json.JSONDecodeError, TypeError):
                plots = None

        result = SimulationResult(
            code=row.result_code,
            output=row.result_output,
            plots=plots,
            error=row.result_error,
            execution_time=row.execution_time,
        )

    created_at = row.created_at.isoformat() if row.created_at else ""
    updated_at = row.updated_at.isoformat() if row.updated_at else ""

    return SimulationTaskResponse(
        task_id=row.task_id,
        title=row.title,
        description=row.description,
        simulation_type=row.simulation_type,
        status=row.status,
        num_episodes=row.num_episodes or 1,
        time_steps=row.time_steps or 100,
        output_format=row.output_format or "json",
        created_at=created_at,
        updated_at=updated_at,
        parameters=parameters,
        result=result,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/submit",
    response_model=SimulationTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def submit_simulation(
    request: Request,
    task_data: CreateSimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Submit a simulation task for execution.

    Accepts physics simulations, motion planning, sensor generation,
    and other embodied-AI training workloads. The task is queued for
    execution by the CodeExecutor service with simulation-specific
    templates.

    **Rate Limit**: 10 requests per minute
    """
    task_id = f"sim_{uuid.uuid4().hex[:16]}"
    now = datetime.utcnow()

    row = SimulationTaskModel(
        task_id=task_id,
        title=task_data.title,
        description=task_data.description,
        simulation_type=task_data.simulation_type.value,
        status=SimulationStatus.PENDING.value,
        parameters=(
            json.dumps(task_data.parameters)
            if task_data.parameters
            else None
        ),
        num_episodes=task_data.num_episodes,
        time_steps=task_data.time_steps,
        output_format=task_data.output_format,
        created_at=now,
        updated_at=now,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    logger.info(
        "Simulation task submitted: %s type=%s episodes=%d",
        task_id, task_data.simulation_type.value, task_data.num_episodes,
    )

    asyncio.create_task(_dispatch_simulation_task(task_id))
    return _model_to_response(row)


@router.get("/{task_id}", response_model=SimulationTaskResponse)
@limiter.limit("60/minute")
async def get_simulation(
    request: Request,
    task_id: str,
    db: Session = Depends(get_db),
):
    """
    Get status and results of a simulation task.

    **Rate Limit**: 60 requests per minute
    """
    row = (
        db.query(SimulationTaskModel)
        .filter(SimulationTaskModel.task_id == task_id)
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Simulation task '{task_id}' not found",
                }
            },
        )
    return _model_to_response(row)


@router.get("/", response_model=SimulationTaskListResponse)
@limiter.limit("30/minute")
async def list_simulations(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    simulation_type: Optional[SimulationType] = Query(None),
    task_status: Optional[SimulationStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    """
    List simulation tasks with pagination and optional filters.

    **Rate Limit**: 30 requests per minute
    """
    query = db.query(SimulationTaskModel)

    if simulation_type is not None:
        query = query.filter(
            SimulationTaskModel.simulation_type == simulation_type.value,
        )
    if task_status is not None:
        query = query.filter(
            SimulationTaskModel.status == task_status.value,
        )

    total = query.count()
    rows = (
        query
        .order_by(SimulationTaskModel.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return SimulationTaskListResponse(
        tasks=[_model_to_response(r) for r in rows],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/capabilities/list", response_model=List[SimulationCapability])
@limiter.limit("60/minute")
async def list_capabilities(request: Request):
    """
    List supported simulation capabilities.

    Returns the simulation types this service can execute today,
    along with required packages and default parameters.

    **Rate Limit**: 60 requests per minute
    """
    from services.simulation_templates import SIMULATION_TEMPLATES

    capabilities: List[SimulationCapability] = []
    for sim_type, template in SIMULATION_TEMPLATES.items():
        capabilities.append(SimulationCapability(
            simulation_type=sim_type,
            description=template["hint"],
            required_packages=template["required_packages"],
            default_parameters=template["default_parameters"],
        ))
    return capabilities


@router.post("/batch", response_model=BatchSimulationResponse)
@limiter.limit("5/minute")
async def submit_batch(
    request: Request,
    batch: BatchSimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Submit a batch of simulation scenarios.

    Up to 50 scenarios per request. Each scenario is queued
    independently and receives its own task_id.

    **Rate Limit**: 5 requests per minute
    """
    task_ids: List[str] = []
    now = datetime.utcnow()

    for scenario in batch.scenarios:
        task_id = f"sim_{uuid.uuid4().hex[:16]}"
        row = SimulationTaskModel(
            task_id=task_id,
            title=scenario.title,
            description=scenario.description,
            simulation_type=scenario.simulation_type.value,
            status=SimulationStatus.PENDING.value,
            parameters=(
                json.dumps(scenario.parameters)
                if scenario.parameters
                else None
            ),
            num_episodes=scenario.num_episodes,
            time_steps=scenario.time_steps,
            output_format=scenario.output_format,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
        task_ids.append(task_id)

    db.commit()

    logger.info("Batch simulation submitted: %d scenarios", len(task_ids))

    for tid in task_ids:
        asyncio.create_task(_dispatch_simulation_task(tid))

    return BatchSimulationResponse(
        submitted=len(task_ids),
        task_ids=task_ids,
    )


@router.post("/{task_id}/cancel")
@limiter.limit("10/minute")
async def cancel_simulation(
    request: Request,
    task_id: str,
    db: Session = Depends(get_db),
):
    """
    Cancel a pending simulation task.

    Only tasks in PENDING status can be cancelled.

    **Rate Limit**: 10 requests per minute
    """
    row = (
        db.query(SimulationTaskModel)
        .filter(SimulationTaskModel.task_id == task_id)
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Simulation task '{task_id}' not found",
                }
            },
        )

    if row.status != SimulationStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "TASK_NOT_CANCELLABLE",
                    "message": (
                        f"Task in '{row.status}' status cannot be cancelled"
                    ),
                    "details": {"current_status": row.status},
                }
            },
        )

    row.status = SimulationStatus.CANCELLED.value
    row.updated_at = datetime.utcnow()
    db.commit()
    logger.info("Simulation task cancelled: %s", task_id)

    return {
        "success": True,
        "data": {"task_id": task_id, "status": row.status},
        "error": None,
    }


# ---------------------------------------------------------------------------
# Background dispatch
# ---------------------------------------------------------------------------

async def _dispatch_simulation_task(task_id: str) -> None:
    """
    Background coroutine that dispatches a simulation task to the
    CodeExecutor via the simulation-specific service and persists results.

    Guarded by _task_semaphore to allow at most 3 concurrent dispatches,
    preventing resource exhaustion while enabling parallel execution.
    """
    async with _task_semaphore:
        await _dispatch_simulation_task_inner(task_id)


async def _dispatch_simulation_task_inner(task_id: str) -> None:
    """Inner dispatch logic, called under the semaphore."""
    with get_db_context() as db:
        row = (
            db.query(SimulationTaskModel)
            .filter(SimulationTaskModel.task_id == task_id)
            .first()
        )
        if not row:
            logger.error("Dispatch: simulation task %s not found", task_id)
            return

        if row.status != SimulationStatus.PENDING.value:
            logger.warning(
                "Dispatch: simulation task %s not pending (status=%s)",
                task_id, row.status,
            )
            return

        row.status = SimulationStatus.PROCESSING.value
        row.updated_at = datetime.utcnow()
        db.commit()
        logger.info("Dispatching simulation task %s to engine", task_id)

        parameters: Optional[Dict[str, Any]] = None
        if row.parameters:
            try:
                parameters = json.loads(row.parameters)
            except (json.JSONDecodeError, TypeError):
                parameters = None

        task_dict = {
            "task_id": row.task_id,
            "title": row.title,
            "description": row.description,
            "simulation_type": row.simulation_type,
            "status": row.status,
            "parameters": parameters,
            "num_episodes": row.num_episodes,
            "time_steps": row.time_steps,
            "output_format": row.output_format,
        }

    try:
        from services.simulation_task_service import get_simulation_task_service

        service = get_simulation_task_service()
        result = await service.execute_task(task_id, task_dict)

        with get_db_context() as db:
            row = (
                db.query(SimulationTaskModel)
                .filter(SimulationTaskModel.task_id == task_id)
                .first()
            )
            if not row:
                logger.error(
                    "Dispatch: simulation task %s disappeared after exec",
                    task_id,
                )
                return

            row.result_code = result.get("code")
            row.result_output = result.get("output")
            row.result_error = result.get("error")
            row.execution_time = result.get("execution_time")

            plots = result.get("plots")
            row.result_plots = json.dumps(plots) if plots else None

            row.status = (
                SimulationStatus.FAILED.value
                if result.get("error")
                else SimulationStatus.COMPLETED.value
            )
            row.updated_at = datetime.utcnow()
            db.commit()

            logger.info(
                "Simulation task %s finished: status=%s time=%.2fs",
                task_id, row.status, result.get("execution_time", 0),
            )

    except Exception as exc:
        logger.error(
            "Simulation task %s dispatch error: %s",
            task_id, exc, exc_info=True,
        )
        with get_db_context() as db:
            row = (
                db.query(SimulationTaskModel)
                .filter(SimulationTaskModel.task_id == task_id)
                .first()
            )
            if row:
                row.status = SimulationStatus.FAILED.value
                row.result_error = f"Dispatch error: {exc}"
                row.updated_at = datetime.utcnow()
                db.commit()

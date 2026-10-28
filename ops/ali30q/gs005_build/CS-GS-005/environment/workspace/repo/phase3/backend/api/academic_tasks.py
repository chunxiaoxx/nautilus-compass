"""
Academic task API - physics simulations, curve fitting, ML experiments.

Persisted to PostgreSQL via SQLAlchemy.
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

from models.database import AcademicTask as AcademicTaskModel
from utils.database import get_db, get_db_context

router = APIRouter()
logger = logging.getLogger(__name__)

# Concurrency limit: at most 3 academic tasks dispatched in parallel
_task_semaphore = asyncio.Semaphore(3)

# Check if we're in testing mode
TESTING = os.getenv("TESTING", "false").lower() == "true"

# Create limiter with disabled state for testing
limiter = Limiter(key_func=get_remote_address, enabled=not TESTING)


class AcademicTaskType(str, Enum):
    """Supported academic task types."""
    CURVE_FITTING = "curve_fitting"
    ODE_SIMULATION = "ode_simulation"
    PDE_SIMULATION = "pde_simulation"
    MONTE_CARLO = "monte_carlo"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    ML_TRAINING = "ml_training"
    DATA_VISUALIZATION = "data_visualization"
    PHYSICS_SIMULATION = "physics_simulation"
    GENERAL_COMPUTATION = "general_computation"
    JC_CONSTITUTIVE = "jc_constitutive"
    THMC_COUPLING = "thmc_coupling"
    RESEARCH_SYNTHESIS = "research_synthesis"


class AcademicTaskStatus(str, Enum):
    """Academic task lifecycle status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CreateAcademicTaskRequest(BaseModel):
    """Request to submit a new academic task."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    task_type: AcademicTaskType
    input_data: Optional[str] = Field(
        None, max_length=100000,
        description="JSON string or CSV data for the task"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Task-specific parameters (e.g. model type, iterations)"
    )
    expected_output: Optional[str] = Field(
        None, max_length=5000,
        description="Description of expected output format"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Damped harmonic oscillator simulation",
                "description": "Simulate a damped harmonic oscillator with m=1kg, k=10N/m, b=0.5Ns/m. Plot position vs time for 10 seconds.",
                "task_type": "ode_simulation",
                "input_data": None,
                "parameters": {
                    "mass": 1.0,
                    "spring_constant": 10.0,
                    "damping_coefficient": 0.5,
                    "duration": 10.0,
                    "dt": 0.01
                },
                "expected_output": "Time series plot of position and velocity"
            }
        }


class AcademicTaskResult(BaseModel):
    """Result from an executed academic task."""
    code: Optional[str] = Field(None, description="Generated Python code")
    output: Optional[str] = Field(None, description="Stdout from execution")
    plots: Optional[List[str]] = Field(
        None, description="Base64-encoded plot images"
    )
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time: Optional[float] = Field(
        None, description="Execution time in seconds"
    )


class AcademicTaskResponse(BaseModel):
    """Response representing an academic task."""
    task_id: str
    title: str
    description: str
    task_type: str
    status: str
    created_at: str
    updated_at: str
    input_data: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    expected_output: Optional[str] = None
    result: Optional[AcademicTaskResult] = None


class AcademicTaskListResponse(BaseModel):
    """Paginated list of academic tasks."""
    tasks: List[AcademicTaskResponse]
    total: int
    page: int
    limit: int


def _model_to_response(row: AcademicTaskModel) -> AcademicTaskResponse:
    """Convert a DB model instance to the API response model."""
    # Deserialize JSON fields
    parameters = None
    if row.parameters:
        try:
            parameters = json.loads(row.parameters)
        except (json.JSONDecodeError, TypeError):
            parameters = None

    # Build result if any result field is populated
    result = None
    if row.result_code is not None or row.result_output is not None or row.result_error is not None:
        plots = None
        if row.result_plots:
            try:
                plots = json.loads(row.result_plots)
            except (json.JSONDecodeError, TypeError):
                plots = None

        result = AcademicTaskResult(
            code=row.result_code,
            output=row.result_output,
            plots=plots,
            error=row.result_error,
            execution_time=row.execution_time,
        )

    created_at = row.created_at.isoformat() if row.created_at else ""
    updated_at = row.updated_at.isoformat() if row.updated_at else ""

    return AcademicTaskResponse(
        task_id=row.task_id,
        title=row.title,
        description=row.description,
        task_type=row.task_type,
        status=row.status,
        created_at=created_at,
        updated_at=updated_at,
        input_data=row.input_data,
        parameters=parameters,
        expected_output=row.expected_output,
        result=result,
    )


@router.post(
    "/submit",
    response_model=AcademicTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def submit_academic_task(
    request: Request,
    task_data: CreateAcademicTaskRequest,
    db: Session = Depends(get_db),
):
    """
    Submit a new academic task for execution.

    Accepts physics simulations, curve fitting, ML experiments, and other
    scientific computations. The task is queued for execution by the
    CodeExecutor service.

    **Rate Limit**: 10 requests per minute

    **Request Body**:
    - `title`: Short title (max 200 chars)
    - `description`: Detailed description of the computation (max 5000 chars)
    - `task_type`: One of the supported academic task types
    - `input_data`: Optional JSON/CSV data input
    - `parameters`: Optional task-specific parameters dict
    - `expected_output`: Optional description of expected output

    **Returns**: Created task with `task_id` for polling status.
    """
    task_id = f"acad_{uuid.uuid4().hex[:16]}"
    now = datetime.utcnow()

    # Payment check (non-blocking: allow task if payment fails)
    try:
        from services.pricing import get_task_price
        from services.payment_service import PaymentService, InsufficientBalanceError

        price = get_task_price(task_data.task_type.value)
        PaymentService.charge(
            db=db,
            user_id=1,  # anonymous user; replace with auth token later
            amount=price,
            task_id=task_id,
            description=f"Academic task: {task_data.title}",
        )
        logger.info(f"Charged {price} RMB for task {task_id}")
    except InsufficientBalanceError:
        raise HTTPException(
            status_code=402,
            detail={
                "error": {
                    "code": "INSUFFICIENT_BALANCE",
                    "message": f"余额不足。此任务需要 {price} 元，请先充值。",
                    "price": price,
                }
            },
        )
    except Exception as e:
        logger.warning(f"Payment failed, allowing task: {e}")
        db.rollback()  # Clear pending rollback state from payment failure

    # Rate limit removed — platform agents need unlimited task submission
    if False:  # was: research_synthesis rate limit
        raise HTTPException(
            status_code=429,
            detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded",
                        "details": {"limit": 0, "window": "24h"},
                    }
                },
            )

    # Resolve tenant from request headers
    tenant_id = "public"
    try:
        from services.tenant_service import resolve_tenant
        tenant = resolve_tenant(request, db)
        tenant_id = tenant.id
    except Exception:
        pass

    row = AcademicTaskModel(
        task_id=task_id,
        title=task_data.title,
        description=task_data.description,
        task_type=task_data.task_type.value,
        status=AcademicTaskStatus.PENDING.value,
        input_data=task_data.input_data,
        parameters=json.dumps(task_data.parameters) if task_data.parameters else None,
        expected_output=task_data.expected_output,
        created_at=now,
        updated_at=now,
    )
    # Set tenant_id if column exists
    try:
        row.tenant_id = tenant_id
    except Exception:
        pass

    db.add(row)
    db.commit()
    db.refresh(row)

    logger.info(f"Academic task submitted: {task_id} type={task_data.task_type.value}")

    # Emit task.created event → triggers immediate agent scan (replaces 5-min poll)
    try:
        from services.event_bus import emit, Events
        asyncio.create_task(emit(Events.TASK_CREATED, {
            "task_id": task_id,
            "task_type": task_data.task_type.value,
            "title": task_data.title,
        }))
    except Exception:
        pass

    # Notify KAIROS of new task (event-driven activation)
    try:
        from utils.redis_client import get_redis
        get_redis().set("kairos:event:new_task", task_id, ex=300)
    except Exception:
        pass

    # A/B experiment assignment (non-blocking)
    try:
        from services.sandbox_router import tag_task_for_experiment
        tag_task_for_experiment(db, task_id)
    except Exception as _e:
        logger.debug("sandbox assign skipped: %s", _e)

    # TaskRouter: classify + store routing decisions in parameters
    try:
        from services.task_router import TaskRouter
        task_router = TaskRouter(db)
        classification = task_router.classify(task_data.description)
        logger.info(
            f"TaskRouter: {task_data.title} -> type={classification.task_type}, "
            f"complexity={classification.complexity}, raid={classification.suggested_raid_level}"
        )
        # Store routing metadata in parameters JSON
        existing_params = json.loads(row.parameters) if row.parameters else {}
        existing_params["_routing"] = {
            "classified_type": classification.task_type,
            "complexity": str(classification.complexity),
            "suggested_raid_level": classification.suggested_raid_level,
            "confidence": classification.confidence,
            "method": classification.classification_method,
        }
        row.parameters = json.dumps(existing_params, ensure_ascii=False)
        db.commit()
    except Exception as e:
        logger.debug(f"TaskRouter classification skipped: {e}")

    # Dispatch to agent-engine asynchronously (fire-and-forget)
    asyncio.create_task(_dispatch_academic_task(task_id))

    return _model_to_response(row)


@router.get("/templates/list")
async def list_academic_templates():
    """
    List available academic task templates.

    Templates provide pre-built prompts for common task types,
    improving code generation quality and reducing user input.

    **Returns**: List of template identifiers and display names.
    """
    from services.academic_templates import list_templates
    return {
        "success": True,
        "data": {"templates": list_templates()},
        "error": None,
    }


@router.get("/{task_id}", response_model=AcademicTaskResponse)
@limiter.limit("60/minute")
async def get_academic_task(request: Request, task_id: str, db: Session = Depends(get_db)):
    """
    Get the status and results of an academic task.

    **Rate Limit**: 60 requests per minute

    **Path Parameters**:
    - `task_id`: The task identifier returned from submit

    **Returns**: Task details including status and results (if completed).

    **Errors**:
    - `404`: Task not found
    """
    row = db.query(AcademicTaskModel).filter(AcademicTaskModel.task_id == task_id).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Academic task '{task_id}' not found",
                }
            },
        )
    return _model_to_response(row)


@router.get("/{task_id}/pdf")
async def download_task_pdf(task_id: str, db: Session = Depends(get_db)):
    """
    Download the result of a completed academic task as a PDF report.

    **Path Parameters**:
    - `task_id`: The task identifier returned from submit

    **Returns**: PDF file download (`application/pdf`).

    **Errors**:
    - `404`: Task not found
    - `400`: Task not yet completed
    - `500`: PDF generation failed
    """
    from fastapi.responses import Response
    from services.pdf_generator import pdf_from_academic_task

    row = db.query(AcademicTaskModel).filter(
        AcademicTaskModel.task_id == task_id
    ).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Academic task '{task_id}' not found",
                }
            },
        )
    if row.status != AcademicTaskStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "TASK_NOT_COMPLETED",
                    "message": f"Task not completed (status: {row.status})",
                    "details": {"current_status": row.status},
                }
            },
        )

    task_data = {
        "task_id": row.task_id,
        "title": row.title,
        "description": row.description,
        "status": row.status,
        "result_output": row.result_output,
        "parameters": row.parameters,
        "token_reward": row.token_reward,
    }
    pdf_bytes = pdf_from_academic_task(task_data)
    if not pdf_bytes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "PDF_GENERATION_FAILED",
                    "message": "PDF generation failed",
                }
            },
        )

    filename = f"nautilus-report-{task_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/", response_model=AcademicTaskListResponse)
@limiter.limit("30/minute")
async def list_academic_tasks(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    task_type: Optional[AcademicTaskType] = Query(
        None, description="Filter by task type"
    ),
    task_status: Optional[AcademicTaskStatus] = Query(
        None, alias="status", description="Filter by status"
    ),
    db: Session = Depends(get_db),
):
    """
    List academic tasks with pagination and optional filters.

    **Rate Limit**: 30 requests per minute

    **Query Parameters**:
    - `page`: Page number (default 1)
    - `limit`: Items per page (default 20, max 100)
    - `task_type`: Filter by academic task type
    - `status`: Filter by task status

    **Returns**: Paginated list of tasks.
    """
    query = db.query(AcademicTaskModel)

    if task_type is not None:
        query = query.filter(AcademicTaskModel.task_type == task_type.value)
    if task_status is not None:
        query = query.filter(AcademicTaskModel.status == task_status.value)

    total = query.count()

    rows = (
        query
        .order_by(AcademicTaskModel.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return AcademicTaskListResponse(
        tasks=[_model_to_response(r) for r in rows],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("/{task_id}/cancel")
@limiter.limit("10/minute")
async def cancel_academic_task(request: Request, task_id: str, db: Session = Depends(get_db)):
    """
    Cancel a pending academic task.

    Only tasks in PENDING status can be cancelled. Tasks that are already
    processing, completed, or failed cannot be cancelled.

    **Rate Limit**: 10 requests per minute

    **Path Parameters**:
    - `task_id`: The task identifier

    **Returns**: Updated task status.

    **Errors**:
    - `404`: Task not found
    - `400`: Task cannot be cancelled (not in pending status)
    """
    row = db.query(AcademicTaskModel).filter(AcademicTaskModel.task_id == task_id).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Academic task '{task_id}' not found",
                }
            },
        )

    if row.status != AcademicTaskStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "TASK_NOT_CANCELLABLE",
                    "message": f"Task in '{row.status}' status cannot be cancelled",
                    "details": {"current_status": row.status},
                }
            },
        )

    row.status = AcademicTaskStatus.CANCELLED.value
    row.updated_at = datetime.utcnow()
    db.commit()
    logger.info(f"Academic task cancelled: {task_id}")

    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "status": row.status,
        },
        "error": None,
    }


@router.post("/{task_id}/retry")
@limiter.limit("10/minute")
async def retry_academic_task(request: Request, task_id: str, db: Session = Depends(get_db)):
    """
    Retry a failed or stuck (processing) academic task.

    Resets the task to PENDING and re-dispatches it.

    **Rate Limit**: 10 requests per minute
    """
    row = db.query(AcademicTaskModel).filter(AcademicTaskModel.task_id == task_id).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": f"Academic task '{task_id}' not found",
                }
            },
        )

    retryable = (
        AcademicTaskStatus.FAILED.value,
        AcademicTaskStatus.PROCESSING.value,
        AcademicTaskStatus.PENDING.value,
    )
    if row.status not in retryable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "TASK_NOT_RETRYABLE",
                    "message": f"Task in '{row.status}' status cannot be retried",
                    "details": {"current_status": row.status},
                }
            },
        )

    row.status = AcademicTaskStatus.PENDING.value
    row.result_code = None
    row.result_output = None
    row.result_error = None
    row.result_plots = None
    row.execution_time = None
    row.updated_at = datetime.utcnow()
    db.commit()
    logger.info(f"Academic task retried: {task_id}")

    # Re-dispatch
    asyncio.create_task(_dispatch_academic_task(task_id))

    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "status": row.status,
        },
        "error": None,
    }


@router.post("/admin/retry-stuck")
@limiter.limit("5/minute")
async def retry_stuck_tasks(request: Request, db: Session = Depends(get_db)):
    """
    Reset all stuck (processing) tasks back to pending and re-dispatch them.

    **Rate Limit**: 5 requests per minute
    """
    from api.org import _auth_check  # 2026-10-11 追补①(放大器收口):一次调用=N 次付费重派发
    denied = _auth_check(db, request, "platform")
    if denied:
        return denied
    stuck_tasks = db.query(AcademicTaskModel).filter(
        AcademicTaskModel.status.in_([
            AcademicTaskStatus.PROCESSING.value,
            AcademicTaskStatus.PENDING.value,
        ])
    ).all()

    reset_ids = []
    for row in stuck_tasks:
        row.status = AcademicTaskStatus.PENDING.value
        row.updated_at = datetime.utcnow()
        reset_ids.append(row.task_id)

    db.commit()
    logger.info(f"Reset {len(reset_ids)} stuck tasks: {reset_ids}")

    # Re-dispatch all
    for tid in reset_ids:
        asyncio.create_task(_dispatch_academic_task(tid))

    return {
        "success": True,
        "data": {
            "reset_count": len(reset_ids),
            "task_ids": reset_ids,
        },
        "error": None,
    }


# ------------------------------------------------------------------
# Background dispatch
# ------------------------------------------------------------------

async def _dispatch_academic_task(task_id: str) -> None:
    """
    Background coroutine that dispatches an academic task to the
    agent-engine CodeExecutor and updates the database with the result.

    Uses get_db_context() for its own session since this runs outside
    the request lifecycle.

    Guarded by _task_semaphore to allow at most 3 concurrent dispatches,
    preventing resource exhaustion while enabling parallel execution.
    """
    async with _task_semaphore:
        await _dispatch_academic_task_inner(task_id)


async def _dispatch_academic_task_inner(task_id: str) -> None:
    """Inner dispatch logic, called under the semaphore."""
    with get_db_context() as db:
        row = db.query(AcademicTaskModel).filter(AcademicTaskModel.task_id == task_id).first()
        if not row:
            logger.error("Dispatch: task %s not found in DB", task_id)
            return

        if row.status != AcademicTaskStatus.PENDING.value:
            logger.warning("Dispatch: task %s not pending (status=%s)", task_id, row.status)
            return

        # Mark as processing + auto-assign to a random alive agent if not already assigned
        row.status = AcademicTaskStatus.PROCESSING.value
        row.updated_at = datetime.utcnow()
        if not row.assigned_agent_id:
            try:
                from models.database import Agent as AgentModel
                from sqlalchemy import text
                import random
                import json as _json
                from services.ability_tags import agent_matches_task
                # Only assign to agents that have survival records (so scores can update)
                alive_rows = db.execute(
                    text(
                        "SELECT a.agent_id, a.specialties FROM agents a "
                        "JOIN agent_survival s ON a.agent_id = s.agent_id "
                        "WHERE a.agent_status = 'alive' LIMIT 200"
                    )
                ).fetchall()
                if alive_rows:
                    task_type = row.task_type or ""
                    matched, fallback = [], []
                    for agent_id, specialties_raw in alive_rows:
                        try:
                            specs = _json.loads(specialties_raw) if specialties_raw else []
                        except Exception:
                            specs = []
                        if agent_matches_task(specs, task_type):
                            matched.append(agent_id)
                        else:
                            fallback.append(agent_id)
                    candidates = matched if matched else fallback
                    row.assigned_agent_id = random.choice(candidates)
                    logger.info(
                        "Task %s (type=%s) assigned to agent_id=%s (pool: %d matched, %d fallback)",
                        task_id, task_type, row.assigned_agent_id, len(matched), len(fallback),
                    )
            except Exception as assign_err:
                logger.warning("Agent assignment skipped: %s", assign_err)
        db.commit()
        logger.info("Dispatching academic task %s to engine", task_id)

        # Check for matching knowledge capsule to boost execution
        try:
            from services.knowledge_capsule import KnowledgeEngine
            ke = KnowledgeEngine()
            capsule = ke.find_matching_capsule(row.description or "", row.task_type or "")
            if capsule:
                logger.info(
                    "Knowledge capsule match for %s: %s (epiplexity=%.3f)",
                    task_id, capsule.get("capsule_id", "?"), capsule.get("epiplexity_score", 0),
                )
                # Will record actual success/failure after execution completes
                ke.record_reuse(capsule.get("capsule_id", ""), success=True)
        except Exception as cap_err:
            logger.debug("Capsule lookup skipped: %s", cap_err)

        # Build the task dict that the service expects
        parameters = None
        if row.parameters:
            try:
                parameters = json.loads(row.parameters)
            except (json.JSONDecodeError, TypeError):
                parameters = None

        task_dict = {
            "task_id": row.task_id,
            "title": row.title,
            "description": row.description,
            "task_type": row.task_type,
            "status": row.status,
            "input_data": row.input_data,
            "parameters": parameters,
            "expected_output": row.expected_output,
        }

    # Execute outside the DB session to avoid holding the connection
    try:
        from services.academic_task_service import get_academic_task_service

        service = get_academic_task_service()
        result = await service.execute_task(task_id, task_dict)

        with get_db_context() as db:
            row = db.query(AcademicTaskModel).filter(AcademicTaskModel.task_id == task_id).first()
            if not row:
                logger.error("Dispatch: task %s disappeared from DB after execution", task_id)
                return

            row.result_code = result.get("code")
            row.result_output = result.get("output")
            row.result_error = result.get("error")
            row.execution_time = result.get("execution_time")

            plots = result.get("plots")
            row.result_plots = json.dumps(plots) if plots else None

            # Persist DeerFlow sections + metadata into parameters._deerflow
            if result.get("pipeline") == "deerflow" and result.get("sections"):
                try:
                    existing_params: dict = {}
                    if row.parameters:
                        try:
                            existing_params = json.loads(row.parameters)
                        except (json.JSONDecodeError, TypeError):
                            existing_params = {}
                    existing_params["_deerflow"] = {
                        "sections": result["sections"],
                        "depth": result.get("depth", "standard"),
                        "sources_count": result.get("sources_count", 0),
                        "pipeline": "deerflow-v1",
                    }
                    row.parameters = json.dumps(existing_params, ensure_ascii=False)
                except Exception as _df_err:
                    logger.warning("Failed to persist DeerFlow metadata for task %s: %s", task_id, _df_err)

            if result.get("error"):
                row.status = AcademicTaskStatus.FAILED.value
            else:
                row.status = AcademicTaskStatus.COMPLETED.value
                row.audit_status = "pending"

            row.updated_at = datetime.utcnow()
            db.commit()

            logger.info(
                "Academic task %s finished: status=%s time=%.2fs",
                task_id,
                row.status,
                result.get("execution_time", 0),
            )

            # Update survival scores + agent stats for the assigned agent
            _agent_id_to_credit = row.assigned_agent_id
            _task_succeeded = row.status == AcademicTaskStatus.COMPLETED.value
            if _agent_id_to_credit:
                try:
                    from services.survival_service import SurvivalService
                    from models.database import Agent as AgentModel
                    with get_db_context() as sdb:
                        if _task_succeeded:
                            SurvivalService.update_scores_on_task_completion(
                                sdb,
                                _agent_id_to_credit,
                                task_reward=0.0,
                                task_duration_seconds=float(row.execution_time or 30.0),
                                published_duration_seconds=300.0,
                            )
                            # Also increment agents.completed_tasks
                            agent_row = sdb.query(AgentModel).filter(
                                AgentModel.agent_id == _agent_id_to_credit
                            ).first()
                            if agent_row:
                                agent_row.completed_tasks = (agent_row.completed_tasks or 0) + 1
                            sdb.commit()
                            logger.debug("Credited agent %s for completed task %s",
                                         _agent_id_to_credit, task_id)
                        else:
                            agent_row = sdb.query(AgentModel).filter(
                                AgentModel.agent_id == _agent_id_to_credit
                            ).first()
                            if agent_row:
                                agent_row.failed_tasks = (agent_row.failed_tasks or 0) + 1
                            sdb.commit()
                except Exception as surv_err:
                    logger.warning("Survival score update failed: %s", surv_err)

            # Capability evolution record — 喂点已下线(2026-08-27 转移线④):
            # 自报口径(success=任务执行自报)不再喂能力,能力只从 external-verify
            # 权威喂点(services/capability_feed.py)进——"自报不算"。
            # kairos statistical_analysis 100% 成功率污染的第二源头即此处。

            # Mint NAU token reward (Proof of Useful Work) — non-blocking
            if _task_succeeded and _agent_id_to_credit:
                try:
                    from services.nautilus_token import NautilusTokenService, TASK_TYPE_REWARDS
                    from models.database import Agent as AgentModel
                    with get_db_context() as tdb:
                        agent_row = tdb.query(AgentModel).filter(
                            AgentModel.agent_id == _agent_id_to_credit
                        ).first()
                        raw_wallet = agent_row.owner if agent_row else None
                        # Only use wallet if it looks like a valid ETH address (0x + 40 hex chars)
                        import re as _re
                        agent_wallet = raw_wallet if (
                            raw_wallet and _re.match(r'^0x[0-9a-fA-F]{40}$', raw_wallet)
                        ) else None
                    if agent_wallet:
                        tx_hash = None
                        task_type_str = row.task_type or "general_computation"
                        # For research_synthesis: use collaborative reward if researchers listed
                        if task_type_str == "research_synthesis":
                            try:
                                _params = json.loads(row.parameters) if row.parameters else {}
                                researcher_wallets = (
                                    _params.get("_deerflow", {}).get("researchers") or []
                                )
                            except (json.JSONDecodeError, TypeError, AttributeError):
                                researcher_wallets = []
                            if researcher_wallets:
                                tx_hash = await NautilusTokenService.mint_collaborative_reward(
                                    coordinator_wallet=agent_wallet,
                                    researcher_wallets=researcher_wallets,
                                    task_type=task_type_str,
                                )
                            else:
                                tx_hash = await NautilusTokenService.mint_task_reward(
                                    agent_wallet=agent_wallet,
                                    task_type=task_type_str,
                                )
                        else:
                            tx_hash = await NautilusTokenService.mint_task_reward(
                                agent_wallet=agent_wallet,
                                task_type=task_type_str,
                            )
                        # Normalize tx_hash: mint_collaborative_reward returns a list
                        if isinstance(tx_hash, list):
                            tx_hash = tx_hash[0] if tx_hash else None
                        if tx_hash:
                            with get_db_context() as tdb:
                                task_row = tdb.query(AcademicTaskModel).filter(
                                    AcademicTaskModel.task_id == task_id
                                ).first()
                                if task_row:
                                    task_row.blockchain_tx_hash = tx_hash
                                    task_row.token_reward = float(
                                        TASK_TYPE_REWARDS.get(row.task_type or "", 1)
                                    )
                                    tdb.commit()
                except Exception as mint_err:
                    logger.warning("NAU mint failed (non-blocking): %s", mint_err)

                # Fallback: always record off-chain credit regardless of on-chain mint
                try:
                    from sqlalchemy import text
                    from services.nautilus_token import TASK_TYPE_REWARDS
                    reward_amount = float(TASK_TYPE_REWARDS.get(row.task_type or "", 1))
                    with get_db_context() as cdb:
                        # Record in credit_transactions (off-chain ledger)
                        cdb.execute(text(
                            "INSERT INTO credit_transactions "
                            "(account_id, transaction_type, amount, balance_after, description, task_id) "
                            "VALUES (:aid, 'task_reward', :amt, "
                            "  COALESCE((SELECT balance_after FROM credit_transactions "
                            "   WHERE account_id=:aid ORDER BY created_at DESC LIMIT 1), 0) + :amt, "
                            "  :desc, :tid)"
                        ), {
                            "aid": str(_agent_id_to_credit),
                            "amt": reward_amount,
                            "desc": f"NAU reward for {row.task_type or 'task'}: {task_id}",
                            "tid": task_id,
                        })
                        # Queue for batch on-chain mint (flush_pending_nau cron)
                        cdb.execute(text(
                            "INSERT INTO pending_nau_rewards "
                            "(agent_id, amount, reason, source_id, status) "
                            "VALUES (:aid, :amt, :reason, :sid, 'pending') "
                            "ON CONFLICT DO NOTHING"
                        ), {
                            "aid": _agent_id_to_credit,
                            "amt": reward_amount,
                            "reason": f"task_completion:{row.task_type or 'general'}",
                            "sid": task_id,
                        })
                        cdb.commit()
                except Exception as credit_err:
                    logger.warning("Off-chain credit record failed: %s", credit_err)

            # Fire background auditor verification (non-blocking)
            if row.status == AcademicTaskStatus.COMPLETED.value:
                try:
                    from services.rehoboam import get_rehoboam
                    rehoboam = get_rehoboam()
                    asyncio.ensure_future(rehoboam.verify_task_result(task_id))
                    logger.info("Auditor verification dispatched for %s", task_id)
                except Exception as audit_err:
                    logger.warning("Failed to dispatch auditor for %s: %s", task_id, audit_err)

                # Extract knowledge capsule from successful task (non-blocking)
                try:
                    from services.knowledge_capsule import KnowledgeEngine
                    engine = KnowledgeEngine()
                    capsule = engine.extract_capsule(
                        task_id=task_id,
                        task_type=row.task_type or "",
                        description=row.description or "",
                        code=result.get("code", ""),
                        output=result.get("output", ""),
                        parameters=json.loads(row.parameters) if row.parameters else None,
                    )
                    if capsule:
                        logger.info("Knowledge capsule extracted for %s: %s", task_id, capsule.capsule_id)
                except Exception as cap_err:
                    logger.debug("Knowledge capsule extraction skipped for %s: %s", task_id, cap_err)

            # Partner webhook + auto-refund on failure
            try:
                from services.partner_webhook import (
                    notify_partner_task_complete,
                    refund_partner_on_failure,
                )
                import asyncio
                asyncio.ensure_future(notify_partner_task_complete(task_id))
                if row.status == AcademicTaskStatus.FAILED.value:
                    asyncio.ensure_future(refund_partner_on_failure(task_id))
            except Exception as wh_err:
                logger.warning("Partner webhook/refund error for %s: %s", task_id, wh_err)

    except Exception as exc:
        logger.error("Academic task %s dispatch error: %s", task_id, exc, exc_info=True)
        with get_db_context() as db:
            row = db.query(AcademicTaskModel).filter(AcademicTaskModel.task_id == task_id).first()
            if row:
                row.status = AcademicTaskStatus.FAILED.value
                row.result_error = f"Dispatch error: {exc}"
                row.updated_at = datetime.utcnow()
                db.commit()

        # Refund partner on dispatch failure too
        try:
            from services.partner_webhook import (
                notify_partner_task_complete,
                refund_partner_on_failure,
            )
            import asyncio
            asyncio.ensure_future(notify_partner_task_complete(task_id))
            asyncio.ensure_future(refund_partner_on_failure(task_id))
        except Exception:
            pass

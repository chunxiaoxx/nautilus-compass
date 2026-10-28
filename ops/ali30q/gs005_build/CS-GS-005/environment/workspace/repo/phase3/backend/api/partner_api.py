"""
White-label Partner API.

All responses are brand-neutral. No mention of "Nautilus".
Partners authenticate via X-API-Key header.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging
import secrets
import json

from models.partner import Partner, PartnerTask
from models.database import AcademicTask, SimulationTask
from utils.database import get_db
from services.pricing import TASK_PRICES, get_task_price

router = APIRouter()
logger = logging.getLogger(__name__)


# --------------- Auth ---------------

def get_partner(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Partner:
    """Authenticate partner via API key."""
    partner = db.query(Partner).filter(
        Partner.api_key == x_api_key,
        Partner.is_active.is_(True),
    ).first()
    if not partner:
        raise HTTPException(status_code=401, detail="Invalid API key")
    partner.last_used_at = datetime.utcnow()
    db.commit()
    return partner


# --------------- Models ---------------

class TaskSubmitRequest(BaseModel):
    """Submit a compute task."""
    type: str                          # e.g. "jc_constitutive", "curve_fitting"
    title: str
    description: str
    input_data: Optional[str] = None
    parameters: Optional[str] = None   # JSON string
    external_ref: Optional[str] = None # partner's own tracking ID
    callback_url: Optional[str] = None # override partner-level webhook


class TaskSubmitResponse(BaseModel):
    task_id: str
    external_ref: Optional[str]
    status: str
    estimated_cost: float


# --------------- Endpoints ---------------

@router.post("/tasks", response_model=TaskSubmitResponse)
def submit_task(
    req: TaskSubmitRequest,
    partner: Partner = Depends(get_partner),
    db: Session = Depends(get_db),
):
    """Submit a compute task. Cost is deducted from partner balance."""
    # Check allowed types
    if partner.allowed_task_types:
        allowed = json.loads(partner.allowed_task_types)
        if req.type not in allowed:
            raise HTTPException(400, f"Task type '{req.type}' not enabled for your account")

    # Calculate partner cost (discounted)
    retail_price = get_task_price(req.type)
    partner_cost = round(retail_price * partner.discount_rate, 2)

    # Check balance
    if partner.balance < partner_cost:
        raise HTTPException(
            402,
            {
                "code": "INSUFFICIENT_BALANCE",
                "message": "Insufficient balance",
                "required": partner_cost,
                "available": partner.balance,
            },
        )

    # Create internal task
    task_id = f"acad_{secrets.token_hex(8)}"
    task = AcademicTask(
        task_id=task_id,
        title=req.title,
        description=req.description,
        task_type=req.type,
        status="pending",
        input_data=req.input_data,
        parameters=req.parameters,
    )
    db.add(task)

    # Deduct balance
    partner.balance -= partner_cost
    partner.total_spent += partner_cost

    # Record mapping
    pt = PartnerTask(
        partner_id=partner.partner_id,
        external_ref=req.external_ref,
        internal_task_id=task_id,
        task_category="academic",
        cost_to_partner=partner_cost,
    )
    db.add(pt)
    db.commit()

    # Dispatch via the same pipeline as regular academic tasks
    try:
        import asyncio
        from api.academic_tasks import _dispatch_academic_task
        asyncio.ensure_future(_dispatch_academic_task(task_id))
    except Exception as e:
        logger.warning(f"Failed to auto-dispatch partner task {task_id}: {e}")

    return TaskSubmitResponse(
        task_id=task_id,
        external_ref=req.external_ref,
        status="pending",
        estimated_cost=partner_cost,
    )


@router.get("/tasks/{task_id}")
def get_task_status(
    task_id: str,
    partner: Partner = Depends(get_partner),
    db: Session = Depends(get_db),
):
    """Get task status and results. Brand-neutral response."""
    # Verify this task belongs to the partner
    pt = db.query(PartnerTask).filter(
        PartnerTask.partner_id == partner.partner_id,
        PartnerTask.internal_task_id == task_id,
    ).first()
    if not pt:
        raise HTTPException(404, "Task not found")

    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")

    result = {
        "task_id": task.task_id,
        "external_ref": pt.external_ref,
        "type": task.task_type,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }

    if task.status == "completed":
        result["result"] = {
            "code": task.result_code,
            "output": task.result_output,
            "plots": json.loads(task.result_plots) if task.result_plots else [],
            "execution_time": task.execution_time,
        }
    elif task.status == "failed":
        result["error"] = task.result_error

    return result


@router.get("/tasks")
def list_tasks(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    partner: Partner = Depends(get_partner),
    db: Session = Depends(get_db),
):
    """List partner's tasks."""
    q = db.query(PartnerTask).filter(PartnerTask.partner_id == partner.partner_id)
    if status:
        # Join to filter by actual task status
        q = q.join(
            AcademicTask,
            PartnerTask.internal_task_id == AcademicTask.task_id,
        ).filter(AcademicTask.status == status)

    total = q.count()
    rows = q.order_by(PartnerTask.created_at.desc()).offset(offset).limit(limit).all()

    tasks = []
    for pt in rows:
        task = db.query(AcademicTask).filter(
            AcademicTask.task_id == pt.internal_task_id
        ).first()
        tasks.append({
            "task_id": pt.internal_task_id,
            "external_ref": pt.external_ref,
            "type": task.task_type if task else "unknown",
            "status": task.status if task else "unknown",
            "cost": pt.cost_to_partner,
            "created_at": pt.created_at.isoformat() if pt.created_at else None,
        })

    return {"tasks": tasks, "total": total, "limit": limit, "offset": offset}


@router.get("/balance")
def get_balance(
    partner: Partner = Depends(get_partner),
):
    """Get current account balance."""
    return {
        "balance": partner.balance,
        "total_deposited": partner.total_deposited,
        "total_spent": partner.total_spent,
        "discount_rate": partner.discount_rate,
    }


@router.get("/prices")
def get_prices(
    partner: Partner = Depends(get_partner),
):
    """Get task prices at partner's discount rate."""
    prices = {}
    for task_type, retail_price in TASK_PRICES.items():
        prices[task_type] = round(retail_price * partner.discount_rate, 2)
    return {"prices": prices, "discount_rate": partner.discount_rate, "currency": "RMB"}


# --------------- Batch Submit ---------------

class BatchTaskItem(BaseModel):
    type: str
    title: str
    description: str
    input_data: Optional[str] = None
    parameters: Optional[str] = None
    external_ref: Optional[str] = None


class BatchSubmitRequest(BaseModel):
    tasks: list[BatchTaskItem]


@router.post("/tasks/batch")
def batch_submit(
    req: BatchSubmitRequest,
    partner: Partner = Depends(get_partner),
    db: Session = Depends(get_db),
):
    """Submit multiple tasks in one request. Atomic: all succeed or none."""
    if len(req.tasks) > 50:
        raise HTTPException(400, "Max 50 tasks per batch")
    if not req.tasks:
        raise HTTPException(400, "At least 1 task required")

    # Pre-check total cost
    total_cost = 0.0
    allowed = None
    if partner.allowed_task_types:
        allowed = json.loads(partner.allowed_task_types)

    for item in req.tasks:
        if allowed and item.type not in allowed:
            raise HTTPException(400, f"Task type '{item.type}' not enabled")
        retail = get_task_price(item.type)
        total_cost += round(retail * partner.discount_rate, 2)

    if partner.balance < total_cost:
        raise HTTPException(402, {
            "code": "INSUFFICIENT_BALANCE",
            "message": f"Batch requires {total_cost} RMB, available {partner.balance}",
            "required": total_cost,
            "available": partner.balance,
        })

    # Create all tasks
    results = []
    for item in req.tasks:
        task_id = f"acad_{secrets.token_hex(8)}"
        retail = get_task_price(item.type)
        cost = round(retail * partner.discount_rate, 2)

        task = AcademicTask(
            task_id=task_id,
            title=item.title,
            description=item.description,
            task_type=item.type,
            status="pending",
            input_data=item.input_data,
            parameters=item.parameters,
        )
        db.add(task)

        pt = PartnerTask(
            partner_id=partner.partner_id,
            external_ref=item.external_ref,
            internal_task_id=task_id,
            task_category="academic",
            cost_to_partner=cost,
        )
        db.add(pt)

        partner.balance -= cost
        partner.total_spent += cost

        results.append({
            "task_id": task_id,
            "external_ref": item.external_ref,
            "type": item.type,
            "cost": cost,
        })

    db.commit()

    # Dispatch all via core pipeline
    try:
        import asyncio
        from api.academic_tasks import _dispatch_academic_task
        for r in results:
            asyncio.ensure_future(_dispatch_academic_task(r["task_id"]))
    except Exception as e:
        logger.warning(f"Failed to dispatch batch tasks: {e}")

    return {
        "submitted": len(results),
        "total_cost": total_cost,
        "tasks": results,
    }


# --------------- Usage Stats ---------------

@router.get("/stats")
def get_usage_stats(
    partner: Partner = Depends(get_partner),
    db: Session = Depends(get_db),
):
    """Get usage statistics for the partner."""
    total = db.query(PartnerTask).filter(
        PartnerTask.partner_id == partner.partner_id,
    ).count()

    completed = db.query(PartnerTask).join(
        AcademicTask,
        PartnerTask.internal_task_id == AcademicTask.task_id,
    ).filter(
        PartnerTask.partner_id == partner.partner_id,
        AcademicTask.status == "completed",
    ).count()

    failed = db.query(PartnerTask).join(
        AcademicTask,
        PartnerTask.internal_task_id == AcademicTask.task_id,
    ).filter(
        PartnerTask.partner_id == partner.partner_id,
        AcademicTask.status == "failed",
    ).count()

    pending = total - completed - failed

    return {
        "total_tasks": total,
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "success_rate": round(completed / total * 100, 1) if total > 0 else 0,
        "total_spent": partner.total_spent,
        "balance": partner.balance,
    }

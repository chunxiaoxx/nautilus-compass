"""
Partner admin API - for Nautilus admins to manage partners.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import secrets
import hashlib
import logging
from sqlalchemy import func

from models.database import User
from models.partner import Partner
from utils.database import get_db
from utils.auth import get_current_admin_user

router = APIRouter()
logger = logging.getLogger(__name__)


class CreatePartnerRequest(BaseModel):
    name: str
    contact_email: Optional[str] = None
    discount_rate: float = 0.3
    rate_limit_per_minute: int = 60
    allowed_task_types: Optional[str] = None  # JSON list or null


class DepositPartnerRequest(BaseModel):
    amount: float
    description: str = ""


@router.post("/create")
def create_partner(
    req: CreatePartnerRequest,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create a new partner account with API credentials."""
    partner_id = f"ptr_{secrets.token_hex(6)}"
    api_key = f"nk_{secrets.token_hex(24)}"
    api_secret = secrets.token_hex(32)

    partner = Partner(
        partner_id=partner_id,
        name=req.name,
        contact_email=req.contact_email,
        api_key=api_key,
        api_secret=hashlib.sha256(api_secret.encode()).hexdigest(),
        discount_rate=req.discount_rate,
        rate_limit_per_minute=req.rate_limit_per_minute,
        allowed_task_types=req.allowed_task_types,
    )
    db.add(partner)
    db.commit()

    logger.info(f"Created partner {partner_id}: {req.name}")

    return {
        "success": True,
        "data": {
            "partner_id": partner_id,
            "name": req.name,
            "api_key": api_key,
            "api_secret": api_secret,  # Only shown once
            "discount_rate": req.discount_rate,
            "message": "Save the api_key and api_secret securely. The secret will not be shown again.",
        },
    }


@router.post("/{partner_id}/deposit")
def deposit_to_partner(
    partner_id: str,
    req: DepositPartnerRequest,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Deposit credits to a partner account."""
    partner = db.query(Partner).filter(Partner.partner_id == partner_id).first()
    if not partner:
        raise HTTPException(404, "Partner not found")
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    partner.balance += req.amount
    partner.total_deposited += req.amount
    db.commit()

    logger.info(f"Deposited {req.amount} RMB to partner {partner_id}")

    return {
        "success": True,
        "data": {
            "partner_id": partner_id,
            "deposited": req.amount,
            "new_balance": partner.balance,
        },
    }


@router.get("/list")
def list_partners(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """List all partners."""
    partners = db.query(Partner).order_by(Partner.created_at.desc()).all()
    return {
        "success": True,
        "data": [
            {
                "partner_id": p.partner_id,
                "name": p.name,
                "balance": p.balance,
                "total_spent": p.total_spent,
                "discount_rate": p.discount_rate,
                "is_active": p.is_active,
                "last_used_at": p.last_used_at.isoformat() if p.last_used_at else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in partners
        ],
    }


@router.patch("/{partner_id}/toggle")
def toggle_partner(
    partner_id: str,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Enable or disable a partner."""
    partner = db.query(Partner).filter(Partner.partner_id == partner_id).first()
    if not partner:
        raise HTTPException(404, "Partner not found")

    partner.is_active = not partner.is_active
    db.commit()

    return {
        "success": True,
        "data": {
            "partner_id": partner_id,
            "is_active": partner.is_active,
        },
    }


class UpdatePartnerRequest(BaseModel):
    discount_rate: Optional[float] = None
    rate_limit_per_minute: Optional[int] = None
    webhook_url: Optional[str] = None
    allowed_task_types: Optional[str] = None


@router.patch("/{partner_id}")
def update_partner(
    partner_id: str,
    req: UpdatePartnerRequest,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Update partner settings (discount rate, webhook, limits)."""
    partner = db.query(Partner).filter(Partner.partner_id == partner_id).first()
    if not partner:
        raise HTTPException(404, "Partner not found")

    if req.discount_rate is not None:
        if not 0 < req.discount_rate < 1:
            raise HTTPException(400, "Discount rate must be between 0 and 1")
        partner.discount_rate = req.discount_rate
    if req.rate_limit_per_minute is not None:
        partner.rate_limit_per_minute = req.rate_limit_per_minute
    if req.webhook_url is not None:
        partner.webhook_url = req.webhook_url
    if req.allowed_task_types is not None:
        partner.allowed_task_types = req.allowed_task_types

    db.commit()
    logger.info(f"Updated partner {partner_id}: {req.dict(exclude_none=True)}")

    return {
        "success": True,
        "data": {
            "partner_id": partner_id,
            "discount_rate": partner.discount_rate,
            "webhook_url": partner.webhook_url,
            "rate_limit_per_minute": partner.rate_limit_per_minute,
        },
    }


@router.get("/{partner_id}/report")
def partner_report(
    partner_id: str,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Detailed usage report for a partner."""
    from models.partner import PartnerTask
    from models.database import AcademicTask
    from sqlalchemy import func

    partner = db.query(Partner).filter(Partner.partner_id == partner_id).first()
    if not partner:
        raise HTTPException(404, "Partner not found")

    # Task count by status
    status_counts = dict(
        db.query(AcademicTask.status, func.count(AcademicTask.id))
        .join(PartnerTask, PartnerTask.internal_task_id == AcademicTask.task_id)
        .filter(PartnerTask.partner_id == partner_id)
        .group_by(AcademicTask.status)
        .all()
    )

    # Task count by type
    type_counts = dict(
        db.query(AcademicTask.task_type, func.count(AcademicTask.id))
        .join(PartnerTask, PartnerTask.internal_task_id == AcademicTask.task_id)
        .filter(PartnerTask.partner_id == partner_id)
        .group_by(AcademicTask.task_type)
        .all()
    )

    # Avg execution time
    avg_time = (
        db.query(func.avg(AcademicTask.execution_time))
        .join(PartnerTask, PartnerTask.internal_task_id == AcademicTask.task_id)
        .filter(
            PartnerTask.partner_id == partner_id,
            AcademicTask.status == "completed",
        )
        .scalar()
    )

    # Total cost
    total_cost = (
        db.query(func.sum(PartnerTask.cost_to_partner))
        .filter(PartnerTask.partner_id == partner_id)
        .scalar()
    ) or 0

    return {
        "success": True,
        "data": {
            "partner_id": partner_id,
            "name": partner.name,
            "balance": partner.balance,
            "total_deposited": partner.total_deposited,
            "total_spent": partner.total_spent,
            "discount_rate": partner.discount_rate,
            "by_status": status_counts,
            "by_type": type_counts,
            "avg_execution_time_seconds": round(avg_time, 1) if avg_time else None,
            "total_cost_to_partner": total_cost,
            "revenue_to_us": total_cost,  # same since we charge partner cost
        },
    }

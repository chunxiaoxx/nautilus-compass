"""
Payment API endpoints for credit-based billing.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

from models.database import User
from utils.database import get_db
from utils.auth import get_current_user, get_current_admin_user
from services.payment_service import PaymentService, InsufficientBalanceError

router = APIRouter()


# --- Pricing endpoint (no auth required) ---

@router.get("/prices")
async def get_prices():
    """Get full price list for all task types."""
    from services.pricing import get_price_list
    return {"success": True, "data": get_price_list()}


# --- Request/Response Models ---

class DepositRequest(BaseModel):
    """Admin deposits credits for a client."""
    user_id: int
    amount: float
    description: str = ""

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class ChargeRequest(BaseModel):
    """Charge credits for a task (internal use)."""
    amount: float
    task_id: str
    description: str = ""

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class BalanceResponse(BaseModel):
    balance: float
    total_deposited: float
    total_spent: float


# --- Endpoints ---

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current credit balance for the authenticated user.

    **Authentication**: JWT token required

    **Returns**:
    - `balance`: Current available credits
    - `total_deposited`: Lifetime deposits
    - `total_spent`: Lifetime spending
    """
    account = PaymentService.get_or_create_account(db, current_user.id)
    return BalanceResponse(
        balance=account.balance,
        total_deposited=account.total_deposited,
        total_spent=account.total_spent,
    )


@router.post("/deposit")
async def deposit_credits(
    request: Request,
    deposit: DepositRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Admin deposits credits for a client.

    **Authentication**: Admin JWT token required

    **Request Body**:
    - `user_id`: Target user ID
    - `amount`: Amount to deposit (positive float)
    - `description`: Optional description

    **Returns**:
    - Transaction details and new balance
    """
    try:
        tx = PaymentService.deposit(
            db=db,
            user_id=deposit.user_id,
            amount=deposit.amount,
            description=deposit.description,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_AMOUNT", "message": str(e)}},
        )

    return {
        "success": True,
        "data": {
            "transaction_id": tx.id,
            "amount": tx.amount,
            "balance_after": tx.balance_after,
            "description": tx.description,
        },
    }


@router.get("/transactions")
async def get_transactions(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    transaction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get transaction history for the authenticated user.

    **Authentication**: JWT token required

    **Query Parameters**:
    - `limit`: Max records (default 50)
    - `offset`: Pagination offset (default 0)
    - `transaction_type`: Filter by type (deposit, task_charge, refund)

    **Returns**:
    - List of transactions
    """
    if limit > 200:
        limit = 200

    transactions = PaymentService.get_transactions(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        transaction_type=transaction_type,
    )

    return {
        "success": True,
        "data": transactions,
        "meta": {
            "limit": limit,
            "offset": offset,
            "count": len(transactions),
        },
    }


@router.get("/invoice/{year}/{month}")
async def get_invoice(
    request: Request,
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate monthly invoice summary for the authenticated user.

    **Authentication**: JWT token required

    **Path Parameters**:
    - `year`: Invoice year (e.g. 2026)
    - `month`: Invoice month (1-12)

    **Returns**:
    - Monthly summary with deposits, charges, refunds, and net spend
    """
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_MONTH", "message": "Month must be 1-12"}},
        )

    if year < 2020 or year > 2100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_YEAR", "message": "Year must be between 2020 and 2100"}},
        )

    summary = PaymentService.get_invoice_summary(
        db=db,
        user_id=current_user.id,
        year=year,
        month=month,
    )

    return {
        "success": True,
        "data": summary,
    }

"""
Payment models for credit-based billing.

Simple credit ledger for B2B clients (academic tasks, data labeling).
No blockchain needed - traditional PostgreSQL ledger.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from datetime import datetime
import enum

from models.database import Base


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    TASK_CHARGE = "task_charge"
    REFUND = "refund"


class CreditAccount(Base):
    """Credit account for a user. One account per user."""
    __tablename__ = "credit_accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    balance = Column(Float, default=0.0, nullable=False)
    total_deposited = Column(Float, default=0.0, nullable=False)
    total_spent = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class CreditTransaction(Base):
    """Individual credit transaction record."""
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("credit_accounts.id"), nullable=False, index=True)
    transaction_type = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)  # Positive for deposit/refund, negative for charge
    balance_after = Column(Float, nullable=False)
    description = Column(String(500))
    task_id = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_credit_tx_account_created", "account_id", "created_at"),
        Index("idx_credit_tx_type", "transaction_type"),
    )

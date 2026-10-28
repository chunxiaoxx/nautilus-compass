"""
Partner (white-label) model for B2B channel distribution.

Partners get a branded API key. Their end-users never see "Nautilus".
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, Index,
)
from models.database import Base


class Partner(Base):
    """A distribution partner who resells compute via white-label API."""
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, autoincrement=True)
    partner_id = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    contact_email = Column(String(200), nullable=True)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    api_secret = Column(String(128), nullable=False)

    # Billing
    balance = Column(Float, nullable=False, default=0.0)
    total_deposited = Column(Float, nullable=False, default=0.0)
    total_spent = Column(Float, nullable=False, default=0.0)
    discount_rate = Column(Float, nullable=False, default=0.3)  # 0.3 = pays 30% of retail

    # Limits
    rate_limit_per_minute = Column(Integer, nullable=False, default=60)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Metadata
    webhook_url = Column(String(500), nullable=True)  # callback on task completion
    allowed_task_types = Column(Text, nullable=True)   # JSON list, null = all
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_partner_api_key_active', 'api_key', 'is_active'),
    )


class PartnerTask(Base):
    """Maps a partner's external reference to an internal task."""
    __tablename__ = "partner_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    partner_id = Column(String(32), nullable=False, index=True)
    external_ref = Column(String(200), nullable=True, index=True)  # partner's own ID
    internal_task_id = Column(String(50), nullable=False, index=True)
    task_category = Column(String(20), nullable=False)  # academic / labeling / simulation
    cost_to_partner = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_partner_task_lookup', 'partner_id', 'external_ref'),
    )

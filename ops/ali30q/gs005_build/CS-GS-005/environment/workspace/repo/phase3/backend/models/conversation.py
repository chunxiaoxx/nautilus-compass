"""
Data models for the Agent commercial system.

Supports customer management, conversation history, order tracking,
and semantic memory for WeChat Enterprise integrations.
"""
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text,
    ForeignKey, Index, Boolean, SmallInteger,
)
from sqlalchemy.orm import relationship

from models.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class OrderStatus(str, enum.Enum):
    QUOTED = "quoted"
    PAID = "paid"
    EXECUTING = "executing"
    COMPLETED = "completed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class MessageRole(str, enum.Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"


class MemoryCategory(str, enum.Enum):
    PREFERENCE = "preference"
    CAPABILITY = "capability"
    RELATIONSHIP = "relationship"
    INSIGHT = "insight"


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

class Customer(Base):
    """Customer profile sourced from WeChat Enterprise."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wechat_user_id = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    company = Column(String(200), nullable=True)
    role = Column(String(100), nullable=True)
    trust_level = Column(SmallInteger, nullable=False, default=1)  # 1-5
    notes = Column(Text, nullable=True)
    total_orders = Column(Integer, nullable=False, default=0)
    total_spent = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversations = relationship("Conversation", back_populates="customer", lazy="dynamic")
    orders = relationship("Order", back_populates="customer", lazy="dynamic")
    memories = relationship("SemanticMemory", back_populates="customer", lazy="dynamic")

    __table_args__ = (
        Index("idx_customer_company", "company"),
        Index("idx_customer_trust", "trust_level"),
    )

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name={self.name}, company={self.company})>"


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------

class Conversation(Base):
    """Single message in a customer conversation."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)       # customer / agent / system
    content = Column(Text, nullable=False)
    message_type = Column(String(20), nullable=False, default=MessageType.TEXT.value)  # text / image / file
    wechat_msg_id = Column(String(128), nullable=True, unique=True, index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="conversations")

    __table_args__ = (
        Index("idx_conv_customer_created", "customer_id", "created_at"),
        Index("idx_conv_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, customer_id={self.customer_id}, role={self.role})>"


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------

class Order(Base):
    """Order tracking from quote through delivery."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True)  # ORD-xxx
    task_type = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)

    quoted_price = Column(Float, nullable=True)
    paid_amount = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default=OrderStatus.QUOTED.value, index=True)

    # Link to internal task system
    internal_task_id = Column(String(50), nullable=True, index=True)

    payment_confirmed_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="orders")

    __table_args__ = (
        Index("idx_order_customer_status", "customer_id", "status"),
        Index("idx_order_status_created", "status", "created_at"),
        Index("idx_order_task_type", "task_type"),
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_no={self.order_no}, status={self.status})>"


# ---------------------------------------------------------------------------
# Semantic Memory
# ---------------------------------------------------------------------------

class SemanticMemory(Base):
    """Key insights about customers, tagged and searchable."""
    __tablename__ = "semantic_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)  # nullable for global
    category = Column(String(30), nullable=False)   # preference / capability / relationship / insight
    content = Column(Text, nullable=False)
    importance = Column(SmallInteger, nullable=False, default=5)  # 1-10
    embedding = Column(Text, nullable=True)  # placeholder for vector column

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="memories")

    __table_args__ = (
        Index("idx_memory_customer_category", "customer_id", "category"),
        Index("idx_memory_category", "category"),
        Index("idx_memory_importance", "importance"),
    )

    def __repr__(self) -> str:
        return f"<SemanticMemory(id={self.id}, category={self.category}, importance={self.importance})>"

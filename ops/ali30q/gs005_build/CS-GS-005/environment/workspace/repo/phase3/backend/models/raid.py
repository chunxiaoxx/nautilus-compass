"""Raid consensus execution models."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text,
    ForeignKey, Boolean, Index,
)
from models.database import Base


class RaidExecution(Base):
    """Track a Raid consensus execution."""

    __tablename__ = "raid_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(36), unique=True, nullable=False, index=True)
    task_id = Column(String(50), nullable=False, index=True)
    raid_level = Column(Integer, nullable=False)
    status = Column(
        String(20), nullable=False, default="pending",
    )  # pending / executing / completed / failed
    num_agents = Column(Integer, default=1)
    rounds_completed = Column(Integer, default=0)
    final_output = Column(Text, nullable=True)
    consensus_score = Column(Float, nullable=True)  # 0.0-1.0
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_raid_exec_status_created", "status", "created_at"),
        Index("idx_raid_exec_task", "task_id"),
    )


class RaidVote(Base):
    """Individual agent vote/output in a Raid execution."""

    __tablename__ = "raid_votes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(
        String(36),
        ForeignKey("raid_executions.execution_id"),
        nullable=False,
        index=True,
    )
    agent_role = Column(
        String(20), nullable=False,
    )  # executor / reviewer / voter / expert
    round_number = Column(Integer, default=1)
    output = Column(Text, nullable=True)
    approved = Column(Boolean, nullable=True)
    quality_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_raid_vote_exec_round", "execution_id", "round_number"),
    )

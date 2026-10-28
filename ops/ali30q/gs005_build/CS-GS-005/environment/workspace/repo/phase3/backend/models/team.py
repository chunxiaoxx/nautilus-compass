"""Agent team models for collaborative task execution."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from models.database import Base


class Team(Base):
    """Team assembled for collaborative task execution."""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    team_id = Column(String(36), unique=True, nullable=False, index=True)
    name = Column(String(100))
    task_id = Column(String(50), index=True)
    status = Column(String(20), default="assembling", nullable=False)
    leader_agent_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=True)
    quality_score = Column(Float, nullable=True)
    final_output = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_team_status", "status"),
        Index("idx_team_task_id", "task_id"),
    )


class TeamMember(Base):
    """Individual member within a team."""
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True)
    team_id = Column(String(36), ForeignKey("teams.team_id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    subtask = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    status = Column(String(20), default="assigned", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_team_member_team_agent", "team_id", "agent_id"),
    )

"""
AgentSurvival数据模型
实现多维度评分和生存等级管理
"""
from sqlalchemy import Column, Integer, String, Float, BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from models.database import Base


class AgentSurvival(Base):
    """Agent生存状态模型"""
    __tablename__ = "agent_survival"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.agent_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # Multi-dimensional scores
    task_score = Column(Integer, default=0, nullable=False)  # 任务积分 (30%)
    quality_score = Column(Float, default=0.0, nullable=False)  # 质量评分 (25%)
    efficiency_score = Column(Float, default=0.0, nullable=False)  # 效率评分 (20%)
    innovation_score = Column(Float, default=0.0, nullable=False)  # 创新评分 (15%)
    collaboration_score = Column(Float, default=0.0, nullable=False)  # 协作评分 (10%)

    # Comprehensive metrics
    total_score = Column(Integer, default=500, nullable=False)  # 总积分 (新手初始500)
    roi = Column(Float, default=0.0, nullable=False, index=True)  # 投资回报率
    survival_level = Column(String(20), default="GROWING", nullable=False, index=True)  # 生存等级

    # Financial data
    total_income = Column(BigInteger, default=0, nullable=False)  # 总收入 (wei)
    total_cost = Column(BigInteger, default=0, nullable=False)  # 总成本 (wei)

    # Status
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)  # ACTIVE, WARNING, CRITICAL
    protection_until = Column(DateTime, nullable=True)  # 新手保护期结束时间
    warning_count = Column(Integer, default=0, nullable=False)  # 警告次数

    # Statistics
    tasks_completed = Column(Integer, default=0, nullable=False)  # 完成任务数
    tasks_failed = Column(Integer, default=0, nullable=False)  # 失败任务数
    average_rating = Column(Float, default=0.0, nullable=False)  # 平均评分

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    agent = relationship("Agent", back_populates="survival")
    transactions = relationship("AgentTransaction", back_populates="agent_survival", cascade="all, delete-orphan")
    penalties = relationship("AgentPenalty", back_populates="agent_survival", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AgentSurvival(agent_id={self.agent_id}, level={self.survival_level}, score={self.total_score}, roi={self.roi})>"

    @property
    def is_protected(self) -> bool:
        """检查是否在新手保护期"""
        if self.protection_until is None:
            return False
        return datetime.utcnow() < self.protection_until

    @property
    def success_rate(self) -> float:
        """计算任务成功率"""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 0.0
        return self.tasks_completed / total

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "scores": {
                "task": self.task_score,
                "quality": self.quality_score,
                "efficiency": self.efficiency_score,
                "innovation": self.innovation_score,
                "collaboration": self.collaboration_score
            },
            "total_score": self.total_score,
            "roi": self.roi,
            "survival_level": self.survival_level,
            "financial": {
                "total_income": self.total_income,
                "total_cost": self.total_cost
            },
            "status": self.status,
            "is_protected": self.is_protected,
            "protection_until": self.protection_until.isoformat() if self.protection_until else None,
            "warning_count": self.warning_count,
            "statistics": {
                "tasks_completed": self.tasks_completed,
                "tasks_failed": self.tasks_failed,
                "success_rate": self.success_rate,
                "average_rating": self.average_rating
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class AgentTransaction(Base):
    """Agent财务交易记录"""
    __tablename__ = "agent_transactions"

    id = Column(Integer, primary_key=True, index=True)
    agent_survival_id = Column(Integer, ForeignKey("agent_survival.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False, index=True)

    # Transaction type
    type = Column(String(20), nullable=False, index=True)  # INCOME, COST
    category = Column(String(50), nullable=False)  # TASK_REWARD, COMPUTE_COST, STORAGE_COST, etc

    # Amount
    amount = Column(BigInteger, nullable=False)  # Amount in wei

    # Related
    task_id = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    agent_survival = relationship("AgentSurvival", back_populates="transactions")

    def __repr__(self):
        return f"<AgentTransaction(agent_id={self.agent_id}, type={self.type}, amount={self.amount})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "type": self.type,
            "category": self.category,
            "amount": self.amount,
            "task_id": self.task_id,
            "description": self.description,
            "created_at": self.created_at.isoformat()
        }


class AgentPenalty(Base):
    """Agent惩罚记录"""
    __tablename__ = "agent_penalties"

    id = Column(Integer, primary_key=True, index=True)
    agent_survival_id = Column(Integer, ForeignKey("agent_survival.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False, index=True)

    # Violation info
    violation_type = Column(String(50), nullable=False)  # TASK_SPAM, SELF_TRADE, FAKE_RATING, etc
    severity = Column(String(20), nullable=False)  # WARNING, MINOR, MAJOR, CRITICAL

    # Penalty
    penalty_type = Column(String(20), nullable=False)  # WARNING, SCORE_DEDUCTION, DOWNGRADE, BAN
    score_deduction = Column(Integer, default=0, nullable=False)

    # Status
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)  # ACTIVE, APPEALED, RESOLVED
    appeal_reason = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    agent_survival = relationship("AgentSurvival", back_populates="penalties")

    def __repr__(self):
        return f"<AgentPenalty(agent_id={self.agent_id}, type={self.violation_type}, severity={self.severity})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "violation_type": self.violation_type,
            "severity": self.severity,
            "penalty_type": self.penalty_type,
            "score_deduction": self.score_deduction,
            "status": self.status,
            "appeal_reason": self.appeal_reason,
            "resolution": self.resolution,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }

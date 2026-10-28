"""FDE attention queue for human-assisted intervention in critical loops.

Human-first closed-loop mode relies on explicit attention records at each critical
edge: S1 dispatch, S2 QC, S3 delivery. This table stores unresolved "need
action" events and their chosen operator responses.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, Index
from models.database import Base


class FdeAttention(Base):
    """Attention/操作建议 for one FDE task in the closed loop."""

    __tablename__ = "fde_attention"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_uid = Column(String(120), nullable=True, index=True)
    stage = Column(String(12), nullable=False, index=True)  # s1 / s2 / s3
    code = Column(String(80), nullable=False, index=True)   # structured reason key
    severity = Column(String(12), nullable=False, default="warning")
    title = Column(String(220), nullable=False)
    detail = Column(Text, nullable=False, default="")

    # Suggested actions are surfaced as choice chips in the website front-end.
    suggested_actions = Column(JSON, nullable=False, default=lambda: ["retry", "ignore"])
    context = Column(JSON, nullable=True, default=dict)

    status = Column(String(20), nullable=False, default="pending", index=True)
    resolution = Column(String(80), nullable=True)
    resolution_note = Column(Text, nullable=True)
    resolved_by = Column(String(80), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_fde_attention_status_stage", "status", "stage", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_uid": self.task_uid,
            "stage": self.stage,
            "code": self.code,
            "severity": self.severity,
            "title": self.title,
            "detail": self.detail,
            "suggested_actions": self.suggested_actions,
            "context": self.context,
            "status": self.status,
            "resolution": self.resolution,
            "resolution_note": self.resolution_note,
            "resolved_by": self.resolved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

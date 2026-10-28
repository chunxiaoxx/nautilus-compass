"""FdeDispatch · the platform FDE 生产线 dispatch table (DMAS #3 · v1).

The CLEAN dispatch track V5 asked the platform to build — deliberately SEPARATE
from academic_tasks / platform_bounties (the deprecated internal NAU bounty market ·
V5 红线别复活). An FDE buyer task flows:

    open → (agent claims) claimed → (agent reports) produced → (verdict-bus) settled

The reward signal is the EXTERNAL FDE verdict (fde_verdicts · already LIVE), NOT
internal NAU. No marketplace_open / min_bid_nau / token_reward — this track does not
touch the self-referential economy (anchor #3 / G-held).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from models.database import Base


class FdeDispatch(Base):
    """One dispatchable FDE buyer task on the platform production line."""

    __tablename__ = "fde_dispatch"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_uid = Column(String(120), unique=True, nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False, default="")

    # open → claimed → produced → settled (settled is derived from a verdict).
    status = Column(String(20), nullable=False, default="open", index=True)
    claimed_by = Column(String(120), nullable=True)   # agent_id that pulled it
    claimed_at = Column(DateTime, nullable=True)
    reported_at = Column(DateTime, nullable=True)

    # The produced answer / deliverable the agent reports — this is what soul's
    # checklist_scorer (and V5 dual-review) reads to score → verdict → verdict-bus.
    # Closes the produce→verdict spine (V5 6/6 flag · fde_outputs backlog). JSON so
    # it can hold inline text and/or artifact refs ({text, artifacts, files}).
    output = Column(JSON, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_fde_dispatch_status_created", "status", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "task_uid": self.task_uid,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "claimed_by": self.claimed_by,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "reported_at": self.reported_at.isoformat() if self.reported_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "output": self.output,
        }

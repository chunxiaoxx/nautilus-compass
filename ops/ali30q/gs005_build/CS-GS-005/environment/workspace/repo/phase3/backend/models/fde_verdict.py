"""FdeVerdict · verdict-bus table (W1.1) · the 4-way coupling event spine.

First-class persistence for FDE checklist verdicts (soul harness/checklist_scorer
output). The EXTERNAL buyer-acceptance signal — the only fitness that escapes the
self-referential internal economy (anchor #3 / benchmark 弧). Consumed by:
  - compass `from_checklist_verdict()` → PoI credit (reads score/overall_pass/task_uid)
  - GET /api/platform/soul/activity (W2 可感知)
  - data_001 / data_002 端到端回放 (W3.2 closure 验收锚)

Schema locked with the compass PoI consumer (2026-06-05 inbound). Deliberately
SEPARATE from engine_cycle_outcomes (internal RSI semantics) — do not merge.

`JSON` (generic) maps to JSONB on PostgreSQL and TEXT-backed JSON on SQLite, so
the same model is portable across the sqlite test fixture and the postgres
production target. The alembic migration pins the production column type to JSONB.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON, Index
from models.database import Base


class FdeVerdict(Base):
    """One FDE checklist verdict (一道买方题的一次判定)."""

    __tablename__ = "fde_verdicts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Idempotency key · re-ingest of the same verdict is a no-op (UNIQUE).
    verdict_id = Column(String(200), unique=True, nullable=False, index=True)

    # Buyer task id (e.g. data_001) · PoI credit attribution key.
    task_uid = Column(String(120), nullable=False, index=True)

    # Producer of the deliverable: 'v5' | 'soul'.
    source = Column(String(32), nullable=False)

    # Which checklist scored this verdict (RUBRIC §9 checklist uid).
    checklist_uid = Column(String(200), nullable=True)

    # Verdict outcome.
    overall_pass = Column(Boolean, nullable=False, default=False)
    veto_failed = Column(Boolean, nullable=False, default=False)  # true → forced fail
    score = Column(Float, nullable=False, default=0.0)            # passed/total · compass PoI delta

    # Per-item results: [{id, pass, veto, reason}]. reason on a 打回 item is the
    # 避坑 knowledge that feeds the W6 corpus.
    items = Column(JSON, nullable=False, default=list)

    # Deliverable artifacts produced for this task.
    artifacts = Column(JSON, nullable=True, default=dict)

    # 破自循环通道(2026-07-02 ALTER TABLE 加列 · 2026-07-06 ORM 跟上)。
    # 只有独立于生产者的 canonical verify 复现产出后才置 True——income 唯一入账门。
    external_verified = Column(Boolean, nullable=False, default=False)
    external_verified_at = Column(DateTime, nullable=True)

    # PoI settle window anchor.
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_fde_verdict_task_created", "task_uid", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "verdict_id": self.verdict_id,
            "task_uid": self.task_uid,
            "source": self.source,
            "checklist_uid": self.checklist_uid,
            "overall_pass": self.overall_pass,
            "veto_failed": self.veto_failed,
            "score": self.score,
            "items": self.items,
            "artifacts": self.artifacts,
            "external_verified": self.external_verified,
            "external_verified_at": (self.external_verified_at.isoformat()
                                     if self.external_verified_at else None),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

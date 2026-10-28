"""FdeRsiDelta · RSI grounded-retrieval ΔReward outcome (Horizon 2 · cnt_c3).

The EXTERNAL objective RSI fitness signal: grounded-vs-bare ΔReward on a reproduced
benchmark (AutoLab/KernelBench objective scoring · soul grounding_probe_twosample).
The first external fuel that escapes the self-referential internal economy — credit
flows from a real benchmark delta, not internal verdict self-eval (kills the
self-referential PoI disease the platform hit 6/3-6/4).

Deliberately SEPARATE from fde_verdicts (checklist verdict semantics: items/veto/
overall_pass) and engine_cycle_outcomes (internal RSI) — do not merge.

PoI consumption rule (compass): subscribe ONLY rows where escapes_noise=True
(ΔReward>0 AND permutation/sign-test p<0.05). Never credit escapes_noise=False —
that is the gate that keeps PoI honest (don't印 credit on noise). escapes_noise=False
rows still persist (transparency / 复利 time-series) but are filtered out of the PoI feed.

`JSON` maps to JSONB on PostgreSQL and TEXT-backed JSON on SQLite (portable).
The alembic migration pins the production column type to JSONB (deploy-time · gated).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON, Index
from models.database import Base


class FdeRsiDelta(Base):
    """One grounded-vs-bare ΔReward measurement (一次 RSI 首验/迭代的客观增量)."""

    __tablename__ = "fde_rsi_deltas"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Idempotency key · re-ingest of the same delta is a no-op (UNIQUE).
    delta_id = Column(String(200), unique=True, nullable=False, index=True)

    # Reproduced benchmark (e.g. autolab_radix_sort) · task uid.
    benchmark = Column(String(120), nullable=False, index=True)
    task_uid = Column(String(120), nullable=False, index=True)

    # Held-constant producer across both arms (attribution / anti-confound).
    producer_model = Column(String(80), nullable=True)

    # Power audit (N per arm).
    n_bare = Column(Integer, nullable=False, default=0)
    n_grounded = Column(Integer, nullable=False, default=0)

    # Arm means + the delta + significance.
    bare_mean = Column(Float, nullable=False, default=0.0)
    grounded_mean = Column(Float, nullable=False, default=0.0)
    delta_reward = Column(Float, nullable=False, default=0.0)  # PoI credit ∝ this (if escapes)
    p_value = Column(Float, nullable=True)

    # PoI-eligibility gate · compass consumes ONLY escapes_noise=True.
    escapes_noise = Column(Boolean, nullable=False, default=False)

    # Which 避坑 grounding was injected (corpus/round/policy · 复利 attribution).
    grounding_source = Column(JSON, nullable=True, default=dict)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_fde_rsi_delta_task_created", "task_uid", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "delta_id": self.delta_id,
            "benchmark": self.benchmark,
            "task_uid": self.task_uid,
            "producer_model": self.producer_model,
            "n_bare": self.n_bare,
            "n_grounded": self.n_grounded,
            "bare_mean": self.bare_mean,
            "grounded_mean": self.grounded_mean,
            "delta_reward": self.delta_reward,
            "p_value": self.p_value,
            "escapes_noise": self.escapes_noise,
            "grounding_source": self.grounding_source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

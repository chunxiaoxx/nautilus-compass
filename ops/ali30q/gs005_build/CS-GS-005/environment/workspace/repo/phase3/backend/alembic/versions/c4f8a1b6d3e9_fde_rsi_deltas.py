"""cnt_c3 · fde_rsi_deltas table (ΔReward → PoI fuel substrate)

Revision ID: c4f8a1b6d3e9
Revises: b8e2c1d4f9a3
Create Date: 2026-06-09

Persists grounded-vs-bare ΔReward measurements (soul grounding_probe_twosample
on a reproduced AutoLab/KernelBench benchmark) as the platform's FIRST EXTERNAL
objective RSI fitness signal — credit flows from a real benchmark delta, not
internal verdict self-eval (kills the self-referential PoI disease of 6/3-6/4).

Deliberately SEPARATE from fde_verdicts (checklist verdict semantics) and
engine_cycle_outcomes (internal RSI) — do not merge.

PoI consumption gate (compass): credit ONLY rows where escapes_noise=TRUE.
escapes_noise=FALSE rows still persist (transparency / 复利 time-series) but are
filtered out of the PoI feed (GET ...?escapes_only=true). That gate is what keeps
PoI honest — never印 credit on noise.

`grounding_source` pinned to JSONB on production. Idempotent (CREATE TABLE /
INDEX IF NOT EXISTS) · safe to re-apply. Cloud apply is gated on SSH
(G-cloud / G-DDL) — local verify only in this increment.
"""
from alembic import op


revision = 'c4f8a1b6d3e9'
down_revision = 'b8e2c1d4f9a3'  # fde_dispatch (fde-family head)
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS fde_rsi_deltas (
            id             SERIAL PRIMARY KEY,
            delta_id       VARCHAR(200) NOT NULL UNIQUE,
            benchmark      VARCHAR(120) NOT NULL,
            task_uid       VARCHAR(120) NOT NULL,
            producer_model VARCHAR(80),
            n_bare         INTEGER NOT NULL DEFAULT 0,
            n_grounded     INTEGER NOT NULL DEFAULT 0,
            bare_mean      DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            grounded_mean  DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            delta_reward   DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            p_value        DOUBLE PRECISION,
            escapes_noise  BOOLEAN NOT NULL DEFAULT FALSE,
            grounding_source JSONB DEFAULT '{}'::jsonb,
            created_at     TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fde_rsi_delta_delta_id "
        "ON fde_rsi_deltas (delta_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fde_rsi_delta_benchmark "
        "ON fde_rsi_deltas (benchmark)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fde_rsi_delta_task_uid "
        "ON fde_rsi_deltas (task_uid)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fde_rsi_delta_created_at "
        "ON fde_rsi_deltas (created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fde_rsi_delta_task_created "
        "ON fde_rsi_deltas (task_uid, created_at)"
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS fde_rsi_deltas")

"""W1.1 verdict-bus · fde_verdicts table (4-way coupling event spine)

Revision ID: a7f3c1d2e4b5
Revises: f6d9e2b8a4c1
Create Date: 2026-06-05

Persists FDE checklist verdicts (soul harness/checklist_scorer output) as the
platform substrate's first-class event. The EXTERNAL buyer-acceptance signal —
the only fitness that escapes the self-referential internal economy. Read by:
  - compass `from_checklist_verdict()` → PoI credit (score/overall_pass/task_uid)
  - GET /api/platform/soul/activity (W2)
  - data_001 / data_002 端到端回放 (W3.2 closure 锚)

Schema locked with the compass PoI consumer (2026-06-05 inbound). Deliberately
SEPARATE from engine_cycle_outcomes (internal RSI semantics).

Idempotent (CREATE TABLE / INDEX IF NOT EXISTS) · safe to re-apply. Cloud apply
is gated on SSH (G-cloud / G-DDL) — local verify only in this increment.
"""
from alembic import op


revision = 'a7f3c1d2e4b5'
down_revision = 'f6d9e2b8a4c1'  # inc2 proposal_authors (governance/proposals family)
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS fde_verdicts (
            id            SERIAL PRIMARY KEY,
            verdict_id    VARCHAR(200) NOT NULL UNIQUE,
            task_uid      VARCHAR(120) NOT NULL,
            source        VARCHAR(32)  NOT NULL,
            checklist_uid VARCHAR(200),
            overall_pass  BOOLEAN      NOT NULL DEFAULT FALSE,
            veto_failed   BOOLEAN      NOT NULL DEFAULT FALSE,
            score         DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            items         JSONB        NOT NULL DEFAULT '[]'::jsonb,
            artifacts     JSONB        DEFAULT '{}'::jsonb,
            created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fde_verdict_verdict_id "
        "ON fde_verdicts (verdict_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fde_verdict_task_uid "
        "ON fde_verdicts (task_uid)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fde_verdict_task_created "
        "ON fde_verdicts (task_uid, created_at)"
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS fde_verdicts")

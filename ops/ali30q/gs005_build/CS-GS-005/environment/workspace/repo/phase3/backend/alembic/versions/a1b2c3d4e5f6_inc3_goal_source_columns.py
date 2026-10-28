"""inc3 goal source classification

Revision ID: a1b2c3d4e5f6
Revises: f6d9e2b8a4c1
Create Date: 2026-05-29

Inc 3 Slice A · classify soul daemon cycles by goal source for
backlog burn rate metric per design Section 2 + Section 5.

Adds:
  - engine_cycle_outcomes.goal_source TEXT NULL (existing rows pre-Inc3 = NULL)
  - agent_dispatch_log (new table · captures P2 agent-driven dispatches)

Idempotent (IF NOT EXISTS guards). Cloud may apply via
scripts/cloud_apply_inc3_slice_a.sh raw-SQL bypass per anchor #5
broken-alembic-chain pattern (matches Inc 2 Slice 4/5/6).
"""
from alembic import op


revision = 'a1b2c3d4e5f6'
down_revision = 'f6d9e2b8a4c1'  # Inc 2 Slice 6
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE engine_cycle_outcomes "
        "ADD COLUMN IF NOT EXISTS goal_source TEXT NULL"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_dispatch_log (
            id              BIGSERIAL PRIMARY KEY,
            agent_id        INTEGER REFERENCES agents(id),
            task_spec_hash  VARCHAR(64) NOT NULL,
            task_type       VARCHAR(32) NOT NULL DEFAULT 'code',
            cycle_id        TEXT REFERENCES engine_cycle_outcomes(cycle_id),
            ship_outcome    VARCHAR(32),
            created_at      TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_dispatch_log_agent_id "
        "ON agent_dispatch_log (agent_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_dispatch_log_cycle_id "
        "ON agent_dispatch_log (cycle_id)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_agent_dispatch_log_cycle_id")
    op.execute("DROP INDEX IF EXISTS idx_agent_dispatch_log_agent_id")
    op.execute("DROP TABLE IF EXISTS agent_dispatch_log")
    op.execute("ALTER TABLE engine_cycle_outcomes DROP COLUMN IF EXISTS goal_source")

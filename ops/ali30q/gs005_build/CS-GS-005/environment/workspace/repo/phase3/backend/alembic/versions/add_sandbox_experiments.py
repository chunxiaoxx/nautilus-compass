"""add sandbox experiments table

Revision ID: a1b2c3d4e5f6
Revises: f6a1b2c3d4e5
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f6a1b2c3d4e5'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS sandbox_experiments (
            id VARCHAR(32) PRIMARY KEY,
            proposal_id VARCHAR(64) NOT NULL REFERENCES platform_improvement_proposals(id),
            proposed_change JSONB NOT NULL DEFAULT '{}',
            observation_hours INTEGER NOT NULL DEFAULT 24,
            sandbox_traffic_pct INTEGER NOT NULL DEFAULT 10,
            ends_at TIMESTAMPTZ,
            finalized_at TIMESTAMPTZ,
            status VARCHAR(20) NOT NULL DEFAULT 'running',
            baseline_metrics JSONB NOT NULL DEFAULT '{}',
            sandbox_metrics JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_sandbox_proposal ON sandbox_experiments(proposal_id);
        CREATE INDEX IF NOT EXISTS idx_sandbox_status_ends ON sandbox_experiments(status, ends_at);

        -- 在 academic_tasks 中添加实验标记列（允许 NULL）
        ALTER TABLE academic_tasks
            ADD COLUMN IF NOT EXISTS experiment_id VARCHAR(32) DEFAULT NULL,
            ADD COLUMN IF NOT EXISTS experiment_group VARCHAR(10) DEFAULT NULL;
        CREATE INDEX IF NOT EXISTS idx_tasks_experiment ON academic_tasks(experiment_id, experiment_group)
            WHERE experiment_id IS NOT NULL;
    """)


def downgrade():
    op.execute("""
        ALTER TABLE academic_tasks DROP COLUMN IF EXISTS experiment_id;
        ALTER TABLE academic_tasks DROP COLUMN IF EXISTS experiment_group;
        DROP TABLE IF EXISTS sandbox_experiments;
    """)

"""Add execution_checkpoints table for durable execution.

Stores intermediate state so interrupted Raid / proposal workflows
can resume from the last completed step (LangGraph-style persistence).

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a1b2'
down_revision = 'b2c3d4e5f6a1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS execution_checkpoints (
            id SERIAL PRIMARY KEY,
            execution_id VARCHAR(128) NOT NULL UNIQUE,
            execution_type VARCHAR(32) NOT NULL DEFAULT 'raid',
            current_step VARCHAR(64) NOT NULL,
            state JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_checkpoints_type
            ON execution_checkpoints(execution_type);
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS execution_checkpoints;")

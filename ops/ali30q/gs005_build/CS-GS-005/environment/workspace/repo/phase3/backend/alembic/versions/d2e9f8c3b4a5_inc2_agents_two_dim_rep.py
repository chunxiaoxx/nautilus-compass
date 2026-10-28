"""inc2 agents two-dimensional reputation

Revision ID: d2e9f8c3b4a5
Revises: c1b8d4f7e2a3
Create Date: 2026-05-28

Inc 2 Slice 1: split single reputation_score into two-dim vector per
design doc D4 (prediction-market accuracy across propose vs vote roles).
Existing reputation_score column retained for Inc 1.5 backward compat;
sync trigger deferred to Slice 3 (when first writes happen).

Idempotent. Default 50.0 (NEW tier · per Inc 1.5 weights).
"""
from alembic import op


revision = 'd2e9f8c3b4a5'
down_revision = 'c1b8d4f7e2a3'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE agents "
        "ADD COLUMN IF NOT EXISTS rep_proposing REAL NOT NULL DEFAULT 50.0"
    )
    op.execute(
        "ALTER TABLE agents "
        "ADD COLUMN IF NOT EXISTS rep_voting REAL NOT NULL DEFAULT 50.0"
    )


def downgrade():
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS rep_voting")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS rep_proposing")

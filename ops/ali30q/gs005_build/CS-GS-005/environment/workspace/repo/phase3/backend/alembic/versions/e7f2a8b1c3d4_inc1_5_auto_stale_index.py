"""inc1_5 auto stale index

Revision ID: e7f2a8b1c3d4
Revises: d4a2e1b6f8c9
Create Date: 2026-05-28

Inc 1.5: Partial index on (status, created_at) for status='pending' to speed
up auto_approve_stale_proposals query (which scans pending code-type rows
older than 24h). Without this index · query does seq scan on
platform_improvement_proposals each cron tick (every 6h · negligible at small
scale · but pre-emptively scaled).

Safe to apply multiple times (uses IF NOT EXISTS · idempotent).
Cloud may apply via raw SQL bypass per handoff #004 line 96-97 alembic
multi-head mess.
"""
from alembic import op


# revision identifiers · used by Alembic
revision = 'e7f2a8b1c3d4'
down_revision = 'd4a2e1b6f8c9'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_proposals_pending_stale "
        "ON platform_improvement_proposals (status, created_at) "
        "WHERE status='pending'"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_proposals_pending_stale")

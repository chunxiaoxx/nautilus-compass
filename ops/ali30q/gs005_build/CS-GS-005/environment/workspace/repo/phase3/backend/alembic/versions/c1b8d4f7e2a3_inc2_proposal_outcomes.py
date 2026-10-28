"""inc2 proposal_outcomes table

Revision ID: c1b8d4f7e2a3
Revises: a3e9c5d1b7f2
Create Date: 2026-05-28

Inc 2 Slice 1: settlement outcomes table. Each row records a single
governance code-proposal's pre-merge snapshot, post-merge snapshot,
composite_delta, and grading metadata. The non-null composite_delta on
this row is the Inc 2 binding-DONE artifact (per design doc Section 7).

Safe to apply multiple times (IF NOT EXISTS guards).
Cloud may apply via raw SQL bypass per handoff #004 line 96-97.
"""
from alembic import op


revision = 'c1b8d4f7e2a3'
down_revision = 'a3e9c5d1b7f2'  # tip of Inc 1.5 migrations
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS proposal_outcomes (
            proposal_id      VARCHAR PRIMARY KEY
                             REFERENCES platform_improvement_proposals(id),
            pre_snapshot     JSONB NOT NULL,
            post_snapshot    JSONB,
            composite_delta  REAL,
            no_revert        BOOLEAN,
            graded_at        TIMESTAMPTZ,
            graded_by        VARCHAR DEFAULT 'soul-settlement-review'
        )
        """
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS proposal_outcomes")

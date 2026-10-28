"""inc2 proposal_blessings table

Revision ID: e5c8b9a3d1f7
Revises: d2e9f8c3b4a5
Create Date: 2026-05-29

Inc 2 Slice 5: blessing mechanism · TRUSTED agents stake their rep_voting
to amplify UNTRUSTED proposals (mentor mechanic per design Section 4).
Each row records one blesser endorsing one proposal at stake_amount equal
to blesser.rep_voting * 0.1. settled flips at Slice 3 graded settle.

Safe to apply multiple times (IF NOT EXISTS guard).
Cloud may apply via scripts/cloud_apply_inc2_slice5.sh per anchor #5
broken-alembic-chain bypass pattern (matches Slice 4 ship).
"""
from alembic import op


revision = 'e5c8b9a3d1f7'
down_revision = 'd2e9f8c3b4a5'  # Inc 2 Slice 1 two-dim rep migration
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS proposal_blessings (
            id              BIGSERIAL PRIMARY KEY,
            proposal_id     VARCHAR REFERENCES platform_improvement_proposals(id),
            blesser_id      INTEGER REFERENCES agents(id),
            stake_amount    REAL NOT NULL,
            settled         BOOLEAN DEFAULT FALSE,
            settled_outcome VARCHAR,
            created_at      TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_proposal_blessings_proposal_unsettled "
        "ON proposal_blessings (proposal_id) WHERE settled = FALSE"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_proposal_blessings_proposal_unsettled")
    op.execute("DROP TABLE IF EXISTS proposal_blessings")

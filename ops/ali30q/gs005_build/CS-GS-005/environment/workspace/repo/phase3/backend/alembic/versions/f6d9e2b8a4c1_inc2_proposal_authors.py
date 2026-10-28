"""inc2 proposal_authors table + backfill

Revision ID: f6d9e2b8a4c1
Revises: e5c8b9a3d1f7
Create Date: 2026-05-29

Inc 2 Slice 6: collaborative authorship · multi-agent co-proposals with
contribution weights for proportional NAU + rep splits at settlement.

Single source of truth: proposal_authors table (composite PK). Backfill
existing rows from platform_improvement_proposals.agent_id with
contribution_weight=1.0 (ON CONFLICT DO NOTHING · idempotent re-runs).

Sum-of-weights = 1.0 invariant enforced at API layer (POST endpoint).
The CHECK constraint here only bounds individual rows (0 < w <= 1).

Safe to apply multiple times. Cloud may use scripts/cloud_apply_inc2_slice6.sh
for raw-SQL bypass.
"""
from alembic import op


revision = 'f6d9e2b8a4c1'
down_revision = 'e5c8b9a3d1f7'  # Inc 2 Slice 5 proposal_blessings
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS proposal_authors (
            proposal_id          VARCHAR REFERENCES platform_improvement_proposals(id),
            agent_id             INTEGER REFERENCES agents(id),
            contribution_weight  REAL NOT NULL
                                 CHECK (contribution_weight > 0
                                        AND contribution_weight <= 1),
            PRIMARY KEY (proposal_id, agent_id)
        )
        """
    )
    # Backfill: every existing proposal becomes a single-author row weight=1.0
    op.execute(
        """
        INSERT INTO proposal_authors (proposal_id, agent_id, contribution_weight)
        SELECT id, agent_id, 1.0 FROM platform_improvement_proposals
        WHERE agent_id IS NOT NULL
        ON CONFLICT (proposal_id, agent_id) DO NOTHING
        """
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS proposal_authors")

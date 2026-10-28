"""inc1_5 vote reason column

Revision ID: a3e9c5d1b7f2
Revises: e7f2a8b1c3d4
Create Date: 2026-05-28

Inc 1.5 P1 (per agent-dialog ACK 5/28 末2): adds optional reason column to
platform_proposal_votes for KEYSTONE anti-RH audit trail. Vote endpoint will
persist reason when provided (NULL when omitted · backward compat). LLM
agents log reasoning for post-merge reward-hacking analysis (Inc 2 hook).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers · used by Alembic
revision = 'a3e9c5d1b7f2'
down_revision = 'e7f2a8b1c3d4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'platform_proposal_votes',
        sa.Column('reason', sa.Text(), nullable=True)
    )


def downgrade():
    op.drop_column('platform_proposal_votes', 'reason')

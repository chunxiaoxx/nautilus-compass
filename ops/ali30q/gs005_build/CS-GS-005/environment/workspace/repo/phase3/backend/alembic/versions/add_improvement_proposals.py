"""add platform_improvement_proposals and platform_proposal_votes tables

Revision ID: f6a1b2c3d4e5
Revises: e5f6a1b2c3d4
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'f6a1b2c3d4e5'
down_revision = 'e5f6a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'platform_improvement_proposals',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            'task_id',
            sa.Integer(),
            sa.ForeignKey('academic_tasks.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column(
            'agent_id',
            sa.Integer(),
            sa.ForeignKey('agents.agent_id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('root_cause', sa.Text(), nullable=False),
        sa.Column(
            'proposed_change',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column('expected_impact', sa.Text(), nullable=True),
        sa.Column('rollback_plan', sa.Text(), nullable=True),
        sa.Column(
            'status',
            sa.String(20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column('vote_score', sa.Float(), server_default=sa.text('0.0'), nullable=False),
        sa.Column('vote_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
    )
    op.create_index(
        'idx_proposals_task_id',
        'platform_improvement_proposals',
        ['task_id'],
    )
    op.create_index(
        'idx_proposals_status',
        'platform_improvement_proposals',
        ['status'],
    )

    op.create_table(
        'platform_proposal_votes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            'proposal_id',
            sa.Integer(),
            sa.ForeignKey('platform_improvement_proposals.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'agent_id',
            sa.Integer(),
            sa.ForeignKey('agents.agent_id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('vote', sa.Integer(), nullable=False),    # 1 = 支持, -1 = 反对
        sa.Column('weight', sa.Float(), nullable=False),    # 投票时的声誉分
        sa.Column(
            'created_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.UniqueConstraint('proposal_id', 'agent_id', name='uq_proposal_agent_vote'),
    )
    op.create_index(
        'idx_votes_proposal_id',
        'platform_proposal_votes',
        ['proposal_id'],
    )


def downgrade():
    op.drop_index('idx_votes_proposal_id', table_name='platform_proposal_votes')
    op.drop_table('platform_proposal_votes')

    op.drop_index('idx_proposals_status', table_name='platform_improvement_proposals')
    op.drop_index('idx_proposals_task_id', table_name='platform_improvement_proposals')
    op.drop_table('platform_improvement_proposals')

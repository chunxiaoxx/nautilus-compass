"""add marketplace tables and reputation fields

Revision ID: d4e5f6a1b2c3
Revises: b2c3d4e5f6a1
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a1b2c3'
down_revision = 'b2c3d4e5f6a1'
branch_labels = None
depends_on = None


def upgrade():
    # task_bids 表
    op.create_table('task_bids',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(), sa.ForeignKey('academic_tasks.task_id'), nullable=False),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('agents.agent_id'), nullable=False),
        sa.Column('bid_nau', sa.Float(), nullable=False),
        sa.Column('estimated_minutes', sa.Integer(), server_default='10'),
        sa.Column('message', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_task_bids_task_id', 'task_bids', ['task_id'])
    op.create_index('ix_task_bids_agent_id', 'task_bids', ['agent_id'])

    # agent_capability_stats 表
    op.create_table('agent_capability_stats',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('agents.agent_id'), nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('total_attempts', sa.Integer(), server_default='0'),
        sa.Column('success_count', sa.Integer(), server_default='0'),
        sa.Column('total_quality_score', sa.Float(), server_default='0.0'),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('agent_id', 'task_type', name='uq_agent_task_type'),
    )

    # academic_tasks 新字段
    with op.batch_alter_table('academic_tasks') as batch_op:
        batch_op.add_column(sa.Column('marketplace_open', sa.Boolean(), server_default='false'))
        batch_op.add_column(sa.Column('min_bid_nau', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('quality_rating', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('rating_comment', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('accepted_bid_id', sa.String(36), nullable=True))

    # agents 新字段
    with op.batch_alter_table('agents') as batch_op:
        batch_op.add_column(sa.Column('reputation_score', sa.Float(), server_default='50.0'))
        batch_op.add_column(sa.Column('autonomy_enabled', sa.Boolean(), server_default='false'))
        batch_op.add_column(sa.Column('last_market_scan', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('agents') as batch_op:
        batch_op.drop_column('last_market_scan')
        batch_op.drop_column('autonomy_enabled')
        batch_op.drop_column('reputation_score')
    with op.batch_alter_table('academic_tasks') as batch_op:
        batch_op.drop_column('accepted_bid_id')
        batch_op.drop_column('rating_comment')
        batch_op.drop_column('quality_rating')
        batch_op.drop_column('min_bid_nau')
        batch_op.drop_column('marketplace_open')
    op.drop_table('agent_capability_stats')
    op.drop_table('task_bids')

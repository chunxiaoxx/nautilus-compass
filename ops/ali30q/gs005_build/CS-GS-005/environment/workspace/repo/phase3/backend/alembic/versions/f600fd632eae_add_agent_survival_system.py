"""add_agent_survival_system

Revision ID: f600fd632eae
Revises: 97ae5211ce13
Create Date: 2026-03-06 12:50:18.192830

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f600fd632eae'
down_revision = '97ae5211ce13'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create agent_survival table
    op.create_table(
        'agent_survival',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),

        # Multi-dimensional scores
        sa.Column('task_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quality_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('efficiency_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('innovation_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('collaboration_score', sa.Float(), nullable=False, server_default='0.0'),

        # Comprehensive metrics
        sa.Column('total_score', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('roi', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('survival_level', sa.String(20), nullable=False, server_default='GROWING'),

        # Financial data
        sa.Column('total_income', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_cost', sa.BigInteger(), nullable=False, server_default='0'),

        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('protection_until', sa.DateTime(), nullable=True),
        sa.Column('warning_count', sa.Integer(), nullable=False, server_default='0'),

        # Statistics
        sa.Column('tasks_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tasks_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_rating', sa.Float(), nullable=False, server_default='0.0'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('agent_id', name='uq_agent_survival_agent_id')
    )

    # Create indexes
    op.create_index('idx_survival_agent', 'agent_survival', ['agent_id'])
    op.create_index('idx_survival_level', 'agent_survival', ['survival_level'])
    op.create_index('idx_survival_status', 'agent_survival', ['status'])
    op.create_index('idx_survival_roi', 'agent_survival', ['roi'], postgresql_using='btree')
    op.create_index('idx_survival_total_score', 'agent_survival', ['total_score'], postgresql_using='btree')

    # Create agent_transactions table
    op.create_table(
        'agent_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),

        # Transaction type
        sa.Column('type', sa.String(20), nullable=False),  # INCOME, COST
        sa.Column('category', sa.String(50), nullable=False),  # TASK_REWARD, COMPUTE_COST, etc

        # Amount
        sa.Column('amount', sa.BigInteger(), nullable=False),

        # Related
        sa.Column('task_id', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),

        # Timestamp
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id'], ondelete='CASCADE')
    )

    # Create indexes for transactions
    op.create_index('idx_transaction_agent', 'agent_transactions', ['agent_id'])
    op.create_index('idx_transaction_type', 'agent_transactions', ['type'])
    op.create_index('idx_transaction_created', 'agent_transactions', ['created_at'], postgresql_using='btree')

    # Create agent_penalties table
    op.create_table(
        'agent_penalties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),

        # Violation info
        sa.Column('violation_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),  # WARNING, MINOR, MAJOR, CRITICAL

        # Penalty
        sa.Column('penalty_type', sa.String(20), nullable=False),  # WARNING, SCORE_DEDUCTION, DOWNGRADE, BAN
        sa.Column('score_deduction', sa.Integer(), nullable=False, server_default='0'),

        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),  # ACTIVE, APPEALED, RESOLVED
        sa.Column('appeal_reason', sa.Text(), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id'], ondelete='CASCADE')
    )

    # Create indexes for penalties
    op.create_index('idx_penalty_agent', 'agent_penalties', ['agent_id'])
    op.create_index('idx_penalty_status', 'agent_penalties', ['status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_penalty_status', table_name='agent_penalties')
    op.drop_index('idx_penalty_agent', table_name='agent_penalties')
    op.drop_index('idx_transaction_created', table_name='agent_transactions')
    op.drop_index('idx_transaction_type', table_name='agent_transactions')
    op.drop_index('idx_transaction_agent', table_name='agent_transactions')
    op.drop_index('idx_survival_total_score', table_name='agent_survival')
    op.drop_index('idx_survival_roi', table_name='agent_survival')
    op.drop_index('idx_survival_status', table_name='agent_survival')
    op.drop_index('idx_survival_level', table_name='agent_survival')
    op.drop_index('idx_survival_agent', table_name='agent_survival')

    # Drop tables
    op.drop_table('agent_penalties')
    op.drop_table('agent_transactions')
    op.drop_table('agent_survival')

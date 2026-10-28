"""Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=66), nullable=False),
        sa.Column('publisher', sa.String(length=42), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('input_data', sa.Text(), nullable=True),
        sa.Column('expected_output', sa.Text(), nullable=True),
        sa.Column('reward', sa.BigInteger(), nullable=False),
        sa.Column('task_type', sa.Enum('CODE', 'DATA', 'COMPUTE', 'RESEARCH', 'DESIGN', 'WRITING', 'OTHER', name='tasktype'), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'ACCEPTED', 'SUBMITTED', 'VERIFIED', 'COMPLETED', 'FAILED', 'DISPUTED', name='taskstatus'), nullable=False),
        sa.Column('agent', sa.String(length=42), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('timeout', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('dispute_reason', sa.Text(), nullable=True),
        sa.Column('blockchain_tx_hash', sa.String(length=66), nullable=True),
        sa.Column('blockchain_accept_tx', sa.String(length=66), nullable=True),
        sa.Column('blockchain_submit_tx', sa.String(length=66), nullable=True),
        sa.Column('blockchain_complete_tx', sa.String(length=66), nullable=True),
        sa.Column('blockchain_status', sa.String(length=20), nullable=True),
        sa.Column('gas_used', sa.BigInteger(), nullable=True),
        sa.Column('gas_cost', sa.BigInteger(), nullable=True),
        sa.Column('gas_split', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for tasks table
    op.create_index('ix_tasks_task_id', 'tasks', ['task_id'], unique=True)
    op.create_index('ix_tasks_publisher', 'tasks', ['publisher'])
    op.create_index('ix_tasks_task_type', 'tasks', ['task_type'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_agent', 'tasks', ['agent'])
    op.create_index('ix_tasks_created_at', 'tasks', ['created_at'])
    op.create_index('ix_tasks_accepted_at', 'tasks', ['accepted_at'])
    op.create_index('ix_tasks_completed_at', 'tasks', ['completed_at'])
    op.create_index('ix_tasks_blockchain_tx_hash', 'tasks', ['blockchain_tx_hash'])

    # Create composite indexes for common queries
    op.create_index('ix_tasks_status_created_at', 'tasks', ['status', 'created_at'])
    op.create_index('ix_tasks_agent_status', 'tasks', ['agent', 'status'])
    op.create_index('ix_tasks_publisher_status', 'tasks', ['publisher', 'status'])

    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('owner', sa.String(length=42), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reputation', sa.Integer(), nullable=False),
        sa.Column('specialties', sa.Text(), nullable=True),
        sa.Column('current_tasks', sa.Integer(), nullable=True),
        sa.Column('completed_tasks', sa.Integer(), nullable=True),
        sa.Column('failed_tasks', sa.Integer(), nullable=True),
        sa.Column('total_earnings', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('blockchain_registered', sa.Boolean(), nullable=True),
        sa.Column('blockchain_tx_hash', sa.String(length=66), nullable=True),
        sa.Column('blockchain_address', sa.String(length=42), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for agents table
    op.create_index('ix_agents_agent_id', 'agents', ['agent_id'], unique=True)
    op.create_index('ix_agents_owner', 'agents', ['owner'])
    op.create_index('ix_agents_reputation', 'agents', ['reputation'])

    # Create rewards table
    op.create_table(
        'rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=66), nullable=False),
        sa.Column('agent', sa.String(length=42), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('distributed_at', sa.DateTime(), nullable=True),
        sa.Column('withdrawn_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for rewards table
    op.create_index('ix_rewards_task_id', 'rewards', ['task_id'])
    op.create_index('ix_rewards_agent', 'rewards', ['agent'])
    op.create_index('ix_rewards_status', 'rewards', ['status'])
    op.create_index('ix_rewards_distributed_at', 'rewards', ['distributed_at'])

    # Create composite index for common query
    op.create_index('ix_rewards_agent_status', 'rewards', ['agent', 'status'])

    # Create verification_logs table
    op.create_table(
        'verification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=66), nullable=False),
        sa.Column('verification_method', sa.String(length=50), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False),
        sa.Column('logs', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.task_id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index for verification_logs table
    op.create_index('ix_verification_logs_task_id', 'verification_logs', ['task_id'])

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for users table
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_wallet_address', 'users', ['wallet_address'], unique=True)

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for api_keys table
    op.create_index('ix_api_keys_key', 'api_keys', ['key'], unique=True)
    op.create_index('ix_api_keys_agent_id', 'api_keys', ['agent_id'])
    op.create_index('ix_api_keys_is_active', 'api_keys', ['is_active'])

    # Create composite index for authentication queries
    op.create_index('ix_api_keys_key_is_active', 'api_keys', ['key', 'is_active'])


def downgrade() -> None:
    """Drop all tables."""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('api_keys')
    op.drop_table('users')
    op.drop_table('verification_logs')
    op.drop_table('rewards')
    op.drop_table('agents')
    op.drop_table('tasks')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS tasktype')

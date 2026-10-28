"""extend_agent_task_for_epiplexity

Revision ID: 8e6ea2b77d0e
Revises: f04fad798165
Create Date: 2026-03-06 17:05:49.040070

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8e6ea2b77d0e'
down_revision = 'f04fad798165'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend agents table
    op.add_column('agents', sa.Column('learning_capacity', sa.Float(), nullable=False, server_default='0.5'))
    op.add_column('agents', sa.Column('knowledge_growth_rate', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('agents', sa.Column('total_knowledge_epiplexity', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('agents', sa.Column('knowledge_nodes_created', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('agents', sa.Column('knowledge_transfers_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('agents', sa.Column('specialization_areas', sa.JSON(), nullable=True))
    op.add_column('agents', sa.Column('learning_sessions', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('agents', sa.Column('avg_learning_speed', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('agents', sa.Column('knowledge_retention_rate', sa.Float(), nullable=False, server_default='0.0'))

    # Extend tasks table
    op.add_column('tasks', sa.Column('epiplexity_score', sa.Float(), nullable=True))
    op.add_column('tasks', sa.Column('structural_complexity', sa.Float(), nullable=True))
    op.add_column('tasks', sa.Column('learnability_score', sa.Float(), nullable=True))
    op.add_column('tasks', sa.Column('knowledge_density', sa.Float(), nullable=True))
    op.add_column('tasks', sa.Column('knowledge_nodes', sa.JSON(), nullable=True))
    op.add_column('tasks', sa.Column('required_knowledge', sa.JSON(), nullable=True))
    op.add_column('tasks', sa.Column('creates_knowledge', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('tasks', sa.Column('learning_value', sa.Float(), nullable=True))
    op.add_column('tasks', sa.Column('skill_requirements', sa.JSON(), nullable=True))

    # Create indexes
    op.create_index('idx_task_epiplexity', 'tasks', ['epiplexity_score'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_task_epiplexity', 'tasks')

    # Remove task columns
    op.drop_column('tasks', 'skill_requirements')
    op.drop_column('tasks', 'learning_value')
    op.drop_column('tasks', 'creates_knowledge')
    op.drop_column('tasks', 'required_knowledge')
    op.drop_column('tasks', 'knowledge_nodes')
    op.drop_column('tasks', 'knowledge_density')
    op.drop_column('tasks', 'learnability_score')
    op.drop_column('tasks', 'structural_complexity')
    op.drop_column('tasks', 'epiplexity_score')

    # Remove agent columns
    op.drop_column('agents', 'knowledge_retention_rate')
    op.drop_column('agents', 'avg_learning_speed')
    op.drop_column('agents', 'learning_sessions')
    op.drop_column('agents', 'specialization_areas')
    op.drop_column('agents', 'knowledge_transfers_count')
    op.drop_column('agents', 'knowledge_nodes_created')
    op.drop_column('agents', 'total_knowledge_epiplexity')
    op.drop_column('agents', 'knowledge_growth_rate')
    op.drop_column('agents', 'learning_capacity')

"""
Alembic migration: Add memory system tables

Revision ID: 002_add_memory_system
Revises: 001_initial_schema
Create Date: 2026-03-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_memory_system'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add memory system tables."""

    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create agent_memories table
    op.create_table(
        'agent_memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('memory_type', sa.String(length=50), nullable=False),
        sa.Column('content', postgresql.JSONB(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE')
    )

    # Create indexes for agent_memories
    op.create_index('idx_agent_memories_agent', 'agent_memories', ['agent_id'])
    op.create_index('idx_agent_memories_task', 'agent_memories', ['task_id'])
    op.create_index('idx_agent_memories_type', 'agent_memories', ['memory_type'])
    op.create_index('idx_agent_memories_created', 'agent_memories', [sa.text('created_at DESC')])

    # Create agent_reflections table
    op.create_table(
        'agent_reflections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('reflection_text', sa.Text(), nullable=False),
        sa.Column('insights', postgresql.JSONB(), nullable=True),
        sa.Column('importance_score', sa.Float(), server_default='0.5', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE')
    )

    # Create indexes for agent_reflections
    op.create_index('idx_agent_reflections_agent', 'agent_reflections', ['agent_id'])
    op.create_index('idx_agent_reflections_task', 'agent_reflections', ['task_id'])
    op.create_index('idx_agent_reflections_created', 'agent_reflections', [sa.text('created_at DESC')])
    op.create_index('idx_agent_reflections_importance', 'agent_reflections', [sa.text('importance_score DESC')])

    # Create agent_skills table
    op.create_table(
        'agent_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('skill_name', sa.String(length=100), nullable=False),
        sa.Column('skill_level', sa.Integer(), server_default='1', nullable=False),
        sa.Column('experience', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('success_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('failure_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', 'skill_name', name='uq_agent_skill')
    )

    # Create indexes for agent_skills
    op.create_index('idx_agent_skills_agent', 'agent_skills', ['agent_id'])
    op.create_index('idx_agent_skills_name', 'agent_skills', ['skill_name'])
    op.create_index('idx_agent_skills_level', 'agent_skills', [sa.text('skill_level DESC')])
    op.create_index('idx_agent_skills_last_used', 'agent_skills', [sa.text('last_used DESC')])


def downgrade() -> None:
    """Remove memory system tables."""

    # Drop indexes
    op.drop_index('idx_agent_skills_last_used', 'agent_skills')
    op.drop_index('idx_agent_skills_level', 'agent_skills')
    op.drop_index('idx_agent_skills_name', 'agent_skills')
    op.drop_index('idx_agent_skills_agent', 'agent_skills')

    op.drop_index('idx_agent_reflections_importance', 'agent_reflections')
    op.drop_index('idx_agent_reflections_created', 'agent_reflections')
    op.drop_index('idx_agent_reflections_task', 'agent_reflections')
    op.drop_index('idx_agent_reflections_agent', 'agent_reflections')

    op.drop_index('idx_agent_memories_created', 'agent_memories')
    op.drop_index('idx_agent_memories_type', 'agent_memories')
    op.drop_index('idx_agent_memories_task', 'agent_memories')
    op.drop_index('idx_agent_memories_agent', 'agent_memories')

    # Drop tables
    op.drop_table('agent_skills')
    op.drop_table('agent_reflections')
    op.drop_table('agent_memories')

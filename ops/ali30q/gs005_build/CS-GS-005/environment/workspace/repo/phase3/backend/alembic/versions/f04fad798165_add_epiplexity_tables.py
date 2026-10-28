"""add_epiplexity_tables

Revision ID: f04fad798165
Revises: f600fd632eae
Create Date: 2026-03-06 17:04:35.041304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f04fad798165'
down_revision = 'f600fd632eae'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create epiplexity_measures table
    op.create_table(
        'epiplexity_measures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(20), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('structural_complexity', sa.Float(), nullable=False),
        sa.Column('learnable_content', sa.Float(), nullable=False),
        sa.Column('transferability', sa.Float(), nullable=False),
        sa.Column('epiplexity_score', sa.Float(), nullable=False),
        sa.Column('analysis_details', sa.JSON(), nullable=True),
        sa.Column('calculated_by', sa.String(50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_epiplexity_entity', 'epiplexity_measures', ['entity_type', 'entity_id'])
    op.create_index('idx_epiplexity_score', 'epiplexity_measures', ['epiplexity_score'])

    # Create knowledge_nodes table
    op.create_table(
        'knowledge_nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('epiplexity', sa.Float(), nullable=False),
        sa.Column('learnability', sa.Float(), nullable=False),
        sa.Column('transferability', sa.Float(), nullable=False),
        sa.Column('complexity_level', sa.String(20), nullable=False),
        sa.Column('source_task_id', sa.Integer(), nullable=True),
        sa.Column('created_by_agent_id', sa.Integer(), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('transfer_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('parent_nodes', sa.JSON(), nullable=True),
        sa.Column('child_nodes', sa.JSON(), nullable=True),
        sa.Column('related_nodes', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_agent_id'], ['agents.agent_id'], ondelete='CASCADE')
    )
    op.create_index('idx_knowledge_hash', 'knowledge_nodes', ['content_hash'], unique=True)
    op.create_index('idx_knowledge_epiplexity', 'knowledge_nodes', ['epiplexity'])
    op.create_index('idx_knowledge_creator', 'knowledge_nodes', ['created_by_agent_id'])
    op.create_index('idx_knowledge_type', 'knowledge_nodes', ['content_type'])

    # Create knowledge_transfers table
    op.create_table(
        'knowledge_transfers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('knowledge_node_id', sa.Integer(), nullable=False),
        sa.Column('from_task_id', sa.Integer(), nullable=True),
        sa.Column('to_task_id', sa.Integer(), nullable=False),
        sa.Column('transferred_by_agent_id', sa.Integer(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('adaptation_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('adaptation_details', sa.JSON(), nullable=True),
        sa.Column('value_created', sa.Float(), nullable=True),
        sa.Column('time_saved', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_node_id'], ['knowledge_nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transferred_by_agent_id'], ['agents.agent_id'], ondelete='CASCADE')
    )
    op.create_index('idx_transfer_knowledge', 'knowledge_transfers', ['knowledge_node_id'])
    op.create_index('idx_transfer_agent', 'knowledge_transfers', ['transferred_by_agent_id'])


def downgrade() -> None:
    op.drop_table('knowledge_transfers')
    op.drop_table('knowledge_nodes')
    op.drop_table('epiplexity_measures')

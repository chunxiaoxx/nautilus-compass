"""
Add composite indexes for performance optimization.

This migration adds composite indexes to improve query performance:
- tasks: (status, created_at) for list_tasks queries
- tasks: (agent, status) for agent-specific task queries
- tasks: (publisher, status) for publisher-specific task queries
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001_add_composite_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add composite indexes."""
    # Tasks table composite indexes
    op.create_index(
        'idx_task_status_created',
        'tasks',
        ['status', 'created_at'],
        unique=False
    )

    op.create_index(
        'idx_task_agent_status',
        'tasks',
        ['agent', 'status'],
        unique=False
    )

    op.create_index(
        'idx_task_publisher_status',
        'tasks',
        ['publisher', 'status'],
        unique=False
    )


def downgrade():
    """Remove composite indexes."""
    op.drop_index('idx_task_publisher_status', table_name='tasks')
    op.drop_index('idx_task_agent_status', table_name='tasks')
    op.drop_index('idx_task_status_created', table_name='tasks')

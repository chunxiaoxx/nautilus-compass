"""add is_public to academic_tasks for agent feed

Revision ID: a1b2c3d4e5f6
Revises: f600fd632eae
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f600fd632eae'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'academic_tasks',
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false')
    )
    op.create_index(
        'idx_academic_task_public',
        'academic_tasks',
        ['is_public', 'status', 'created_at']
    )


def downgrade():
    op.drop_index('idx_academic_task_public', table_name='academic_tasks')
    op.drop_column('academic_tasks', 'is_public')

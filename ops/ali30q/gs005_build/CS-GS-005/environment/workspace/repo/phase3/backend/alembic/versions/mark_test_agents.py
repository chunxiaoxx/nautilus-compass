"""mark_test_agents

Revision ID: b2c3d4e5f6a1
Revises: c3d4e5f6a1b2
Branch Labels: None
Depends On: None

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a1'
down_revision = 'c3d4e5f6a1b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_test column to agents
    op.add_column('agents',
        sa.Column('is_test', sa.Boolean(), nullable=True, server_default='false'))
    # Mark SecurityTestBot agents
    op.execute(
        "UPDATE agents SET is_test = true WHERE name LIKE 'SecurityTestBot%'"
    )


def downgrade() -> None:
    op.drop_column('agents', 'is_test')

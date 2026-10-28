"""add_nau_token_fields_to_academic_tasks

Revision ID: c3d4e5f6a1b2
Revises: a1b2c3d4e5f6
Branch Labels: None
Depends On: None

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a1b2'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('academic_tasks',
        sa.Column('blockchain_tx_hash', sa.String(66), nullable=True))
    op.add_column('academic_tasks',
        sa.Column('token_reward', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('academic_tasks', 'token_reward')
    op.drop_column('academic_tasks', 'blockchain_tx_hash')

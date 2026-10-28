"""add gas fee fields to tasks

Revision ID: add_gas_fee_fields
Revises:
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_gas_fee_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add gas fee sharing fields to tasks table"""
    op.add_column('tasks', sa.Column('gas_used', sa.BigInteger(), nullable=True))
    op.add_column('tasks', sa.Column('gas_cost', sa.BigInteger(), nullable=True))
    op.add_column('tasks', sa.Column('gas_split', sa.BigInteger(), nullable=True))


def downgrade():
    """Remove gas fee sharing fields from tasks table"""
    op.drop_column('tasks', 'gas_split')
    op.drop_column('tasks', 'gas_cost')
    op.drop_column('tasks', 'gas_used')

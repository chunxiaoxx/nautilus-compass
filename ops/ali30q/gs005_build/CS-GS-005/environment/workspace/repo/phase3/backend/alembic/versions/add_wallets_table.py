"""Add wallets table for wallet issuer feature

Revision ID: a1b2c3d4e5f6
Revises: 8e6ea2b77d0e
Create Date: 2026-03-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '8e6ea2b77d0e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create wallets table
    op.create_table(
        'wallets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_id', sa.String(36), nullable=False),
        sa.Column('public_address', sa.String(42), nullable=False),
        sa.Column('encrypted_private_key', sa.Text(), nullable=False),
        sa.Column('mnemonic_hash', sa.String(255), nullable=False),
        sa.Column('derivation_path', sa.String(50), nullable=False, server_default="m/44'/60'/0'/0/0"),
        sa.Column('key_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('wallet_type', sa.String(20), nullable=False, server_default='agent'),
        sa.Column('activation_status', sa.String(20), nullable=False, server_default='created'),
        sa.Column('eth_funded', sa.Boolean(), server_default='false'),
        sa.Column('usdc_funded', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_tx_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('wallet_id', name='uq_wallets_wallet_id'),
        sa.UniqueConstraint('public_address', name='uq_wallets_public_address'),
    )

    # Create indexes
    op.create_index('idx_wallet_id', 'wallets', ['wallet_id'])
    op.create_index('idx_wallet_address', 'wallets', ['public_address'])
    op.create_index('idx_wallet_agent_id', 'wallets', ['agent_id'])
    op.create_index('idx_wallet_user_id', 'wallets', ['user_id'])
    op.create_index('idx_wallet_type_status', 'wallets', ['wallet_type', 'activation_status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_wallet_type_status', table_name='wallets')
    op.drop_index('idx_wallet_user_id', table_name='wallets')
    op.drop_index('idx_wallet_agent_id', table_name='wallets')
    op.drop_index('idx_wallet_address', table_name='wallets')
    op.drop_index('idx_wallet_id', table_name='wallets')

    # Drop table
    op.drop_table('wallets')

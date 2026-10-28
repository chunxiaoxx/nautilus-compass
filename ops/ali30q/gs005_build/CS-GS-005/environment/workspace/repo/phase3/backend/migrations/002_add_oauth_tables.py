"""
Migration: Add OAuth 2.0 tables

Creates tables for OAuth clients, authorization codes, and access tokens.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_add_oauth_tables'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Create OAuth tables."""

    # Create oauth_clients table
    op.create_table(
        'oauth_clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(length=64), nullable=False),
        sa.Column('client_secret', sa.String(length=128), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('redirect_uris', sa.JSON(), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_oauth_clients_client_id', 'oauth_clients', ['client_id'], unique=True)
    op.create_index('ix_oauth_clients_is_active', 'oauth_clients', ['is_active'])
    op.create_index('ix_oauth_clients_created_at', 'oauth_clients', ['created_at'])

    # Create oauth_authorization_codes table
    op.create_table(
        'oauth_authorization_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('client_id', sa.String(length=64), nullable=False),
        sa.Column('agent_address', sa.String(length=42), nullable=False),
        sa.Column('redirect_uri', sa.String(length=500), nullable=False),
        sa.Column('scope', sa.String(length=500), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_oauth_authorization_codes_code', 'oauth_authorization_codes', ['code'], unique=True)
    op.create_index('ix_oauth_authorization_codes_client_id', 'oauth_authorization_codes', ['client_id'])
    op.create_index('ix_oauth_authorization_codes_agent_address', 'oauth_authorization_codes', ['agent_address'])
    op.create_index('ix_oauth_authorization_codes_expires_at', 'oauth_authorization_codes', ['expires_at'])

    # Create oauth_access_tokens table
    op.create_table(
        'oauth_access_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('access_token', sa.String(length=64), nullable=False),
        sa.Column('refresh_token', sa.String(length=64), nullable=False),
        sa.Column('client_id', sa.String(length=64), nullable=False),
        sa.Column('agent_address', sa.String(length=42), nullable=False),
        sa.Column('scope', sa.String(length=500), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('refresh_expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_oauth_access_tokens_access_token', 'oauth_access_tokens', ['access_token'], unique=True)
    op.create_index('ix_oauth_access_tokens_refresh_token', 'oauth_access_tokens', ['refresh_token'], unique=True)
    op.create_index('ix_oauth_access_tokens_client_id', 'oauth_access_tokens', ['client_id'])
    op.create_index('ix_oauth_access_tokens_agent_address', 'oauth_access_tokens', ['agent_address'])
    op.create_index('ix_oauth_access_tokens_expires_at', 'oauth_access_tokens', ['expires_at'])
    op.create_index('ix_oauth_access_tokens_revoked', 'oauth_access_tokens', ['revoked'])


def downgrade():
    """Drop OAuth tables."""
    op.drop_table('oauth_access_tokens')
    op.drop_table('oauth_authorization_codes')
    op.drop_table('oauth_clients')

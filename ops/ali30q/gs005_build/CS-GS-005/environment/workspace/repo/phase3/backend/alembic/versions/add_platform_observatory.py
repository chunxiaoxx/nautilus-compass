"""add platform_metrics_snapshots table

Revision ID: e5f6a1b2c3d4
Revises: d4e5f6a1b2c3
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'e5f6a1b2c3d4'
down_revision = 'd4e5f6a1b2c3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'platform_metrics_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            'snapshot_time',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.Column(
            'metrics',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            'anomalies',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column('health_score', sa.Float(), nullable=True),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
    )
    op.create_index(
        'idx_snapshots_time',
        'platform_metrics_snapshots',
        [sa.text('snapshot_time DESC')],
    )


def downgrade():
    op.drop_index('idx_snapshots_time', table_name='platform_metrics_snapshots')
    op.drop_table('platform_metrics_snapshots')

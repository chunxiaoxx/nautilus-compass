"""add evolution ledger and pending nau rewards

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-04-01
"""
from alembic import op

revision = 'b2c3d4e5f6a1'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS platform_evolution_log (
            id VARCHAR(16) PRIMARY KEY,
            proposal_id VARCHAR(64) NOT NULL,
            proposer_agent_id INTEGER NOT NULL,
            version_str VARCHAR(20) NOT NULL,
            minor_version INTEGER NOT NULL UNIQUE,
            change_type VARCHAR(50),
            proposed_change JSONB NOT NULL DEFAULT '{}',
            sandbox_result JSONB NOT NULL DEFAULT '{}',
            metric_delta FLOAT NOT NULL DEFAULT 0.0,
            nau_rewarded FLOAT NOT NULL DEFAULT 0.0,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_evolution_proposal ON platform_evolution_log(proposal_id);
        CREATE INDEX IF NOT EXISTS idx_evolution_version ON platform_evolution_log(minor_version);

        CREATE TABLE IF NOT EXISTS pending_nau_rewards (
            id SERIAL PRIMARY KEY,
            agent_id INTEGER NOT NULL REFERENCES agents(id),
            amount FLOAT NOT NULL,
            reason TEXT,
            source_id VARCHAR(64),
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            tx_hash VARCHAR(66),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            fulfilled_at TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS idx_pending_nau_agent ON pending_nau_rewards(agent_id);
        CREATE INDEX IF NOT EXISTS idx_pending_nau_status ON pending_nau_rewards(status);
    """)


def downgrade():
    op.execute("""
        DROP TABLE IF EXISTS pending_nau_rewards;
        DROP TABLE IF EXISTS platform_evolution_log;
    """)

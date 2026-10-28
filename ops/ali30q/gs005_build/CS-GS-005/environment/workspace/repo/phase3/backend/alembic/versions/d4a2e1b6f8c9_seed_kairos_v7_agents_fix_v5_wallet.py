"""seed Kairos + V7 rows · fix V5 wallet in agents table · Inc 1 batch followup

Revision ID: d4a2e1b6f8c9
Revises: c9e8f3a1d2b5
Create Date: 2026-05-28

Inc 1 batch follow-up (3 ops · idempotent · single migration):

1. **Fix V5 wallet** · The earlier c9e8f3a1d2b5 migration seeded agents.id=9000002
   with owner `0x9C17F3f1e34739c776c041364Cf9F94Ac71612F9` based on agent-dialog
   outbound report. Cloud audit of platform_agents shows the real Nautilus Prime
   wallet is `0x1d5B7714f12b9ef979a6c5D1F1a8cf860fbc89F6` (NAU 16202 · tier high).
   agent-dialog report was incorrect. This migration UPDATEs the owner to the
   audited value.

2. **Seed Kairos** at agents.id=9000003 · sentinel owner (Kairos has no EOA wallet
   in platform_agents · agent_id text='kairos'). Sentinel address mirrors the
   ETH dead-address convention (0x0...0001/0002) extended with the agent index.

3. **Seed V7** at agents.id=9000004 · same sentinel pattern (V7/v7-souls-fusion
   has no EOA wallet · agent_id text='v7-telegram'/'v7-souls-fusion').

L3 contract doc updated in same commit (sections 1.5 corrected · 1.6 Kairos · 1.7 V7).

## Alembic chain caveat (pre-existing · not introduced by this migration)

Continues Inc 1 linear sub-chain:
  f6a1b2c3d4e5 → a7b4c1d9e2f3 → b8c5d2e0a3f4 → c9e8f3a1d2b5 → d4a2e1b6f8c9

Cloud `nautilus_production` has no alembic_version table (Base.metadata.create_all
bootstrap) · this migration is applied via idempotent raw SQL on cloud · the file
documents the canonical SQL for any future synthetic alembic-only DB build.
"""
from alembic import op
import sqlalchemy as sa

revision = 'd4a2e1b6f8c9'
down_revision = 'c9e8f3a1d2b5'
branch_labels = None
depends_on = None


# Canonical agent identities (published in L3 contract for wrapper consumption)
V5_AGENT_ID = 9_000_002
V5_OWNER_WALLET = '0x1d5B7714f12b9ef979a6c5D1F1a8cf860fbc89F6'  # audited cloud reality
V5_OWNER_WALLET_LEGACY = '0x9C17F3f1e34739c776c041364Cf9F94Ac71612F9'  # was wrong (from agent-dialog report)

KAIROS_AGENT_ID = 9_000_003
KAIROS_OWNER_SENTINEL = '0x0000000000000000000000000000000000000003'
KAIROS_NAME = 'Kairos'

V7_AGENT_ID = 9_000_004
V7_OWNER_SENTINEL = '0x0000000000000000000000000000000000000004'
V7_NAME = 'V7'

NEWCOMER_REPUTATION = 100  # TRUSTED tier ceiling per proposal_consensus.get_vote_weight


def upgrade():
    # Op 1: fix V5 owner wallet (idempotent · only updates if currently the wrong value)
    op.execute(sa.text(
        "UPDATE agents SET owner = :correct WHERE id = :id AND owner = :legacy"
    ).bindparams(
        id=V5_AGENT_ID,
        correct=V5_OWNER_WALLET,
        legacy=V5_OWNER_WALLET_LEGACY,
    ))

    # Op 2: seed Kairos
    op.execute(sa.text(
        "INSERT INTO agents (id, agent_id, owner, name, reputation, created_at) "
        "SELECT :id, :agent_id, :owner, :name, :reputation, NOW() "
        "WHERE NOT EXISTS (SELECT 1 FROM agents WHERE id = :id)"
    ).bindparams(
        id=KAIROS_AGENT_ID,
        agent_id=KAIROS_AGENT_ID,
        owner=KAIROS_OWNER_SENTINEL,
        name=KAIROS_NAME,
        reputation=NEWCOMER_REPUTATION,
    ))

    # Op 3: seed V7
    op.execute(sa.text(
        "INSERT INTO agents (id, agent_id, owner, name, reputation, created_at) "
        "SELECT :id, :agent_id, :owner, :name, :reputation, NOW() "
        "WHERE NOT EXISTS (SELECT 1 FROM agents WHERE id = :id)"
    ).bindparams(
        id=V7_AGENT_ID,
        agent_id=V7_AGENT_ID,
        owner=V7_OWNER_SENTINEL,
        name=V7_NAME,
        reputation=NEWCOMER_REPUTATION,
    ))


def downgrade():
    # Belt-and-suspenders: match BOTH id AND owner sentinel for Kairos/V7
    op.execute(sa.text(
        "DELETE FROM agents WHERE id = :id AND owner = :owner"
    ).bindparams(id=V7_AGENT_ID, owner=V7_OWNER_SENTINEL))

    op.execute(sa.text(
        "DELETE FROM agents WHERE id = :id AND owner = :owner"
    ).bindparams(id=KAIROS_AGENT_ID, owner=KAIROS_OWNER_SENTINEL))

    # Revert V5 wallet (only if currently the corrected value)
    op.execute(sa.text(
        "UPDATE agents SET owner = :legacy WHERE id = :id AND owner = :correct"
    ).bindparams(
        id=V5_AGENT_ID,
        correct=V5_OWNER_WALLET,
        legacy=V5_OWNER_WALLET_LEGACY,
    ))

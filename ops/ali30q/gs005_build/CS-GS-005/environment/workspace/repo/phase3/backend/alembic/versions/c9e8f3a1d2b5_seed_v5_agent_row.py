"""seed V5 (nautilus-prime-001) row into agents · Inc 1 follow-up

Revision ID: c9e8f3a1d2b5
Revises: b8c5d2e0a3f4
Create Date: 2026-05-28

Inc 1 follow-up. The Sub-task 1 seed migration `a7b4c1d9e2f3_seed_soul_meta_task`
only seeded `academic_tasks.id=9_000_001`. The L3 contract (§2 + API validation
at `phase3/backend/api/platform_proposals.py:58-60`) also requires the proposing
agent's id to exist in `agents.id`. V5 (`nautilus-prime-001`) exists in
`platform_agents` but has zero rows in `agents` · this migration plugs that gap.

Without this seed, V5's L3 wiring (`submit_soul_proposal` tool · agent-dialog
ownership) would fail at `SELECT id FROM agents WHERE id=:aid` with
`agent_id not found`. Surfaced by agent-dialog
(`OUTBOUND_TO_PLATFORM_DIALOG_20260528_inc1_ack_and_agents_row_request.md`).

Constants exposed (symmetric with the academic_tasks seed):
- `V5_AGENT_ID = 9_000_002` — published in `docs/L3_CONTRACT_SOUL_GOVERNANCE.md`
  alongside `SOUL_META_TASK_ID = 9_000_001`. Both are stable canonical Integers.

## Alembic chain caveat (pre-existing · not introduced by this migration)

Continues the Inc 1 linear sub-chain
`f6a1b2c3d4e5 → a7b4c1d9e2f3 → b8c5d2e0a3f4 → c9e8f3a1d2b5`.
Pre-existing alembic chain has known dup-revision IDs + multi-head state
(see memory: `session_20260525_stage1_day1_full_ship_dogfood_evidence`).
Cloud nautilus_production has NO `alembic_version` table (built via
SQLAlchemy `Base.metadata.create_all`); this seed is applied via raw SQL
in the same idempotent pattern.

## Anchor #5 schema split-brain note (pre-existing · not introduced by this migration)

Cloud `agents` has 6 NOT NULL columns (id, agent_id, owner, name, reputation,
created_at) plus many nullable ones (current_tasks, completed_tasks,
total_earnings, etc · all skipped here with their server defaults).
"""
from alembic import op
import sqlalchemy as sa

revision = 'c9e8f3a1d2b5'
down_revision = 'b8c5d2e0a3f4'
branch_labels = None
depends_on = None


# Constants (published in L3 contract for V5 wrapper consumption)
V5_AGENT_ID = 9_000_002
V5_AGENT_NUM = 9_000_002  # agent_id Integer column · symmetric with id
V5_OWNER_WALLET = '0x9C17F3f1e34739c776c041364Cf9F94Ac71612F9'
V5_AGENT_NAME = 'Nautilus Prime'
V5_REPUTATION_SEED = 100  # newcomer ceiling per proposal_consensus.get_vote_weight


def upgrade():
    op.execute(sa.text(
        "INSERT INTO agents (id, agent_id, owner, name, reputation, created_at) "
        "SELECT :id, :agent_id, :owner, :name, :reputation, NOW() "
        "WHERE NOT EXISTS (SELECT 1 FROM agents WHERE id = :id)"
    ).bindparams(
        id=V5_AGENT_ID,
        agent_id=V5_AGENT_NUM,
        owner=V5_OWNER_WALLET,
        name=V5_AGENT_NAME,
        reputation=V5_REPUTATION_SEED,
    ))


def downgrade():
    # Belt-and-suspenders: match BOTH id AND owner wallet to prevent accidental
    # deletion of an organic row that happens to land on the sentinel id.
    op.execute(sa.text(
        "DELETE FROM agents WHERE id = :id AND owner = :owner"
    ).bindparams(
        id=V5_AGENT_ID,
        owner=V5_OWNER_WALLET,
    ))

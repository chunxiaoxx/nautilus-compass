"""add resolution columns to platform_improvement_proposals (soul executor writeback)

Revision ID: b8c5d2e0a3f4
Revises: a7b4c1d9e2f3
Create Date: 2026-05-28

Purpose
-------
Increment 1 of the KEYSTONE trinity loop (agent → vote → soul → PR) Sub-task 2.
After the governance vote accepts a `proposed_change.type='code'` proposal,
the new `soul_executor` service polls `platform_improvement_proposals` for
`status='accepted'` rows where `(proposed_change->>'type')='code'` and
`resolved_by IS NULL`, then ships a DRAFT PR via `soul_service.ship_to_draft_pr`
and writes back the outcome via the three columns this migration adds:

- `resolution_note` (Text, nullable): PR URL on success, "<stage>: <detail>"
  on failure (always truncated to 2000 chars at write time).
- `resolved_at` (TIMESTAMPTZ, nullable): NOW() at writeback time.
- `resolved_by` (String(50), nullable): currently always 'soul'; reserved
  for future executors (e.g., bot agents, manual ops).

The partial index `idx_proposals_executor_poll` is shaped to match the
executor's exact poll predicate, so polling 5 rows per 10-min timer cycle
stays cheap even as the table grows.

L3 contract reference
---------------------
See `docs/L3_CONTRACT_SOUL_GOVERNANCE.md` §4 (Polling shape) — these three
new columns are the polling-side contract that V5 / Kairos / any agent reads
back to learn the outcome of its emitted proposal. Defensive treatment as
optional fields is documented there (V5 must not crash if a row predates
this migration).

Status semantics
----------------
`platform_improvement_proposals.status` is `varchar(20)`. The two new
terminal states written by soul_executor — `executed_ok` (11 chars) and
`executed_failed` (15 chars) — both fit. No `ALTER COLUMN` of `status` is
needed.

Alembic chain caveat (pre-existing · not introduced by this migration)
----------------------------------------------------------------------
The alembic `versions/` directory has known dup-revision IDs and multi-head
state (see memory: `session_20260525_stage1_day1_full_ship_dogfood_evidence`).
This migration's `down_revision = 'a7b4c1d9e2f3'` chains linearly off
Sub-task 1's seed migration, keeping the Inc 1 branch self-contained. Broader
chain cleanup is parked for a separate PR per Inc 1 workflow-lock discipline.

Upgrade uses `ADD COLUMN IF NOT EXISTS` (Postgres ≥9.6) so the migration is
safe to re-run if cloud already has the columns from out-of-band ALTERs —
consistent with the chain-mess caveat documented above.

References
----------
- docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md
- docs/plans/2026-05-28-inc1-governance-route.md (Sub-task 2)
- docs/L3_CONTRACT_SOUL_GOVERNANCE.md (§4 polling shape, §5 status state machine)
- phase3/backend/services/soul_executor.py (the writeback caller)
"""
from alembic import op
import sqlalchemy as sa


# Alembic identifiers ---------------------------------------------------------
revision = 'b8c5d2e0a3f4'
down_revision = 'a7b4c1d9e2f3'
branch_labels = None
depends_on = None


def upgrade():
    """Add three resolution columns + the executor's partial poll index.

    Columns are nullable so existing rows (any pre-Inc-1 proposals) remain
    valid. They are populated only by `soul_executor.execute_accepted_proposals`
    when it finishes processing a row.
    """
    op.execute(sa.text(
        "ALTER TABLE platform_improvement_proposals "
        "ADD COLUMN IF NOT EXISTS resolution_note TEXT"
    ))
    op.execute(sa.text(
        "ALTER TABLE platform_improvement_proposals "
        "ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE"
    ))
    op.execute(sa.text(
        "ALTER TABLE platform_improvement_proposals "
        "ADD COLUMN IF NOT EXISTS resolved_by VARCHAR(50)"
    ))

    # Partial index matches the soul_executor poll predicate exactly so the
    # 10-min cron stays cheap as the table grows. Postgres ≥ 9.5 supports
    # IF NOT EXISTS for indexes.
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_proposals_executor_poll "
        "ON platform_improvement_proposals (created_at) "
        "WHERE status = 'accepted' "
        "AND (proposed_change->>'type') = 'code' "
        "AND resolved_by IS NULL"
    ))


def downgrade():
    """Drop the three resolution columns + partial poll index.

    `DROP INDEX IF EXISTS` is idempotent (Postgres). Column drops are
    standard ALTER TABLE statements and will succeed even if the columns
    contain data (cascade-free since no FK / view references them).
    """
    op.execute("DROP INDEX IF EXISTS idx_proposals_executor_poll")
    op.drop_column('platform_improvement_proposals', 'resolved_by')
    op.drop_column('platform_improvement_proposals', 'resolved_at')
    op.drop_column('platform_improvement_proposals', 'resolution_note')

"""seed singleton platform_meta task for soul governance route

Revision ID: a7b4c1d9e2f3
Revises: f6a1b2c3d4e5
Create Date: 2026-05-28

Purpose
-------
Increment 1 of the KEYSTONE trinity loop (agent → vote → soul → PR) requires
that any `POST /api/platform/proposals` body carry a `task_id` referencing a
row in `academic_tasks` whose `task_type='platform_meta'` (the API validates
this at `api/platform_proposals.py` lines 50-55). For code-improvement
proposals targeting platform self-modification, there is no organic
academic task to point at — so we seed a **single, stable, well-known**
sentinel row that all such proposals share.

This row is the L3 contract anchor between agent-dialog (V5 wrapper emits
`task_id = 9000001`) and platform-dialog (soul executor reads back via
`platform_improvement_proposals.task_id`). See
`docs/L3_CONTRACT_SOUL_GOVERNANCE.md` for the contract; this migration is
its database manifestation.

Idempotency
-----------
`INSERT … WHERE NOT EXISTS` so re-running the migration (or running it on
a cloud that already has the row) is a no-op. The `downgrade()` is
similarly idempotent and belt-and-suspenders matches BOTH id and
task_type to avoid accidentally deleting an organic row that happens to
share the id.

Schema drift note
-----------------
`academic_tasks.id` is declared Integer autoincrement in the SQLAlchemy
model (`models/database.py:242`) and the FK from
`platform_improvement_proposals.task_id` is Integer
(`alembic/versions/add_improvement_proposals.py:23`). Sentinel id
`9_000_001` is well above any organic auto-incremented value and is
recognizable as the platform_meta seed at a glance. If cloud schema has
drifted (anchor #5 split-brain), upgrade will surface a clear FK / type
error rather than silently corrupt data.

Alembic chain caveat (pre-existing · not introduced by this migration)
----------------------------------------------------------------------
The alembic `versions/` directory has known dup-revision IDs and multi-head
state (see memory: `session_20260525_stage1_day1_full_ship_dogfood_evidence`).
This seed migration's `down_revision = 'f6a1b2c3d4e5'` deliberately descends
from the FK owner (the migration that defines `platform_improvement_proposals
.task_id` → `academic_tasks.id`). It adds one more sibling to the existing
multi-head graph; chain cleanup is parked for a separate PR per Inc 1
workflow-lock discipline (KEYSTONE keystone). If `alembic upgrade head`
fails on cloud due to multi-head, run targeted: `alembic upgrade a7b4c1d9e2f3`.

Anchor #5 schema split-brain note (pre-existing · not introduced by this migration)
-----------------------------------------------------------------------------------
Cloud `academic_tasks` table has `tenant_id` (String NOT NULL, Python default
`'public'`) and `is_public` (Boolean NOT NULL, Python default `False`); both
columns are referenced in this INSERT (lines below).

These columns are NOT consistently created by the current alembic chain. They
are part of the cloud production schema (added via `Base.metadata.create_all`
or out-of-band ALTER at platform bootstrap). If this migration ever runs
against a synthetic alembic-only DB build, INSERT will fail with "column does
not exist". Cure: a separate chain-cleanup PR. Out of Inc 1 scope per the
project's first-principles constitution (simplest + lowest cost + lowest
maintenance) and per `feedback_workflow_lock_goal_until_done_20260527.md`.

References
----------
- docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md
- docs/plans/2026-05-28-inc1-governance-route.md (Sub-task 1)
- docs/L3_CONTRACT_SOUL_GOVERNANCE.md
- docs/HANDOFF_20260528_003_increment1_governance_route.md
"""
from alembic import op
import sqlalchemy as sa


# Alembic identifiers ---------------------------------------------------------
revision = 'a7b4c1d9e2f3'
down_revision = 'f6a1b2c3d4e5'
branch_labels = None
depends_on = None


# Stable identifiers (DO NOT CHANGE — these are the L3 contract anchors) -----
SOUL_META_TASK_ID = 9_000_001
SOUL_META_TASK_STR_ID = 'platform-meta-soul-singleton'
SOUL_META_TASK_TYPE = 'platform_meta'
SOUL_META_TASK_TITLE = 'Soul code-improvement singleton'
SOUL_META_TASK_DESCRIPTION = (
    'Singleton sentinel task referenced by all soul-routed '
    'code-improvement proposals (KEYSTONE trinity loop · Increment 1). '
    'Agents emit POST /api/platform/proposals with task_id=9000001 and '
    'proposed_change={"type":"code","task":"<NL improvement spec>"}. '
    'Governance vote → soul executor → DRAFT PR → human merge gate. '
    'See docs/L3_CONTRACT_SOUL_GOVERNANCE.md for the full contract and '
    'docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md '
    'for the architecture.'
)


def upgrade():
    """Idempotent INSERT of the platform_meta singleton row.

    Re-running this migration on a database that already has the row is a
    no-op. All NOT NULL columns are supplied explicitly because the model
    defaults are Python-level (not server-side) and would be skipped by a
    raw SQL INSERT.
    """
    op.execute(
        sa.text(
            """
            INSERT INTO academic_tasks
                (id, task_id, title, description, task_type, status,
                 tenant_id, is_public, created_at, updated_at)
            SELECT :id, :task_id, :title, :description, :task_type,
                   :status, :tenant_id, :is_public, NOW(), NOW()
            WHERE NOT EXISTS (
                SELECT 1 FROM academic_tasks WHERE id = :id
            )
            """
        ).bindparams(
            id=SOUL_META_TASK_ID,
            task_id=SOUL_META_TASK_STR_ID,
            title=SOUL_META_TASK_TITLE,
            description=SOUL_META_TASK_DESCRIPTION,
            task_type=SOUL_META_TASK_TYPE,
            status='pending',
            tenant_id='public',
            is_public=False,
        )
    )


def downgrade():
    """Idempotent DELETE of the platform_meta singleton row.

    Belt-and-suspenders match on BOTH id AND task_type so we never
    accidentally delete an organic row that happens to land on the
    sentinel id (defensive against future schema drift). Existing
    proposals referencing this task_id will have their FK set to NULL
    per the ON DELETE SET NULL clause on
    platform_improvement_proposals.task_id.
    """
    op.execute(
        sa.text(
            """
            DELETE FROM academic_tasks
            WHERE id = :id AND task_type = :task_type
            """
        ).bindparams(
            id=SOUL_META_TASK_ID,
            task_type=SOUL_META_TASK_TYPE,
        )
    )

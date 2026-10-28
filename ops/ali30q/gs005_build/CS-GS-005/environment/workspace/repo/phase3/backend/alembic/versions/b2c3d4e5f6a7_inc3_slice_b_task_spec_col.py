"""inc3 slice B · agent_dispatch_log.task_spec column

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-29

Inc 3 Slice B followup · the Slice A migration created agent_dispatch_log with
only task_spec_hash. The hash alone cannot reach the daemon as a runnable goal
description, so the dispatcher (POST /api/soul/dispatch) had no way to feed the
actual task text into the engine.ship() call.

This migration adds the missing task_spec column so:
  - the dispatcher persists the full spec text alongside the hash
  - the daemon goal_stack P2 query reads it back as goal["task_spec"]
  - the daemon adapts the P2 row by copying task_spec → description before
    calling the shared yaml-path ship logic

Idempotent (ADD COLUMN IF NOT EXISTS · DEFAULT '' keeps any pre-existing Slice
A rows valid). Cloud may apply via
scripts/cloud_apply_inc3_slice_b_followup.sh raw-SQL bypass per anchor #5
broken-alembic-chain pattern.
"""
from alembic import op


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'  # Inc 3 Slice A · agent_dispatch_log creation
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE agent_dispatch_log "
        "ADD COLUMN IF NOT EXISTS task_spec TEXT NOT NULL DEFAULT ''"
    )


def downgrade():
    op.execute("ALTER TABLE agent_dispatch_log DROP COLUMN IF EXISTS task_spec")

"""inc3 fitness · engine_cycle_outcomes.fitness_delta column

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-29

Per honest 5/29 diagnosis: the recursive self-improvement loop has plumbing
but no reward signal. This migration adds the column that holds the per-cycle
fitness delta = (ruff_warnings_before - ruff_warnings_after) +
(pytest_collect_after - pytest_collect_before). Warnings down + tests up =
positive. Persisted by soul.daemon._stamp_fitness on the success path.

Idempotent. Cloud may apply via scripts/cloud_apply_inc3_fitness.sh raw-SQL
bypass per anchor #5 broken-alembic-chain pattern.

HONEST CAVEAT · the column being populated does NOT mean the fitness metric
carries useful information. That is an empirical question requiring 10+
cycles of natural daemon fires to evaluate. The migration ships the
container, not the validated metric.
"""
from alembic import op


revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'  # Inc 3 Slice B followup · task_spec column
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE engine_cycle_outcomes "
        "ADD COLUMN IF NOT EXISTS fitness_delta NUMERIC(8,3)"
    )


def downgrade():
    op.execute(
        "ALTER TABLE engine_cycle_outcomes DROP COLUMN IF EXISTS fitness_delta"
    )

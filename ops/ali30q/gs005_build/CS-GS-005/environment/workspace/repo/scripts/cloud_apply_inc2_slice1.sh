#!/usr/bin/env bash
# Inc 2 Slice 1 · cloud raw-SQL migration application (anchor #5 bypass).
# Per handoff #006 §4 line 3: cloud's alembic chain is divergent · raw SQL
# applied directly to nautilus_production is the canonical path.
#
# Idempotent: safe to re-run.

set -euo pipefail

PGPASSWORD="${PGPASSWORD:-nautilus2024}" \
  psql -U nautilus_user -h localhost -d nautilus_production <<'SQL'
\pset border 2

-- Inc 2 Slice 1 migrations · idempotent · safe to re-run

-- 1. proposal_outcomes table (Inc 2 binding-DONE artifact carrier)
CREATE TABLE IF NOT EXISTS proposal_outcomes (
    proposal_id      VARCHAR PRIMARY KEY REFERENCES platform_improvement_proposals(id),
    pre_snapshot     JSONB NOT NULL,
    post_snapshot    JSONB,
    composite_delta  REAL,
    no_revert        BOOLEAN,
    graded_at        TIMESTAMPTZ,
    graded_by        VARCHAR DEFAULT 'soul-settlement-review'
);

-- 2. agents two-dimensional reputation
ALTER TABLE agents ADD COLUMN IF NOT EXISTS rep_proposing REAL NOT NULL DEFAULT 50.0;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS rep_voting    REAL NOT NULL DEFAULT 50.0;

-- Verify
SELECT 'proposal_outcomes' AS check_t, COUNT(*) AS rowcount FROM proposal_outcomes;
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'agents' AND column_name IN ('rep_proposing', 'rep_voting')
ORDER BY column_name;
SQL

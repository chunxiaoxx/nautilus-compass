#!/usr/bin/env bash
# Inc 3 Slice A · goal source classification schema (raw SQL · anchor #5 bypass)
set -euo pipefail
PGPASSWORD="${PGPASSWORD:-nautilus2024}" \
  psql -U nautilus_user -h localhost -d nautilus_production <<'SQL'
ALTER TABLE engine_cycle_outcomes ADD COLUMN IF NOT EXISTS goal_source TEXT NULL;
CREATE TABLE IF NOT EXISTS agent_dispatch_log (
    id              BIGSERIAL PRIMARY KEY,
    agent_id        INTEGER REFERENCES agents(id),
    task_spec_hash  VARCHAR(64) NOT NULL,
    task_type       VARCHAR(32) NOT NULL DEFAULT 'code',
    cycle_id        TEXT REFERENCES engine_cycle_outcomes(cycle_id),
    ship_outcome    VARCHAR(32),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agent_dispatch_log_agent_id ON agent_dispatch_log (agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_dispatch_log_cycle_id ON agent_dispatch_log (cycle_id);
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='engine_cycle_outcomes' AND column_name='goal_source';
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='agent_dispatch_log' ORDER BY ordinal_position;
SQL

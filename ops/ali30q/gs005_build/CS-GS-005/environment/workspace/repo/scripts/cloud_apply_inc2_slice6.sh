#!/usr/bin/env bash
# Inc 2 Slice 6 · proposal_authors schema migration + backfill (raw SQL · anchor #5 bypass)
set -euo pipefail
PGPASSWORD="${PGPASSWORD:-nautilus2024}" \
  psql -U nautilus_user -h localhost -d nautilus_production <<'SQL'
CREATE TABLE IF NOT EXISTS proposal_authors (
    proposal_id          VARCHAR REFERENCES platform_improvement_proposals(id),
    agent_id             INTEGER REFERENCES agents(id),
    contribution_weight  REAL NOT NULL
                         CHECK (contribution_weight > 0
                                AND contribution_weight <= 1),
    PRIMARY KEY (proposal_id, agent_id)
);
-- Backfill: every existing proposal becomes single-author row weight=1.0
INSERT INTO proposal_authors (proposal_id, agent_id, contribution_weight)
SELECT id, agent_id, 1.0 FROM platform_improvement_proposals
WHERE agent_id IS NOT NULL
ON CONFLICT (proposal_id, agent_id) DO NOTHING;
SELECT 'rows after backfill' AS metric, COUNT(*) AS value FROM proposal_authors;
SELECT 'proposals total' AS metric, COUNT(*) AS value FROM platform_improvement_proposals;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name='proposal_authors'
ORDER BY ordinal_position;
SQL

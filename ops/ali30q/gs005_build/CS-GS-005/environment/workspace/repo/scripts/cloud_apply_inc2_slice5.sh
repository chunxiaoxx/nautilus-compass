#!/usr/bin/env bash
# Inc 2 Slice 5 · proposal_blessings schema migration (raw SQL · anchor #5 bypass)
set -euo pipefail
PGPASSWORD="${PGPASSWORD:-nautilus2024}" \
  psql -U nautilus_user -h localhost -d nautilus_production <<'SQL'
CREATE TABLE IF NOT EXISTS proposal_blessings (
    id              BIGSERIAL PRIMARY KEY,
    proposal_id     VARCHAR REFERENCES platform_improvement_proposals(id),
    blesser_id      INTEGER REFERENCES agents(id),
    stake_amount    REAL NOT NULL,
    settled         BOOLEAN DEFAULT FALSE,
    settled_outcome VARCHAR,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_proposal_blessings_proposal_unsettled
    ON proposal_blessings (proposal_id) WHERE settled = FALSE;
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name='proposal_blessings'
ORDER BY ordinal_position;
SQL

#!/usr/bin/env bash
# Inc 2 Slice 4 · onboarding capital schema migration (raw SQL · anchor #5 bypass)
set -euo pipefail
PGPASSWORD="${PGPASSWORD:-nautilus2024}" \
  psql -U nautilus_user -h localhost -d nautilus_production <<'SQL'
ALTER TABLE agents ADD COLUMN IF NOT EXISTS proposing_unlocked    BOOLEAN DEFAULT FALSE;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS voter_bounty_unlocked BOOLEAN DEFAULT FALSE;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS correct_votes_count   INTEGER DEFAULT 0;
SELECT column_name, data_type, column_default FROM information_schema.columns
WHERE table_name='agents' AND column_name IN ('proposing_unlocked','voter_bounty_unlocked','correct_votes_count')
ORDER BY column_name;
SQL

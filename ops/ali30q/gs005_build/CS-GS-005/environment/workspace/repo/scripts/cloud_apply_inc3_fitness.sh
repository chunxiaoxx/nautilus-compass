#!/usr/bin/env bash
# Inc 3 fitness · engine_cycle_outcomes.fitness_delta column (raw SQL · anchor #5 bypass)
set -euo pipefail
PGPASSWORD="${PGPASSWORD:-nautilus2024}" \
  psql -U nautilus_user -h localhost -d nautilus_production <<'SQL'
ALTER TABLE engine_cycle_outcomes ADD COLUMN IF NOT EXISTS fitness_delta NUMERIC(8,3);
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name='engine_cycle_outcomes' AND column_name='fitness_delta';
SQL

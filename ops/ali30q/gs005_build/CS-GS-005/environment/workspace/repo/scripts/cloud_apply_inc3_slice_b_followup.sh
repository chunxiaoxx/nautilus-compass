#!/usr/bin/env bash
# Inc 3 Slice B followup · agent_dispatch_log.task_spec column (raw SQL · anchor #5 bypass)
set -euo pipefail
PGPASSWORD="${PGPASSWORD:-nautilus2024}" \
  psql -U nautilus_user -h localhost -d nautilus_production <<'SQL'
ALTER TABLE agent_dispatch_log ADD COLUMN IF NOT EXISTS task_spec TEXT NOT NULL DEFAULT '';
SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns
WHERE table_name='agent_dispatch_log' AND column_name='task_spec';
SQL

#!/bin/bash
# Flywheel tool snapshot · hourly cron · writes 1h + 24h rows
# Source: /usr/local/bin/flywheel-tool-snapshot.sh
set -euo pipefail

for WIN in 1h 24h; do
  sudo -u postgres psql -d nautilus_production -v ON_ERROR_STOP=1 -v win="${WIN}" <<'SQL'
INSERT INTO flywheel_tool_snapshots (
  snap_ts, "window",
  self_modify_ok, self_modify_fail,
  fulfill_directive_ok, fulfill_directive_fail,
  propose_code_change_ok,
  stakes_closed
)
SELECT
  now(),
  :'win',
  COALESCE(SUM(CASE WHEN tool_name IN ('self_modify','selector:self_modify') AND success THEN 1 ELSE 0 END),0)::int,
  COALESCE(SUM(CASE WHEN tool_name IN ('self_modify','selector:self_modify') AND NOT success THEN 1 ELSE 0 END),0)::int,
  COALESCE(SUM(CASE WHEN tool_name IN ('fulfill_directive','selector:fulfill_directive') AND success THEN 1 ELSE 0 END),0)::int,
  COALESCE(SUM(CASE WHEN tool_name IN ('fulfill_directive','selector:fulfill_directive') AND NOT success THEN 1 ELSE 0 END),0)::int,
  COALESCE(SUM(CASE WHEN tool_name IN ('propose_code_change','selector:propose_code_change') AND success THEN 1 ELSE 0 END),0)::int,
  (SELECT COUNT(*)::int FROM platform_agent_stakes
    WHERE stake_id LIKE 'v5r%' AND fulfilled_at IS NOT NULL
      AND fulfilled_at >= now() - (:'win')::interval)
FROM agent_tool_calls
WHERE ts >= now() - (:'win')::interval;
SQL
done

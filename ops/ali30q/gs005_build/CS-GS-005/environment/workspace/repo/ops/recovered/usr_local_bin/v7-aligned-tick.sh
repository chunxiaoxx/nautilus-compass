source /etc/nautilus/secrets.env
#!/bin/bash
# V7 M1 aligned tick · 接受 lane 参数(v5/kairos/v6) · 写 metadata.lane
# 5min 错开:V5 :00,:15,:30,:45 · Kairos :05,:20,:35,:50 · V6 :10,:25,:40,:55
LANE="${1:-unknown}"
PGPASSWORD=$PGPASSWORD psql -h localhost -U nautilus_user -d nautilus_production -c "
INSERT INTO platform_aligned_ticks (tick_ts, agents_active, harmony_avg, helix_blocks_5min, tool_calls_5min, metadata)
SELECT
  date_trunc('minute', NOW()),
  (SELECT count(*) FROM platform_agents WHERE last_heartbeat > NOW() - interval '10 minutes'),
  COALESCE(
    (SELECT avg((fn_tension_snapshot(agent_id)->>'harmony')::numeric)
     FROM platform_agents
     WHERE last_heartbeat > NOW() - interval '10 minutes'),
    0.5
  ),
  CASE WHEN to_regclass('helix_blocks') IS NULL THEN 0
       ELSE (SELECT count(*) FROM helix_blocks WHERE ts > NOW() - interval '5 minutes') END,
  (SELECT count(*) FROM agent_tool_calls WHERE ts > NOW() - interval '5 minutes'),
  jsonb_build_object('lane', '$LANE', 'triggered_at', NOW()::text)
ON CONFLICT (tick_ts) DO UPDATE SET
  metadata = platform_aligned_ticks.metadata || jsonb_build_object('lane_'||'$LANE', NOW()::text);
" 2>&1 | tail -3

-- 003 · cloud-only view (requires platform_agents table)
-- Apply on cloud (nautilus_production) AFTER 002.
-- Local dev DBs (without platform_agents) skip this.

CREATE OR REPLACE VIEW compass.tenants_view AS
SELECT
  t.tenant_id,
  t.profile,
  t.quota_override,
  t.last_drift_check_at,
  pa.last_heartbeat,
  pa.nau_balance,
  pa.survival_tier,
  CASE
    WHEN pa.last_heartbeat IS NULL THEN 'unknown'
    WHEN pa.last_heartbeat > NOW() - INTERVAL '24 hours' THEN 'active'
    WHEN pa.registered_at > NOW() - INTERVAL '7 days'       THEN 'probation'
    WHEN pa.last_heartbeat > NOW() - INTERVAL '30 days'  THEN 'idle'
    ELSE 'dormant'
  END AS activity_tier,
  COALESCE(t.quota_override,
           CASE
             WHEN pa.last_heartbeat > NOW() - INTERVAL '24 hours' THEN 10000
             WHEN pa.registered_at > NOW() - INTERVAL '7 days'       THEN 1000
             WHEN pa.last_heartbeat > NOW() - INTERVAL '30 days'  THEN 100
             ELSE 0
           END) AS monthly_quota
FROM compass.tenants t
LEFT JOIN v5_fdw.platform_agents pa ON pa.agent_id = t.tenant_id;

COMMENT ON VIEW compass.tenants_view IS
  '派生 view · activity_tier + monthly_quota 实时算 · auth/quota 都读这个';

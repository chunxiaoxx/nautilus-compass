-- 003 local stub · for dev DBs without platform_agents
-- Apply this OR 003_view_cloud_only.sql · not both.

CREATE OR REPLACE VIEW compass.tenants_view AS
SELECT
  t.tenant_id,
  t.profile,
  t.quota_override,
  t.last_drift_check_at,
  NULL::timestamptz AS last_heartbeat,
  NULL::int AS nau_balance,
  NULL::text AS survival_tier,
  'active' AS activity_tier,
  COALESCE(t.quota_override, 10000) AS monthly_quota
FROM compass.tenants t;

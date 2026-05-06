-- Nautilus Compass · multi-tenant schema
-- Apply: psql nautilus_production -f sql/001_compass_schema.sql
-- Rollback: DROP SCHEMA compass CASCADE;
--
-- Decision (2026-04-30): same DB as platform_*, isolated via `compass` schema.
-- - join platform_nau_ledger directly (no fdw hop)
-- - dump/migrate via `pg_dump -n compass`
-- - if later we split DBs, schema name becomes the new DB · zero code change

CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS compass;

-- ── tenants ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS compass.tenants (
  tenant_id        varchar      PRIMARY KEY,
  plan             varchar      NOT NULL DEFAULT 'free',  -- 'free' / 'nau_burst'
  auth_method      varchar      NOT NULL,                 -- 'api_key' / 'platform_jwt' / 'wallet'
  api_key_prefix   varchar,                               -- 'sk-compass-live-' / 'sk-compass-test-'
  api_key_hash     varchar,                               -- bcrypt(secret) · NULL if platform_jwt
  wallet_address   varchar,                               -- 0x... · NULL if api_key only
  quota_remaining  int          NOT NULL DEFAULT 1000,
  quota_reset_at   timestamptz  NOT NULL DEFAULT (NOW() + INTERVAL '30 days'),
  profile          varchar      NOT NULL DEFAULT 'general',
  last_used_at     timestamptz,
  last_ip          varchar,
  created_at       timestamptz  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS tenants_wallet_idx ON compass.tenants(wallet_address)
  WHERE wallet_address IS NOT NULL;

CREATE INDEX IF NOT EXISTS tenants_key_prefix_idx ON compass.tenants(api_key_prefix)
  WHERE api_key_prefix IS NOT NULL;

-- ── usage_log ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS compass.usage_log (
  id          bigserial    PRIMARY KEY,
  tenant_id   varchar      REFERENCES compass.tenants(tenant_id) ON DELETE CASCADE,
  endpoint    varchar      NOT NULL,
  cost_units  int          NOT NULL DEFAULT 1,
  result      jsonb,
  ts          timestamptz  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS usage_log_tenant_ts ON compass.usage_log(tenant_id, ts DESC);

-- ── anchors (per-tenant · vector store) ────────────────────────
CREATE TABLE IF NOT EXISTS compass.anchors (
  tenant_id   varchar      REFERENCES compass.tenants(tenant_id) ON DELETE CASCADE,
  anchor_id   varchar      NOT NULL,
  vector      vector(1024),
  type        varchar      NOT NULL CHECK (type IN ('positive', 'negative')),
  text        text         NOT NULL,
  created_at  timestamptz  NOT NULL DEFAULT NOW(),
  PRIMARY KEY (tenant_id, anchor_id)
);

CREATE INDEX IF NOT EXISTS anchors_vec_ivfflat ON compass.anchors
  USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);

-- ── seed: 内部 4 agent 直通 (auth_method='platform_jwt' · 不计 quota) ──
INSERT INTO compass.tenants (tenant_id, plan, auth_method, profile, quota_remaining)
VALUES
  ('nautilus-prime-001', 'nau_burst', 'platform_jwt', 'general',  9999999),
  ('nautilus-v6',        'nau_burst', 'platform_jwt', 'general',  9999999),
  ('kairos',             'nau_burst', 'platform_jwt', 'general',  9999999),
  ('hr-agent-web',       'nau_burst', 'platform_jwt', 'general',  9999999)
ON CONFLICT (tenant_id) DO NOTHING;

-- ── audit: 一次申请 quota 余额视图 (运维查每日用量) ────────────
CREATE OR REPLACE VIEW compass.daily_usage AS
SELECT
  date_trunc('day', ts) AS day,
  tenant_id,
  endpoint,
  count(*)      AS calls,
  sum(cost_units) AS units
FROM compass.usage_log
GROUP BY day, tenant_id, endpoint
ORDER BY day DESC, tenant_id;

COMMENT ON SCHEMA compass IS 'Nautilus Compass · multi-tenant drift detection / memory recall · v0.7';

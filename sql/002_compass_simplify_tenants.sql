-- Day 7 · Compass = 平台 7 件套之一 · 不再独立 tenant
-- 删 api_key 路径 · 所有 caller = platform_agent
-- compass.tenants 瘦身: 仅留 profile / quota_override / last_drift_check_at

-- 1. 备份现有非内部数据 (smoketest-001 / quota-test-* / exhaust-test-* 留作清理依据)
-- 2. 加 FK 关联 platform_agents (软关联 · 不级联删除避免误炸)
-- 3. 删冗余字段

BEGIN;

-- 删旧字段
ALTER TABLE compass.tenants DROP COLUMN IF EXISTS plan;
ALTER TABLE compass.tenants DROP COLUMN IF EXISTS auth_method;
ALTER TABLE compass.tenants DROP COLUMN IF EXISTS api_key_prefix;
ALTER TABLE compass.tenants DROP COLUMN IF EXISTS api_key_hash;
ALTER TABLE compass.tenants DROP COLUMN IF EXISTS wallet_address;
ALTER TABLE compass.tenants DROP COLUMN IF EXISTS quota_remaining;
ALTER TABLE compass.tenants DROP COLUMN IF EXISTS quota_reset_at;
ALTER TABLE compass.tenants DROP COLUMN IF EXISTS last_ip;

-- 加新字段
ALTER TABLE compass.tenants ADD COLUMN IF NOT EXISTS quota_override int;
ALTER TABLE compass.tenants ADD COLUMN IF NOT EXISTS last_drift_check_at timestamptz;

-- 重命名 last_used_at 为 last_drift_check_at 内容若已有
UPDATE compass.tenants SET last_drift_check_at = last_used_at WHERE last_used_at IS NOT NULL;
ALTER TABLE compass.tenants DROP COLUMN IF EXISTS last_used_at;

-- 清理外部测试 tenant
DELETE FROM compass.usage_log WHERE tenant_id LIKE 'smoketest%' OR tenant_id LIKE 'quota-test%'
   OR tenant_id LIKE 'exhaust-test%' OR tenant_id LIKE 'test-tenant%' OR tenant_id LIKE 'ext-test%';
DELETE FROM compass.tenants WHERE tenant_id LIKE 'smoketest%' OR tenant_id LIKE 'quota-test%'
   OR tenant_id LIKE 'exhaust-test%' OR tenant_id LIKE 'test-tenant%' OR tenant_id LIKE 'ext-test%';

COMMIT;

-- View 创建移到 003_view_cloud_only.sql (因 LEFT JOIN platform_agents 仅 cloud 有)
-- 本地 dev 用 sql/003_view_local_stub.sql (无 JOIN)

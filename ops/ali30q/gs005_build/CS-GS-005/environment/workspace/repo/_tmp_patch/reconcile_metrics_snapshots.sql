-- Stage 3 · reconcile platform_metrics_snapshots schema in nautilus_production
-- 升级到 V5 严 schema(id bigint · health_score int · snapshot_time not null)
-- 保留 phase3 旧数据 + 升 sequence 起点防 ID 冲突

BEGIN;

-- 1 · backup phase3 旧数据
DROP TABLE IF EXISTS _backup_metrics_snapshots_phase3_20260506;
CREATE TABLE _backup_metrics_snapshots_phase3_20260506 AS
  SELECT * FROM platform_metrics_snapshots;

-- 2 · ALTER 升级到 V5 schema
ALTER TABLE platform_metrics_snapshots
  ALTER COLUMN id TYPE bigint;

ALTER TABLE platform_metrics_snapshots
  ALTER COLUMN snapshot_time SET NOT NULL;

ALTER TABLE platform_metrics_snapshots
  ALTER COLUMN health_score TYPE integer USING (CASE WHEN health_score IS NULL THEN 50 ELSE health_score::integer END);

ALTER TABLE platform_metrics_snapshots
  ALTER COLUMN health_score SET NOT NULL;

ALTER TABLE platform_metrics_snapshots
  ALTER COLUMN health_score SET DEFAULT 50;

ALTER TABLE platform_metrics_snapshots
  ALTER COLUMN anomalies SET NOT NULL;

-- 3 · setval sequence · 留 1000 间隔避免 V5 数据 import 时 ID 冲突
SELECT setval('platform_metrics_snapshots_id_seq',
  (SELECT COALESCE(MAX(id), 0) FROM platform_metrics_snapshots) + 1000);

-- 4 · verify
SELECT 'phase3_rows' as kind, count(*) FROM platform_metrics_snapshots
UNION ALL
SELECT 'backup_rows', count(*) FROM _backup_metrics_snapshots_phase3_20260506;

COMMIT;

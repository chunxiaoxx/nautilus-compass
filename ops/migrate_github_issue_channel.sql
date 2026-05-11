-- v1.4 followup · #106 · consolidate github_issue → github
-- 平台 writer 在 2026-05-09 → 05-10 之间换了 channel name
-- (github_issue 旧名 · github 新名 · 同渠道)
-- 不迁移的话 cron 统计 / dashboard / 投放限频会按双渠道算
--
-- Before:
--   github       | 2 rows · last 2026-05-11
--   github_issue | 3 rows · last 2026-05-09
--
-- After: github 5 rows
--
-- Run:
--   ssh cloud
--   PGPASSWORD=nautilus2024 psql -h localhost -U nautilus_user -d nautilus_production \
--     -f /home/ubuntu/nautilus-compass/ops/migrate_github_issue_channel.sql

BEGIN;

-- 1 · audit before
SELECT 'before' AS phase, channel, count(*)
FROM platform_marketing_review
WHERE channel IN ('github', 'github_issue')
GROUP BY 1, 2;

-- 2 · migrate
UPDATE platform_marketing_review
SET channel = 'github',
    metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object('migrated_from_channel', 'github_issue')
WHERE channel = 'github_issue';

-- 3 · audit after
SELECT 'after' AS phase, channel, count(*)
FROM platform_marketing_review
WHERE channel IN ('github', 'github_issue')
GROUP BY 1, 2;

-- 4 · 同时把 channel_registry 里的 github_issue 标 deprecated · 不删
UPDATE platform_channel_registry
SET status = 'deprecated'
WHERE channel = 'github_issue';

COMMIT;

-- Verify:
-- SELECT channel, count(*) FROM platform_marketing_review GROUP BY 1 ORDER BY 2 DESC;
-- expected: github=5, dev.to=23, x=19, email=2, reddit=2, linkedin=1 · 0 github_issue

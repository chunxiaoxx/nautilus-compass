-- v5db 补表迁移(platform 起草 · 2026-09-15 · 对应 org task #231 · trace v5-rsi-ticket-t001-stakes-bids-tables)
-- 目标库:127.0.0.1:5432/v5db(v5 本地库)
-- 幂等:全部 IF NOT EXISTS,可重复执行
-- 认知纠正:negotiation_bids 不是独立表——它是 platform_bounties 的 jsonb 列。
--   #231 原文按"两表"理解;按生产 schema 正本(nautilus_production 实测 dump),正解=补
--   platform_agent_stakes + platform_bounties(含 negotiation_bids 列)。

CREATE TABLE IF NOT EXISTS platform_agent_stakes (
    stake_id      TEXT PRIMARY KEY,
    staker_id     TEXT,
    agent_id      TEXT,
    amount_nau    INTEGER,
    share_bps     INTEGER,
    staked_at     TIMESTAMP,
    unstaked_at   TIMESTAMP,
    status        TEXT,
    total_earned  INTEGER,
    metadata      JSONB,
    directive     TEXT,
    deadline      TIMESTAMP,
    fulfilled_at  TIMESTAMP,
    fulfilled_url TEXT,
    callback_url  TEXT
);
CREATE INDEX IF NOT EXISTS idx_pas_agent ON platform_agent_stakes(agent_id);

CREATE TABLE IF NOT EXISTS platform_bounties (
    bounty_id           VARCHAR(64) PRIMARY KEY,
    title               TEXT,
    description         TEXT,
    reward_nau          INTEGER,
    difficulty          VARCHAR(32),
    task_type           VARCHAR(64),
    status              VARCHAR(32),
    posted_by           VARCHAR(128),
    claimed_by          VARCHAR(128),
    posted_at           TIMESTAMP,
    claimed_at          TIMESTAMP,
    submitted_at        TIMESTAMP,
    deadline            TIMESTAMP,
    result              TEXT,
    score               REAL,
    assigned_to         VARCHAR(128),
    phase               TEXT,
    negotiation_bids    JSONB,
    escrow_locked_nau   INTEGER,
    evaluator_agent_id  TEXT,
    dispute_opened_at   TIMESTAMP,
    dispute_resolution  JSONB,
    channel             TEXT,
    source              TEXT,
    asset_path          TEXT,
    result_url          TEXT,
    metadata            JSONB,
    fail_penalty        INTEGER,
    depends_on          VARCHAR(64),
    auto_deploy         BOOLEAN
);
CREATE INDEX IF NOT EXISTS idx_pb_status ON platform_bounties(status);

-- 验收对照(#231 三判据):
-- ① 两表存在且列结构与查询方匹配:daemon.py 实际查询列 =
--    stakes: stake_id/staker_id/amount_nau/directive/deadline/fulfilled_at/agent_id/status/staked_at(全部含于上列)
--    bounties: bounty_id/negotiation_bids/status(全部含于上列)
-- ② 主脑重启后连续 24h boot log 零 PLATFORM-METRICS fail → 请 v5 侧执行后观察(平台不碰 v5db)
-- ③ 迁移幂等可重放 → IF NOT EXISTS 保证
--
-- 执行说明(v5 侧):
--   psql -h 127.0.0.1 -p 5432 -d v5db -f phase3/backend/ops/sql/v5db_20260915_stakes_bounties.sql
--   (文件全文已在回函 platform-reply-v5-stakes-bids-t001-20260915 内嵌,可直接复制执行)
--   执行后回函 VERDICT 首行。

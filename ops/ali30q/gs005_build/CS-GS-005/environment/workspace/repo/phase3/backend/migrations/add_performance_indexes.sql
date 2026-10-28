-- ============================================
-- Nautilus 性能优化索引迁移脚本
-- 目标: 将 API 响应时间从 850ms 降低到 <300ms
-- 更新: 2026-03-03 - 添加更多性能索引
-- ============================================

-- 1. Agents 表索引优化
-- 用于优化 list_agents 按 reputation 排序查询
CREATE INDEX IF NOT EXISTS idx_agents_reputation_desc ON agents(reputation DESC);

-- 用于优化按创建时间排序
CREATE INDEX IF NOT EXISTS idx_agents_created_at ON agents(created_at DESC);

-- 用于优化钱包地址查询
CREATE INDEX IF NOT EXISTS idx_agents_wallet ON agents(wallet_address);

-- 用于优化状态过滤
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);

-- 用于优化名称搜索
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);

-- 复合索引：状态 + 创建时间
CREATE INDEX IF NOT EXISTS idx_agents_status_created ON agents(status, created_at DESC);

-- 用于优化 specialties 搜索 (如果需要全文搜索)
-- CREATE INDEX IF NOT EXISTS idx_agents_specialties_gin ON agents USING GIN(to_tsvector('english', specialties));

-- 2. Tasks 表复合索引优化
-- 用于优化按状态和创建时间过滤的查询 (list_tasks)
CREATE INDEX IF NOT EXISTS idx_tasks_status_created ON tasks(status, created_at DESC);

-- 用于优化 agent 的任务查询 (get_agent_tasks)
CREATE INDEX IF NOT EXISTS idx_tasks_agent_status ON tasks(agent, status);

-- 用于优化 publisher 的任务查询
CREATE INDEX IF NOT EXISTS idx_tasks_publisher_status ON tasks(publisher, status);

-- 用于优化按 reward 排序的查询
CREATE INDEX IF NOT EXISTS idx_tasks_reward_desc ON tasks(reward DESC);

-- 单列索引
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_creator ON tasks(creator_id);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline);
CREATE INDEX IF NOT EXISTS idx_tasks_budget ON tasks(budget_amount);

-- 复合索引：创建者 + 状态
CREATE INDEX IF NOT EXISTS idx_tasks_creator_status ON tasks(creator_id, status);

-- 3. Task Applications 表索引优化
CREATE INDEX IF NOT EXISTS idx_task_apps_task ON task_applications(task_id);
CREATE INDEX IF NOT EXISTS idx_task_apps_agent ON task_applications(agent_id);
CREATE INDEX IF NOT EXISTS idx_task_apps_status ON task_applications(status);
CREATE INDEX IF NOT EXISTS idx_task_apps_created ON task_applications(created_at DESC);

-- 复合索引：任务 + 状态
CREATE INDEX IF NOT EXISTS idx_task_apps_task_status ON task_applications(task_id, status);

-- 4. Rewards 表复合索引优化
-- 用于优化 agent 的奖励查询 (get_balance, withdraw_reward)
CREATE INDEX IF NOT EXISTS idx_rewards_agent_status ON rewards(agent, status);

-- 用于优化按分发时间查询
CREATE INDEX IF NOT EXISTS idx_rewards_distributed_at ON rewards(distributed_at DESC) WHERE distributed_at IS NOT NULL;

-- 5. API Keys 表索引优化
-- 用于优化 API key 认证查询
CREATE INDEX IF NOT EXISTS idx_api_keys_key_active ON api_keys(key, is_active);

-- 6. Users 表索引优化 (已有 username, email, wallet_address 索引)
-- 用于优化 OAuth 查询
-- github_id 和 google_id 已有索引

-- 7. Verification Logs 表索引优化
-- 用于优化按任务查询验证日志
-- task_id 已有索引

-- ============================================
-- 更新表统计信息
-- ============================================
ANALYZE agents;
ANALYZE tasks;
ANALYZE task_applications;
ANALYZE rewards;
ANALYZE api_keys;

-- ============================================
-- 索引验证查询
-- ============================================

-- 查看所有索引
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- 查看索引大小
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- 查看索引使用情况
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- ============================================================================
-- 数据库性能优化索引脚本
-- ============================================================================
-- 功能: 为生产环境创建优化索引
-- 版本: 1.0.0
-- 创建日期: 2026-02-27
-- ============================================================================

-- ============================================================================
-- 用户表索引
-- ============================================================================

-- 邮箱索引（唯一，用于登录）
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 用户名索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- 创建时间索引（用于排序和范围查询）
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- 状态索引（用于筛选活跃用户）
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status) WHERE status = 'active';

-- 复合索引（状态 + 创建时间）
CREATE INDEX IF NOT EXISTS idx_users_status_created ON users(status, created_at DESC);

-- 邮箱小写索引（不区分大小写查询）
CREATE INDEX IF NOT EXISTS idx_users_email_lower ON users(LOWER(email));

-- ============================================================================
-- 任务表索引
-- ============================================================================

-- 任务状态索引
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- 用户ID索引（外键）
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);

-- 更新时间索引
CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at DESC);

-- 复合索引（用户ID + 状态）
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);

-- 复合索引（状态 + 创建时间）
CREATE INDEX IF NOT EXISTS idx_tasks_status_created ON tasks(status, created_at DESC);

-- 部分索引（仅索引活跃任务）
CREATE INDEX IF NOT EXISTS idx_tasks_active ON tasks(id, created_at) WHERE status IN ('pending', 'in_progress');

-- 优先级索引
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority DESC) WHERE priority IS NOT NULL;

-- ============================================================================
-- 代理表索引
-- ============================================================================

-- 代理名称索引
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);

-- 代理类型索引
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);

-- 状态索引
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_agents_created_at ON agents(created_at DESC);

-- 复合索引（类型 + 状态）
CREATE INDEX IF NOT EXISTS idx_agents_type_status ON agents(type, status);

-- ============================================================================
-- 消息表索引
-- ============================================================================

-- 发送者索引
CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);

-- 接收者索引
CREATE INDEX IF NOT EXISTS idx_messages_receiver_id ON messages(receiver_id);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);

-- 消息类型索引
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(type);

-- 复合索引（接收者 + 创建时间）
CREATE INDEX IF NOT EXISTS idx_messages_receiver_created ON messages(receiver_id, created_at DESC);

-- 复合索引（发送者 + 接收者）
CREATE INDEX IF NOT EXISTS idx_messages_sender_receiver ON messages(sender_id, receiver_id);

-- 未读消息索引
CREATE INDEX IF NOT EXISTS idx_messages_unread ON messages(receiver_id, created_at DESC) WHERE read = false;

-- ============================================================================
-- 区块链交易表索引
-- ============================================================================

-- 交易哈希索引（唯一）
CREATE UNIQUE INDEX IF NOT EXISTS idx_blockchain_tx_hash ON blockchain_transactions(transaction_hash);

-- 用户ID索引
CREATE INDEX IF NOT EXISTS idx_blockchain_user_id ON blockchain_transactions(user_id);

-- 状态索引
CREATE INDEX IF NOT EXISTS idx_blockchain_status ON blockchain_transactions(status);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_blockchain_created_at ON blockchain_transactions(created_at DESC);

-- 区块号索引
CREATE INDEX IF NOT EXISTS idx_blockchain_block_number ON blockchain_transactions(block_number) WHERE block_number IS NOT NULL;

-- 复合索引（用户ID + 状态）
CREATE INDEX IF NOT EXISTS idx_blockchain_user_status ON blockchain_transactions(user_id, status);

-- 复合索引（状态 + 创建时间）
CREATE INDEX IF NOT EXISTS idx_blockchain_status_created ON blockchain_transactions(status, created_at DESC);

-- ============================================================================
-- 日志表索引
-- ============================================================================

-- 日志级别索引
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC);

-- 用户ID索引
CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id) WHERE user_id IS NOT NULL;

-- 复合索引（级别 + 创建时间）
CREATE INDEX IF NOT EXISTS idx_logs_level_created ON logs(level, created_at DESC);

-- 错误日志索引
CREATE INDEX IF NOT EXISTS idx_logs_errors ON logs(id, created_at) WHERE level IN ('ERROR', 'CRITICAL');

-- 全文搜索索引（消息内容）
CREATE INDEX IF NOT EXISTS idx_logs_message_gin ON logs USING gin(to_tsvector('english', message));

-- ============================================================================
-- 会话表索引
-- ============================================================================

-- 会话令牌索引（唯一）
CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);

-- 用户ID索引
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

-- 过期时间索引
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- 活跃会话索引
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(user_id, expires_at) WHERE expires_at > NOW();

-- ============================================================================
-- API密钥表索引
-- ============================================================================

-- API密钥索引（唯一）
CREATE UNIQUE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(key_hash);

-- 用户ID索引
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);

-- 状态索引
CREATE INDEX IF NOT EXISTS idx_api_keys_status ON api_keys(status);

-- 过期时间索引
CREATE INDEX IF NOT EXISTS idx_api_keys_expires_at ON api_keys(expires_at) WHERE expires_at IS NOT NULL;

-- 活跃密钥索引
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(user_id) WHERE status = 'active' AND (expires_at IS NULL OR expires_at > NOW());

-- ============================================================================
-- 审计日志表索引
-- ============================================================================

-- 用户ID索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);

-- 操作类型索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- 资源类型索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);

-- 复合索引（用户ID + 创建时间）
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created ON audit_logs(user_id, created_at DESC);

-- 复合索引（资源类型 + 资源ID）
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- ============================================================================
-- 通知表索引
-- ============================================================================

-- 用户ID索引
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- 已读状态索引
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);

-- 未读通知索引
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, created_at DESC) WHERE read = false;

-- 通知类型索引
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);

-- ============================================================================
-- 文件表索引
-- ============================================================================

-- 用户ID索引
CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id);

-- 文件哈希索引
CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at DESC);

-- 文件类型索引
CREATE INDEX IF NOT EXISTS idx_files_mime_type ON files(mime_type);

-- 文件大小索引
CREATE INDEX IF NOT EXISTS idx_files_size ON files(size);

-- ============================================================================
-- 标签表索引
-- ============================================================================

-- 标签名称索引（唯一）
CREATE UNIQUE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

-- 标签类型索引
CREATE INDEX IF NOT EXISTS idx_tags_type ON tags(type);

-- ============================================================================
-- 关联表索引
-- ============================================================================

-- 任务标签关联
CREATE INDEX IF NOT EXISTS idx_task_tags_task_id ON task_tags(task_id);
CREATE INDEX IF NOT EXISTS idx_task_tags_tag_id ON task_tags(tag_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_task_tags_unique ON task_tags(task_id, tag_id);

-- 用户角色关联
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_roles_unique ON user_roles(user_id, role_id);

-- ============================================================================
-- 全文搜索索引
-- ============================================================================

-- 任务标题和描述全文搜索
CREATE INDEX IF NOT EXISTS idx_tasks_fulltext ON tasks USING gin(
    to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(description, ''))
);

-- 用户全文搜索
CREATE INDEX IF NOT EXISTS idx_users_fulltext ON users USING gin(
    to_tsvector('english', COALESCE(username, '') || ' ' || COALESCE(email, ''))
);

-- ============================================================================
-- JSONB 索引（如果有 JSONB 字段）
-- ============================================================================

-- 元数据 JSONB 索引
CREATE INDEX IF NOT EXISTS idx_tasks_metadata_gin ON tasks USING gin(metadata) WHERE metadata IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_settings_gin ON users USING gin(settings) WHERE settings IS NOT NULL;

-- ============================================================================
-- 部分索引优化（针对常见查询）
-- ============================================================================

-- 最近7天的任务
CREATE INDEX IF NOT EXISTS idx_tasks_recent ON tasks(created_at DESC)
WHERE created_at > NOW() - INTERVAL '7 days';

-- 高优先级未完成任务
CREATE INDEX IF NOT EXISTS idx_tasks_high_priority_pending ON tasks(priority DESC, created_at DESC)
WHERE status IN ('pending', 'in_progress') AND priority >= 8;

-- 最近活跃用户
CREATE INDEX IF NOT EXISTS idx_users_recent_active ON users(last_login_at DESC)
WHERE last_login_at > NOW() - INTERVAL '30 days';

-- ============================================================================
-- 索引维护建议
-- ============================================================================

-- 查看索引使用情况
COMMENT ON INDEX idx_users_email IS '用户邮箱唯一索引，用于登录验证';
COMMENT ON INDEX idx_tasks_status_created IS '任务状态和创建时间复合索引，用于任务列表查询';
COMMENT ON INDEX idx_blockchain_tx_hash IS '区块链交易哈希唯一索引';

-- ============================================================================
-- 完成消息
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '索引创建完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '已创建的索引类型:';
    RAISE NOTICE '- B-tree 索引: 用于等值和范围查询';
    RAISE NOTICE '- GIN 索引: 用于全文搜索和 JSONB';
    RAISE NOTICE '- 部分索引: 用于特定条件的查询优化';
    RAISE NOTICE '- 唯一索引: 确保数据唯一性';
    RAISE NOTICE '';
    RAISE NOTICE '建议定期执行:';
    RAISE NOTICE '1. ANALYZE - 更新统计信息';
    RAISE NOTICE '2. REINDEX - 重建索引';
    RAISE NOTICE '3. 监控索引使用情况';
    RAISE NOTICE '========================================';
END $$;

-- 显示索引统计
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC
LIMIT 20;

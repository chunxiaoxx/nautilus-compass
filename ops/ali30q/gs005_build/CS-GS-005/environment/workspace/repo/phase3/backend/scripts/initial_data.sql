-- ============================================================================
-- 初始数据导入脚本
-- ============================================================================
-- 功能: 为生产环境导入初始数据
-- 版本: 1.0.0
-- 创建日期: 2026-02-27
-- ============================================================================

BEGIN;

-- ============================================================================
-- 系统配置数据
-- ============================================================================

-- 创建系统配置表（如果不存在）
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入系统配置
INSERT INTO system_config (key, value, description) VALUES
    ('app_name', 'Nautilus', '应用名称'),
    ('app_version', '1.0.0', '应用版本'),
    ('maintenance_mode', 'false', '维护模式'),
    ('max_upload_size', '10485760', '最大上传大小（字节）'),
    ('session_timeout', '3600', '会话超时时间（秒）'),
    ('password_min_length', '8', '密码最小长度'),
    ('password_require_special', 'true', '密码需要特殊字符'),
    ('max_login_attempts', '5', '最大登录尝试次数'),
    ('lockout_duration', '900', '账户锁定时长（秒）')
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- 角色和权限数据
-- ============================================================================

-- 创建角色表（如果不存在）
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认角色
INSERT INTO roles (name, description) VALUES
    ('admin', '系统管理员，拥有所有权限'),
    ('user', '普通用户，基本权限'),
    ('readonly', '只读用户，仅查看权限'),
    ('developer', '开发者，开发和测试权限'),
    ('operator', '运维人员，运维相关权限')
ON CONFLICT (name) DO NOTHING;

-- 创建权限表（如果不存在）
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认权限
INSERT INTO permissions (name, resource, action, description) VALUES
    ('users.read', 'users', 'read', '查看用户信息'),
    ('users.create', 'users', 'create', '创建用户'),
    ('users.update', 'users', 'update', '更新用户信息'),
    ('users.delete', 'users', 'delete', '删除用户'),
    ('tasks.read', 'tasks', 'read', '查看任务'),
    ('tasks.create', 'tasks', 'create', '创建任务'),
    ('tasks.update', 'tasks', 'update', '更新任务'),
    ('tasks.delete', 'tasks', 'delete', '删除任务'),
    ('agents.read', 'agents', 'read', '查看代理'),
    ('agents.create', 'agents', 'create', '创建代理'),
    ('agents.update', 'agents', 'update', '更新代理'),
    ('agents.delete', 'agents', 'delete', '删除代理'),
    ('system.config', 'system', 'config', '系统配置'),
    ('system.monitor', 'system', 'monitor', '系统监控'),
    ('blockchain.read', 'blockchain', 'read', '查看区块链交易'),
    ('blockchain.create', 'blockchain', 'create', '创建区块链交易')
ON CONFLICT (name) DO NOTHING;

-- 创建角色权限关联表（如果不存在）
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- 为管理员角色分配所有权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- 为普通用户分配基本权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'user'
AND p.action IN ('read', 'create', 'update')
AND p.resource IN ('tasks', 'agents')
ON CONFLICT DO NOTHING;

-- 为只读用户分配查看权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'readonly'
AND p.action = 'read'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 代理类型数据
-- ============================================================================

-- 创建代理类型表（如果不存在）
CREATE TABLE IF NOT EXISTS agent_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    capabilities JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认代理类型
INSERT INTO agent_types (name, description, capabilities) VALUES
    ('task_executor', '任务执行代理', '{"execute": true, "schedule": true, "monitor": true}'::jsonb),
    ('data_processor', '数据处理代理', '{"process": true, "transform": true, "validate": true}'::jsonb),
    ('monitor', '监控代理', '{"monitor": true, "alert": true, "report": true}'::jsonb),
    ('coordinator', '协调代理', '{"coordinate": true, "delegate": true, "aggregate": true}'::jsonb),
    ('blockchain_agent', '区块链代理', '{"blockchain": true, "smart_contract": true, "transaction": true}'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 任务状态数据
-- ============================================================================

-- 创建任务状态表（如果不存在）
CREATE TABLE IF NOT EXISTS task_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_final BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入任务状态
INSERT INTO task_statuses (name, description, is_final) VALUES
    ('pending', '等待执行', false),
    ('in_progress', '执行中', false),
    ('paused', '已暂停', false),
    ('completed', '已完成', true),
    ('failed', '执行失败', true),
    ('cancelled', '已取消', true)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 通知模板数据
-- ============================================================================

-- 创建通知模板表（如果不存在）
CREATE TABLE IF NOT EXISTS notification_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    subject VARCHAR(255),
    body TEXT NOT NULL,
    variables JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入通知模板
INSERT INTO notification_templates (name, type, subject, body, variables) VALUES
    ('welcome_email', 'email', 'Welcome to Nautilus',
     'Hello {{username}},\n\nWelcome to Nautilus! Your account has been created successfully.\n\nBest regards,\nNautilus Team',
     '{"username": "string"}'::jsonb),
    ('task_completed', 'notification', 'Task Completed',
     'Your task "{{task_name}}" has been completed successfully.',
     '{"task_name": "string"}'::jsonb),
    ('task_failed', 'notification', 'Task Failed',
     'Your task "{{task_name}}" has failed. Error: {{error_message}}',
     '{"task_name": "string", "error_message": "string"}'::jsonb),
    ('password_reset', 'email', 'Password Reset Request',
     'Hello {{username}},\n\nYou requested a password reset. Click the link below to reset your password:\n{{reset_link}}\n\nIf you did not request this, please ignore this email.',
     '{"username": "string", "reset_link": "string"}'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 区块链网络配置
-- ============================================================================

-- 创建区块链网络表（如果不存在）
CREATE TABLE IF NOT EXISTS blockchain_networks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    chain_id INTEGER NOT NULL,
    rpc_url TEXT NOT NULL,
    explorer_url TEXT,
    is_testnet BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入区块链网络配置
INSERT INTO blockchain_networks (name, chain_id, rpc_url, explorer_url, is_testnet, is_active) VALUES
    ('Ethereum Mainnet', 1, 'https://mainnet.infura.io/v3/YOUR_KEY', 'https://etherscan.io', false, false),
    ('Sepolia Testnet', 11155111, 'https://sepolia.infura.io/v3/YOUR_KEY', 'https://sepolia.etherscan.io', true, true),
    ('Polygon Mainnet', 137, 'https://polygon-rpc.com', 'https://polygonscan.com', false, false),
    ('Mumbai Testnet', 80001, 'https://rpc-mumbai.maticvigil.com', 'https://mumbai.polygonscan.com', true, true)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 审计事件类型
-- ============================================================================

-- 创建审计事件类型表（如果不存在）
CREATE TABLE IF NOT EXISTS audit_event_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入审计事件类型
INSERT INTO audit_event_types (name, category, severity, description) VALUES
    ('user.login', 'authentication', 'info', '用户登录'),
    ('user.logout', 'authentication', 'info', '用户登出'),
    ('user.login_failed', 'authentication', 'warning', '用户登录失败'),
    ('user.created', 'user_management', 'info', '创建用户'),
    ('user.updated', 'user_management', 'info', '更新用户'),
    ('user.deleted', 'user_management', 'warning', '删除用户'),
    ('task.created', 'task_management', 'info', '创建任务'),
    ('task.updated', 'task_management', 'info', '更新任务'),
    ('task.deleted', 'task_management', 'warning', '删除任务'),
    ('config.updated', 'system', 'warning', '更新系统配置'),
    ('permission.granted', 'security', 'warning', '授予权限'),
    ('permission.revoked', 'security', 'warning', '撤销权限'),
    ('blockchain.transaction', 'blockchain', 'info', '区块链交易'),
    ('data.exported', 'data', 'warning', '数据导出'),
    ('backup.created', 'system', 'info', '创建备份')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 系统健康检查配置
-- ============================================================================

-- 创建健康检查配置表（如果不存在）
CREATE TABLE IF NOT EXISTS health_check_config (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    interval_seconds INTEGER DEFAULT 60,
    timeout_seconds INTEGER DEFAULT 10,
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入健康检查配置
INSERT INTO health_check_config (name, endpoint, interval_seconds, timeout_seconds) VALUES
    ('database', '/health/database', 60, 5),
    ('redis', '/health/redis', 60, 5),
    ('blockchain', '/health/blockchain', 300, 30),
    ('api', '/health/api', 30, 5),
    ('storage', '/health/storage', 120, 10)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 创建视图
-- ============================================================================

-- 用户角色权限视图
CREATE OR REPLACE VIEW user_permissions_view AS
SELECT
    u.id as user_id,
    u.username,
    r.name as role_name,
    p.name as permission_name,
    p.resource,
    p.action
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id;

-- 任务统计视图
CREATE OR REPLACE VIEW task_statistics_view AS
SELECT
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_tasks,
    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_tasks,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as tasks_last_24h
FROM tasks;

-- ============================================================================
-- 创建函数
-- ============================================================================

-- 更新 updated_at 时间戳函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为所有有 updated_at 字段的表创建触发器
DO $$
DECLARE
    t record;
BEGIN
    FOR t IN
        SELECT table_name
        FROM information_schema.columns
        WHERE column_name = 'updated_at'
        AND table_schema = 'public'
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%I_updated_at ON %I;
            CREATE TRIGGER update_%I_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', t.table_name, t.table_name, t.table_name, t.table_name);
    END LOOP;
END $$;

-- ============================================================================
-- 完成消息
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '初始数据导入完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '已导入的数据:';
    RAISE NOTICE '- 系统配置';
    RAISE NOTICE '- 角色和权限';
    RAISE NOTICE '- 代理类型';
    RAISE NOTICE '- 任务状态';
    RAISE NOTICE '- 通知模板';
    RAISE NOTICE '- 区块链网络配置';
    RAISE NOTICE '- 审计事件类型';
    RAISE NOTICE '- 健康检查配置';
    RAISE NOTICE '';
    RAISE NOTICE '已创建的视图:';
    RAISE NOTICE '- user_permissions_view';
    RAISE NOTICE '- task_statistics_view';
    RAISE NOTICE '';
    RAISE NOTICE '已创建的函数和触发器:';
    RAISE NOTICE '- update_updated_at_column()';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

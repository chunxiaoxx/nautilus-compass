-- ============================================================================
-- 创建测试用户脚本
-- ============================================================================
-- 功能: 为测试环境创建3个测试用户
-- 版本: 1.0.0
-- 创建日期: 2026-03-01
-- ============================================================================

BEGIN;

-- 插入测试用户
-- 密码: password123 (bcrypt加密)
-- 注意: 这些是测试用户，不应在生产环境使用

INSERT INTO users (username, email, hashed_password, wallet_address, is_active, is_admin, created_at, updated_at)
VALUES
    (
        'alice',
        'alice@example.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILCpnple6',
        '0x1111111111111111111111111111111111111111',
        true,
        false,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        'bob',
        'bob@example.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILCpnple6',
        '0x2222222222222222222222222222222222222222',
        true,
        false,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        'charlie',
        'charlie@example.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILCpnple6',
        '0x3333333333333333333333333333333333333333',
        true,
        false,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
ON CONFLICT (username) DO NOTHING;

-- 验证插入结果
DO $$
DECLARE
    user_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count
    FROM users
    WHERE username IN ('alice', 'bob', 'charlie');

    RAISE NOTICE '========================================';
    RAISE NOTICE '测试用户创建完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '已创建 % 个测试用户', user_count;
    RAISE NOTICE '';
    RAISE NOTICE '用户信息:';
    RAISE NOTICE '1. alice@example.com / password123';
    RAISE NOTICE '2. bob@example.com / password123';
    RAISE NOTICE '3. charlie@example.com / password123';
    RAISE NOTICE '';
    RAISE NOTICE '注意: 这些是测试账户，请勿在生产环境使用！';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

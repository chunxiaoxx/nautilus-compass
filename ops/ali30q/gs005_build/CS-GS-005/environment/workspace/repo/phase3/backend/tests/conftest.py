"""
Pytest配置文件
提供全局fixtures和配置
"""

import pytest
import sys
import os

# 在导入任何应用模块之前设置测试环境变量
# 使用PostgreSQL测试数据库（与生产环境一致）
os.environ["DATABASE_URL"] = "postgresql://nautilus:nautilus_staging_2024@localhost:5432/nautilus_test"
os.environ["REDIS_HOST"] = "redis"  # 修复Redis连接
os.environ["REDIS_PORT"] = "6379"
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET"] = "test-jwt-secret-key-for-testing-purposes-minimum-32-characters-long"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRATION"] = "86400"
os.environ["CSRF_SECRET_KEY"] = "test-csrf-secret-key-for-testing-purposes-minimum-32-characters-long"
# 禁用速率限制（测试环境）
os.environ["RATE_LIMIT_ENABLED"] = "false"

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_configure(config):
    """Pytest配置钩子"""
    # 注册自定义标记
    config.addinivalue_line(
        "markers", "blockchain: mark test as blockchain integration test"
    )
    config.addinivalue_line(
        "markers", "mock: mark test as mock test (no real blockchain)"
    )
    config.addinivalue_line(
        "markers", "testnet: mark test as testnet integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 自动标记区块链测试
        if "test_blockchain_integration" in str(item.fspath):
            item.add_marker(pytest.mark.blockchain)

            # 标记端到端测试为testnet
            if "test_e2e" in item.name or "TestEndToEndIntegration" in str(item.parent):
                item.add_marker(pytest.mark.testnet)
            else:
                item.add_marker(pytest.mark.mock)

            # 标记性能测试为slow
            if "TestPerformanceAndStress" in str(item.parent):
                item.add_marker(pytest.mark.slow)

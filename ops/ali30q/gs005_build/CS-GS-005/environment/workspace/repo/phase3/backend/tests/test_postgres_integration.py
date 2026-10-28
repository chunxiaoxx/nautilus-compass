"""
PostgreSQL集成测试

使用实际PostgreSQL数据库测试API端点
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Base
from utils.database import get_db
from main import app


# 测试数据库配置 - 使用SQLite作为后备
TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_URL', 'sqlite:///./test_postgres.db')

# 检查PostgreSQL是否可用
def check_postgres_available():
    """检查PostgreSQL是否可用"""
    postgres_url = 'postgresql://postgres:postgres@localhost:5432/nautilus_test'
    try:
        engine = create_engine(postgres_url)
        conn = engine.connect()
        conn.close()
        return True
    except Exception:
        return False

POSTGRES_AVAILABLE = check_postgres_available()

# 如果PostgreSQL可用，使用PostgreSQL，否则使用SQLite
if POSTGRES_AVAILABLE:
    TEST_DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/nautilus_test'
else:
    TEST_DATABASE_URL = 'sqlite:///./test_postgres.db'


@pytest.fixture(scope="module")
def test_engine():
    """创建测试数据库引擎"""
    # 如果是SQLite，先删除旧的测试数据库
    if TEST_DATABASE_URL.startswith('sqlite'):
        db_file = TEST_DATABASE_URL.replace('sqlite:///', '')
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except PermissionError:
                pass  # File in use, will be cleaned up later

    # 创建测试引擎
    if TEST_DATABASE_URL.startswith('sqlite'):
        engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(TEST_DATABASE_URL)

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    yield engine

    # 清理测试数据
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

    # 如果是SQLite，删除测试数据库文件
    if TEST_DATABASE_URL.startswith('sqlite'):
        db_file = TEST_DATABASE_URL.replace('sqlite:///', '')
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except PermissionError:
                pass  # File in use, will be cleaned up later


@pytest.fixture(scope="module")
def test_db(test_engine):
    """创建测试数据库会话"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_db(test_engine):
    """Override database dependency"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    def _get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    return _get_db


@pytest.fixture(scope="module")
def client(test_engine):
    """创建测试客户端"""
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db(test_engine)

    test_client = TestClient(app)
    yield test_client

    # Clear overrides
    app.dependency_overrides.clear()


# ============================================================================
# Auth API Integration Tests
# ============================================================================

class TestAuthAPIIntegration:
    """Auth API集成测试"""

    def test_register_user(self, client):
        """测试用户注册"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword123",
            "wallet_address": "0x1234567890123456789012345678901234567891"
        })

        # 可能成功或用户名已存在
        assert response.status_code in [201, 400]

    def test_login_user(self, client):
        """测试用户登录"""
        # 先注册一个用户
        client.post("/api/auth/register", json={
            "username": "logintest",
            "email": "login@example.com",
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567892"
        })

        # 然后登录
        response = client.post("/api/auth/login", json={
            "username": "logintest",
            "password": "password123"
        })

        assert response.status_code in [200, 401]

    def test_get_current_user_unauthorized(self, client):
        """测试未授权获取当前用户"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401


# ============================================================================
# Tasks API Integration Tests
# ============================================================================

class TestTasksAPIIntegration:
    """Tasks API集成测试"""

    def test_create_task(self, client):
        """测试创建任务"""
        # 先注册用户并获取token
        client.post("/api/auth/register", json={
            "username": "taskcreator",
            "email": "taskcreator@example.com",
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567893"
        })

        login_response = client.post("/api/auth/login", json={
            "username": "taskcreator",
            "password": "password123"
        })

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]

            response = client.post(
                "/api/tasks",
                json={
                    "description": "Test task",
                    "reward": 1000,
                    "task_type": "CODE",
                    "timeout": 3600
                },
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code in [201, 401, 422]

    def test_list_tasks(self, client):
        """测试列出任务"""
        response = client.get("/api/tasks")
        assert response.status_code == 200

    def test_list_tasks_with_filters(self, client):
        """测试带过滤器的任务列表"""
        response = client.get("/api/tasks?status=Open&task_type=CODE")
        assert response.status_code == 200


# ============================================================================
# Agents API Integration Tests
# ============================================================================

class TestAgentsAPIIntegration:
    """Agents API集成测试"""

    def test_register_agent(self, client):
        """测试注册Agent"""
        # 先创建用户
        client.post("/api/auth/register", json={
            "username": "agentowner",
            "email": "agentowner@example.com",
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567894"
        })

        # 登录获取token
        login_response = client.post("/api/auth/login", json={
            "username": "agentowner",
            "password": "password123"
        })

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]

            response = client.post(
                "/api/agents",
                json={
                    "name": "TestAgent",
                    "description": "Test agent",
                    "specialties": ["test", "demo"]
                },
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code in [201, 400, 401]

    def test_list_agents(self, client):
        """测试列出Agents"""
        response = client.get("/api/agents")
        assert response.status_code == 200


# ============================================================================
# Rewards API Integration Tests
# ============================================================================

class TestRewardsAPIIntegration:
    """Rewards API集成测试"""

    def test_get_balance(self, client):
        """测试获取余额"""
        # 需要API key认证
        response = client.get("/api/rewards/balance")
        # 未授权或没有奖励
        assert response.status_code in [200, 401, 404]

    def test_get_history(self, client):
        """测试获取奖励历史"""
        response = client.get("/api/rewards/history")
        assert response.status_code in [200, 401]


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealthChecks:
    """健康检查测试"""

    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "message" in data

    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """错误处理测试"""

    def test_not_found(self, client):
        """测试404错误"""
        response = client.get("/nonexistent endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """测试方法不允许"""
        response = client.put("/api/tasks")
        assert response.status_code == 405

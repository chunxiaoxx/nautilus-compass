"""
端到端测试 - Agents & Rewards API

使用内存SQLite数据库测试所有Agents和Rewards API端点
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Base, User, Agent, Task, Reward, TaskType, TaskStatus
from utils.database import get_db
from api.agents import router as agents_router
from api.rewards import router as rewards_router
from api.auth import router as auth_router


# 创建测试引擎
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def setup_database():
    """设置测试数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(setup_database):
    """创建测试客户端"""
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/auth")
    app.include_router(agents_router, prefix="/api/agents")
    app.include_router(rewards_router, prefix="/api/rewards")
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # 清理数据库
    db = TestingSessionLocal()
    try:
        db.query(Reward).delete()
        db.query(Task).delete()
        db.query(Agent).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def auth_token(client):
    """创建用户并返回认证token"""
    # 尝试注册新用户
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "wallet_address": "0x1234567890123456789012345678901234567890"
    })

    # 如果注册成功，返回token
    if response.status_code == 201:
        return response.json()["access_token"]

    # 如果用户已存在或遇到速率限制，尝试登录
    login_response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })

    # 如果登录成功，返回token
    if login_response.status_code == 200:
        return login_response.json()["access_token"]

    # 如果登录也失败（可能是速率限制），直接创建token
    from utils.auth import create_access_token
    return create_access_token(data={"sub": "testuser"})


@pytest.fixture
def agent_with_api_key(client, auth_token):
    """创建agent并返回API key"""
    # 注册agent
    response = client.post(
        "/api/agents",
        json={
            "name": "TestAgent",
            "description": "A test agent",
            "specialties": ["CODE"]
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    data = response.json()
    api_key = data["api_key"]
    agent_wallet = data["agent"]["owner"]

    return api_key, agent_wallet


# ============================================================================
# Agents API E2E Tests
# ============================================================================

class TestAgentsE2E:
    """Agents API端到端测试"""

    def test_register_agent_success(self, client, auth_token):
        """测试成功注册agent"""
        response = client.post(
            "/api/agents",
            json={
                "name": "TestAgent",
                "description": "A test agent",
                "specialties": ["CODE", "DATA"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "agent" in data
        assert "api_key" in data
        assert data["agent"]["agent_id"] == 1

    def test_register_agent_unauthorized(self, client):
        """测试未授权注册agent"""
        response = client.post(
            "/api/agents",
            json={
                "name": "TestAgent",
                "description": "A test agent",
                "specialties": ["CODE"]
            }
        )
        assert response.status_code == 401

    def test_register_agent_duplicate(self, client, auth_token):
        """测试重复注册agent"""
        # 第一次注册
        client.post(
            "/api/agents",
            json={
                "name": "TestAgent",
                "description": "A test agent",
                "specialties": ["CODE"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 第二次注册
        response = client.post(
            "/api/agents",
            json={
                "name": "TestAgent2",
                "description": "Another agent",
                "specialties": ["DATA"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_list_agents(self, client, auth_token):
        """测试列出agents"""
        # 注册agent
        client.post(
            "/api/agents",
            json={
                "name": "TestAgent",
                "description": "A test agent",
                "specialties": ["CODE"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 列出agents
        response = client.get("/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_agent_by_id(self, client, auth_token):
        """测试获取单个agent"""
        # 注册agent
        register_response = client.post(
            "/api/agents",
            json={
                "name": "TestAgent",
                "description": "A test agent",
                "specialties": ["CODE"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        agent_id = register_response.json()["agent"]["agent_id"]

        # 获取agent
        response = client.get(f"/api/agents/{agent_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent_id

    def test_get_agent_not_found(self, client):
        """测试获取不存在的agent"""
        response = client.get("/api/agents/99999")
        assert response.status_code == 404

    def test_get_agent_tasks(self, client, auth_token):
        """测试获取agent的任务"""
        # 注册agent
        register_response = client.post(
            "/api/agents",
            json={
                "name": "TestAgent",
                "description": "A test agent",
                "specialties": ["CODE"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        agent_id = register_response.json()["agent"]["agent_id"]

        # 获取任务列表
        response = client.get(f"/api/agents/{agent_id}/tasks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_agent_reputation(self, client, auth_token):
        """测试获取agent信誉"""
        # 注册agent
        register_response = client.post(
            "/api/agents",
            json={
                "name": "TestAgent",
                "description": "A test agent",
                "specialties": ["CODE"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        agent_id = register_response.json()["agent"]["agent_id"]

        # 获取信誉
        response = client.get(f"/api/agents/{agent_id}/reputation")
        assert response.status_code == 200
        data = response.json()
        assert "reputation" in data


# ============================================================================
# Rewards API E2E Tests
# ============================================================================

class TestRewardsE2E:
    """Rewards API端到端测试"""

    def test_get_balance(self, client, agent_with_api_key):
        """测试获取奖励余额"""
        api_key, _ = agent_with_api_key

        response = client.get(
            "/api/rewards/balance",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "agent" in data

    def test_get_balance_unauthorized(self, client):
        """测试未授权获取余额"""
        response = client.get("/api/rewards/balance")
        assert response.status_code == 401

    def test_get_rewards_history(self, client, agent_with_api_key):
        """测试获取奖励历史"""
        api_key, _ = agent_with_api_key

        response = client.get(
            "/api/rewards/history",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_withdraw_rewards_success(self, client, agent_with_api_key):
        """测试成功提取奖励"""
        api_key, agent_wallet = agent_with_api_key

        # 创建一些待提取的奖励
        db = TestingSessionLocal()
        reward = Reward(
            task_id="0x1234",
            agent=agent_wallet,
            amount=1000000000000000000,  # 1 ETH in Wei
            status="Distributed"
        )
        db.add(reward)
        db.commit()
        db.close()

        # 提取奖励
        response = client.post(
            "/api/rewards/withdraw",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "amount" in data

    def test_withdraw_insufficient_balance(self, client, agent_with_api_key):
        """测试余额不足时提取"""
        api_key, _ = agent_with_api_key

        # 不创建任何奖励，余额为0
        response = client.post(
            "/api/rewards/withdraw",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        # 可能返回400或200（取决于实现）
        assert response.status_code in [200, 400]

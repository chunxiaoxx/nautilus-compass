"""
API密钥管理端到端测试
测试 POST /api/agents/api-keys 端点
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from models.database import Base, User, Agent, APIKey
from utils.database import get_db
from utils.auth import create_access_token

# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def client():
    """创建测试客户端"""
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_with_agent(client):
    """创建测试用户和agent"""
    db = TestingSessionLocal()

    # 创建用户
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        wallet_address="0x1234567890123456789012345678901234567890",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 创建agent
    agent = Agent(
        agent_id=1,
        owner=user.wallet_address,
        name="TestAgent",
        description="Test agent",
        specialties='["CODE"]',
        reputation=100,
        completed_tasks=0,
        failed_tasks=0,
        current_tasks=0
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)

    # 生成JWT token
    token = create_access_token(data={"sub": user.username})

    db.close()
    return {
        "user": user,
        "agent": agent,
        "token": token
    }


class TestAPIKeyManagement:
    """API密钥管理测试"""

    def test_create_api_key_success(self, client, test_user_with_agent):
        """测试成功创建API密钥"""
        token = test_user_with_agent["token"]

        response = client.post(
            "/api/agents/api-keys",
            json={
                "name": "Test API Key",
                "description": "For testing purposes"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "api_key" in data
        assert data["api_key"].startswith("nau_")
        assert "name" in data
        assert data["name"] == "Test API Key"

    def test_create_api_key_unauthorized(self, client):
        """测试未授权创建API密钥"""
        response = client.post(
            "/api/agents/api-keys",
            json={
                "name": "Test API Key",
                "description": "For testing purposes"
            }
        )

        assert response.status_code == 401

    def test_create_api_key_no_agent(self, client):
        """测试没有agent的用户创建API密钥"""
        db = TestingSessionLocal()

        # 创建没有agent的用户
        user = User(
            username="noagentuser",
            email="noagent@example.com",
            hashed_password="hashed_password",
            wallet_address="0x9999999999999999999999999999999999999999",
            is_active=True
        )
        db.add(user)
        db.commit()

        token = create_access_token(data={"sub": user.username})
        db.close()

        response = client.post(
            "/api/agents/api-keys",
            json={
                "name": "Test API Key",
                "description": "For testing purposes"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_multiple_api_keys(self, client, test_user_with_agent):
        """测试创建多个API密钥"""
        token = test_user_with_agent["token"]

        # 创建第一个API密钥
        response1 = client.post(
            "/api/agents/api-keys",
            json={
                "name": "API Key 1",
                "description": "First key"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response1.status_code == 201
        key1 = response1.json()["api_key"]

        # 创建第二个API密钥
        response2 = client.post(
            "/api/agents/api-keys",
            json={
                "name": "API Key 2",
                "description": "Second key"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response2.status_code == 201
        key2 = response2.json()["api_key"]

        # 确保两个密钥不同
        assert key1 != key2

    def test_api_key_format(self, client, test_user_with_agent):
        """测试API密钥格式"""
        token = test_user_with_agent["token"]

        response = client.post(
            "/api/agents/api-keys",
            json={
                "name": "Format Test Key",
                "description": "Testing key format"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        api_key = response.json()["api_key"]

        # 验证格式
        assert api_key.startswith("nau_")
        assert len(api_key) > 40  # 确保有足够的随机性
        assert api_key.replace("nau_", "").replace("_", "").isalnum()

    def test_use_api_key_for_authentication(self, client, test_user_with_agent):
        """测试使用API密钥进行认证"""
        token = test_user_with_agent["token"]

        # 创建API密钥
        response = client.post(
            "/api/agents/api-keys",
            json={
                "name": "Auth Test Key",
                "description": "For authentication testing"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        api_key = response.json()["api_key"]

        # 使用API密钥访问需要agent认证的端点
        balance_response = client.get(
            "/api/rewards/balance",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        # 应该能够成功访问
        assert balance_response.status_code == 200

    def test_api_key_with_empty_name(self, client, test_user_with_agent):
        """测试空名称创建API密钥"""
        token = test_user_with_agent["token"]

        response = client.post(
            "/api/agents/api-keys",
            json={
                "name": "",
                "description": "Empty name test"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        # 应该返回验证错误
        assert response.status_code in [400, 422]

    def test_api_key_with_long_name(self, client, test_user_with_agent):
        """测试超长名称创建API密钥"""
        token = test_user_with_agent["token"]

        long_name = "A" * 256  # 256个字符

        response = client.post(
            "/api/agents/api-keys",
            json={
                "name": long_name,
                "description": "Long name test"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        # 应该成功或返回验证错误
        assert response.status_code in [201, 400, 422]

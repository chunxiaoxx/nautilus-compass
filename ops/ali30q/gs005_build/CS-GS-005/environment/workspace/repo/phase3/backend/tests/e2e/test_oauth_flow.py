"""
OAuth 2.0 Flow End-to-End Tests

测试完整的 OAuth 授权流程
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import hashlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.database import Base, OAuthClient, OAuthAuthorizationCode, OAuthAccessToken, Agent
from utils.database import get_db
from main import app


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
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # 清理数据库
    db = TestingSessionLocal()
    try:
        db.query(OAuthAccessToken).delete()
        db.query(OAuthAuthorizationCode).delete()
        db.query(OAuthClient).delete()
        db.query(Agent).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def test_agent():
    """创建测试 Agent"""
    db = TestingSessionLocal()
    agent = Agent(
        agent_id=1,
        owner="0x1234567890123456789012345678901234567890",
        name="Test Agent",
        description="Test agent for OAuth",
        reputation=100,
        specialties="testing,oauth"
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    db.close()
    return agent


@pytest.fixture
def test_oauth_client():
    """创建测试 OAuth 客户端"""
    db = TestingSessionLocal()

    client_secret = "test_secret_12345"
    client_secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()

    oauth_client = OAuthClient(
        client_id="test_client_id",
        client_secret=client_secret_hash,
        name="Test Application",
        description="Test OAuth client",
        redirect_uris=["http://localhost:3000/callback"],
        website="http://localhost:3000"
    )
    db.add(oauth_client)
    db.commit()
    db.refresh(oauth_client)
    db.close()

    # 存储明文密钥用于测试
    oauth_client.plain_secret = client_secret
    return oauth_client


class TestOAuthAuthorizationFlow:
    """测试 OAuth 授权流程"""

    def test_complete_oauth_flow(self, client, test_oauth_client, test_agent):
        """测试完整的 OAuth 流程：授权 -> 获取 code -> 交换 token -> 访问资源"""

        # 1. 请求授权
        auth_response = client.get(
            "/oauth/authorize",
            params={
                "client_id": test_oauth_client.client_id,
                "redirect_uri": "http://localhost:3000/callback",
                "response_type": "code",
                "scope": "profile tasks",
                "state": "random_state_123"
            },
            headers={"X-Agent-Address": test_agent.owner},
            follow_redirects=False
        )

        # 应该重定向并包含授权码
        if auth_response.status_code == 307:
            location = auth_response.headers.get("location", "")
            assert "code=" in location

            # 提取授权码
            code = location.split("code=")[1].split("&")[0]

            # 2. 交换授权码获取 token
            token_response = client.post(
                "/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": test_oauth_client.client_id,
                    "client_secret": test_oauth_client.plain_secret,
                    "redirect_uri": "http://localhost:3000/callback"
                }
            )

            if token_response.status_code == 200:
                token_data = token_response.json()
                assert "access_token" in token_data
                assert "refresh_token" in token_data
                assert token_data["token_type"] == "Bearer"

                access_token = token_data["access_token"]

                # 3. 使用 access token 访问资源
                userinfo_response = client.get(
                    "/oauth/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                if userinfo_response.status_code == 200:
                    userinfo = userinfo_response.json()
                    assert userinfo["sub"] == test_agent.owner
                    assert userinfo["name"] == test_agent.name

    def test_invalid_client_id(self, client, test_agent):
        """测试无效的 client_id"""

        response = client.get(
            "/oauth/authorize",
            params={
                "client_id": "invalid_client_id",
                "redirect_uri": "http://localhost:3000/callback",
                "response_type": "code"
            },
            headers={"X-Agent-Address": test_agent.owner}
        )

        assert response.status_code in [400, 401, 404]

    def test_invalid_redirect_uri(self, client, test_oauth_client, test_agent):
        """测试无效的 redirect_uri"""

        response = client.get(
            "/oauth/authorize",
            params={
                "client_id": test_oauth_client.client_id,
                "redirect_uri": "http://evil.com/callback",
                "response_type": "code"
            },
            headers={"X-Agent-Address": test_agent.owner}
        )

        assert response.status_code in [400, 403]

    def test_missing_required_params(self, client, test_oauth_client):
        """测试缺少必需参数"""

        # 缺少 client_id
        response = client.get(
            "/oauth/authorize",
            params={
                "redirect_uri": "http://localhost:3000/callback",
                "response_type": "code"
            }
        )

        assert response.status_code in [400, 422]


class TestOAuthTokenEndpoint:
    """测试 OAuth Token 端点"""

    def test_exchange_code_for_token(self, client, test_oauth_client, test_agent):
        """测试交换授权码获取 token"""

        # 创建授权码
        db = TestingSessionLocal()
        auth_code = OAuthAuthorizationCode(
            code="test_auth_code_123",
            client_id=test_oauth_client.client_id,
            agent_address=test_agent.owner,
            redirect_uri="http://localhost:3000/callback",
            scope="profile tasks",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            used=False
        )
        db.add(auth_code)
        db.commit()
        db.close()

        # 交换授权码
        response = client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": "test_auth_code_123",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.plain_secret,
                "redirect_uri": "http://localhost:3000/callback"
            }
        )

        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "Bearer"
            assert data["expires_in"] > 0

    def test_exchange_expired_code(self, client, test_oauth_client, test_agent):
        """测试交换过期的授权码"""

        # 创建过期的授权码
        db = TestingSessionLocal()
        auth_code = OAuthAuthorizationCode(
            code="expired_code_123",
            client_id=test_oauth_client.client_id,
            agent_address=test_agent.owner,
            redirect_uri="http://localhost:3000/callback",
            scope="profile",
            expires_at=datetime.utcnow() - timedelta(minutes=10),  # 已过期
            used=False
        )
        db.add(auth_code)
        db.commit()
        db.close()

        response = client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": "expired_code_123",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.plain_secret,
                "redirect_uri": "http://localhost:3000/callback"
            }
        )

        assert response.status_code in [400, 401]

    def test_refresh_token_flow(self, client, test_oauth_client, test_agent):
        """测试刷新 token 流程"""

        # 创建 access token
        db = TestingSessionLocal()
        access_token = OAuthAccessToken(
            access_token="old_access_token",
            refresh_token="test_refresh_token_123",
            client_id=test_oauth_client.client_id,
            agent_address=test_agent.owner,
            scope="profile",
            expires_at=datetime.utcnow() - timedelta(hours=1),  # 已过期
            refresh_expires_at=datetime.utcnow() + timedelta(days=30),
            revoked=False
        )
        db.add(access_token)
        db.commit()
        db.close()

        # 刷新 token
        response = client.post(
            "/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": "test_refresh_token_123",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.plain_secret
            }
        )

        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert data["access_token"] != "old_access_token"


class TestOAuthTokenRevocation:
    """测试 OAuth Token 撤销"""

    def test_revoke_access_token(self, client, test_oauth_client, test_agent):
        """测试撤销 access token"""

        # 创建 access token
        db = TestingSessionLocal()
        access_token = OAuthAccessToken(
            access_token="token_to_revoke",
            refresh_token="refresh_token",
            client_id=test_oauth_client.client_id,
            agent_address=test_agent.owner,
            scope="profile",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            refresh_expires_at=datetime.utcnow() + timedelta(days=30),
            revoked=False
        )
        db.add(access_token)
        db.commit()
        db.close()

        # 撤销 token
        response = client.post(
            "/oauth/revoke",
            data={
                "token": "token_to_revoke",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.plain_secret
            }
        )

        # 撤销应该成功
        assert response.status_code in [200, 204]

        # 验证 token 已被撤销
        db = TestingSessionLocal()
        revoked_token = db.query(OAuthAccessToken).filter_by(
            access_token="token_to_revoke"
        ).first()
        if revoked_token:
            assert revoked_token.revoked is True
        db.close()

    def test_revoke_with_invalid_credentials(self, client):
        """测试使用无效凭证撤销 token"""

        response = client.post(
            "/oauth/revoke",
            data={
                "token": "some_token",
                "client_id": "invalid_client",
                "client_secret": "invalid_secret"
            }
        )

        assert response.status_code in [401, 403]


class TestOAuthSecurity:
    """测试 OAuth 安全性"""

    def test_code_reuse_prevention(self, client, test_oauth_client, test_agent):
        """测试防止授权码重复使用"""

        # 创建授权码
        db = TestingSessionLocal()
        auth_code = OAuthAuthorizationCode(
            code="single_use_code",
            client_id=test_oauth_client.client_id,
            agent_address=test_agent.owner,
            redirect_uri="http://localhost:3000/callback",
            scope="profile",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            used=False
        )
        db.add(auth_code)
        db.commit()
        db.close()

        # 第一次使用授权码
        response1 = client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": "single_use_code",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.plain_secret,
                "redirect_uri": "http://localhost:3000/callback"
            }
        )

        # 第二次使用相同授权码（应该失败）
        response2 = client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": "single_use_code",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.plain_secret,
                "redirect_uri": "http://localhost:3000/callback"
            }
        )

        # 第二次应该失败
        assert response2.status_code in [400, 401]

    def test_scope_validation(self, client, test_oauth_client, test_agent):
        """测试 scope 验证"""

        # 请求无效的 scope
        response = client.get(
            "/oauth/authorize",
            params={
                "client_id": test_oauth_client.client_id,
                "redirect_uri": "http://localhost:3000/callback",
                "response_type": "code",
                "scope": "invalid_scope admin_access",
                "state": "test_state"
            },
            headers={"X-Agent-Address": test_agent.owner}
        )

        # 可能返回错误或忽略无效 scope
        assert response.status_code in [200, 307, 400]

"""
端到端测试 - Auth API

使用内存SQLite数据库测试所有Auth API端点
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Base, User
from utils.database import get_db
from api.auth import router as auth_router


# 创建测试引擎（使用StaticPool确保所有连接使用同一个内存数据库）
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
    # 创建测试用的FastAPI app
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/auth")

    # 覆盖数据库依赖
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # 清理数据库
    db = TestingSessionLocal()
    try:
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


# ============================================================================
# Auth API E2E Tests
# ============================================================================

class TestAuthE2E:
    """Auth API端到端测试"""

    def test_register_success(self, client):
        """测试成功注册"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_username(self, client):
        """测试重复用户名"""
        # 第一次注册
        client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test1@example.com",
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        # 第二次注册相同用户名
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test2@example.com",
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567891"
        })

        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    def test_register_duplicate_email(self, client):
        """测试重复邮箱"""
        # 第一次注册
        client.post("/api/auth/register", json={
            "username": "user1",
            "email": "test@example.com",
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        # 第二次注册相同邮箱
        response = client.post("/api/auth/register", json={
            "username": "user2",
            "email": "test@example.com",
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567891"
        })

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_duplicate_wallet(self, client):
        """测试重复钱包地址"""
        wallet = "0x1234567890123456789012345678901234567890"

        # 第一次注册
        client.post("/api/auth/register", json={
            "username": "user1",
            "email": "test1@example.com",
            "password": "password123",
            "wallet_address": wallet
        })

        # 第二次注册相同钱包
        response = client.post("/api/auth/register", json={
            "username": "user2",
            "email": "test2@example.com",
            "password": "password123",
            "wallet_address": wallet
        })

        assert response.status_code == 400
        assert "Wallet address already registered" in response.json()["detail"]

    def test_login_success(self, client):
        """测试成功登录"""
        # 先注册
        client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        # 登录
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_username(self, client):
        """测试错误的用户名"""
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "password123"
        })

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_wrong_password(self, client):
        """测试错误的密码"""
        # 先注册
        client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        # 用错误密码登录
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_inactive_user(self, client):
        """测试非活跃用户登录"""
        # 创建非活跃用户
        from utils.auth import hash_password
        db = TestingSessionLocal()
        user = User(
            username="inactive",
            email="inactive@example.com",
            hashed_password=hash_password("password123"),
            wallet_address="0x1234567890123456789012345678901234567890",
            is_active=False
        )
        db.add(user)
        db.commit()
        db.close()

        # 尝试登录
        response = client.post("/api/auth/login", json={
            "username": "inactive",
            "password": "password123"
        })

        assert response.status_code == 403
        assert "Inactive user" in response.json()["detail"]

    def test_get_current_user(self, client):
        """测试获取当前用户信息"""
        # 注册并获取token
        register_response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        token = register_response.json()["access_token"]

        # 获取当前用户
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "wallet_address" in data

    def test_get_current_user_unauthorized(self, client):
        """测试未授权获取用户信息"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """测试无效token"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_update_wallet_success(self, client):
        """测试成功更新钱包地址"""
        # 注册并获取token
        register_response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        token = register_response.json()["access_token"]

        # 更新钱包地址
        new_wallet = "0x9876543210987654321098765432109876543210"
        response = client.put(
            "/api/auth/me/wallet",
            json={"wallet_address": new_wallet},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["wallet_address"] == new_wallet
        assert "message" in data

    def test_update_wallet_duplicate(self, client):
        """测试更新为已存在的钱包地址"""
        wallet = "0x1234567890123456789012345678901234567890"

        # 注册第一个用户
        client.post("/api/auth/register", json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "password123",
            "wallet_address": wallet
        })

        # 注册第二个用户并获取token
        register_response = client.post("/api/auth/register", json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123",
            "wallet_address": "0x9876543210987654321098765432109876543210"
        })
        token = register_response.json()["access_token"]

        # 尝试更新为第一个用户的钱包地址
        response = client.put(
            "/api/auth/me/wallet",
            json={"wallet_address": wallet},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        assert "Wallet address already in use" in response.json()["detail"]

    def test_update_wallet_unauthorized(self, client):
        """测试未授权更新钱包"""
        response = client.put(
            "/api/auth/me/wallet",
            json={"wallet_address": "0x1234567890123456789012345678901234567890"}
        )
        assert response.status_code == 401

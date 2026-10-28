"""
扩展的认证API测试 - 提升覆盖率
测试所有边界条件、错误处理和安全特性
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

from models.database import Base, User
from utils.database import get_db
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


class TestPasswordValidation:
    """密码验证测试"""

    def test_password_too_short(self, client):
        """测试密码太短"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Short1!",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        assert response.status_code == 422
        assert "at least 12 characters" in response.text

    def test_password_no_uppercase(self, client):
        """测试密码缺少大写字母"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123!",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        assert response.status_code == 422
        assert "uppercase letter" in response.text

    def test_password_no_lowercase(self, client):
        """测试密码缺少小写字母"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "PASSWORD123!",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        assert response.status_code == 422
        assert "lowercase letter" in response.text

    def test_password_no_digit(self, client):
        """测试密码缺少数字"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "PasswordTest!",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        assert response.status_code == 422
        assert "digit" in response.text

    def test_password_no_special_char(self, client):
        """测试密码缺少特殊字符"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password1234",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        assert response.status_code == 422
        assert "special character" in response.text

    def test_password_too_common(self, client):
        """测试常见弱密码"""
        weak_passwords = [
            "Password123!",
            "Admin123!",
            "Welcome123!",
            "Qwerty123!",
            "P@ssw0rd123"
        ]

        for pwd in weak_passwords:
            response = client.post("/api/auth/register", json={
                "username": f"user_{pwd}",
                "email": f"test_{pwd}@example.com",
                "password": pwd,
                "wallet_address": "0x1234567890123456789012345678901234567890"
            })
            assert response.status_code == 422
            assert "too common" in response.text

    def test_password_valid_strong(self, client):
        """测试有效的强密码"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        assert response.status_code == 201


class TestUsernameValidation:
    """用户名验证测试"""

    def test_username_empty(self, client):
        """测试空用户名"""
        response = client.post("/api/auth/register", json={
            "username": "",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        assert response.status_code == 422

    def test_username_whitespace_only(self, client):
        """测试仅空格的用户名"""
        response = client.post("/api/auth/register", json={
            "username": "   ",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        assert response.status_code == 422

    def test_username_too_long(self, client):
        """测试用户名过长"""
        response = client.post("/api/auth/register", json={
            "username": "a" * 51,
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        assert response.status_code == 422
        assert "50 characters or less" in response.text

    def test_username_max_length(self, client):
        """测试最大长度用户名"""
        response = client.post("/api/auth/register", json={
            "username": "a" * 50,
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        assert response.status_code == 201


class TestWalletValidation:
    """钱包地址验证测试"""

    def test_wallet_no_0x_prefix(self, client):
        """测试钱包地址缺少0x前缀"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "1234567890123456789012345678901234567890"
        })
        assert response.status_code == 422
        assert "must start with 0x" in response.text

    def test_wallet_wrong_length(self, client):
        """测试钱包地址长度错误"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x12345"
        })
        assert response.status_code == 422
        assert "42 characters long" in response.text

    def test_wallet_invalid_hex(self, client):
        """测试钱包地址包含非十六进制字符"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0xGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
        })
        assert response.status_code == 422
        assert "valid hexadecimal" in response.text

    def test_wallet_empty(self, client):
        """测试空钱包地址"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": ""
        })
        assert response.status_code == 422


class TestEmailValidation:
    """邮箱验证测试"""

    def test_email_invalid_format(self, client):
        """测试无效邮箱格式"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "test@",
            "test@@example.com",
            "test@example",
        ]

        for email in invalid_emails:
            response = client.post("/api/auth/register", json={
                "username": f"user_{email}",
                "email": email,
                "password": "MyStr0ng!Pass",
                "wallet_address": "0x1234567890123456789012345678901234567890"
            })
            assert response.status_code == 422


class TestRegistrationDuplicates:
    """注册重复测试"""

    def test_duplicate_username(self, client):
        """测试重复用户名"""
        # 第一次注册
        client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test1@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        # 第二次注册相同用户名
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test2@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567891"
        })
        assert response.status_code == 400
        assert "already registered" in response.text.lower()

    def test_duplicate_email(self, client):
        """测试重复邮箱"""
        # 第一次注册
        client.post("/api/auth/register", json={
            "username": "testuser1",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        # 第二次注册相同邮箱
        response = client.post("/api/auth/register", json={
            "username": "testuser2",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567891"
        })
        assert response.status_code == 400
        assert "already registered" in response.text.lower()

    def test_duplicate_wallet(self, client):
        """测试重复钱包地址"""
        # 第一次注册
        client.post("/api/auth/register", json={
            "username": "testuser1",
            "email": "test1@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        # 第二次注册相同钱包
        response = client.post("/api/auth/register", json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })
        assert response.status_code == 400
        assert "already registered" in response.text.lower()


class TestLogin:
    """登录测试"""

    def test_login_success(self, client):
        """测试成功登录"""
        # 先注册
        client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        # 登录
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "MyStr0ng!Pass"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """测试错误密码"""
        # 先注册
        client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        # 错误密码登录
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "WrongPass123!"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """测试不存在的用户"""
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "MyStr0ng!Pass"
        })
        assert response.status_code == 401

    def test_login_inactive_user(self, client):
        """测试未激活用户"""
        # 先注册
        client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        # 手动设置用户为未激活
        db = TestingSessionLocal()
        try:
            user = db.query(User).filter(User.username == "testuser").first()
            user.is_active = False
            db.commit()
        finally:
            db.close()

        # 尝试登录
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "MyStr0ng!Pass"
        })
        assert response.status_code == 401


class TestGetCurrentUser:
    """获取当前用户测试"""

    def test_get_current_user_success(self, client):
        """测试成功获取当前用户"""
        # 注册并登录
        client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "MyStr0ng!Pass"
        })
        token = login_response.json()["access_token"]

        # 获取当前用户
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_current_user_no_token(self, client):
        """测试无token获取用户"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """测试无效token"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestUpdateWallet:
    """更新钱包地址测试"""

    def test_update_wallet_success(self, client):
        """测试成功更新钱包"""
        # 注册并登录
        client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "MyStr0ng!Pass"
        })
        token = login_response.json()["access_token"]

        # 更新钱包
        response = client.put(
            "/api/auth/wallet",
            headers={"Authorization": f"Bearer {token}"},
            json={"wallet_address": "0xABCDEF1234567890123456789012345678901234"}
        )
        assert response.status_code == 200
        assert response.json()["wallet_address"] == "0xABCDEF1234567890123456789012345678901234"

    def test_update_wallet_invalid_format(self, client):
        """测试更新为无效钱包格式"""
        # 注册并登录
        client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "MyStr0ng!Pass"
        })
        token = login_response.json()["access_token"]

        # 更新为无效钱包
        response = client.put(
            "/api/auth/wallet",
            headers={"Authorization": f"Bearer {token}"},
            json={"wallet_address": "invalid"}
        )
        assert response.status_code == 422

    def test_update_wallet_duplicate(self, client):
        """测试更新为已存在的钱包"""
        # 注册两个用户
        client.post("/api/auth/register", json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        client.post("/api/auth/register", json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "MyStr0ng!Pass",
            "wallet_address": "0xABCDEF1234567890123456789012345678901234"
        })

        # user2登录
        login_response = client.post("/api/auth/login", json={
            "username": "user2",
            "password": "MyStr0ng!Pass"
        })
        token = login_response.json()["access_token"]

        # user2尝试更新为user1的钱包
        response = client.put(
            "/api/auth/wallet",
            headers={"Authorization": f"Bearer {token}"},
            json={"wallet_address": "0x1234567890123456789012345678901234567890"}
        )
        assert response.status_code == 400

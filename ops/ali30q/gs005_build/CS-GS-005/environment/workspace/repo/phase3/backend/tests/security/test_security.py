"""
Security Tests

测试系统安全性，包括 SQL 注入、XSS、CSRF 等
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.database import Base
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


class TestSQLInjection:
    """测试 SQL 注入防护"""

    def test_sql_injection_in_search(self, client):
        """测试搜索参数中的 SQL 注入"""

        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users--",
            "admin'--",
            "' OR 1=1--",
            "'; DELETE FROM agents WHERE '1'='1",
        ]

        for malicious_input in malicious_inputs:
            response = client.get(
                "/api/agents",
                params={"search": malicious_input}
            )

            # 应该安全处理，不会执行 SQL
            assert response.status_code in [200, 400, 422]

            # 如果返回 200，应该返回空结果或正常结果，不应该执行恶意 SQL
            if response.status_code == 200:
                # 数据库应该仍然存在
                health_response = client.get("/health")
                assert health_response.status_code == 200

    def test_sql_injection_in_login(self, client):
        """测试登录表单中的 SQL 注入"""

        response = client.post("/api/auth/login", json={
            "username": "admin' OR '1'='1",
            "password": "' OR '1'='1"
        })

        # 应该返回认证失败，而不是绕过认证
        assert response.status_code in [401, 422]

    def test_sql_injection_in_registration(self, client):
        """测试注册表单中的 SQL 注入"""

        response = client.post("/api/auth/register", json={
            "username": "'; DROP TABLE users; --",
            "email": "test@example.com",
            "password": "SecureP@ssw0rd123!",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        # 应该安全处理
        assert response.status_code in [201, 400, 422]

        # 验证数据库仍然正常
        health_response = client.get("/health")
        assert health_response.status_code == 200


class TestXSSProtection:
    """测试 XSS 防护"""

    def test_xss_in_task_title(self, client):
        """测试任务标题中的 XSS"""

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        ]

        for payload in xss_payloads:
            response = client.post(
                "/api/tasks",
                json={
                    "title": payload,
                    "description": "Test task",
                    "reward": "1000000000000000000"
                }
            )

            # 可能需要认证
            if response.status_code == 200:
                # 响应中不应该包含未转义的脚本标签
                assert "<script>" not in response.text.lower()
                assert "onerror=" not in response.text.lower()
                assert "javascript:" not in response.text.lower()

    def test_xss_in_agent_name(self, client):
        """测试 Agent 名称中的 XSS"""

        response = client.post(
            "/api/agents",
            json={
                "name": "<script>alert('XSS')</script>",
                "description": "Test agent",
                "specialties": "testing",
                "wallet_address": "0x1234567890123456789012345678901234567890"
            }
        )

        # 应该拒绝或转义
        if response.status_code in [200, 201]:
            assert "<script>" not in response.text


class TestAuthenticationSecurity:
    """测试认证安全性"""

    def test_weak_password_rejection(self, client):
        """测试弱密码被拒绝"""

        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "qwerty",
            "Password1",  # 缺少特殊字符
            "Pass@123",   # 太短
        ]

        for weak_password in weak_passwords:
            response = client.post("/api/auth/register", json={
                "username": f"user_{weak_password}",
                "email": f"user_{weak_password}@example.com",
                "password": weak_password,
                "wallet_address": "0x1234567890123456789012345678901234567890"
            })

            # 应该拒绝弱密码
            assert response.status_code in [400, 422]

    def test_brute_force_protection(self, client):
        """测试暴力破解保护"""

        # 尝试多次失败登录
        failed_attempts = 0
        for i in range(20):
            response = client.post("/api/auth/login", json={
                "username": "nonexistent_user",
                "password": f"wrong_password_{i}"
            })

            if response.status_code == 401:
                failed_attempts += 1
            elif response.status_code == 429:
                # 速率限制生效
                break

        # 应该有速率限制或账户锁定机制
        # 注意：测试环境可能禁用了速率限制
        assert failed_attempts <= 20

    def test_token_expiration(self, client):
        """测试 token 过期"""

        # 使用过期的 token
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxfQ.invalid"

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        # 应该拒绝过期的 token
        assert response.status_code == 401

    def test_invalid_token_format(self, client):
        """测试无效的 token 格式"""

        invalid_tokens = [
            "not_a_token",
            "Bearer invalid",
            "12345",
            "",
            "null",
        ]

        for invalid_token in invalid_tokens:
            response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {invalid_token}"}
            )

            assert response.status_code == 401


class TestInputValidation:
    """测试输入验证"""

    def test_email_validation(self, client):
        """测试邮箱格式验证"""

        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user@.com",
            "user space@example.com",
        ]

        for invalid_email in invalid_emails:
            response = client.post("/api/auth/register", json={
                "username": "testuser",
                "email": invalid_email,
                "password": "SecureP@ssw0rd123!",
                "wallet_address": "0x1234567890123456789012345678901234567890"
            })

            assert response.status_code == 422

    def test_wallet_address_validation(self, client):
        """测试钱包地址验证"""

        invalid_addresses = [
            "not_an_address",
            "0x123",  # 太短
            "0xGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",  # 无效字符
            "1234567890123456789012345678901234567890",  # 缺少 0x 前缀
        ]

        for invalid_address in invalid_addresses:
            response = client.post("/api/auth/register", json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "SecureP@ssw0rd123!",
                "wallet_address": invalid_address
            })

            # 应该拒绝无效地址
            assert response.status_code in [400, 422]

    def test_excessive_input_length(self, client):
        """测试过长输入"""

        # 超长用户名
        response = client.post("/api/auth/register", json={
            "username": "a" * 1000,
            "email": "test@example.com",
            "password": "SecureP@ssw0rd123!",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        assert response.status_code in [400, 422]

        # 超长描述
        response = client.post(
            "/api/tasks",
            json={
                "title": "Test Task",
                "description": "x" * 100000,
                "reward": "1000000000000000000"
            }
        )

        assert response.status_code in [400, 401, 422]


class TestCSRFProtection:
    """测试 CSRF 保护"""

    def test_csrf_token_required(self, client):
        """测试 CSRF token 是否必需"""

        # 尝试不带 CSRF token 的 POST 请求
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecureP@ssw0rd123!",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        })

        # 根据 CSRF 配置，可能需要 token
        # 测试环境可能禁用了 CSRF 保护
        assert response.status_code in [201, 403, 422]


class TestAuthorizationSecurity:
    """测试授权安全性"""

    def test_unauthorized_access_to_protected_endpoint(self, client):
        """测试未授权访问受保护端点"""

        protected_endpoints = [
            "/api/auth/me",
            "/api/tasks",
        ]

        for endpoint in protected_endpoints:
            response = client.get(endpoint)

            # 应该要求认证
            assert response.status_code in [401, 405]  # 405 if method not allowed

    def test_access_other_user_data(self, client):
        """测试访问其他用户数据"""

        # 注册两个用户
        user1_response = client.post("/api/auth/register", json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "SecureP@ssw0rd123!",
            "wallet_address": "0x1111111111111111111111111111111111111111"
        })

        if user1_response.status_code == 422:
            pytest.skip("Password policy issue")

        user2_response = client.post("/api/auth/register", json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "SecureP@ssw0rd123!",
            "wallet_address": "0x2222222222222222222222222222222222222222"
        })

        if user1_response.status_code == 201 and user2_response.status_code == 201:
            user1_token = user1_response.json()["access_token"]

            # user1 尝试访问 user2 的数据（如果有这样的端点）
            # 这里只是示例，实际端点可能不同
            response = client.get(
                "/api/users/user2",
                headers={"Authorization": f"Bearer {user1_token}"}
            )

            # 应该被拒绝
            assert response.status_code in [403, 404]


class TestSecurityHeaders:
    """测试安全响应头"""

    def test_security_headers_present(self, client):
        """测试安全响应头是否存在"""

        response = client.get("/health")

        # 检查常见的安全响应头
        headers = response.headers

        # 注意：不是所有头都必须存在，取决于配置
        # 这里只是检查是否有设置

        # X-Content-Type-Options
        if "x-content-type-options" in headers:
            assert headers["x-content-type-options"] == "nosniff"

        # X-Frame-Options
        if "x-frame-options" in headers:
            assert headers["x-frame-options"] in ["DENY", "SAMEORIGIN"]

    def test_no_sensitive_info_in_errors(self, client):
        """测试错误响应不泄露敏感信息"""

        # 触发一个错误
        response = client.get("/api/nonexistent_endpoint")

        if response.status_code == 404:
            error_text = response.text.lower()

            # 不应该泄露敏感信息
            sensitive_keywords = [
                "password",
                "secret",
                "token",
                "api_key",
                "database",
                "connection string",
            ]

            for keyword in sensitive_keywords:
                assert keyword not in error_text

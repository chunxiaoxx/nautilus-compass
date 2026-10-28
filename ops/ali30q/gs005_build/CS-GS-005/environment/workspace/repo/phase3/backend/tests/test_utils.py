"""
工具模块单元测试

为 utils/ 目录添加单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# Utils Tests
# ============================================================================

class TestAuthUtils:
    """测试auth工具模块"""

    def test_generate_api_key(self):
        """测试API密钥生成"""
        from utils.auth import generate_api_key

        # 生成密钥
        key1 = generate_api_key()
        key2 = generate_api_key()

        # 验证密钥格式
        assert isinstance(key1, str)
        assert len(key1) > 20  # API密钥应该足够长

        # 验证生成的密钥是唯一的
        assert key1 != key2

    def test_hash_password(self):
        """测试密码哈希"""
        from utils.auth import hash_password

        password = "testpassword123"
        hashed = hash_password(password)

        # 验证返回的是字符串
        assert isinstance(hashed, str)
        # 验证哈希后的密码与原密码不同
        assert hashed != password

    def test_verify_password(self):
        """测试密码验证"""
        from utils.auth import hash_password, verify_password

        password = "testpassword123"
        hashed = hash_password(password)

        # 验证正确密码
        assert verify_password(password, hashed) is True

        # 验证错误密码
        assert verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self):
        """测试访问令牌创建"""
        from utils.auth import create_access_token

        data = {"sub": "testuser", "wallet": "0x123"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        """测试访问令牌解码"""
        from utils.auth import create_access_token, decode_access_token

        data = {"sub": "testuser", "wallet": "0x123"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded.get("sub") == "testuser"
        assert decoded.get("wallet") == "0x123"

    def test_decode_access_token_invalid(self):
        """测试无效令牌解码"""
        from fastapi import HTTPException
        from utils.auth import decode_access_token

        # 测试无效令牌 - 应该抛出异常
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("invalid-token")

        assert exc_info.value.status_code == 401


class TestDatabaseUtils:
    """测试database工具模块"""

    def test_get_db_generator(self):
        """测试数据库会话生成器"""
        from utils.database import get_db

        # 获取生成器
        db_gen = get_db()

        # 验证生成器存在
        assert db_gen is not None

        # 测试生成器可以迭代（使用mock）
        with patch('utils.database.engine') as mock_engine:
            with patch('utils.database.SessionLocal') as mock_session:
                mock_session_instance = MagicMock()
                mock_session.return_value = mock_session_instance

                db_gen = get_db()
                # 获取session
                try:
                    db = next(db_gen)
                    # 验证返回的是session
                    assert db is not None
                except StopIteration:
                    pass

    def test_init_db(self):
        """测试数据库初始化"""
        with patch('utils.database.Base') as mock_base:
            with patch('utils.database.engine') as mock_engine:
                # 模拟导入以避免实际数据库连接
                import importlib
                import utils.database
                importlib.reload(utils.database)

                # 测试init_db函数存在
                assert hasattr(utils.database, 'init_db')


class TestUtilsIntegration:
    """测试工具模块集成"""

    def test_auth_utils_exported(self):
        """测试auth工具导出"""
        from utils.auth import (
            generate_api_key,
            hash_password,
            verify_password,
            create_access_token,
            decode_access_token,
            get_current_user,
            get_current_agent
        )

        assert generate_api_key is not None
        assert hash_password is not None
        assert verify_password is not None
        assert create_access_token is not None
        assert decode_access_token is not None
        assert get_current_user is not None
        assert get_current_agent is not None

    def test_database_utils_exported(self):
        """测试database工具导出"""
        from utils.database import get_db, init_db

        assert get_db is not None
        assert init_db is not None

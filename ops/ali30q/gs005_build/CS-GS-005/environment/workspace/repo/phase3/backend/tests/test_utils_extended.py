"""
扩展工具模块测试 - Auth

为utils/auth.py添加更多测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# Extended Auth Utils Tests
# ============================================================================

class TestAuthUtilsExtended:
    """扩展Auth工具测试"""

    def test_create_access_token_with_expiry(self):
        """测试带过期时间的令牌创建"""
        from utils.auth import create_access_token

        data = {"sub": "testuser"}
        expires = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_default_expiry(self):
        """测试默认过期时间的令牌创建"""
        from utils.auth import create_access_token

        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_password_edge_cases(self):
        """测试密码验证边界情况"""
        from utils.auth import verify_password, hash_password

        # 测试错误密码
        password = "testpassword"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_generate_api_key_with_custom_prefix(self):
        """测试自定义前缀的API密钥生成"""
        from utils.auth import generate_api_key

        with patch.dict(os.environ, {'API_KEY_PREFIX': 'test_'}):
            # 重新导入以获取新配置
            import importlib
            import utils.auth
            importlib.reload(utils.auth)

            key = utils.auth.generate_api_key()
            assert key.startswith('test_')

    def test_generate_api_key_with_custom_length(self):
        """测试自定义长度的API密钥生成"""
        from utils.auth import generate_api_key

        with patch.dict(os.environ, {'API_KEY_LENGTH': '16'}):
            import importlib
            import utils.auth
            importlib.reload(utils.auth)

            key = utils.auth.generate_api_key()
            # key = prefix + 16 chars
            assert len(key) > 16

    def test_jwt_config_constants(self):
        """测试JWT配置常量"""
        from utils.auth import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION

        assert JWT_SECRET is not None
        assert JWT_ALGORITHM is not None
        assert JWT_EXPIRATION > 0


class TestAuthDependencies:
    """测试认证依赖"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """测试获取当前用户成功"""
        from utils.auth import get_current_user, create_access_token

        # 创建mock用户
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.is_active = True

        # 创建token
        token = create_access_token({"sub": "testuser"})

        # Mock依赖
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # 调用函数
        with patch('utils.auth.get_db', return_value=iter([mock_db])):
            from utils.auth import get_current_user
            result = await get_current_user(mock_credentials, mock_db)

        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """测试无效令牌获取用户"""
        from utils.auth import get_current_user

        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid-token"

        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self):
        """测试用户不存在"""
        from utils.auth import get_current_user, create_access_token

        token = create_access_token({"sub": "nonexistent"})

        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self):
        """测试非活跃用户"""
        from utils.auth import get_current_user, create_access_token

        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.is_active = False

        token = create_access_token({"sub": "testuser"})

        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_current_agent_success(self):
        """测试获取当前Agent成功"""
        from utils.auth import get_current_agent

        mock_agent = MagicMock()
        mock_agent.agent_id = 1

        mock_api_key = MagicMock()
        mock_api_key.agent_id = 1
        mock_api_key.is_active = True

        mock_credentials = MagicMock()
        mock_credentials.credentials = "nau_testkey"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_api_key, mock_agent]

        with patch.dict(os.environ, {'API_KEY_PREFIX': 'nau_'}):
            result = await get_current_agent(mock_credentials, mock_db)

    @pytest.mark.asyncio
    async def test_get_current_agent_invalid_format(self):
        """测试无效API密钥格式"""
        from utils.auth import get_current_agent

        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid"

        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_agent(mock_credentials, mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_agent_not_found(self):
        """测试Agent不存在"""
        from utils.auth import get_current_agent

        mock_credentials = MagicMock()
        mock_credentials.credentials = "nau_testkey"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch.dict(os.environ, {'API_KEY_PREFIX': 'nau_'}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_agent(mock_credentials, mock_db)

        assert exc_info.value.status_code == 401


class TestAuthAdmin:
    """测试管理员认证"""

    @pytest.mark.asyncio
    async def test_get_current_admin_user_success(self):
        """测试获取当前管理员用户成功"""
        from utils.auth import get_current_admin_user

        mock_user = MagicMock()
        mock_user.is_admin = True

        result = await get_current_admin_user(mock_user)

        assert result.is_admin is True

    @pytest.mark.asyncio
    async def test_get_current_admin_user_not_admin(self):
        """测试非管理员用户"""
        from utils.auth import get_current_admin_user

        mock_user = MagicMock()
        mock_user.is_admin = False

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(mock_user)

        assert exc_info.value.status_code == 403


class TestUserOrAgent:
    """测试用户或Agent认证"""

    @pytest.mark.asyncio
    async def test_get_current_user_or_agent_with_jwt(self):
        """测试使用JWT获取用户或Agent"""
        from utils.auth import get_current_user_or_agent, create_access_token

        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.wallet_address = "0x123"
        mock_user.is_active = True

        mock_agent = MagicMock()
        mock_agent.agent_id = 1

        token = create_access_token({"sub": "testuser"})

        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_agent]

        result = await get_current_user_or_agent(mock_credentials, mock_db)

        assert result[0] == mock_user

    @pytest.mark.asyncio
    async def test_get_current_user_or_agent_with_api_key(self):
        """测试使用API密钥获取用户或Agent"""
        from utils.auth import get_current_user_or_agent

        mock_agent = MagicMock()
        mock_agent.agent_id = 1

        mock_api_key = MagicMock()
        mock_api_key.agent_id = 1
        mock_api_key.is_active = True

        mock_credentials = MagicMock()
        mock_credentials.credentials = "nau_testkey"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_api_key, mock_agent]

        with patch.dict(os.environ, {'API_KEY_PREFIX': 'nau_'}):
            result = await get_current_user_or_agent(mock_credentials, mock_db)

        assert result[1] == mock_agent
        assert result[0] is None

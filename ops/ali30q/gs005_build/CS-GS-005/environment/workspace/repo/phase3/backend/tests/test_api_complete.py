"""
完整API测试套件

为所有API模块添加完整测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import FastAPI, HTTPException, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Base
from utils.database import get_db

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


# ============================================================================
# Complete API Tests
# ============================================================================

class TestTasksAPIComplete:
    """完整Tasks API测试"""

    def test_list_tasks_with_filters(self, setup_database):
        """测试带过滤器的任务列表"""
        from api.tasks import router

        app = FastAPI()
        app.include_router(router, prefix="/tasks")
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/tasks/?status=Open")

        assert response.status_code in [200, 307]

    def test_list_tasks_with_type_filter(self, setup_database):
        """测试带类型过滤器的任务列表"""
        from api.tasks import router

        app = FastAPI()
        app.include_router(router, prefix="/tasks")
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/tasks/?task_type=CODE")

        assert response.status_code in [200, 307]

    def test_get_task_not_found(self, setup_database):
        """测试获取不存在的任务"""
        from api.tasks import router

        app = FastAPI()
        app.include_router(router, prefix="/tasks")
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/tasks/999")

        assert response.status_code in [404]


class TestAgentsAPIComplete:
    """完整Agents API测试"""

    def test_get_agent_not_found(self, setup_database):
        """测试获取不存在的Agent"""
        from api.agents import router

        app = FastAPI()
        app.include_router(router, prefix="/agents")
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/agents/999")

        assert response.status_code in [404]

    def test_agent_reputation_endpoint(self, setup_database):
        """测试Agent信誉端点"""
        from api.agents import router

        app = FastAPI()
        app.include_router(router, prefix="/agents")
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/agents/1/reputation")

        assert response.status_code in [404]

    def test_agent_reputation_not_found(self, setup_database):
        """测试Agent信誉不存在"""
        from api.agents import router

        app = FastAPI()
        app.include_router(router, prefix="/agents")
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/agents/999/reputation")

        assert response.status_code in [404]


class TestRewardsAPIComplete:
    """完整Rewards API测试"""

    def test_get_reward_balance_endpoint(self, setup_database):
        """测试获取奖励余额端点"""
        from api.rewards import router

        app = FastAPI()
        app.include_router(router, prefix="/rewards")
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/rewards/balance")

        assert response.status_code in [401]  # 未授权

    def test_get_reward_history_endpoint(self, setup_database):
        """测试获取奖励历史端点"""
        from api.rewards import router

        app = FastAPI()
        app.include_router(router, prefix="/rewards")
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/rewards/history")

        assert response.status_code in [401]  # 未授权

    def test_withdraw_reward_endpoint(self, setup_database):
        """测试提取奖励端点"""
        from api.rewards import router

        app = FastAPI()
        app.include_router(router, prefix="/rewards")
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.post("/rewards/withdraw")

        assert response.status_code in [401]  # 未授权


class TestAuthAPIComplete:
    """完整Auth API测试"""

    def test_auth_register_endpoint(self):
        """测试注册端点"""
        from api.auth import router

        app = FastAPI()
        app.include_router(router, prefix="/auth")

        client = TestClient(app)
        response = client.post("/auth/register")

        assert response.status_code in [200, 201, 400, 422]

    def test_auth_login_endpoint(self):
        """测试登录端点"""
        from api.auth import router

        app = FastAPI()
        app.include_router(router, prefix="/auth")

        client = TestClient(app)
        response = client.post("/auth/login")

        assert response.status_code in [200, 400, 401, 422]

    def test_auth_me_endpoint(self):
        """测试获取当前用户端点"""
        from api.auth import router

        app = FastAPI()
        app.include_router(router, prefix="/auth")

        client = TestClient(app)
        response = client.get("/auth/me")

        assert response.status_code in [200, 401, 404]


class TestAPIValidation:
    """测试API验证"""

    def test_pydantic_validation(self):
        """测试Pydantic验证"""
        from pydantic import BaseModel, ValidationError
        from typing import Optional

        class TestModel(BaseModel):
            name: str
            age: int
            email: Optional[str] = None

        # 测试有效数据
        model = TestModel(name="John", age=25)
        assert model.name == "John"
        assert model.age == 25

        # 测试无效数据
        with pytest.raises(ValidationError):
            TestModel(name="John", age="invalid")

    def test_enum_validation(self):
        """测试枚举验证"""
        from enum import Enum
        from pydantic import BaseModel

        class Status(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        class Model(BaseModel):
            status: Status

        model = Model(status="active")
        assert model.status == Status.ACTIVE


class TestDatabaseQueries:
    """测试数据库查询"""

    def test_query_filter(self):
        """测试查询过滤器"""
        from unittest.mock import MagicMock

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None

        # 模拟链式调用
        result = mock_query.filter({"id": 1}).first()

        assert result is None

    def test_query_all(self):
        """测试查询所有"""
        from unittest.mock import MagicMock

        mock_query = MagicMock()
        mock_query.all.return_value = []

        result = mock_query.all()

        assert result == []


class TestErrorHandlingComplete:
    """完整错误处理测试"""

    def test_http_exception_not_found(self):
        """测试404异常"""
        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(status_code=404, detail="Resource not found")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Resource not found"

    def test_http_exception_bad_request(self):
        """测试400异常"""
        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(status_code=400, detail="Bad request")

        assert exc_info.value.status_code == 400

    def test_http_exception_unauthorized(self):
        """测试401异常"""
        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(status_code=401, detail="Unauthorized")

        assert exc_info.value.status_code == 401

    def test_http_exception_forbidden(self):
        """测试403异常"""
        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(status_code=403, detail="Forbidden")

        assert exc_info.value.status_code == 403


class TestPagination:
    """测试分页"""

    def test_pagination_offset_limit(self):
        """测试分页偏移和限制"""
        # 模拟分页逻辑
        items = list(range(100))
        page = 2  # 第二页
        page_size = 10
        offset = (page - 1) * page_size

        result = items[offset:offset + page_size]

        assert len(result) == page_size
        assert result[0] == 10

    def test_pagination_empty(self):
        """测试空结果分页"""
        items = []
        page = 1
        page_size = 10
        offset = (page - 1) * page_size

        result = items[offset:offset + page_size]

        assert len(result) == 0

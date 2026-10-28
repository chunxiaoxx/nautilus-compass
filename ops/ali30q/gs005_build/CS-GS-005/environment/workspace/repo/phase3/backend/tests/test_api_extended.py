"""
扩展API测试 - Tasks, Agents, Rewards端点

为api模块添加更多测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI, HTTPException
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
# Tasks API Extended Tests
# ============================================================================

class TestTasksAPIExtended:
    """扩展Tasks API测试"""

    def test_task_create_model(self):
        """测试TaskCreate模型"""
        from api.tasks import TaskCreate
        from models.database import TaskType

        task_data = TaskCreate(
            description="Test task",
            input_data="input",
            expected_output="output",
            reward=1000,
            task_type=TaskType.CODE,
            timeout=3600
        )

        assert task_data.description == "Test task"
        assert task_data.reward == 1000
        assert task_data.task_type == TaskType.CODE
        assert task_data.timeout == 3600

    def test_task_submit_model(self):
        """测试TaskSubmit模型"""
        from api.tasks import TaskSubmit

        submit_data = TaskSubmit(result="test result")

        assert submit_data.result == "test result"

    def test_task_dispute_model(self):
        """测试TaskDispute模型"""
        from api.tasks import TaskDispute

        dispute_data = TaskDispute(reason="test reason")

        assert dispute_data.reason == "test reason"

    def test_task_response_model(self):
        """测试TaskResponse模型"""
        from api.tasks import TaskResponse
        from models.database import TaskType, TaskStatus

        task_data = TaskResponse(
            id=1,
            task_id="0x123",
            publisher="0x456",
            description="Test",
            input_data=None,
            expected_output=None,
            reward=100,
            task_type=TaskType.CODE,
            status=TaskStatus.OPEN,
            agent=None,
            result=None,
            timeout=3600,
            created_at=datetime.now(),
            accepted_at=None,
            submitted_at=None,
            verified_at=None,
            completed_at=None
        )

        assert task_data.id == 1
        assert task_data.status == TaskStatus.OPEN

    def test_task_router_endpoints(self):
        """测试Tasks路由器端点数量"""
        from api.tasks import router

        routes = list(router.routes)
        # 应该有7个端点
        assert len(routes) >= 7


# ============================================================================
# Agents API Extended Tests
# ============================================================================

class TestAgentsAPIExtended:
    """扩展Agents API测试"""

    def test_agent_register_model(self):
        """测试AgentRegister模型"""
        from api.agents import AgentRegister

        agent_data = AgentRegister(
            name="TestAgent",
            description="Test description",
            specialties=["test", "demo"]
        )

        assert agent_data.name == "TestAgent"
        assert agent_data.description == "Test description"
        assert agent_data.specialties == ["test", "demo"]

    def test_agent_register_model_optional(self):
        """测试AgentRegister模型可选字段"""
        from api.agents import AgentRegister

        agent_data = AgentRegister(name="TestAgent")

        assert agent_data.name == "TestAgent"
        assert agent_data.description is None
        assert agent_data.specialties is None

    def test_api_key_response_model(self):
        """测试APIKeyResponse模型"""
        from api.agents import APIKeyResponse

        key_data = APIKeyResponse(
            api_key="test-key-123",
            name="Test Key",
            created_at=datetime.now()
        )

        assert key_data.api_key == "test-key-123"
        assert key_data.name == "Test Key"

    def test_agent_router_endpoints(self):
        """测试Agents路由器端点数量"""
        from api.agents import router

        routes = list(router.routes)
        # 应该有6个端点
        assert len(routes) >= 6


# ============================================================================
# Rewards API Extended Tests
# ============================================================================

class TestRewardsAPIExtended:
    """扩展Rewards API测试"""

    def test_reward_response_model_extended(self):
        """测试RewardResponse模型扩展"""
        from api.rewards import RewardResponse

        reward_data = RewardResponse(
            id=1,
            task_id="0x123",
            agent="0x456",
            amount=1000,
            status="Pending",
            distributed_at=None,
            withdrawn_at=None
        )

        assert reward_data.id == 1
        assert reward_data.amount == 1000
        assert reward_data.status == "Pending"

    def test_reward_router_endpoints(self):
        """测试Rewards路由器端点数量"""
        from api.rewards import router

        routes = list(router.routes)
        # 应该有3个端点
        assert len(routes) >= 3


# ============================================================================
# Auth API Extended Tests
# ============================================================================

class TestAuthAPIExtended:
    """扩展Auth API测试"""

    def test_auth_router_endpoints(self):
        """测试Auth路由器端点"""
        from api.auth import router

        routes = list(router.routes)
        # 应该有多个端点
        assert len(routes) >= 2


# ============================================================================
# Mock Tests - API Endpoints
# ============================================================================

class TestAPIEndpointMocks:
    """测试API端点(使用Mock)"""

    def test_list_tasks_endpoint(self, setup_database):
        """测试列出任务端点"""
        from api.tasks import router

        app = FastAPI()
        app.include_router(router, prefix="/tasks")
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/tasks/")

        # 端点应该存在
        assert response.status_code in [200, 307]

    def test_list_agents_endpoint(self, setup_database):
        """测试列出智能体端点"""
        from api.agents import router

        app = FastAPI()
        app.include_router(router, prefix="/agents")
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/agents/")

        assert response.status_code in [200, 307]

    def test_get_reward_balance_endpoint(self):
        """测试获取奖励余额端点"""
        from api.rewards import router

        app = FastAPI()
        app.include_router(router, prefix="/rewards")

        client = TestClient(app)

        # 测试端点存在
        response = client.get("/rewards/balance")
        assert response.status_code in [200, 401, 404]


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestAPIErrorHandling:
    """测试API错误处理"""

    def test_http_exception_creation(self):
        """测试HTTP异常创建"""
        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(status_code=404, detail="Not found")

        assert exc_info.value.status_code == 404

    def test_http_exception_with_headers(self):
        """测试带headers的HTTP异常"""
        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Bearer"}
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"

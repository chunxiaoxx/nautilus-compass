"""
API模块单元测试

为 api/agents.py, api/tasks.py, api/rewards.py, api/auth.py 添加单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# API Models Tests
# ============================================================================

class TestModels:
    """测试数据模型"""

    def test_task_status_enum(self):
        """测试TaskStatus枚举"""
        from models.database import TaskStatus

        # 验证枚举值
        assert TaskStatus.OPEN.value == "Open"
        assert TaskStatus.ACCEPTED.value == "Accepted"
        assert TaskStatus.SUBMITTED.value == "Submitted"
        assert TaskStatus.VERIFIED.value == "Verified"
        assert TaskStatus.COMPLETED.value == "Completed"
        assert TaskStatus.FAILED.value == "Failed"
        assert TaskStatus.DISPUTED.value == "Disputed"

    def test_agent_model(self):
        """测试Agent模型"""
        from models.database import Agent

        agent = Agent(
            agent_id=1,
            owner="0x1234567890123456789012345678901234567890",
            name="TestAgent",
            description="Test description",
            specialties="test,demo",
            reputation=100,
            completed_tasks=10,
            failed_tasks=1,
            total_earnings=1000
        )

        assert agent.name == "TestAgent"
        assert agent.reputation == 100

    def test_task_model(self):
        """测试Task模型"""
        from models.database import Task, TaskStatus, TaskType

        task = Task(
            task_id="task-1",
            description="Test description",
            reward=100,
            task_type=TaskType.CODE,
            status=TaskStatus.OPEN,
            publisher="0x123",
            agent=None,
            timeout=3600
        )

        assert task.description == "Test description"
        assert task.status == TaskStatus.OPEN


# ============================================================================
# API Agents Tests
# ============================================================================

class TestAgentsAPI:
    """测试Agents API端点"""

    def test_agent_response_model(self):
        """测试AgentResponse模型"""
        from api.agents import AgentResponse
        from datetime import datetime

        # 测试模型创建
        agent_data = {
            "id": 1,
            "agent_id": 1,
            "owner": "0x123",
            "name": "TestAgent",
            "description": "Test description",
            "reputation": 100,
            "specialties": "test,demo",
            "current_tasks": 0,
            "completed_tasks": 10,
            "failed_tasks": 1,
            "total_earnings": 1000,
            "created_at": datetime.now()
        }

        response = AgentResponse(**agent_data)
        assert response.name == "TestAgent"
        assert response.reputation == 100


# ============================================================================
# API Rewards Tests
# ============================================================================

class TestRewardsAPI:
    """测试Rewards API端点"""

    def test_reward_response_model(self):
        """测试RewardResponse模型"""
        from api.rewards import RewardResponse
        from datetime import datetime

        reward_data = {
            "id": 1,
            "task_id": "task-1",
            "agent": "0x123",
            "amount": 100,
            "status": "Distributed",
            "distributed_at": datetime.now(),
            "withdrawn_at": None
        }

        response = RewardResponse(**reward_data)
        assert response.amount == 100
        assert response.status == "Distributed"


# ============================================================================
# API Auth Tests
# ============================================================================

class TestAuthAPI:
    """测试Auth API端点"""

    def test_auth_router_exists(self):
        """测试Auth路由器存在"""
        from api.auth import router as auth_router

        assert auth_router is not None

    def test_auth_endpoints_count(self):
        """测试Auth端点数量"""
        from api.auth import router as auth_router

        # 获取所有路由
        routes = list(auth_router.routes)
        assert len(routes) >= 2, f"Expected at least 2 routes, got {len(routes)}"


# ============================================================================
# Integration Tests
# ============================================================================

class TestAPIIntegration:
    """测试API集成"""

    def test_router_registration(self):
        """测试路由器注册"""
        from api.agents import router as agents_router
        from api.tasks import router as tasks_router
        from api.rewards import router as rewards_router
        from api.auth import router as auth_router

        # 验证路由存在
        assert agents_router is not None
        assert tasks_router is not None
        assert rewards_router is not None
        assert auth_router is not None

    def test_all_endpoints_defined(self):
        """测试所有端点已定义"""
        from api.agents import router as agents_router
        from api.tasks import router as tasks_router
        from api.rewards import router as rewards_router
        from api.auth import router as auth_router

        # 统计端点数量
        agents_routes = len([r for r in agents_router.routes])
        tasks_routes = len([r for r in tasks_router.routes])
        rewards_routes = len([r for r in rewards_router.routes])
        auth_routes = len([r for r in auth_router.routes])

        total_routes = agents_routes + tasks_routes + rewards_routes + auth_routes

        # 至少应该有10个以上的端点
        assert total_routes >= 10, f"Expected at least 10 routes, got {total_routes}"

    def test_models_exported(self):
        """测试模型导出"""
        from models.database import Agent, Task, TaskStatus, User, Reward, APIKey

        assert Agent is not None
        assert Task is not None
        assert TaskStatus is not None
        assert User is not None
        assert Reward is not None
        assert APIKey is not None

    def test_utils_exported(self):
        """测试工具导出"""
        from utils.database import get_db
        from utils.auth import generate_api_key, hash_password, verify_password

        assert get_db is not None
        assert generate_api_key is not None
        assert hash_password is not None
        assert verify_password is not None

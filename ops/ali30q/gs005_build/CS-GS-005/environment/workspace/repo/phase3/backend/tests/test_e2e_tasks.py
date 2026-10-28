"""
端到端测试 - Tasks API

使用内存SQLite数据库测试所有Tasks API端点
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

from models.database import Base, User, Task, Agent, TaskType, TaskStatus
from utils.database import get_db
from api.tasks import router as tasks_router
from api.auth import router as auth_router
from utils.auth import hash_password


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
    app.include_router(tasks_router, prefix="/api/tasks")
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # 清理数据库
    db = TestingSessionLocal()
    try:
        db.query(Task).delete()
        db.query(Agent).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def auth_token(client):
    """创建用户并返回认证token"""
    # 尝试注册新用户
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "wallet_address": "0x1234567890123456789012345678901234567890"
    })

    # 如果注册成功，返回token
    if response.status_code == 201:
        return response.json()["access_token"]

    # 如果用户已存在或遇到速率限制，尝试登录
    login_response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })

    # 如果登录成功，返回token
    if login_response.status_code == 200:
        return login_response.json()["access_token"]

    # 如果登录也失败（可能是速率限制），直接创建token
    from utils.auth import create_access_token
    return create_access_token(data={"sub": "testuser"})


@pytest.fixture
def agent_with_token(client):
    """创建agent用户并返回token"""
    # 注册用户
    response = client.post("/api/auth/register", json={
        "username": "agentuser",
        "email": "agent@example.com",
        "password": "password123",
        "wallet_address": "0x1234567890123456789012345678901234567891"
    })
    token = response.json()["access_token"]

    # 创建agent
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == "agentuser").first()
    wallet_address = user.wallet_address  # 在关闭会话前获取值

    agent = Agent(
        agent_id=1,
        owner=wallet_address,
        name="TestAgent",
        reputation=100,
        completed_tasks=0,
        failed_tasks=0,
        total_earnings=0
    )
    db.add(agent)
    db.commit()
    db.close()

    return token, wallet_address


# ============================================================================
# Tasks API E2E Tests
# ============================================================================

class TestTasksE2E:
    """Tasks API端到端测试"""

    def test_create_task_success(self, client, auth_token):
        """测试成功创建任务"""
        response = client.post(
            "/api/tasks",
            json={
                "description": "Test task",
                "reward": 1000,
                "task_type": "CODE",
                "timeout": 3600
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Test task"
        assert data["reward"] == 1000
        assert data["status"] == "Open"

    def test_create_task_unauthorized(self, client):
        """测试未授权创建任务"""
        response = client.post(
            "/api/tasks",
            json={
                "description": "Test task",
                "reward": 1000,
                "task_type": "CODE",
                "timeout": 3600
            }
        )
        assert response.status_code == 401

    def test_list_tasks(self, client, auth_token):
        """测试列出任务"""
        # 创建几个任务
        for i in range(3):
            client.post(
                "/api/tasks",
                json={
                    "description": f"Task {i}",
                    "reward": 1000 + i * 100,
                    "task_type": "CODE",
                    "timeout": 3600
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        # 列出任务
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_list_tasks_with_filters(self, client, auth_token):
        """测试带过滤器的任务列表"""
        # 创建不同类型的任务
        client.post(
            "/api/tasks",
            json={
                "description": "Code task",
                "reward": 1000,
                "task_type": "CODE",
                "timeout": 3600
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        client.post(
            "/api/tasks",
            json={
                "description": "Data task",
                "reward": 2000,
                "task_type": "DATA",
                "timeout": 3600
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 过滤CODE类型
        response = client.get("/api/tasks?task_type=CODE")
        assert response.status_code == 200
        data = response.json()
        assert all(task["task_type"] == "CODE" for task in data)

    def test_get_task_by_id(self, client, auth_token):
        """测试获取单个任务"""
        # 创建任务
        create_response = client.post(
            "/api/tasks",
            json={
                "description": "Test task",
                "reward": 1000,
                "task_type": "CODE",
                "timeout": 3600
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        task_data = create_response.json()
        task_db_id = task_data["id"]  # 使用数据库ID

        # 获取任务
        response = client.get(f"/api/tasks/{task_db_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_db_id

    def test_get_task_not_found(self, client):
        """测试获取不存在的任务"""
        response = client.get("/api/tasks/99999")
        assert response.status_code == 404

    def test_accept_task_success(self, client, agent_with_token):
        """测试成功接受任务"""
        agent_token, agent_wallet = agent_with_token

        # 创建任务
        db = TestingSessionLocal()
        task = Task(
            task_id="0x1234",
            description="Test task",
            reward=1000,
            task_type=TaskType.CODE,
            status=TaskStatus.OPEN,
            publisher="0x1234567890123456789012345678901234567890",
            timeout=3600
        )
        db.add(task)
        db.commit()
        task_db_id = task.id
        db.close()

        # 接受任务
        response = client.post(
            f"/api/tasks/{task_db_id}/accept",
            headers={"Authorization": f"Bearer {agent_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Accepted"

    def test_accept_task_not_found(self, client, agent_with_token):
        """测试接受不存在的任务"""
        agent_token, _ = agent_with_token
        response = client.post(
            "/api/tasks/99999/accept",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        assert response.status_code == 404

    def test_accept_task_not_open(self, client, agent_with_token):
        """测试接受非Open状态的任务"""
        agent_token, agent_wallet = agent_with_token

        # 创建已接受的任务
        db = TestingSessionLocal()
        task = Task(
            task_id="0x1235",
            description="Test task",
            reward=1000,
            task_type=TaskType.CODE,
            status=TaskStatus.ACCEPTED,
            publisher="0x1234567890123456789012345678901234567890",
            agent=agent_wallet,
            timeout=3600
        )
        db.add(task)
        db.commit()
        task_db_id = task.id
        db.close()

        # 尝试再次接受
        response = client.post(
            f"/api/tasks/{task_db_id}/accept",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        assert response.status_code == 400

    def test_submit_task_success(self, client, agent_with_token):
        """测试成功提交任务"""
        agent_token, agent_wallet = agent_with_token

        # 创建已接受的任务
        db = TestingSessionLocal()
        task = Task(
            task_id="0x1236",
            description="Test task",
            reward=1000,
            task_type=TaskType.CODE,
            status=TaskStatus.ACCEPTED,
            publisher="0x1234567890123456789012345678901234567890",
            agent=agent_wallet,
            timeout=3600
        )
        db.add(task)
        db.commit()
        task_db_id = task.id
        db.close()

        # 提交任务
        response = client.post(
            f"/api/tasks/{task_db_id}/submit",
            json={"result": "Task completed successfully"},
            headers={"Authorization": f"Bearer {agent_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Submitted"

    def test_submit_task_not_accepted(self, client, agent_with_token):
        """测试提交未接受的任务"""
        agent_token, _ = agent_with_token

        # 创建Open状态的任务
        db = TestingSessionLocal()
        task = Task(
            task_id="0x1237",
            description="Test task",
            reward=1000,
            task_type=TaskType.CODE,
            status=TaskStatus.OPEN,
            publisher="0x1234567890123456789012345678901234567890",
            timeout=3600
        )
        db.add(task)
        db.commit()
        task_db_id = task.id
        db.close()

        # 尝试提交
        response = client.post(
            f"/api/tasks/{task_db_id}/submit",
            json={"result": "Task completed"},
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        assert response.status_code == 400

    def test_submit_task_wrong_agent(self, client, agent_with_token):
        """测试错误的agent提交任务"""
        agent_token, _ = agent_with_token

        # 创建分配给其他agent的任务
        db = TestingSessionLocal()
        task = Task(
            task_id="0x1238",
            description="Test task",
            reward=1000,
            task_type=TaskType.CODE,
            status=TaskStatus.ACCEPTED,
            publisher="0x1234567890123456789012345678901234567890",
            agent="0x9999999999999999999999999999999999999999",
            timeout=3600
        )
        db.add(task)
        db.commit()
        task_db_id = task.id
        db.close()

        # 尝试提交
        response = client.post(
            f"/api/tasks/{task_db_id}/submit",
            json={"result": "Task completed"},
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        assert response.status_code == 403

    def test_dispute_task_success(self, client, agent_with_token):
        """测试成功提出争议"""
        agent_token, agent_wallet = agent_with_token

        # 创建已失败的任务
        db = TestingSessionLocal()
        task = Task(
            task_id="0x1241",
            description="Test task",
            reward=1000,
            task_type=TaskType.CODE,
            status=TaskStatus.FAILED,
            publisher="0x1234567890123456789012345678901234567890",
            agent=agent_wallet,
            timeout=3600
        )
        db.add(task)
        db.commit()
        task_db_id = task.id
        db.close()

        # 提出争议
        response = client.post(
            f"/api/tasks/{task_db_id}/dispute",
            json={"reason": "Task was completed correctly"},
            headers={"Authorization": f"Bearer {agent_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Disputed"

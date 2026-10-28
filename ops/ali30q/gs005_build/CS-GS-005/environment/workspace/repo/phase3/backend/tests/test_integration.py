"""
Nautilus Phase 3 - Backend API Integration Tests

Tests for all API endpoints, authentication, and WebSocket functionality.
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from models.database import Base, User, Task, Agent
from utils.auth import hash_password
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override database dependency
def override_get_db():
    """Override database session for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
async def client():
    """Create test client"""
    from main import app
    from utils.database import get_db

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create tables
    Base.metadata.create_all(bind=engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Drop tables
    Base.metadata.drop_all(bind=engine)

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_user():
    """Create test user"""
    db = TestingSessionLocal()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        wallet_address="0x1234567890123456789012345678901234567890"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def test_agent():
    """Create test agent"""
    db = TestingSessionLocal()
    agent = Agent(
        agent_id=1,
        owner="0x1234567890123456789012345678901234567890",
        name="TestAgent",
        description="Test agent for integration tests",
        specialties='["CODE", "DATA"]',
        reputation=100,
        completed_tasks=0,
        failed_tasks=0,
        total_earnings=0
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    db.close()
    return agent


class TestAuthAPI:
    """Test authentication endpoints"""

    @pytest.mark.asyncio
    async def test_register_user(self, client):
        """Test user registration"""
        response = await client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "wallet_address": "0x1111111111111111111111111111111111111111"
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username"""
        response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "another@example.com",
            "password": "password123",
            "wallet_address": "0x2222222222222222222222222222222222222222"
        })
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user):
        """Test successful login"""
        response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, client, test_user):
        """Test getting current user info"""
        # Login first
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]

        # Get user info
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"


class TestTasksAPI:
    """Test task endpoints"""

    @pytest.mark.asyncio
    async def test_create_task(self, client, test_user):
        """Test creating a task"""
        # Login first
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]

        # Create task
        response = await client.post(
            "/api/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "description": "Test task",
                "input_data": "input",
                "expected_output": "output",
                "reward": 100,
                "task_type": "CODE",
                "timeout": 3600
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Test task"
        assert data["status"] == "Open"

    @pytest.mark.asyncio
    async def test_list_tasks(self, client):
        """Test listing tasks"""
        response = await client.get("/api/tasks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_task(self, client, test_user):
        """Test getting task details"""
        # Create task first
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]

        create_response = await client.post(
            "/api/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "description": "Test task",
                "input_data": "input",
                "expected_output": "output",
                "reward": 100,
                "task_type": "CODE",
                "timeout": 3600
            }
        )
        task_id = create_response.json()["id"]

        # Get task
        response = await client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id

    @pytest.mark.asyncio
    async def test_accept_task(self, client, test_user):
        """Test accepting a task"""
        # Login and create task
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]

        create_response = await client.post(
            "/api/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "description": "Test task",
                "input_data": "input",
                "expected_output": "output",
                "reward": 100,
                "task_type": "CODE",
                "timeout": 3600
            }
        )
        task_id = create_response.json()["id"]

        # Register agent to get API key
        agent_response = await client.post(
            "/api/agents",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "TestAgent",
                "description": "Test agent",
                "specialties": ["CODE"]
            }
        )
        api_key = agent_response.json()["api_key"]

        # Accept task with API key
        response = await client.post(
            f"/api/tasks/{task_id}/accept",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Accepted"


class TestAgentsAPI:
    """Test agent endpoints"""

    @pytest.mark.asyncio
    async def test_register_agent(self, client, test_user):
        """Test registering an agent"""
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]

        response = await client.post(
            "/api/agents",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "NewAgent",
                "description": "A new test agent",
                "specialties": ["CODE", "DATA"]
            }
        )
        assert response.status_code == 201
        data = response.json()
        # API returns agent and api_key
        assert "agent" in data
        assert "api_key" in data
        assert data["agent"]["name"] == "NewAgent"

    @pytest.mark.asyncio
    async def test_list_agents(self, client):
        """Test listing agents"""
        response = await client.get("/api/agents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_agent(self, client, test_agent):
        """Test getting agent details"""
        response = await client.get(f"/api/agents/{test_agent.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_agent.id
        assert data["name"] == "TestAgent"


class TestRewardsAPI:
    """Test reward endpoints"""

    @pytest.mark.asyncio
    async def test_get_balance(self, client, test_user):
        """Test getting reward balance"""
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]

        # Register agent to get API key
        agent_response = await client.post(
            "/api/agents",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "RewardAgent",
                "description": "Test agent for rewards",
                "specialties": ["CODE"]
            }
        )
        api_key = agent_response.json()["api_key"]

        # Get balance with API key
        response = await client.get(
            "/api/rewards/balance",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        # API returns balance, balance_eth, and agent, not total_earned
        assert "agent" in data


class TestEndToEnd:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    async def test_complete_task_workflow(self, client):
        """Test complete task workflow from creation to completion"""
        # 1. Register user
        register_response = await client.post("/api/auth/register", json={
            "username": "publisher",
            "email": "publisher@example.com",
            "password": "password123",
            "wallet_address": "0x1111111111111111111111111111111111111111"
        })
        assert register_response.status_code == 201

        # 2. Login
        login_response = await client.post("/api/auth/login", json={
            "username": "publisher",
            "password": "password123"
        })
        token = login_response.json()["access_token"]

        # 3. Create task
        task_response = await client.post(
            "/api/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "description": "Calculate sum of 1+2",
                "input_data": "1,2",
                "expected_output": "3",
                "reward": 100,
                "task_type": "COMPUTE",
                "timeout": 3600
            }
        )
        assert task_response.status_code == 201
        task_id = task_response.json()["id"]

        # 4. Register agent
        agent_response = await client.post(
            "/api/agents",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "ComputeAgent",
                "description": "Agent for compute tasks",
                "specialties": ["COMPUTE"]
            }
        )
        assert agent_response.status_code == 201
        api_key = agent_response.json()["api_key"]

        # 5. Accept task with API key
        accept_response = await client.post(
            f"/api/tasks/{task_id}/accept",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert accept_response.status_code == 200
        assert accept_response.json()["status"] == "Accepted"

        # 6. Submit result with API key
        submit_response = await client.post(
            f"/api/tasks/{task_id}/submit",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"result": "3"}
        )
        assert submit_response.status_code == 200
        assert submit_response.json()["status"] == "Submitted"

        # 7. Verify task status
        status_response = await client.get(f"/api/tasks/{task_id}/status")
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["status"] in ["Submitted", "Verified", "Completed"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

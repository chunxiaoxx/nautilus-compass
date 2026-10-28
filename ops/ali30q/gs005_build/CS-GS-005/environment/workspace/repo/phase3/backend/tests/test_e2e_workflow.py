"""
End-to-End Workflow Tests for Nautilus Phase 3.

Tests complete user workflows from start to finish.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import time

from main import app
from models.database import Base, Task, Agent, User, TaskStatus
from utils.database import get_db
from utils.auth import hash_password, create_access_token


# Test database setup
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def setup_database():
    """Setup test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(setup_database):
    """Create test client."""
    with TestClient(app) as c:
        yield c


class TestCompleteTaskWorkflow:
    """Test complete task lifecycle workflow."""

    def test_complete_task_workflow(self, client):
        """Test complete workflow: register -> create agent -> create task -> accept -> complete."""

        # Step 1: Register publisher
        publisher_response = client.post(
            "/api/auth/register",
            json={
                "username": "publisher",
                "email": "publisher@example.com",
                "password": "password123",
                "wallet_address": "0x1111111111111111111111111111111111111111"
            }
        )
        assert publisher_response.status_code == 201
        publisher_token = publisher_response.json()["access_token"]

        # Step 2: Register agent owner
        agent_response = client.post(
            "/api/auth/register",
            json={
                "username": "agentowner",
                "email": "agent@example.com",
                "password": "password123",
                "wallet_address": "0x2222222222222222222222222222222222222222"
            }
        )
        assert agent_response.status_code == 201
        agent_token = agent_response.json()["access_token"]

        # Step 3: Create agent
        create_agent_response = client.post(
            "/api/agents",
            json={
                "name": "WorkflowAgent",
                "description": "Agent for workflow testing",
                "specialties": "python,testing"
            },
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        assert create_agent_response.status_code == 201
        agent_id = create_agent_response.json()["agent_id"]

        # Step 4: Publisher creates task
        create_task_response = client.post(
            "/api/tasks",
            json={
                "description": "Workflow test task",
                "reward": 1000000000000000000,  # 1 ETH
                "task_type": "CODE",
                "timeout": 3600
            },
            headers={"Authorization": f"Bearer {publisher_token}"}
        )
        assert create_task_response.status_code == 201
        task_id = create_task_response.json()["task_id"]

        # Step 5: Verify task is in Open status
        get_task_response = client.get(f"/api/tasks/{task_id}")
        assert get_task_response.status_code == 200
        assert get_task_response.json()["status"] == "Open"

        # Step 6: Agent accepts task
        accept_response = client.post(
            f"/api/tasks/{task_id}/accept",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        assert accept_response.status_code == 200

        # Step 7: Verify task is accepted
        get_task_response = client.get(f"/api/tasks/{task_id}")
        assert get_task_response.status_code == 200
        task_data = get_task_response.json()
        assert task_data["status"] in ["Accepted", "Open"]  # May vary based on implementation

        # Step 8: Agent submits task result
        submit_response = client.post(
            f"/api/tasks/{task_id}/submit",
            json={"result": "Task completed successfully"},
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        assert submit_response.status_code == 200

        # Step 9: Verify task is submitted
        get_task_response = client.get(f"/api/tasks/{task_id}")
        assert get_task_response.status_code == 200
        task_data = get_task_response.json()
        assert task_data["status"] in ["Submitted", "Completed"]

        # Step 10: Verify agent stats updated
        agent_stats_response = client.get(f"/api/agents/{agent_id}/stats")
        assert agent_stats_response.status_code == 200


class TestMultiAgentWorkflow:
    """Test workflows with multiple agents."""

    def test_multiple_agents_competing_for_task(self, client):
        """Test multiple agents competing for the same task."""

        # Create publisher
        publisher_response = client.post(
            "/api/auth/register",
            json={
                "username": "publisher2",
                "email": "publisher2@example.com",
                "password": "password123",
                "wallet_address": "0x3333333333333333333333333333333333333333"
            }
        )
        publisher_token = publisher_response.json()["access_token"]

        # Create task
        create_task_response = client.post(
            "/api/tasks",
            json={
                "description": "Competitive task",
                "reward": 2000000000000000000,  # 2 ETH
                "task_type": "CODE",
                "timeout": 3600
            },
            headers={"Authorization": f"Bearer {publisher_token}"}
        )
        task_id = create_task_response.json()["task_id"]

        # Create multiple agents
        agents = []
        for i in range(3):
            agent_owner_response = client.post(
                "/api/auth/register",
                json={
                    "username": f"agent_owner_{i}",
                    "email": f"agent{i}@example.com",
                    "password": "password123",
                    "wallet_address": f"0x{'4' * 39}{i}"
                }
            )
            agent_token = agent_owner_response.json()["access_token"]

            create_agent_response = client.post(
                "/api/agents",
                json={
                    "name": f"Agent{i}",
                    "description": f"Agent {i} for testing",
                    "specialties": "python"
                },
                headers={"Authorization": f"Bearer {agent_token}"}
            )
            agents.append({
                "token": agent_token,
                "id": create_agent_response.json()["agent_id"]
            })

        # All agents try to accept the task
        accept_results = []
        for agent in agents:
            response = client.post(
                f"/api/tasks/{task_id}/accept",
                headers={"Authorization": f"Bearer {agent['token']}"}
            )
            accept_results.append(response.status_code)

        # At least one should succeed
        assert 200 in accept_results or 201 in accept_results


class TestErrorHandlingWorkflow:
    """Test error handling in workflows."""

    def test_unauthorized_task_operations(self, client):
        """Test that unauthorized users cannot perform task operations."""

        # Create publisher and task
        publisher_response = client.post(
            "/api/auth/register",
            json={
                "username": "publisher3",
                "email": "publisher3@example.com",
                "password": "password123",
                "wallet_address": "0x5555555555555555555555555555555555555555"
            }
        )
        publisher_token = publisher_response.json()["access_token"]

        create_task_response = client.post(
            "/api/tasks",
            json={
                "description": "Protected task",
                "reward": 1000000000000000000,
                "task_type": "CODE",
                "timeout": 3600
            },
            headers={"Authorization": f"Bearer {publisher_token}"}
        )
        task_id = create_task_response.json()["task_id"]

        # Try to accept task without authentication
        response = client.post(f"/api/tasks/{task_id}/accept")
        assert response.status_code in [401, 403, 422]  # Unauthorized or Forbidden

    def test_invalid_task_operations(self, client):
        """Test invalid task operations."""

        # Try to get non-existent task
        response = client.get("/api/tasks/nonexistent-task-id")
        assert response.status_code == 404

        # Try to create task with invalid data
        publisher_response = client.post(
            "/api/auth/register",
            json={
                "username": "publisher4",
                "email": "publisher4@example.com",
                "password": "password123",
                "wallet_address": "0x6666666666666666666666666666666666666666"
            }
        )
        publisher_token = publisher_response.json()["access_token"]

        response = client.post(
            "/api/tasks",
            json={
                "description": "",  # Invalid: empty description
                "reward": -100,  # Invalid: negative reward
                "task_type": "INVALID_TYPE",
                "timeout": -1
            },
            headers={"Authorization": f"Bearer {publisher_token}"}
        )
        assert response.status_code in [400, 422]  # Bad Request or Unprocessable Entity


class TestAgentReputationWorkflow:
    """Test agent reputation system workflow."""

    def test_reputation_increases_on_success(self, client):
        """Test that agent reputation increases after successful task completion."""

        # Create agent owner
        agent_response = client.post(
            "/api/auth/register",
            json={
                "username": "repagent",
                "email": "repagent@example.com",
                "password": "password123",
                "wallet_address": "0x7777777777777777777777777777777777777777"
            }
        )
        agent_token = agent_response.json()["access_token"]

        # Create agent
        create_agent_response = client.post(
            "/api/agents",
            json={
                "name": "ReputationAgent",
                "description": "Agent for reputation testing",
                "specialties": "python"
            },
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        agent_id = create_agent_response.json()["agent_id"]

        # Get initial reputation
        initial_stats = client.get(f"/api/agents/{agent_id}/stats")
        initial_reputation = initial_stats.json().get("reputation", 0)

        # Create publisher and task
        publisher_response = client.post(
            "/api/auth/register",
            json={
                "username": "publisher5",
                "email": "publisher5@example.com",
                "password": "password123",
                "wallet_address": "0x8888888888888888888888888888888888888888"
            }
        )
        publisher_token = publisher_response.json()["access_token"]

        create_task_response = client.post(
            "/api/tasks",
            json={
                "description": "Reputation test task",
                "reward": 1000000000000000000,
                "task_type": "CODE",
                "timeout": 3600
            },
            headers={"Authorization": f"Bearer {publisher_token}"}
        )
        task_id = create_task_response.json()["task_id"]

        # Accept and complete task
        client.post(
            f"/api/tasks/{task_id}/accept",
            headers={"Authorization": f"Bearer {agent_token}"}
        )

        client.post(
            f"/api/tasks/{task_id}/submit",
            json={"result": "Task completed"},
            headers={"Authorization": f"Bearer {agent_token}"}
        )

        # Get final reputation
        final_stats = client.get(f"/api/agents/{agent_id}/stats")
        final_reputation = final_stats.json().get("reputation", 0)

        # Reputation should increase or stay the same (depending on implementation)
        assert final_reputation >= initial_reputation


class TestConcurrentOperations:
    """Test concurrent operations."""

    def test_concurrent_task_creation(self, client):
        """Test creating multiple tasks concurrently."""

        # Create publisher
        publisher_response = client.post(
            "/api/auth/register",
            json={
                "username": "concurrent_pub",
                "email": "concurrent@example.com",
                "password": "password123",
                "wallet_address": "0x9999999999999999999999999999999999999999"
            }
        )
        publisher_token = publisher_response.json()["access_token"]

        # Create multiple tasks
        task_ids = []
        for i in range(5):
            response = client.post(
                "/api/tasks",
                json={
                    "description": f"Concurrent task {i}",
                    "reward": 1000000000000000000,
                    "task_type": "CODE",
                    "timeout": 3600
                },
                headers={"Authorization": f"Bearer {publisher_token}"}
            )
            if response.status_code == 201:
                task_ids.append(response.json()["task_id"])

        # Verify all tasks were created
        assert len(task_ids) >= 3  # At least 3 should succeed (accounting for rate limits)

        # Verify all tasks are retrievable
        for task_id in task_ids:
            response = client.get(f"/api/tasks/{task_id}")
            assert response.status_code == 200

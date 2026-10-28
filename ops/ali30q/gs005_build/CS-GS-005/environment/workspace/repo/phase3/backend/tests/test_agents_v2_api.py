"""
Tests for Agent V2 API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from eth_account import Account
from eth_account.messages import encode_defunct
from datetime import datetime, timezone

from main import app
from models.agent_v2 import AgentV2, Base
from utils.database import get_db
from utils.agent_auth import create_agent_message


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_agents_v2.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_account():
    """Create test Ethereum account."""
    return Account.create()


class TestAgentRegistration:
    """Test agent registration endpoint."""

    def test_register_agent_success(self, client, test_db, test_account):
        """Test successful agent registration."""
        # Create registration message
        name = "TestAgent"
        message = create_agent_message(f"Register agent: {name}")

        # Sign message
        message_hash = encode_defunct(text=message)
        signed = test_account.sign_message(message_hash)
        signature = signed.signature.hex()

        # Register agent
        response = client.post(
            "/api/agents/v2/register",
            json={
                "address": test_account.address,
                "name": name,
                "description": "Test agent description",
                "specialties": ["Python", "Testing"],
                "message": message,
                "signature": signature
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["address"].lower() == test_account.address.lower()
        assert data["name"] == name
        assert "monitoring_url" in data
        assert "monitoring_qr_code" in data

    def test_register_agent_invalid_signature(self, client, test_db, test_account):
        """Test registration with invalid signature."""
        name = "TestAgent"
        message = create_agent_message(f"Register agent: {name}")

        # Use invalid signature
        invalid_signature = "0x" + "00" * 65

        response = client.post(
            "/api/agents/v2/register",
            json={
                "address": test_account.address,
                "name": name,
                "message": message,
                "signature": invalid_signature
            }
        )

        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]

    def test_register_agent_duplicate_address(self, client, test_db, test_account):
        """Test registration with duplicate address."""
        # First registration
        name = "TestAgent"
        message = create_agent_message(f"Register agent: {name}")
        message_hash = encode_defunct(text=message)
        signed = test_account.sign_message(message_hash)
        signature = signed.signature.hex()

        client.post(
            "/api/agents/v2/register",
            json={
                "address": test_account.address,
                "name": name,
                "message": message,
                "signature": signature
            }
        )

        # Second registration (should fail)
        message2 = create_agent_message(f"Register agent: {name}")
        message_hash2 = encode_defunct(text=message2)
        signed2 = test_account.sign_message(message_hash2)
        signature2 = signed2.signature.hex()

        response = client.post(
            "/api/agents/v2/register",
            json={
                "address": test_account.address,
                "name": name,
                "message": message2,
                "signature": signature2
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_agent_invalid_address_format(self, client, test_db):
        """Test registration with invalid address format."""
        response = client.post(
            "/api/agents/v2/register",
            json={
                "address": "invalid_address",
                "name": "TestAgent",
                "message": "test",
                "signature": "0x00"
            }
        )

        assert response.status_code == 422  # Validation error


class TestAgentQueries:
    """Test agent query endpoints."""

    def setup_method(self):
        """Setup test data."""
        db = TestingSessionLocal()

        # Create test agents
        self.agent1 = AgentV2(
            address="0x1111111111111111111111111111111111111111",
            name="Agent 1",
            reputation=150,
            completed_tasks=10
        )
        self.agent2 = AgentV2(
            address="0x2222222222222222222222222222222222222222",
            name="Agent 2",
            reputation=200,
            completed_tasks=20
        )

        db.add(self.agent1)
        db.add(self.agent2)
        db.commit()
        db.close()

    def test_list_agents(self, client, test_db):
        """Test listing agents."""
        self.setup_method()

        response = client.get("/api/agents/v2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Should be sorted by reputation (descending)
        assert data[0]["reputation"] >= data[1]["reputation"]

    def test_list_agents_pagination(self, client, test_db):
        """Test agent listing with pagination."""
        self.setup_method()

        response = client.get("/api/agents/v2?skip=0&limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_agent_by_address(self, client, test_db):
        """Test getting agent by address."""
        self.setup_method()

        response = client.get(f"/api/agents/v2/{self.agent1.address}")

        assert response.status_code == 200
        data = response.json()
        assert data["address"] == self.agent1.address
        assert data["name"] == self.agent1.name

    def test_get_agent_not_found(self, client, test_db):
        """Test getting non-existent agent."""
        response = client.get("/api/agents/v2/0x9999999999999999999999999999999999999999")

        assert response.status_code == 404

    def test_get_agent_reputation(self, client, test_db):
        """Test getting agent reputation."""
        self.setup_method()

        response = client.get(f"/api/agents/v2/{self.agent1.address}/reputation")

        assert response.status_code == 200
        data = response.json()
        assert data["address"] == self.agent1.address
        assert data["reputation"] == self.agent1.reputation
        assert data["completed_tasks"] == self.agent1.completed_tasks
        assert "success_rate" in data


class TestAuthenticatedEndpoints:
    """Test endpoints requiring authentication."""

    def test_get_my_profile(self, client, test_db, test_account):
        """Test getting authenticated agent's profile."""
        # First register agent
        db = TestingSessionLocal()
        agent = AgentV2(
            address=test_account.address.lower(),
            name="TestAgent",
            reputation=100
        )
        db.add(agent)
        db.commit()
        db.close()

        # Create authenticated request
        message = create_agent_message("GET /api/agents/v2/me/profile")
        message_hash = encode_defunct(text=message)
        signed = test_account.sign_message(message_hash)
        signature = signed.signature.hex()

        response = client.get(
            "/api/agents/v2/me/profile",
            headers={
                "X-Agent-Address": test_account.address,
                "X-Agent-Signature": signature,
                "X-Agent-Message": message
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["address"].lower() == test_account.address.lower()
        assert data["name"] == "TestAgent"

    def test_get_my_balance(self, client, test_db, test_account):
        """Test getting authenticated agent's balance."""
        # Register agent with earnings
        db = TestingSessionLocal()
        agent = AgentV2(
            address=test_account.address.lower(),
            name="TestAgent",
            total_earnings=1000000000000000000,  # 1 ETH in Wei
            completed_tasks=10
        )
        db.add(agent)
        db.commit()
        db.close()

        # Create authenticated request
        message = create_agent_message("GET /api/agents/v2/me/balance")
        message_hash = encode_defunct(text=message)
        signed = test_account.sign_message(message_hash)
        signature = signed.signature.hex()

        response = client.get(
            "/api/agents/v2/me/balance",
            headers={
                "X-Agent-Address": test_account.address,
                "X-Agent-Signature": signature,
                "X-Agent-Message": message
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_earnings"] == 1000000000000000000
        assert data["completed_tasks"] == 10
        assert data["average_reward"] == 100000000000000000

    def test_authenticated_request_without_headers(self, client, test_db):
        """Test authenticated endpoint without required headers."""
        response = client.get("/api/agents/v2/me/profile")

        assert response.status_code == 422  # Missing required headers

    def test_authenticated_request_invalid_signature(self, client, test_db, test_account):
        """Test authenticated endpoint with invalid signature."""
        # Register agent
        db = TestingSessionLocal()
        agent = AgentV2(
            address=test_account.address.lower(),
            name="TestAgent"
        )
        db.add(agent)
        db.commit()
        db.close()

        # Create request with invalid signature
        message = create_agent_message("GET /api/agents/v2/me/profile")

        response = client.get(
            "/api/agents/v2/me/profile",
            headers={
                "X-Agent-Address": test_account.address,
                "X-Agent-Signature": "0x" + "00" * 65,
                "X-Agent-Message": message
            }
        )

        assert response.status_code == 401

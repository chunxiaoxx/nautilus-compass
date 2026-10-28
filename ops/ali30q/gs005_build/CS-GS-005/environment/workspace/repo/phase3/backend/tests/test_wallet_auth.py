"""
Tests for wallet authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
import secrets

from main import app
from models.database import Base, User, Agent
from utils.database import get_db
from utils.redis_cache import get_redis_cache


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_wallet_auth.db"
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
def client():
    """Create test client."""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_wallet():
    """Create a test wallet."""
    # Generate a random private key
    private_key = "0x" + secrets.token_hex(32)
    account = Account.from_key(private_key)

    return {
        "address": account.address.lower(),
        "private_key": private_key,
        "account": account
    }


@pytest.fixture
def redis_cache():
    """Get Redis cache instance."""
    return get_redis_cache()


def sign_message(message: str, private_key: str) -> str:
    """Sign a message with a private key."""
    w3 = Web3()
    account = Account.from_key(private_key)
    encoded_message = encode_defunct(text=message)
    signed_message = w3.eth.account.sign_message(encoded_message, private_key=private_key)
    return signed_message.signature.hex()


class TestGetNonce:
    """Tests for GET /api/auth/nonce endpoint."""

    def test_get_nonce_success(self, client, test_wallet, redis_cache):
        """Test successful nonce generation."""
        if not redis_cache:
            pytest.skip("Redis not available")

        response = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")

        assert response.status_code == 200
        data = response.json()

        assert "nonce" in data
        assert "message" in data
        assert len(data["nonce"]) == 64  # 32 bytes hex
        assert data["nonce"] in data["message"]
        assert "Sign this message to authenticate with Nautilus" in data["message"]

        # Verify nonce is stored in Redis
        stored_nonce = redis_cache.get(f"wallet_nonce:{test_wallet['address']}")
        assert stored_nonce == data["nonce"]

    def test_get_nonce_invalid_address(self, client):
        """Test nonce generation with invalid wallet address."""
        response = client.get("/api/auth/nonce?wallet_address=invalid")

        assert response.status_code == 400
        assert "Invalid wallet address" in response.json()["detail"]

    def test_get_nonce_missing_0x(self, client):
        """Test nonce generation with wallet address missing 0x prefix."""
        response = client.get("/api/auth/nonce?wallet_address=742d35Cc6634C0532925a3b844Bc9e7595f0bEb")

        assert response.status_code == 400

    def test_get_nonce_wrong_length(self, client):
        """Test nonce generation with wrong length wallet address."""
        response = client.get("/api/auth/nonce?wallet_address=0x123")

        assert response.status_code == 400

    def test_get_nonce_normalizes_address(self, client, redis_cache):
        """Test that wallet address is normalized to lowercase."""
        if not redis_cache:
            pytest.skip("Redis not available")

        uppercase_address = "0x742D35CC6634C0532925A3B844BC9E7595F0BEB"
        response = client.get(f"/api/auth/nonce?wallet_address={uppercase_address}")

        assert response.status_code == 200

        # Verify nonce is stored with lowercase address
        lowercase_address = uppercase_address.lower()
        stored_nonce = redis_cache.get(f"wallet_nonce:{lowercase_address}")
        assert stored_nonce is not None


class TestWalletRegister:
    """Tests for POST /api/auth/wallet-register endpoint."""

    def test_wallet_register_success(self, client, test_wallet, redis_cache):
        """Test successful wallet registration."""
        if not redis_cache:
            pytest.skip("Redis not available")

        # Get nonce
        nonce_response = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        nonce_data = nonce_response.json()
        message = nonce_data["message"]

        # Sign message
        signature = sign_message(message, test_wallet["private_key"])

        # Register
        register_data = {
            "wallet_address": test_wallet["address"],
            "signature": signature,
            "message": message,
            "username": "test_user",
            "email": "test@example.com"
        }

        response = client.post("/api/auth/wallet-register", json=register_data)

        assert response.status_code == 201
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify nonce is deleted after use
        stored_nonce = redis_cache.get(f"wallet_nonce:{test_wallet['address']}")
        assert stored_nonce is None

        # Verify user is created in database
        db = next(override_get_db())
        user = db.query(User).filter(User.wallet_address == test_wallet["address"]).first()
        assert user is not None
        assert user.username == "test_user"
        assert user.email == "test@example.com"
        assert user.is_active is True

        # Verify agent is created
        agent = db.query(Agent).filter(Agent.owner == test_wallet["address"]).first()
        assert agent is not None
        assert agent.name == "test_user"

    def test_wallet_register_auto_username(self, client, test_wallet, redis_cache):
        """Test wallet registration with auto-generated username."""
        if not redis_cache:
            pytest.skip("Redis not available")

        # Get nonce
        nonce_response = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        nonce_data = nonce_response.json()
        message = nonce_data["message"]

        # Sign message
        signature = sign_message(message, test_wallet["private_key"])

        # Register without username
        register_data = {
            "wallet_address": test_wallet["address"],
            "signature": signature,
            "message": message
        }

        response = client.post("/api/auth/wallet-register", json=register_data)

        assert response.status_code == 201

        # Verify user has auto-generated username
        db = next(override_get_db())
        user = db.query(User).filter(User.wallet_address == test_wallet["address"]).first()
        assert user is not None
        assert user.username.startswith("user_")

    def test_wallet_register_invalid_signature(self, client, test_wallet, redis_cache):
        """Test wallet registration with invalid signature."""
        if not redis_cache:
            pytest.skip("Redis not available")

        # Get nonce
        nonce_response = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        nonce_data = nonce_response.json()
        message = nonce_data["message"]

        # Use invalid signature
        invalid_signature = "0x" + "00" * 65

        register_data = {
            "wallet_address": test_wallet["address"],
            "signature": invalid_signature,
            "message": message
        }

        response = client.post("/api/auth/wallet-register", json=register_data)

        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]

    def test_wallet_register_expired_nonce(self, client, test_wallet, redis_cache):
        """Test wallet registration with expired nonce."""
        if not redis_cache:
            pytest.skip("Redis not available")

        # Try to register without getting nonce first
        register_data = {
            "wallet_address": test_wallet["address"],
            "signature": "0x" + "00" * 65,
            "message": "Sign this message to authenticate with Nautilus: expired_nonce"
        }

        response = client.post("/api/auth/wallet-register", json=register_data)

        assert response.status_code == 400
        assert "Nonce not found or expired" in response.json()["detail"]

    def test_wallet_register_duplicate_address(self, client, test_wallet, redis_cache):
        """Test wallet registration with already registered address."""
        if not redis_cache:
            pytest.skip("Redis not available")

        # First registration
        nonce_response = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        nonce_data = nonce_response.json()
        message = nonce_data["message"]
        signature = sign_message(message, test_wallet["private_key"])

        register_data = {
            "wallet_address": test_wallet["address"],
            "signature": signature,
            "message": message
        }

        response1 = client.post("/api/auth/wallet-register", json=register_data)
        assert response1.status_code == 201

        # Try to register again
        nonce_response2 = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        nonce_data2 = nonce_response2.json()
        message2 = nonce_data2["message"]
        signature2 = sign_message(message2, test_wallet["private_key"])

        register_data2 = {
            "wallet_address": test_wallet["address"],
            "signature": signature2,
            "message": message2
        }

        response2 = client.post("/api/auth/wallet-register", json=register_data2)

        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]

    def test_wallet_register_invalid_address_format(self, client):
        """Test wallet registration with invalid address format."""
        register_data = {
            "wallet_address": "invalid_address",
            "signature": "0x" + "00" * 65,
            "message": "test message"
        }

        response = client.post("/api/auth/wallet-register", json=register_data)

        assert response.status_code == 422  # Validation error


class TestWalletLogin:
    """Tests for POST /api/auth/wallet-login endpoint."""

    def test_wallet_login_success(self, client, test_wallet, redis_cache):
        """Test successful wallet login."""
        if not redis_cache:
            pytest.skip("Redis not available")

        # First register the wallet
        nonce_response = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        nonce_data = nonce_response.json()
        message = nonce_data["message"]
        signature = sign_message(message, test_wallet["private_key"])

        register_data = {
            "wallet_address": test_wallet["address"],
            "signature": signature,
            "message": message,
            "username": "test_user"
        }

        client.post("/api/auth/wallet-register", json=register_data)

        # Now login
        nonce_response2 = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        nonce_data2 = nonce_response2.json()
        message2 = nonce_data2["message"]
        signature2 = sign_message(message2, test_wallet["private_key"])

        login_data = {
            "wallet_address": test_wallet["address"],
            "signature": signature2,
            "message": message2
        }

        response = client.post("/api/auth/wallet-login", json=login_data)

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify nonce is deleted after use
        stored_nonce = redis_cache.get(f"wallet_nonce:{test_wallet['address']}")
        assert stored_nonce is None

    def test_wallet_login_not_registered(self, client, test_wallet, redis_cache):
        """Test wallet login with unregistered address."""
        if not redis_cache:
            pytest.skip("Redis not available")

        # Get nonce
        nonce_response = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        nonce_data = nonce_response.json()
        message = nonce_data["message"]
        signature = sign_message(message, test_wallet["private_key"])

        login_data = {
            "wallet_address": test_wallet["address"],
            "signature": signature,
            "message": message
        }

        response = client.post("/api/auth/wallet-login", json=login_data)

        assert response.status_code == 404
        assert "not registered" in response.json()["detail"]

    def test_wallet_login_invalid_signature(self, client, test_wallet, redis_cache):
        """Test wallet login with invalid signature."""
        if not redis_cache:
            pytest.skip("Redis not available")

        # First register
        nonce_response = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        nonce_data = nonce_response.json()
        message = nonce_data["message"]
        signature = sign_message(message, test_wallet["private_key"])

        register_data = {
            "wallet_address": test_wallet["address"],
            "signature": signature,
            "message": message
        }

        client.post("/api/auth/wallet-register", json=register_data)

        # Try to login with invalid signature
        nonce_response2 = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        nonce_data2 = nonce_response2.json()
        message2 = nonce_data2["message"]

        login_data = {
            "wallet_address": test_wallet["address"],
            "signature": "0x" + "00" * 65,
            "message": message2
        }

        response = client.post("/api/auth/wallet-login", json=login_data)

        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]

    def test_wallet_login_case_insensitive(self, client, test_wallet, redis_cache):
        """Test that wallet login is case-insensitive."""
        if not redis_cache:
            pytest.skip("Redis not available")

        # Register with lowercase
        nonce_response = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        nonce_data = nonce_response.json()
        message = nonce_data["message"]
        signature = sign_message(message, test_wallet["private_key"])

        register_data = {
            "wallet_address": test_wallet["address"],
            "signature": signature,
            "message": message
        }

        client.post("/api/auth/wallet-register", json=register_data)

        # Login with uppercase
        uppercase_address = test_wallet["address"].upper()
        nonce_response2 = client.get(f"/api/auth/nonce?wallet_address={uppercase_address}")
        nonce_data2 = nonce_response2.json()
        message2 = nonce_data2["message"]
        signature2 = sign_message(message2, test_wallet["private_key"])

        login_data = {
            "wallet_address": uppercase_address,
            "signature": signature2,
            "message": message2
        }

        response = client.post("/api/auth/wallet-login", json=login_data)

        assert response.status_code == 200


class TestWalletAuthIntegration:
    """Integration tests for wallet authentication flow."""

    def test_full_auth_flow(self, client, test_wallet, redis_cache):
        """Test complete authentication flow: nonce -> register -> login."""
        if not redis_cache:
            pytest.skip("Redis not available")

        # Step 1: Get nonce
        nonce_response = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        assert nonce_response.status_code == 200
        nonce_data = nonce_response.json()

        # Step 2: Register
        message = nonce_data["message"]
        signature = sign_message(message, test_wallet["private_key"])

        register_data = {
            "wallet_address": test_wallet["address"],
            "signature": signature,
            "message": message,
            "username": "integration_test_user",
            "email": "integration@test.com"
        }

        register_response = client.post("/api/auth/wallet-register", json=register_data)
        assert register_response.status_code == 201
        register_token = register_response.json()["access_token"]

        # Step 3: Use token to access protected endpoint
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {register_token}"}
        )
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["username"] == "integration_test_user"
        assert user_data["wallet_address"] == test_wallet["address"]

        # Step 4: Get new nonce for login
        nonce_response2 = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        assert nonce_response2.status_code == 200
        nonce_data2 = nonce_response2.json()

        # Step 5: Login
        message2 = nonce_data2["message"]
        signature2 = sign_message(message2, test_wallet["private_key"])

        login_data = {
            "wallet_address": test_wallet["address"],
            "signature": signature2,
            "message": message2
        }

        login_response = client.post("/api/auth/wallet-login", json=login_data)
        assert login_response.status_code == 200
        login_token = login_response.json()["access_token"]

        # Step 6: Use login token
        me_response2 = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {login_token}"}
        )
        assert me_response2.status_code == 200
        assert me_response2.json()["username"] == "integration_test_user"

    def test_nonce_reuse_prevention(self, client, test_wallet, redis_cache):
        """Test that nonce cannot be reused."""
        if not redis_cache:
            pytest.skip("Redis not available")

        # Get nonce
        nonce_response = client.get(f"/api/auth/nonce?wallet_address={test_wallet['address']}")
        nonce_data = nonce_response.json()
        message = nonce_data["message"]
        signature = sign_message(message, test_wallet["private_key"])

        register_data = {
            "wallet_address": test_wallet["address"],
            "signature": signature,
            "message": message
        }

        # First registration succeeds
        response1 = client.post("/api/auth/wallet-register", json=register_data)
        assert response1.status_code == 201

        # Try to reuse same nonce (should fail)
        response2 = client.post("/api/auth/wallet-register", json=register_data)
        assert response2.status_code == 400
        assert "Nonce not found or expired" in response2.json()["detail"]

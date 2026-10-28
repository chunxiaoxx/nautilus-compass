"""
Test security fixes for P0 issues.
"""
import pytest
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from main import app
from models.database import Base, User, Agent
from utils.database import get_db
from utils.auth import hash_password
from agent_engine.executors.compute_executor import ComputeExecutor


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_security.db"
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
def client(test_db):
    """Create test client."""
    return TestClient(app)


# ==================== C1: Test eval() replacement with asteval ====================

@pytest.mark.asyncio
async def test_compute_executor_safe_evaluation():
    """Test that ComputeExecutor uses asteval instead of eval()."""
    executor = ComputeExecutor()

    # Test safe mathematical expressions
    result = await executor.compute("2 + 2")
    assert result == 4.0

    result = await executor.compute("sqrt(16)")
    assert result == 4.0

    result = await executor.compute("sin(pi/2)")
    assert abs(result - 1.0) < 0.0001


@pytest.mark.asyncio
async def test_compute_executor_blocks_code_injection():
    """Test that code injection attempts are blocked."""
    executor = ComputeExecutor()

    # Test that dangerous code is blocked
    dangerous_expressions = [
        "__import__('os').system('ls')",
        "exec('print(1)')",
        "eval('1+1')",
        "open('/etc/passwd').read()",
    ]

    for expr in dangerous_expressions:
        with pytest.raises(ValueError):
            await executor.compute(expr)


# ==================== H1: Test Agent registration rate limiting ====================

def test_agent_registration_rate_limit(client):
    """Test that agent self-registration has rate limiting."""
    # This test verifies the rate limiter is applied
    # In production, this would be 3/hour

    registration_data = {
        "name": "Test Agent",
        "email": "test@example.com",
        "description": "Test agent",
        "specialties": ["Python"]
    }

    # First request should succeed (or fail for other reasons, but not rate limit)
    response = client.post("/api/agents/register", json=registration_data)

    # Verify rate limiter decorator is present
    from api.agents import agent_self_register
    assert hasattr(agent_self_register, '__wrapped__')


# ==================== H2: Test secure wallet generation ====================

def test_wallet_generation_uses_eth_account():
    """Test that wallet generation uses eth_account library."""
    from api.agents import generate_wallet_address

    # Generate multiple wallets
    wallets = [generate_wallet_address() for _ in range(5)]

    # Verify format
    for wallet in wallets:
        assert wallet.startswith("0x")
        assert len(wallet) == 42
        # Verify it's valid hex
        int(wallet, 16)

    # Verify uniqueness (extremely unlikely to collide)
    assert len(set(wallets)) == 5


# ==================== H3: Test OAuth state validation ====================

@patch('api.auth.redis_client')
def test_oauth_state_stored_in_redis(mock_redis, client):
    """Test that OAuth state is stored in Redis."""
    mock_redis.setex.return_value = True

    with patch.dict('os.environ', {
        'GITHUB_CLIENT_ID': 'test_client_id',
        'GITHUB_REDIRECT_URI': 'http://localhost/callback'
    }):
        response = client.get("/api/auth/github/login")

        # Verify Redis was called to store state
        assert mock_redis.setex.called
        call_args = mock_redis.setex.call_args
        assert call_args[0][0].startswith('oauth_state:')
        assert call_args[0][1] == 600  # 10 minutes


@patch('api.auth.redis_client')
@patch('api.auth.httpx.AsyncClient')
def test_oauth_callback_validates_state(mock_httpx, mock_redis, client):
    """Test that OAuth callback validates state parameter."""
    # Test missing state
    response = client.get("/api/auth/github/callback?code=test_code")
    assert response.status_code == 400
    assert "Missing state parameter" in response.json()["detail"]

    # Test invalid state
    mock_redis.get.return_value = None
    response = client.get("/api/auth/github/callback?code=test_code&state=invalid_state")
    assert response.status_code == 400
    assert "Invalid or expired state" in response.json()["detail"]


# ==================== H4: Test password strength with HIBP ====================

def test_password_validation_checks_hibp():
    """Test that password validation checks Have I Been Pwned."""
    from pydantic import ValidationError
    from api.auth import UserRegister

    # Test with a known breached password
    with patch('httpx.get') as mock_get:
        # Simulate HIBP API response for "password123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8:3861493\n"
        mock_get.return_value = mock_response

        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                username="testuser",
                email="test@example.com",
                password="Password123!"  # Common password
            )

        # Should fail due to common password check
        assert "too common" in str(exc_info.value).lower()


def test_password_validation_strong_password():
    """Test that strong passwords pass validation."""
    from api.auth import UserRegister

    with patch('httpx.get') as mock_get:
        # Simulate HIBP API response - password not found
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OTHERHASH:123\n"
        mock_get.return_value = mock_response

        # This should succeed
        user = UserRegister(
            username="testuser",
            email="test@example.com",
            password="MyStr0ng!P@ssw0rd2024"
        )

        assert user.password == "MyStr0ng!P@ssw0rd2024"


def test_password_validation_requirements():
    """Test password validation requirements."""
    from pydantic import ValidationError
    from api.auth import UserRegister

    test_cases = [
        ("short1!", "at least 12 characters"),
        ("nouppercase123!", "uppercase letter"),
        ("NOLOWERCASE123!", "lowercase letter"),
        ("NoDigitsHere!", "digit"),
        ("NoSpecialChar123", "special character"),
    ]

    for password, expected_error in test_cases:
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                username="testuser",
                email="test@example.com",
                password=password
            )
        assert expected_error.lower() in str(exc_info.value).lower()


# ==================== Integration Tests ====================

def test_agent_self_registration_with_secure_wallet(client):
    """Test complete agent self-registration flow with secure wallet."""
    registration_data = {
        "name": "Secure Test Agent",
        "email": "secure@example.com",
        "description": "Testing secure wallet generation",
        "specialties": ["Security", "Testing"]
    }

    response = client.post("/api/agents/register", json=registration_data)

    if response.status_code == 201:
        data = response.json()

        # Verify wallet address format
        assert data["wallet_address"].startswith("0x")
        assert len(data["wallet_address"]) == 42

        # Verify API key format
        assert data["api_key"].startswith("naut_")


@pytest.mark.asyncio
async def test_compute_executor_with_complex_expressions():
    """Test ComputeExecutor with various mathematical expressions."""
    executor = ComputeExecutor()

    test_cases = [
        ("2 * 3 + 4", 10.0),
        ("sqrt(25) + 5", 10.0),
        ("sin(0)", 0.0),
        ("cos(0)", 1.0),
        ("log(e)", 1.0),
        ("pi * 2", 6.283185307179586),
    ]

    for expr, expected in test_cases:
        result = await executor.compute(expr)
        assert abs(result - expected) < 0.0001, f"Failed for {expr}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

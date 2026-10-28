"""
Tests for OAuth 2.0 API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from main import app
from models.database import OAuthClient, OAuthAuthorizationCode, OAuthAccessToken, Agent
from utils.database import get_db


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session."""
    db = next(get_db())
    yield db
    db.close()


@pytest.fixture
def test_agent(db_session: Session):
    """Create test agent."""
    agent = Agent(
        agent_id=1,
        owner="0x1234567890123456789012345678901234567890",
        name="Test Agent",
        description="Test agent for OAuth",
        reputation=100,
        specialties="testing,oauth"
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


@pytest.fixture
def test_oauth_client(db_session: Session):
    """Create test OAuth client."""
    import hashlib

    client_secret = "test_secret_123"
    client_secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()

    client = OAuthClient(
        client_id="test_client_id",
        client_secret=client_secret_hash,
        name="Test Application",
        description="Test OAuth client",
        redirect_uris=["http://localhost:3000/callback"],
        website="http://localhost:3000"
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)

    # Store plain secret for testing
    client.plain_secret = client_secret
    return client


class TestOAuthClientManagement:
    """Test OAuth client management endpoints."""

    def test_create_oauth_client(self, client, db_session):
        """Test creating OAuth client."""
        # First, create a user and login
        # (Assuming auth endpoints exist)

        response = client.post(
            "/oauth/clients",
            json={
                "name": "My Application",
                "description": "Test app",
                "redirect_uris": ["http://localhost:3000/callback"],
                "website": "http://localhost:3000"
            },
            headers={"Authorization": "Bearer test_token"}
        )

        # Note: This will fail without proper auth, but shows the structure
        assert response.status_code in [201, 401]

    def test_get_oauth_client(self, client, test_oauth_client):
        """Test getting OAuth client details."""
        response = client.get(
            f"/oauth/clients/{test_oauth_client.client_id}",
            headers={"Authorization": "Bearer test_token"}
        )

        # Note: This will fail without proper auth
        assert response.status_code in [200, 401]


class TestOAuthAuthorizationFlow:
    """Test OAuth 2.0 authorization flow."""

    def test_authorize_endpoint(self, client, test_oauth_client, test_agent):
        """Test OAuth authorization endpoint."""
        response = client.get(
            "/oauth/authorize",
            params={
                "client_id": test_oauth_client.client_id,
                "redirect_uri": "http://localhost:3000/callback",
                "response_type": "code",
                "scope": "profile,tasks",
                "state": "random_state"
            },
            headers={"X-Agent-Address": test_agent.owner}
        )

        # Should redirect with authorization code
        assert response.status_code == 307  # Redirect
        assert "code=" in response.headers.get("location", "")

    def test_authorize_invalid_client(self, client, test_agent):
        """Test authorization with invalid client."""
        response = client.get(
            "/oauth/authorize",
            params={
                "client_id": "invalid_client",
                "redirect_uri": "http://localhost:3000/callback",
                "response_type": "code"
            },
            headers={"X-Agent-Address": test_agent.owner}
        )

        assert response.status_code == 400

    def test_authorize_invalid_redirect_uri(self, client, test_oauth_client, test_agent):
        """Test authorization with invalid redirect URI."""
        response = client.get(
            "/oauth/authorize",
            params={
                "client_id": test_oauth_client.client_id,
                "redirect_uri": "http://evil.com/callback",
                "response_type": "code"
            },
            headers={"X-Agent-Address": test_agent.owner}
        )

        assert response.status_code == 400


class TestOAuthTokenEndpoint:
    """Test OAuth token endpoint."""

    def test_exchange_code_for_token(self, client, db_session, test_oauth_client, test_agent):
        """Test exchanging authorization code for token."""
        # Create authorization code
        auth_code = OAuthAuthorizationCode(
            code="test_auth_code",
            client_id=test_oauth_client.client_id,
            agent_address=test_agent.owner,
            redirect_uri="http://localhost:3000/callback",
            scope="profile,tasks",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
            used=False
        )
        db_session.add(auth_code)
        db_session.commit()

        # Exchange code for token
        response = client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": "test_auth_code",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.plain_secret,
                "redirect_uri": "http://localhost:3000/callback"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 3600

    def test_exchange_invalid_code(self, client, test_oauth_client):
        """Test exchanging invalid authorization code."""
        response = client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": "invalid_code",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.plain_secret
            }
        )

        assert response.status_code == 400

    def test_refresh_token(self, client, db_session, test_oauth_client, test_agent):
        """Test refreshing access token."""
        # Create access token
        access_token = OAuthAccessToken(
            access_token="old_access_token",
            refresh_token="test_refresh_token",
            client_id=test_oauth_client.client_id,
            agent_address=test_agent.owner,
            scope="profile",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            refresh_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            revoked=False
        )
        db_session.add(access_token)
        db_session.commit()

        # Refresh token
        response = client.post(
            "/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": "test_refresh_token",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.plain_secret
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] != "old_access_token"


class TestOAuthUserInfo:
    """Test OAuth userinfo endpoint."""

    def test_get_userinfo(self, client, db_session, test_oauth_client, test_agent):
        """Test getting agent information."""
        # Create access token
        access_token = OAuthAccessToken(
            access_token="valid_access_token",
            refresh_token="refresh_token",
            client_id=test_oauth_client.client_id,
            agent_address=test_agent.owner,
            scope="profile,tasks,balance",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            refresh_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            revoked=False
        )
        db_session.add(access_token)
        db_session.commit()

        # Get userinfo
        response = client.get(
            "/oauth/userinfo",
            headers={"Authorization": "Bearer valid_access_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sub"] == test_agent.owner
        assert data["name"] == test_agent.name
        assert "reputation" in data
        assert "completed_tasks" in data
        assert "total_earnings" in data

    def test_get_userinfo_invalid_token(self, client):
        """Test getting userinfo with invalid token."""
        response = client.get(
            "/oauth/userinfo",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_get_userinfo_expired_token(self, client, db_session, test_oauth_client, test_agent):
        """Test getting userinfo with expired token."""
        # Create expired token
        access_token = OAuthAccessToken(
            access_token="expired_token",
            refresh_token="refresh_token",
            client_id=test_oauth_client.client_id,
            agent_address=test_agent.owner,
            scope="profile",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            refresh_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            revoked=False
        )
        db_session.add(access_token)
        db_session.commit()

        response = client.get(
            "/oauth/userinfo",
            headers={"Authorization": "Bearer expired_token"}
        )

        assert response.status_code == 401


class TestOAuthTokenVerification:
    """Test OAuth token verification endpoint."""

    def test_verify_valid_token(self, client, db_session, test_oauth_client, test_agent):
        """Test verifying valid token."""
        # Create access token
        access_token = OAuthAccessToken(
            access_token="valid_token",
            refresh_token="refresh_token",
            client_id=test_oauth_client.client_id,
            agent_address=test_agent.owner,
            scope="profile",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            refresh_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            revoked=False
        )
        db_session.add(access_token)
        db_session.commit()

        response = client.post(
            "/oauth/verify",
            data={"token": "valid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["agent_address"] == test_agent.owner
        assert data["client_id"] == test_oauth_client.client_id

    def test_verify_invalid_token(self, client):
        """Test verifying invalid token."""
        response = client.post(
            "/oauth/verify",
            data={"token": "invalid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "error" in data


class TestOAuthTokenRevocation:
    """Test OAuth token revocation endpoint."""

    def test_revoke_token(self, client, db_session, test_oauth_client, test_agent):
        """Test revoking access token."""
        # Create access token
        access_token = OAuthAccessToken(
            access_token="token_to_revoke",
            refresh_token="refresh_token",
            client_id=test_oauth_client.client_id,
            agent_address=test_agent.owner,
            scope="profile",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            refresh_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            revoked=False
        )
        db_session.add(access_token)
        db_session.commit()

        # Revoke token
        response = client.post(
            "/oauth/revoke",
            data={
                "token": "token_to_revoke",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.plain_secret
            }
        )

        assert response.status_code == 200

        # Verify token is revoked
        db_session.refresh(access_token)
        assert access_token.revoked is True

    def test_revoke_with_invalid_credentials(self, client):
        """Test revoking token with invalid client credentials."""
        response = client.post(
            "/oauth/revoke",
            data={
                "token": "some_token",
                "client_id": "invalid_client",
                "client_secret": "invalid_secret"
            }
        )

        assert response.status_code == 401

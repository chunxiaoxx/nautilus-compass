"""
Quick test script for OAuth 2.0 implementation.

Run this to verify OAuth endpoints are working.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from main import app
from models.database import Base, Agent, OAuthClient
from utils.database import get_engine, get_db
from sqlalchemy.orm import Session
import hashlib


def setup_test_data():
    """Setup test data for OAuth testing."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    db = next(get_db())

    # Create test agent
    test_agent = db.query(Agent).filter(Agent.owner == "0x1234567890123456789012345678901234567890").first()
    if not test_agent:
        test_agent = Agent(
            agent_id=999,
            owner="0x1234567890123456789012345678901234567890",
            name="Test OAuth Agent",
            description="Agent for OAuth testing",
            reputation=100,
            specialties="testing,oauth"
        )
        db.add(test_agent)
        db.commit()
        print("✓ Created test agent")
    else:
        print("✓ Test agent already exists")

    # Create test OAuth client
    client_secret = "test_secret_12345"
    client_secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()

    test_client = db.query(OAuthClient).filter(OAuthClient.client_id == "test_client_oauth").first()
    if not test_client:
        test_client = OAuthClient(
            client_id="test_client_oauth",
            client_secret=client_secret_hash,
            name="Test OAuth Application",
            description="Test OAuth client",
            redirect_uris=["http://localhost:3000/callback", "http://localhost:5000/callback"],
            website="http://localhost:3000"
        )
        db.add(test_client)
        db.commit()
        print("✓ Created test OAuth client")
        print(f"  Client ID: test_client_oauth")
        print(f"  Client Secret: {client_secret}")
    else:
        print("✓ Test OAuth client already exists")

    db.close()
    return test_agent, client_secret


def test_oauth_endpoints():
    """Test OAuth endpoints."""
    print("\n" + "="*60)
    print("Testing OAuth 2.0 Endpoints")
    print("="*60)

    # Setup test data
    test_agent, client_secret = setup_test_data()

    client = TestClient(app)

    # Test 1: Authorization endpoint
    print("\n1. Testing authorization endpoint...")
    response = client.get(
        "/oauth/authorize",
        params={
            "client_id": "test_client_oauth",
            "redirect_uri": "http://localhost:3000/callback",
            "response_type": "code",
            "scope": "profile,tasks",
            "state": "test_state_123"
        },
        headers={"X-Agent-Address": "0x1234567890123456789012345678901234567890"},
        follow_redirects=False
    )

    if response.status_code == 307:
        print("✓ Authorization endpoint working")
        location = response.headers.get("location", "")
        if "code=" in location:
            print("✓ Authorization code generated")
            # Extract code
            code = location.split("code=")[1].split("&")[0]
            print(f"  Authorization code: {code[:20]}...")

            # Test 2: Token endpoint
            print("\n2. Testing token endpoint...")
            token_response = client.post(
                "/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": "test_client_oauth",
                    "client_secret": client_secret,
                    "redirect_uri": "http://localhost:3000/callback"
                }
            )

            if token_response.status_code == 200:
                print("✓ Token endpoint working")
                token_data = token_response.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                print(f"✓ Access token: {access_token[:20]}...")
                print(f"✓ Refresh token: {refresh_token[:20]}...")

                # Test 3: Userinfo endpoint
                print("\n3. Testing userinfo endpoint...")
                userinfo_response = client.get(
                    "/oauth/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                if userinfo_response.status_code == 200:
                    print("✓ Userinfo endpoint working")
                    user_info = userinfo_response.json()
                    print(f"  Agent: {user_info.get('name')}")
                    print(f"  Address: {user_info.get('sub')}")
                    print(f"  Reputation: {user_info.get('reputation')}")
                else:
                    print(f"✗ Userinfo endpoint failed: {userinfo_response.status_code}")

                # Test 4: Verify endpoint
                print("\n4. Testing verify endpoint...")
                verify_response = client.post(
                    "/oauth/verify",
                    data={"token": access_token}
                )

                if verify_response.status_code == 200:
                    print("✓ Verify endpoint working")
                    verify_data = verify_response.json()
                    if verify_data.get("valid"):
                        print("✓ Token is valid")
                    else:
                        print("✗ Token validation failed")
                else:
                    print(f"✗ Verify endpoint failed: {verify_response.status_code}")

                # Test 5: Refresh token
                print("\n5. Testing refresh token...")
                refresh_response = client.post(
                    "/oauth/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": "test_client_oauth",
                        "client_secret": client_secret
                    }
                )

                if refresh_response.status_code == 200:
                    print("✓ Refresh token working")
                    new_token_data = refresh_response.json()
                    new_access_token = new_token_data.get("access_token")
                    print(f"✓ New access token: {new_access_token[:20]}...")
                else:
                    print(f"✗ Refresh token failed: {refresh_response.status_code}")

                # Test 6: Revoke token
                print("\n6. Testing revoke endpoint...")
                revoke_response = client.post(
                    "/oauth/revoke",
                    data={
                        "token": access_token,
                        "client_id": "test_client_oauth",
                        "client_secret": client_secret
                    }
                )

                if revoke_response.status_code == 200:
                    print("✓ Revoke endpoint working")
                    print("✓ Token revoked successfully")
                else:
                    print(f"✗ Revoke endpoint failed: {revoke_response.status_code}")

            else:
                print(f"✗ Token endpoint failed: {token_response.status_code}")
                print(f"  Response: {token_response.text}")
        else:
            print("✗ No authorization code in redirect")
    else:
        print(f"✗ Authorization endpoint failed: {response.status_code}")
        print(f"  Response: {response.text}")

    # Test error cases
    print("\n7. Testing error cases...")

    # Invalid client_id
    response = client.get(
        "/oauth/authorize",
        params={
            "client_id": "invalid_client",
            "redirect_uri": "http://localhost:3000/callback",
            "response_type": "code"
        },
        headers={"X-Agent-Address": "0x1234567890123456789012345678901234567890"}
    )
    if response.status_code == 400:
        print("✓ Invalid client_id rejected")
    else:
        print(f"✗ Invalid client_id not rejected: {response.status_code}")

    # Invalid redirect_uri
    response = client.get(
        "/oauth/authorize",
        params={
            "client_id": "test_client_oauth",
            "redirect_uri": "http://evil.com/callback",
            "response_type": "code"
        },
        headers={"X-Agent-Address": "0x1234567890123456789012345678901234567890"}
    )
    if response.status_code == 400:
        print("✓ Invalid redirect_uri rejected")
    else:
        print(f"✗ Invalid redirect_uri not rejected: {response.status_code}")

    # Invalid token
    response = client.get(
        "/oauth/userinfo",
        headers={"Authorization": "Bearer invalid_token"}
    )
    if response.status_code == 401:
        print("✓ Invalid token rejected")
    else:
        print(f"✗ Invalid token not rejected: {response.status_code}")

    print("\n" + "="*60)
    print("OAuth 2.0 Testing Complete!")
    print("="*60)


if __name__ == "__main__":
    try:
        test_oauth_endpoints()
        print("\n✅ All OAuth tests passed!")
    except Exception as e:
        print(f"\n✗ OAuth testing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

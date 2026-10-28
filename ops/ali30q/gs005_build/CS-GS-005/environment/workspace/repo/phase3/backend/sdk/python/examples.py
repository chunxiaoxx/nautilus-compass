"""
Nautilus OAuth 2.0 SDK Examples

Demonstrates how to integrate Nautilus OAuth into your application.
"""
from nautilus_oauth import NautilusOAuth
from flask import Flask, request, redirect, session
import secrets


# ============================================================================
# Example 1: Flask Web Application Integration
# ============================================================================

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Initialize OAuth client
oauth = NautilusOAuth(
    client_id="your_client_id_here",
    client_secret="your_client_secret_here",
    redirect_uri="http://localhost:5000/callback",
    base_url="https://nautilus.social"
)


@app.route('/')
def index():
    """Home page."""
    if 'access_token' in session:
        # User is logged in
        user_info = oauth.get_user_info(session['access_token'])
        return f"""
        <h1>Welcome, {user_info['name']}!</h1>
        <p>Agent Address: {user_info['sub']}</p>
        <p>Reputation: {user_info.get('reputation', 'N/A')}</p>
        <p>Completed Tasks: {user_info.get('completed_tasks', 'N/A')}</p>
        <a href="/logout">Logout</a>
        """
    else:
        # User is not logged in
        return '<a href="/login">Login with Nautilus</a>'


@app.route('/login')
def login():
    """Redirect to Nautilus OAuth authorization."""
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    auth_url = oauth.get_authorization_url(
        scope="profile,tasks,balance",
        state=state
    )
    return redirect(auth_url)


@app.route('/callback')
def callback():
    """OAuth callback handler."""
    # Verify state to prevent CSRF
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        return "Invalid state parameter", 400

    # Exchange code for token
    code = request.args.get('code')
    if not code:
        return "No authorization code received", 400

    try:
        token_response = oauth.exchange_code(code)
        session['access_token'] = token_response['access_token']
        session['refresh_token'] = token_response['refresh_token']
        return redirect('/')
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/logout')
def logout():
    """Logout and revoke token."""
    if 'access_token' in session:
        try:
            oauth.revoke_token(session['access_token'])
        except Exception:
            pass
        session.clear()
    return redirect('/')


# ============================================================================
# Example 2: API Server Integration
# ============================================================================

from fastapi import FastAPI, Depends, HTTPException, Header
from typing import Optional

api_app = FastAPI()


async def verify_nautilus_token(authorization: str = Header(...)) -> dict:
    """
    Dependency to verify Nautilus OAuth token.

    Use this in your API endpoints to require Nautilus authentication.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")

    # Verify token
    verification = oauth.verify_token(token)

    if not verification.get('valid'):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return verification


@api_app.get("/api/protected")
async def protected_endpoint(token_info: dict = Depends(verify_nautilus_token)):
    """
    Protected API endpoint that requires Nautilus authentication.
    """
    return {
        "message": "This is a protected endpoint",
        "agent_address": token_info['agent_address'],
        "client_id": token_info['client_id']
    }


@api_app.get("/api/agent-info")
async def get_agent_info(authorization: str = Header(...)):
    """
    Get agent information from Nautilus.
    """
    token = authorization.replace("Bearer ", "")

    try:
        user_info = oauth.get_user_info(token)
        return user_info
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# ============================================================================
# Example 3: CLI Application
# ============================================================================

def cli_oauth_flow():
    """
    OAuth flow for CLI applications.

    This uses device flow simulation - user opens browser to authorize.
    """
    import webbrowser

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Get authorization URL
    auth_url = oauth.get_authorization_url(
        scope="profile,tasks",
        state=state
    )

    print("Opening browser for authorization...")
    print(f"If browser doesn't open, visit: {auth_url}")
    webbrowser.open(auth_url)

    # In a real CLI app, you'd need to run a local server to receive the callback
    # For simplicity, we'll ask user to paste the code
    print("\nAfter authorizing, you'll be redirected to a URL with a 'code' parameter.")
    code = input("Paste the authorization code here: ")

    # Exchange code for token
    try:
        token_response = oauth.exchange_code(code)
        access_token = token_response['access_token']

        # Get user info
        user_info = oauth.get_user_info(access_token)

        print(f"\n✓ Successfully authenticated!")
        print(f"Agent: {user_info['name']}")
        print(f"Address: {user_info['sub']}")
        print(f"Reputation: {user_info.get('reputation', 'N/A')}")

        # Save token for future use
        with open('.nautilus_token', 'w') as f:
            f.write(access_token)

        return access_token
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return None


# ============================================================================
# Example 4: Background Service with Token Refresh
# ============================================================================

import time
from datetime import datetime, timedelta


class NautilusAuthService:
    """
    Background service that maintains OAuth authentication.

    Automatically refreshes tokens before they expire.
    """

    def __init__(self, oauth_client: NautilusOAuth):
        self.oauth = oauth_client
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

    def authenticate(self, code: str):
        """Initial authentication with authorization code."""
        token_response = self.oauth.exchange_code(code)
        self._update_tokens(token_response)

    def _update_tokens(self, token_response: dict):
        """Update stored tokens."""
        self.access_token = token_response['access_token']
        self.refresh_token = token_response['refresh_token']
        self.token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=token_response['expires_in']
        )

    def get_valid_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token
        """
        # Check if token needs refresh (refresh 5 minutes before expiry)
        if self.token_expires_at and \
           datetime.now(timezone.utc) >= self.token_expires_at - timedelta(minutes=5):
            self._refresh_token()

        return self.access_token

    def _refresh_token(self):
        """Refresh access token."""
        try:
            token_response = self.oauth.refresh_token(self.refresh_token)
            self._update_tokens(token_response)
            print("✓ Token refreshed successfully")
        except Exception as e:
            print(f"✗ Token refresh failed: {e}")
            raise

    def make_authenticated_request(self, endpoint: str) -> dict:
        """
        Make an authenticated request to Nautilus API.

        Args:
            endpoint: API endpoint (e.g., "/api/tasks")

        Returns:
            API response
        """
        token = self.get_valid_token()

        import requests
        response = requests.get(
            f"{self.oauth.base_url}{endpoint}",
            headers={'Authorization': f'Bearer {token}'}
        )
        response.raise_for_status()
        return response.json()


# ============================================================================
# Example 5: Multi-Agent Management
# ============================================================================

class MultiAgentManager:
    """
    Manage multiple agent authentications.

    Useful for platforms that integrate multiple Nautilus agents.
    """

    def __init__(self, oauth_client: NautilusOAuth):
        self.oauth = oauth_client
        self.agents = {}  # agent_address -> token_info

    def add_agent(self, code: str) -> str:
        """
        Add an agent by exchanging authorization code.

        Returns:
            Agent address
        """
        token_response = self.oauth.exchange_code(code)
        user_info = self.oauth.get_user_info(token_response['access_token'])

        agent_address = user_info['sub']
        self.agents[agent_address] = {
            'access_token': token_response['access_token'],
            'refresh_token': token_response['refresh_token'],
            'user_info': user_info
        }

        return agent_address

    def get_agent_info(self, agent_address: str) -> dict:
        """Get cached agent information."""
        if agent_address not in self.agents:
            raise ValueError(f"Agent {agent_address} not found")
        return self.agents[agent_address]['user_info']

    def remove_agent(self, agent_address: str):
        """Remove agent and revoke token."""
        if agent_address in self.agents:
            token = self.agents[agent_address]['access_token']
            try:
                self.oauth.revoke_token(token)
            except Exception:
                pass
            del self.agents[agent_address]

    def list_agents(self) -> list:
        """List all authenticated agents."""
        return [
            {
                'address': addr,
                'name': info['user_info']['name'],
                'reputation': info['user_info'].get('reputation')
            }
            for addr, info in self.agents.items()
        ]


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    print("Nautilus OAuth SDK Examples")
    print("=" * 50)
    print()
    print("1. Flask Web App (run with: flask run)")
    print("2. FastAPI Server (run with: uvicorn examples:api_app)")
    print("3. CLI OAuth Flow")
    print("4. Background Service")
    print("5. Multi-Agent Manager")
    print()

    choice = input("Select example (1-5): ")

    if choice == "3":
        cli_oauth_flow()
    else:
        print(f"To run example {choice}, see the code comments above.")

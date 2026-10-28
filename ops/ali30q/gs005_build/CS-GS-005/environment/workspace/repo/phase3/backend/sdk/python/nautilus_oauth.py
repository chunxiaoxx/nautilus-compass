"""
Nautilus OAuth 2.0 Python SDK

Simple OAuth client for integrating with Nautilus Agent authentication.
"""
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlencode


class NautilusOAuth:
    """Nautilus OAuth 2.0 client."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        base_url: str = "https://nautilus.social"
    ):
        """
        Initialize Nautilus OAuth client.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: Redirect URI for authorization callback
            base_url: Nautilus API base URL
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def get_authorization_url(
        self,
        scope: str = "profile,tasks,balance",
        state: Optional[str] = None
    ) -> str:
        """
        Get authorization URL for user to authorize.

        Args:
            scope: Requested scopes (comma-separated)
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': scope
        }

        if state:
            params['state'] = state

        return f"{self.base_url}/oauth/authorize?{urlencode(params)}"

    def exchange_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback

        Returns:
            Token response with access_token, refresh_token, etc.

        Raises:
            requests.HTTPError: If token exchange fails
        """
        response = self.session.post(
            f"{self.base_url}/oauth/token",
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri
            }
        )
        response.raise_for_status()
        return response.json()

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            Token response with new access_token

        Raises:
            requests.HTTPError: If token refresh fails
        """
        response = self.session.post(
            f"{self.base_url}/oauth/token",
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
        )
        response.raise_for_status()
        return response.json()

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get agent information using access token.

        Args:
            access_token: Access token

        Returns:
            Agent information

        Raises:
            requests.HTTPError: If request fails
        """
        response = self.session.get(
            f"{self.base_url}/oauth/userinfo",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        return response.json()

    def verify_token(self, access_token: str) -> Dict[str, Any]:
        """
        Verify access token validity.

        Args:
            access_token: Access token to verify

        Returns:
            Verification result

        Raises:
            requests.HTTPError: If request fails
        """
        response = self.session.post(
            f"{self.base_url}/oauth/verify",
            data={'token': access_token}
        )
        response.raise_for_status()
        return response.json()

    def revoke_token(
        self,
        token: str,
        token_type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Revoke access or refresh token.

        Args:
            token: Token to revoke
            token_type_hint: 'access_token' or 'refresh_token'

        Returns:
            Revocation result

        Raises:
            requests.HTTPError: If request fails
        """
        data = {
            'token': token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        if token_type_hint:
            data['token_type_hint'] = token_type_hint

        response = self.session.post(
            f"{self.base_url}/oauth/revoke",
            data=data
        )
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    # Initialize OAuth client
    oauth = NautilusOAuth(
        client_id="your_client_id",
        client_secret="your_client_secret",
        redirect_uri="https://yourapp.com/callback"
    )

    # Step 1: Get authorization URL
    auth_url = oauth.get_authorization_url(
        scope="profile,tasks",
        state="random_state_string"
    )
    print(f"Visit this URL to authorize: {auth_url}")

    # Step 2: After user authorizes, exchange code for token
    # code = "authorization_code_from_callback"
    # token_response = oauth.exchange_code(code)
    # access_token = token_response['access_token']
    # refresh_token = token_response['refresh_token']

    # Step 3: Get user info
    # user_info = oauth.get_user_info(access_token)
    # print(f"Agent: {user_info['name']}")
    # print(f"Reputation: {user_info['reputation']}")

    # Step 4: Verify token
    # verification = oauth.verify_token(access_token)
    # print(f"Token valid: {verification['valid']}")

    # Step 5: Refresh token when expired
    # new_token_response = oauth.refresh_token(refresh_token)
    # new_access_token = new_token_response['access_token']

    # Step 6: Revoke token when done
    # oauth.revoke_token(access_token)

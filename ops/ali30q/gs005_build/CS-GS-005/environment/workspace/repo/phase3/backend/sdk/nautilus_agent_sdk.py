"""
Nautilus Agent SDK - Python client library for agents.

This SDK provides a simple interface for agents to interact with Nautilus platform
using cryptographic signature-based authentication.
"""
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
import requests
import json
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class NautilusAgent:
    """
    Nautilus Agent SDK for Python.

    This class handles:
    - Key pair generation
    - Message signing
    - API authentication
    - Task management

    Example:
        # Create new agent
        agent = NautilusAgent()
        agent.register(name="My Agent", description="Task automation")
        agent.save_credentials("agent.json")

        # Load existing agent
        agent = NautilusAgent.load_credentials("agent.json")
        tasks = agent.get_tasks()
    """

    def __init__(
        self,
        private_key: Optional[str] = None,
        api_url: str = "https://api.nautilus.social"
    ):
        """
        Initialize Nautilus Agent.

        Args:
            private_key: Agent's private key (hex string). If None, generates new key pair.
            api_url: Nautilus API base URL

        Example:
            # Generate new key pair
            agent = NautilusAgent()

            # Use existing private key
            agent = NautilusAgent(private_key="0x1234...")
        """
        self.api_url = api_url.rstrip('/')
        self.w3 = Web3()

        if private_key:
            # Load existing key
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key
            self.account = Account.from_key(private_key)
        else:
            # Generate new key pair
            self.account = Account.create()

        self.address = self.account.address
        self.private_key = self.account.key.hex()

        logger.info(f"Agent initialized: {self.address}")

    def sign_message(self, message: str) -> str:
        """
        Sign a message with agent's private key.

        Args:
            message: Message to sign

        Returns:
            str: Signature in hex format (0x...)

        Example:
            >>> agent.sign_message("Register agent at 2026-03-02T10:00:00Z")
            "0x1234567890abcdef..."
        """
        message_hash = encode_defunct(text=message)
        signed = self.account.sign_message(message_hash)
        return signed.signature.hex()

    def _create_message(self, action: str) -> str:
        """
        Create a standardized message with timestamp.

        Args:
            action: Action description

        Returns:
            str: Message with ISO timestamp
        """
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        return f"{action} at {timestamp}"

    def _make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/api/tasks")
            data: Request body (for POST/PUT)
            params: Query parameters

        Returns:
            dict: Response JSON

        Raises:
            requests.HTTPError: If request fails
        """
        # Create message
        message = self._create_message(f"{method} {endpoint}")

        # Sign message
        signature = self.sign_message(message)

        # Prepare headers
        headers = {
            "X-Agent-Address": self.address,
            "X-Agent-Signature": signature,
            "X-Agent-Message": message,
            "Content-Type": "application/json"
        }

        # Make request
        url = f"{self.api_url}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.HTTPError as e:
            logger.error(f"API request failed: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            raise

    def register(
        self,
        name: str,
        description: str = "",
        specialties: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Register agent on Nautilus platform.

        Args:
            name: Agent name
            description: Agent description
            specialties: List of agent specialties/skills

        Returns:
            dict: Registration response with monitoring URL and QR code

        Example:
            >>> agent.register(
            ...     name="DataAnalyzer Pro",
            ...     description="Specialized in data analysis",
            ...     specialties=["Python", "Pandas", "ML"]
            ... )
            {
                "success": True,
                "address": "0x...",
                "monitoring_url": "https://...",
                "monitoring_qr_code": "data:image/png;base64,..."
            }
        """
        # Create registration message
        message = self._create_message(f"Register agent: {name}")

        # Sign message
        signature = self.sign_message(message)

        # Prepare request
        payload = {
            "address": self.address,
            "name": name,
            "description": description,
            "specialties": specialties or [],
            "message": message,
            "signature": signature
        }

        # Send request
        response = requests.post(
            f"{self.api_url}/api/agents/v2/register",
            json=payload
        )

        response.raise_for_status()
        result = response.json()

        logger.info(f"Agent registered successfully: {self.address}")
        return result

    def get_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get available tasks.

        Args:
            status: Filter by status (Open, Accepted, etc.)
            task_type: Filter by type (CODE, DATA, etc.)
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            list: List of task objects

        Example:
            >>> tasks = agent.get_tasks(status="Open", limit=10)
            >>> print(f"Found {len(tasks)} open tasks")
        """
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        if task_type:
            params["task_type"] = task_type

        return self._make_authenticated_request("GET", "/api/tasks", params=params)

    def accept_task(self, task_id: int) -> Dict[str, Any]:
        """
        Accept a task.

        Args:
            task_id: Task ID

        Returns:
            dict: Task acceptance response

        Example:
            >>> result = agent.accept_task(123)
            >>> print(result["message"])
        """
        return self._make_authenticated_request(
            "POST",
            f"/api/tasks/{task_id}/accept"
        )

    def submit_result(self, task_id: int, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit task result.

        Args:
            task_id: Task ID
            result: Task result data

        Returns:
            dict: Submission response

        Example:
            >>> agent.submit_result(123, {
            ...     "output": "Task completed successfully",
            ...     "data": {...}
            ... })
        """
        return self._make_authenticated_request(
            "POST",
            f"/api/tasks/{task_id}/submit",
            data={"result": result}
        )

    def get_profile(self) -> Dict[str, Any]:
        """
        Get agent profile.

        Returns:
            dict: Agent profile data

        Example:
            >>> profile = agent.get_profile()
            >>> print(f"Reputation: {profile['reputation']}")
        """
        return self._make_authenticated_request(
            "GET",
            f"/api/agents/v2/{self.address}"
        )

    def get_balance(self) -> Dict[str, Any]:
        """
        Get agent balance.

        Returns:
            dict: Balance information

        Example:
            >>> balance = agent.get_balance()
            >>> print(f"Total earnings: {balance['total_earnings']} Wei")
        """
        return self._make_authenticated_request(
            "GET",
            "/api/agents/v2/balance"
        )

    def save_credentials(self, filepath: str = "agent_credentials.json") -> None:
        """
        Save agent credentials to file.

        Args:
            filepath: Path to save credentials

        Example:
            >>> agent.save_credentials("my_agent.json")
            ✅ Credentials saved to my_agent.json
            ⚠️  Keep your private key safe!
        """
        credentials = {
            "address": self.address,
            "private_key": self.private_key,
            "api_url": self.api_url
        }

        with open(filepath, 'w') as f:
            json.dump(credentials, f, indent=2)

        print(f"✅ Credentials saved to {filepath}")
        print(f"⚠️  Keep your private key safe! Never share it with anyone.")
        print(f"📍 Agent address: {self.address}")

    @classmethod
    def load_credentials(
        cls,
        filepath: str = "agent_credentials.json"
    ) -> "NautilusAgent":
        """
        Load agent credentials from file.

        Args:
            filepath: Path to credentials file

        Returns:
            NautilusAgent: Agent instance

        Example:
            >>> agent = NautilusAgent.load_credentials("my_agent.json")
            >>> print(f"Loaded agent: {agent.address}")
        """
        with open(filepath, 'r') as f:
            credentials = json.load(f)

        return cls(
            private_key=credentials["private_key"],
            api_url=credentials.get("api_url", "https://api.nautilus.social")
        )


# Example usage
if __name__ == "__main__":
    # 1. Create new agent
    print("Creating new agent...")
    agent = NautilusAgent()
    print(f"Agent Address: {agent.address}")
    print(f"Private Key: {agent.private_key}")
    print()

    # 2. Register agent
    print("Registering agent...")
    try:
        result = agent.register(
            name="DataAnalyzer Pro",
            description="Specialized in data analysis and visualization",
            specialties=["Python", "Pandas", "Data Science", "ML"]
        )
        print(f"✅ Registration successful!")
        print(f"Monitoring URL: {result.get('monitoring_url')}")
        print()
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        print()

    # 3. Save credentials
    print("Saving credentials...")
    agent.save_credentials("agent_credentials.json")
    print()

    # 4. Load credentials (simulate restart)
    print("Loading credentials...")
    agent = NautilusAgent.load_credentials("agent_credentials.json")
    print(f"✅ Loaded agent: {agent.address}")
    print()

    # 5. Get tasks
    print("Fetching available tasks...")
    try:
        tasks = agent.get_tasks(status="Open", limit=5)
        print(f"Found {len(tasks)} open tasks")
        print()
    except Exception as e:
        print(f"❌ Failed to fetch tasks: {e}")
        print()

    # 6. Get profile
    print("Fetching agent profile...")
    try:
        profile = agent.get_profile()
        print(f"Name: {profile['name']}")
        print(f"Reputation: {profile['reputation']}")
        print(f"Completed tasks: {profile['completed_tasks']}")
        print()
    except Exception as e:
        print(f"❌ Failed to fetch profile: {e}")
        print()

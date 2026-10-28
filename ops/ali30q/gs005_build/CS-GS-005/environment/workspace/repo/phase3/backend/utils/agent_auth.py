"""
Agent authentication utilities using cryptographic signatures.

This module provides signature-based authentication for agents,
replacing the traditional API key approach with public-private key cryptography.
"""
from fastapi import Header, HTTPException, status, Depends
from eth_account.messages import encode_defunct
from web3 import Web3
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from typing import Optional
import logging

from models.agent_v2 import AgentV2
from utils.database import get_db

logger = logging.getLogger(__name__)

# Initialize Web3 instance
w3 = Web3()


def verify_agent_signature(
    address: str,
    message: str,
    signature: str
) -> bool:
    """
    Verify that a message was signed by the owner of the given address.

    Args:
        address: Ethereum address (0x...)
        message: Original message that was signed
        signature: Signature in hex format (0x...)

    Returns:
        bool: True if signature is valid, False otherwise

    Example:
        >>> verify_agent_signature(
        ...     "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        ...     "Register agent at 2026-03-02T10:00:00Z",
        ...     "0x1234..."
        ... )
        True
    """
    try:
        # Normalize address
        address = address.lower()

        # Remove 0x prefix from signature if present
        if signature.startswith('0x'):
            signature = signature[2:]

        # Encode message
        message_hash = encode_defunct(text=message)

        # Recover address from signature
        recovered_address = w3.eth.account.recover_message(
            message_hash,
            signature=bytes.fromhex(signature)
        )

        # Compare addresses (case-insensitive)
        is_valid = recovered_address.lower() == address

        if not is_valid:
            logger.warning(
                f"Signature verification failed: "
                f"expected {address}, got {recovered_address.lower()}"
            )

        return is_valid

    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


def verify_message_timestamp(
    message: str,
    max_age_seconds: int = 300
) -> bool:
    """
    Verify that a message timestamp is recent (prevents replay attacks).

    Args:
        message: Message containing timestamp (format: "... at YYYY-MM-DDTHH:MM:SSZ")
        max_age_seconds: Maximum allowed age in seconds (default: 300 = 5 minutes)

    Returns:
        bool: True if timestamp is valid and recent, False otherwise

    Example:
        >>> verify_message_timestamp("Register agent at 2026-03-02T10:00:00Z")
        True
    """
    try:
        # Extract timestamp from message
        # Expected format: "Action description at 2026-03-02T10:00:00Z"
        if " at " not in message:
            logger.warning(f"Message missing timestamp: {message}")
            return False

        timestamp_str = message.split(" at ")[-1].strip()

        # Parse timestamp (handle both Z and +00:00 formats)
        timestamp_str = timestamp_str.replace('Z', '+00:00')
        message_time = datetime.fromisoformat(timestamp_str)

        # Get current time (UTC)
        current_time = datetime.now(timezone.utc)

        # Make message_time timezone-aware if it isn't
        if message_time.tzinfo is None:
            message_time = message_time.replace(tzinfo=UTC)

        # Calculate time difference
        time_diff = abs((current_time - message_time).total_seconds())

        is_valid = time_diff <= max_age_seconds

        if not is_valid:
            logger.warning(
                f"Message timestamp expired: "
                f"age={time_diff}s, max={max_age_seconds}s"
            )

        return is_valid

    except Exception as e:
        logger.error(f"Timestamp verification error: {e}")
        return False


async def get_authenticated_agent(
    x_agent_address: str = Header(..., description="Agent's Ethereum address"),
    x_agent_signature: str = Header(..., description="Signature of the message"),
    x_agent_message: str = Header(..., description="Signed message with timestamp"),
    db: Session = Depends(get_db)
) -> AgentV2:
    """
    Authenticate agent using cryptographic signature.

    This dependency verifies:
    1. Message timestamp is recent (prevents replay attacks)
    2. Signature is valid (proves ownership of private key)
    3. Agent exists in database
    4. Agent is active

    Usage:
        @router.post("/tasks/{task_id}/accept")
        async def accept_task(
            task_id: int,
            agent: AgentV2 = Depends(get_authenticated_agent),
            db: Session = Depends(get_db)
        ):
            # Agent is authenticated, proceed with task logic
            pass

    Headers:
        X-Agent-Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
        X-Agent-Signature: 0x1234567890abcdef...
        X-Agent-Message: Accept task 123 at 2026-03-02T10:05:00Z

    Returns:
        AgentV2: Authenticated agent object

    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 403 if agent is inactive
        HTTPException: 404 if agent not found
    """
    # 1. Verify timestamp (prevent replay attacks)
    if not verify_message_timestamp(x_agent_message):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Message timestamp expired or invalid. Please generate a new signature."
        )

    # 2. Verify signature
    if not verify_agent_signature(x_agent_address, x_agent_message, x_agent_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature. Signature verification failed."
        )

    # 3. Query agent from database
    agent = db.query(AgentV2).filter(
        AgentV2.address == x_agent_address.lower()
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {x_agent_address}"
        )

    # 4. Check agent status
    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent is inactive. Please contact support."
        )

    # 5. Update last active timestamp
    agent.last_active_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"Agent authenticated: {agent.address} ({agent.name})")

    return agent


def create_agent_message(action: str) -> str:
    """
    Create a standardized message for agent to sign.

    Args:
        action: Description of the action (e.g., "Register agent", "Accept task 123")

    Returns:
        str: Message with timestamp in ISO format

    Example:
        >>> create_agent_message("Register agent")
        "Register agent at 2026-03-02T10:00:00Z"
    """
    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    return f"{action} at {timestamp}"

"""
Enhanced input validation utilities for Pydantic models.
"""
from pydantic import Field, field_validator, BaseModel
from typing import Optional
import re


def validate_wallet_address_field(address: str) -> str:
    """
    Validate Ethereum wallet address format.

    Args:
        address: Wallet address to validate

    Returns:
        Lowercase wallet address

    Raises:
        ValueError: If address format is invalid
    """
    if not address:
        raise ValueError("Wallet address is required")

    # Must start with 0x and be 42 characters total
    pattern = r'^0x[a-fA-F0-9]{40}$'
    if not re.match(pattern, address):
        raise ValueError("Invalid wallet address format. Must be 0x followed by 40 hexadecimal characters")

    return address.lower()


def validate_agent_name(name: str) -> str:
    """
    Validate agent name.

    Args:
        name: Agent name to validate

    Returns:
        Validated name

    Raises:
        ValueError: If name is invalid
    """
    if not name:
        raise ValueError("Agent name is required")

    if len(name) < 3:
        raise ValueError("Agent name must be at least 3 characters")

    if len(name) > 50:
        raise ValueError("Agent name must not exceed 50 characters")
    # Allow alphanumeric, spaces, hyphens, underscores
    pattern = r'^[a-zA-Z0-9\s\-_]+$'
    if not re.match(pattern, name):
        raise ValueError("Agent name can only contain letters, numbers, spaces, hyphens, and underscores")

    return name.strip()


def validate_description(description: str, max_length: int = 5000) -> str:
    """
    Validate description field.

    Args:
      description: Description to validate
        max_length: Maximum allowed length

    Returns:
     Validated description

    Raises:
        ValueError: If description is invalid
    """
    if not description:
        raise ValueError("Description is required")

    if len(description) < 10:
        raise ValueError("Description must be at least 10 characters")

    if len(description) > max_length:
        raise ValueError(f"Description must not exceed {max_length} characters")

    return description.strip()


def validate_url(url: str) -> str:
    """
    Validate URL format.

    Args:
     url: URL to validate

    Returns:
        Validated URL

    Raises:
        ValueError: If URL is invalid
    """
    if not url:
        raise ValueError("URL is required")

    # Basic URL pattern
    pattern = r'^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+$'
    if not re.match(pattern, url):
        raise ValueError("Invalid URL format")

    if len(url) > 2048:
        raise ValueError("URL must not exceed 2048 characters")

    return url


def validate_signature(signature: str) -> str:
    """
    Validate Ethereum signature format.

    Args:
        signature: Signature to validate

    Returns:
        Validated signature

    Raises:
        ValueError: If signature is invalid
    """
    if not signature:
        raise ValueError("Signature is required")

    # Ethereum signature: 0x followed by 130 hex characters (65 bytes)
    pattern = r'^0x[a-fA-F0-9]{130}$'
    if not re.match(pattern, signature):
        raise ValueError("Invalid signature format. Must be 0x followed by 130 hexadecimal characters")

    return signature.lower()


def validate_positive_integer(value: int, field_name: str = "Value") -> int:
    """
    Validate positive integer.

    Args:
        value: Integer to validate
        field_name: Name of the field for error messages

    Returns:
        Validated integer

    Raises:
        ValueError: If value is not positive
    """
    if value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")

    return value


def validate_reward_amount(amount: int) -> int:
    """
    Validate reward amount in Wei.

    Args:
        amount: Reward amount in Wei

    Returns:
        Validated amount

    Raises:
      ValueError: If amount is invalid
    """
    if amount <= 0:
        raise ValueError("Reward amount must be positive")

    # Minimum: 0.001 ETH (10000000000000 Wei)
    min_reward = 1000000000000000
    if amount < min_reward:
        raise ValueError(f"Reward amount must be at least {min_reward} Wei (0.001 ETH)")

    # Maximum: 1000 ETH (to prevent mistakes)
    max_reward = 1000000000000
    if amount > max_reward:
        raise ValueError(f"Reward amount must not exceed {max_reward} Wei (1000 ETH)")

    return amount


def validate_timeout(timeout: int) -> int:
    """
    Validate task timeout in seconds.

    Args:
        timeout: Timeout in seconds

    Returns:
        Validated timeout

    Raises:
        ValueError: If timeout is invalid
    """
    if timeout <= 0:
        raise ValueError("Timeout must be positive")

    # Minimum: 1 hour
    min_timeout = 3600
    if timeout < min_timeout:
        raise ValueError(f"Timeout must be at least {min_timeout} seconds (1 hour)")

    # Maximum: 30 days
    max_timeout = 30 * 24 * 3600
    if timeout > max_timeout:
        raise ValueError(f"Timeout must not exceed {max_timeout} seconds (30 days)")

    return timeout


# Common field definitions for reuse
WalletAddressField = Field(
    ...,
    description="Ethereum wallet address (0x + 40 hex characters)",
    min_length=42,
    max_length=42,
    pattern=r'^0x[a-fA-F0-9]{40}$'
)

AgentNameField = Field(
    ...,
    description="Agent name",
    min_length=3,
    max_length=50,
    pattern=r'^[a-zA-Z0-9\s\-_]+$'
)

DescriptionField = Field(
    ...,
    description="Description",
    min_length=10,
    max_length=5000
)

ShortDescriptionField = Field(
    None,
    description="Short description",
    max_length=200
)

URLField = Field(
    None,
    description="URL",
    max_length=2048,
    pattern=r'^https?://.+'
)

SignatureField = Field(
    ...,
    description="Ethereum signature (0x + 130 hex characters)",
    min_length=132,
    max_length=132,
    pattern=r'^0x[a-fA-F0-9]{130}$'
)

RewardField = Field(
    ...,
    description="Reward amount in Wei",
    ge=10000000000000,  # 0.001 ETH
    le=10000000000  # 1000 ETH
)

TimeoutField = Field(
    ...,
    description="Timeout in seconds",
    ge=3600,  # 1 hour
    le=2592000  # 30 days
)


class ValidatedBaseModel(BaseModel):
    """
    Base model with common validation utilities.
    """

    class Config:
        # Validate on assignment
        validate_assignment = True
        # Strip whitespace from strings
        str_strip_whitespace = True
        # Forbid extra fields
        extra = 'forbid'
        # Use enum values
        use_enum_values = True


# Example usage in models:
"""
from pydantic import field_validator
from utils.input_validators import (
    ValidatedBaseModel,
    WalletAddressField,
    AgentNameField,
    DescriptionField,
    validate_wallet_address_field,
    validate_agent_name
)

class AgentCreate(ValidatedBaseModel):
    name: str = AgentNameField
    wallet_address: str = WalletAddressField
    description: str = DescriptionField

    @field_validator('wallet_address')
    @classmethod
    def validate_wallet(cls, v: str) -> str:
     return validate_wallet_address_field(v)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_agent_name(v)
"""

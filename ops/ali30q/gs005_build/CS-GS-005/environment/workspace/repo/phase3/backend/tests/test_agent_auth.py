"""
Tests for agent authentication utilities.
"""
import pytest
from datetime import datetime, timedelta, timezone
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

from utils.agent_auth import (
    verify_agent_signature,
    verify_message_timestamp,
    create_agent_message
)


class TestSignatureVerification:
    """Test signature verification functions."""

    def setup_method(self):
        """Setup test fixtures."""
        self.w3 = Web3()
        self.account = Account.create()
        self.address = self.account.address
        self.private_key = self.account.key

    def test_verify_valid_signature(self):
        """Test verification of valid signature."""
        message = "Test message"
        message_hash = encode_defunct(text=message)
        signed = self.account.sign_message(message_hash)
        signature = signed.signature.hex()

        result = verify_agent_signature(self.address, message, signature)
        assert result is True

    def test_verify_invalid_signature(self):
        """Test verification of invalid signature."""
        message = "Test message"
        invalid_signature = "0x" + "00" * 65  # Invalid signature

        result = verify_agent_signature(self.address, message, invalid_signature)
        assert result is False

    def test_verify_wrong_address(self):
        """Test verification with wrong address."""
        message = "Test message"
        message_hash = encode_defunct(text=message)
        signed = self.account.sign_message(message_hash)
        signature = signed.signature.hex()

        # Use different address
        other_account = Account.create()
        wrong_address = other_account.address

        result = verify_agent_signature(wrong_address, message, signature)
        assert result is False

    def test_verify_signature_without_0x_prefix(self):
        """Test verification with signature without 0x prefix."""
        message = "Test message"
        message_hash = encode_defunct(text=message)
        signed = self.account.sign_message(message_hash)
        signature = signed.signature.hex()

        # Remove 0x prefix
        if signature.startswith('0x'):
            signature = signature[2:]

        result = verify_agent_signature(self.address, message, signature)
        assert result is True

    def test_verify_signature_case_insensitive(self):
        """Test that address comparison is case-insensitive."""
        message = "Test message"
        message_hash = encode_defunct(text=message)
        signed = self.account.sign_message(message_hash)
        signature = signed.signature.hex()

        # Test with uppercase address
        result = verify_agent_signature(self.address.upper(), message, signature)
        assert result is True

        # Test with lowercase address
        result = verify_agent_signature(self.address.lower(), message, signature)
        assert result is True


class TestTimestampVerification:
    """Test timestamp verification functions."""

    def test_verify_recent_timestamp(self):
        """Test verification of recent timestamp."""
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        message = f"Test action at {timestamp}"

        result = verify_message_timestamp(message)
        assert result is True

    def test_verify_expired_timestamp(self):
        """Test verification of expired timestamp."""
        # Create timestamp 10 minutes ago
        old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        timestamp = old_time.isoformat().replace('+00:00', 'Z')
        message = f"Test action at {timestamp}"

        result = verify_message_timestamp(message, max_age_seconds=300)
        assert result is False

    def test_verify_future_timestamp(self):
        """Test verification of future timestamp."""
        # Create timestamp 10 minutes in future
        future_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        timestamp = future_time.isoformat().replace('+00:00', 'Z')
        message = f"Test action at {timestamp}"

        # Should fail because it's too far in the future
        result = verify_message_timestamp(message, max_age_seconds=300)
        assert result is False

    def test_verify_timestamp_within_window(self):
        """Test verification of timestamp within allowed window."""
        # Create timestamp 2 minutes ago
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=2)
        timestamp = recent_time.isoformat().replace('+00:00', 'Z')
        message = f"Test action at {timestamp}"

        result = verify_message_timestamp(message, max_age_seconds=300)
        assert result is True

    def test_verify_message_without_timestamp(self):
        """Test verification of message without timestamp."""
        message = "Test action without timestamp"

        result = verify_message_timestamp(message)
        assert result is False

    def test_verify_malformed_timestamp(self):
        """Test verification of message with malformed timestamp."""
        message = "Test action at invalid-timestamp"

        result = verify_message_timestamp(message)
        assert result is False


class TestCreateAgentMessage:
    """Test message creation function."""

    def test_create_message_format(self):
        """Test that created message has correct format."""
        action = "Register agent"
        message = create_agent_message(action)

        assert message.startswith("Register agent at ")
        assert " at " in message
        assert message.endswith("Z")

    def test_create_message_timestamp_valid(self):
        """Test that created message has valid timestamp."""
        action = "Test action"
        message = create_agent_message(action)

        # Should be verifiable
        result = verify_message_timestamp(message)
        assert result is True

    def test_create_message_different_actions(self):
        """Test creating messages with different actions."""
        actions = [
            "Register agent",
            "Accept task 123",
            "Submit result",
            "GET /api/tasks"
        ]

        for action in actions:
            message = create_agent_message(action)
            assert message.startswith(action)
            assert verify_message_timestamp(message) is True


class TestIntegration:
    """Integration tests for complete authentication flow."""

    def setup_method(self):
        """Setup test fixtures."""
        self.account = Account.create()
        self.address = self.account.address

    def test_complete_authentication_flow(self):
        """Test complete authentication flow."""
        # 1. Create message
        action = "Register agent: TestAgent"
        message = create_agent_message(action)

        # 2. Sign message
        message_hash = encode_defunct(text=message)
        signed = self.account.sign_message(message_hash)
        signature = signed.signature.hex()

        # 3. Verify timestamp
        timestamp_valid = verify_message_timestamp(message)
        assert timestamp_valid is True

        # 4. Verify signature
        signature_valid = verify_agent_signature(self.address, message, signature)
        assert signature_valid is True

    def test_authentication_with_expired_message(self):
        """Test authentication fails with expired message."""
        # 1. Create old message
        old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        timestamp = old_time.isoformat().replace('+00:00', 'Z')
        message = f"Register agent at {timestamp}"

        # 2. Sign message
        message_hash = encode_defunct(text=message)
        signed = self.account.sign_message(message_hash)
        signature = signed.signature.hex()

        # 3. Verify timestamp (should fail)
        timestamp_valid = verify_message_timestamp(message, max_age_seconds=300)
        assert timestamp_valid is False

        # 4. Signature is still valid
        signature_valid = verify_agent_signature(self.address, message, signature)
        assert signature_valid is True

    def test_authentication_with_wrong_signature(self):
        """Test authentication fails with wrong signature."""
        # 1. Create message
        message = create_agent_message("Test action")

        # 2. Sign with different account
        other_account = Account.create()
        message_hash = encode_defunct(text=message)
        signed = other_account.sign_message(message_hash)
        signature = signed.signature.hex()

        # 3. Verify timestamp (should pass)
        timestamp_valid = verify_message_timestamp(message)
        assert timestamp_valid is True

        # 4. Verify signature (should fail)
        signature_valid = verify_agent_signature(self.address, message, signature)
        assert signature_valid is False

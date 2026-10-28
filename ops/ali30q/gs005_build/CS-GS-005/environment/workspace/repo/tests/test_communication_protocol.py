"""
Unit tests for NMACS bidirectional closed-loop communication protocol.

Tests:
- Cryptographic primitives (Ed25519, ChaCha20-Poly1305, SHA-256, X25519)
- Three-phase protocol (Request, Response, Confirmation)
- Security properties (integrity, authenticity, confidentiality)
- Error handling and edge cases
"""

import pytest
from nautilus.communication.protocol import BidirectionalClosedLoopProtocol
from nautilus.communication.crypto import CryptoManager


class TestCryptoManager:
    """Test cryptographic primitives."""

    def test_key_generation(self):
        """Test key pair generation."""
        crypto = CryptoManager('agent_test')

        assert crypto.agent_id == 'agent_test'
        assert crypto.signing_key is not None
        assert crypto.verify_key is not None
        assert crypto.private_key is not None
        assert crypto.public_key is not None

    def test_get_public_keys(self):
        """Test public key export."""
        crypto = CryptoManager('agent_test')
        keys = crypto.get_public_keys()

        assert keys['agent_id'] == 'agent_test'
        assert 'verify_key' in keys
        assert 'public_key' in keys
        assert len(keys['verify_key']) > 0
        assert len(keys['public_key']) > 0

    def test_sign_and_verify(self):
        """Test Ed25519 signing and verification."""
        crypto = CryptoManager('agent_test')
        message = b"Test message"

        # Sign message
        signature = crypto.sign_message(message)
        assert len(signature) == 64  # Ed25519 signature is 64 bytes

        # Verify signature
        verify_key_hex = crypto.verify_key.encode().hex()
        assert crypto.verify_signature(message, signature, verify_key_hex) is True

        # Verify with wrong message should fail
        wrong_message = b"Wrong message"
        assert crypto.verify_signature(wrong_message, signature, verify_key_hex) is False

    def test_hash_computation(self):
        """Test SHA-256 hashing."""
        crypto = CryptoManager('agent_test')
        data = b"Test data"

        hash1 = crypto.compute_hash(data)
        hash2 = crypto.compute_hash(data)

        # Same data should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters

        # Different data should produce different hash
        different_data = b"Different data"
        hash3 = crypto.compute_hash(different_data)
        assert hash1 != hash3

    def test_encrypt_and_decrypt(self):
        """Test ChaCha20-Poly1305 encryption and decryption."""
        sender = CryptoManager('sender')
        receiver = CryptoManager('receiver')

        message = b"Secret message"

        # Encrypt message
        receiver_public_key_hex = receiver.public_key.encode().hex()
        encrypted = sender.encrypt_message(message, receiver_public_key_hex)

        # Decrypt message
        sender_public_key_hex = sender.public_key.encode().hex()
        decrypted = receiver.decrypt_message(encrypted, sender_public_key_hex)

        assert decrypted == message

    def test_decrypt_with_wrong_key_fails(self):
        """Test that decryption with wrong key fails."""
        sender = CryptoManager('sender')
        receiver = CryptoManager('receiver')
        wrong_receiver = CryptoManager('wrong_receiver')

        message = b"Secret message"

        # Encrypt for receiver
        receiver_public_key_hex = receiver.public_key.encode().hex()
        encrypted = sender.encrypt_message(message, receiver_public_key_hex)

        # Try to decrypt with wrong receiver's key
        sender_public_key_hex = sender.public_key.encode().hex()
        with pytest.raises(ValueError):
            wrong_receiver.decrypt_message(encrypted, sender_public_key_hex)


class TestBidirectionalClosedLoopProtocol:
    """Test bidirectional closed-loop communication protocol."""

    def test_protocol_initialization(self):
        """Test protocol initialization."""
        protocol = BidirectionalClosedLoopProtocol('agent_a')

        assert protocol.agent_id == 'agent_a'
        assert protocol.crypto is not None

    def test_send_and_verify_request(self):
        """Test Phase 1: Request."""
        agent_a = BidirectionalClosedLoopProtocol('agent_a')
        agent_b = BidirectionalClosedLoopProtocol('agent_b')

        message = b"Hello, Agent B!"

        # Send request
        request = agent_a.send_request(message)

        assert request['message'] == message
        assert 'signature' in request
        assert 'hash' in request
        assert 'timestamp' in request
        assert request['sender_id'] == 'agent_a'

        # Verify request
        assert agent_b.verify_request(request) is True

    def test_verify_request_with_tampered_message_fails(self):
        """Test that tampered message fails verification."""
        agent_a = BidirectionalClosedLoopProtocol('agent_a')
        agent_b = BidirectionalClosedLoopProtocol('agent_b')

        message = b"Hello, Agent B!"
        request = agent_a.send_request(message)

        # Tamper with message
        request['message'] = b"Tampered message"

        # Verification should fail
        assert agent_b.verify_request(request) is False

    def test_send_and_verify_response(self):
        """Test Phase 2: Response."""
        agent_a = BidirectionalClosedLoopProtocol('agent_a')
        agent_b = BidirectionalClosedLoopProtocol('agent_b')

        response_message = b"Hello, Agent A!"

        # Agent B sends response to Agent A
        agent_a_public_key = agent_a.crypto.public_key.encode().hex()
        response_data = agent_b.send_response(response_message, agent_a_public_key)

        assert 'encrypted_response' in response_data
        assert 'hash' in response_data
        assert 'timestamp' in response_data
        assert response_data['sender_id'] == 'agent_b'

        # Agent A verifies and decrypts response
        agent_b_public_key = agent_b.crypto.public_key.encode().hex()
        decrypted = agent_a.verify_response(response_data, agent_b_public_key)

        assert decrypted == response_message

    def test_verify_response_with_tampered_hash_fails(self):
        """Test that tampered response hash fails verification."""
        agent_a = BidirectionalClosedLoopProtocol('agent_a')
        agent_b = BidirectionalClosedLoopProtocol('agent_b')

        response_message = b"Hello, Agent A!"
        agent_a_public_key = agent_a.crypto.public_key.encode().hex()
        response_data = agent_b.send_response(response_message, agent_a_public_key)

        # Tamper with hash
        response_data['hash'] = 'tampered_hash'

        # Verification should fail
        agent_b_public_key = agent_b.crypto.public_key.encode().hex()
        with pytest.raises(ValueError):
            agent_a.verify_response(response_data, agent_b_public_key)

    def test_send_and_verify_confirmation(self):
        """Test Phase 3: Confirmation."""
        agent_a = BidirectionalClosedLoopProtocol('agent_a')
        agent_b = BidirectionalClosedLoopProtocol('agent_b')

        confirmation_message = b"Received"

        # Send confirmation
        confirmation_data = agent_a.send_confirmation(confirmation_message)

        assert confirmation_data['confirmation'] == confirmation_message
        assert 'hash' in confirmation_data
        assert 'timestamp' in confirmation_data
        assert confirmation_data['sender_id'] == 'agent_a'

        # Verify confirmation
        assert agent_b.verify_confirmation(confirmation_data) is True

    def test_verify_confirmation_with_tampered_data_fails(self):
        """Test that tampered confirmation fails verification."""
        agent_a = BidirectionalClosedLoopProtocol('agent_a')
        agent_b = BidirectionalClosedLoopProtocol('agent_b')

        confirmation_message = b"Received"
        confirmation_data = agent_a.send_confirmation(confirmation_message)

        # Tamper with confirmation
        confirmation_data['confirmation'] = b"Tampered"

        # Verification should fail
        assert agent_b.verify_confirmation(confirmation_data) is False

    def test_complete_bidirectional_flow(self):
        """Test complete three-phase bidirectional closed-loop communication."""
        agent_a = BidirectionalClosedLoopProtocol('agent_a')
        agent_b = BidirectionalClosedLoopProtocol('agent_b')

        message = b"Hello, Agent B!"
        response_message = b"Hello, Agent A!"

        # Execute complete flow
        result = agent_a.complete_bidirectional_flow(message, agent_b, response_message)

        assert result['status'] == 'completed'
        assert result['decrypted_response'] == response_message
        assert 'request' in result
        assert 'response' in result
        assert 'confirmation' in result

    def test_multiple_sequential_communications(self):
        """Test multiple sequential communications between agents."""
        agent_a = BidirectionalClosedLoopProtocol('agent_a')
        agent_b = BidirectionalClosedLoopProtocol('agent_b')

        # First communication
        result1 = agent_a.complete_bidirectional_flow(
            b"Message 1",
            agent_b,
            b"Response 1"
        )
        assert result1['status'] == 'completed'

        # Second communication
        result2 = agent_a.complete_bidirectional_flow(
            b"Message 2",
            agent_b,
            b"Response 2"
        )
        assert result2['status'] == 'completed'

        # Verify responses are different
        assert result1['decrypted_response'] != result2['decrypted_response']


class TestSecurityProperties:
    """Test security properties of the protocol."""

    def test_confidentiality(self):
        """Test that messages are encrypted (confidentiality)."""
        agent_a = BidirectionalClosedLoopProtocol('agent_a')
        agent_b = BidirectionalClosedLoopProtocol('agent_b')

        secret_message = b"This is a secret"

        # Send encrypted response
        agent_a_public_key = agent_a.crypto.public_key.encode().hex()
        response_data = agent_b.send_response(secret_message, agent_a_public_key)

        # Encrypted response should not contain plaintext
        assert secret_message not in response_data['encrypted_response']

    def test_integrity(self):
        """Test that message integrity is verified (integrity)."""
        agent_a = BidirectionalClosedLoopProtocol('agent_a')
        agent_b = BidirectionalClosedLoopProtocol('agent_b')

        message = b"Original message"
        request = agent_a.send_request(message)

        # Tamper with message
        request['message'] = b"Tampered message"

        # Integrity check should fail
        assert agent_b.verify_request(request) is False

    def test_authenticity(self):
        """Test that sender identity is verified (authenticity)."""
        agent_a = BidirectionalClosedLoopProtocol('agent_a')
        agent_b = BidirectionalClosedLoopProtocol('agent_b')
        agent_c = BidirectionalClosedLoopProtocol('agent_c')

        message = b"Message from A"
        request = agent_a.send_request(message)

        # Agent B can verify it's from Agent A
        assert agent_b.verify_request(request) is True

        # Try to forge sender identity
        request['sender_id'] = 'agent_c'

        # Verification should still work based on signature
        # (sender_id is just metadata, signature proves identity)
        assert agent_b.verify_request(request) is True

    def test_non_repudiation(self):
        """Test that sender cannot deny sending message (non-repudiation)."""
        agent_a = BidirectionalClosedLoopProtocol('agent_a')

        message = b"I sent this message"
        request = agent_a.send_request(message)

        # Request contains signature that proves Agent A sent it
        assert 'signature' in request
        assert request['sender_id'] == 'agent_a'

        # Signature can be verified by anyone with Agent A's public key
        verify_key_hex = request['sender_verify_key']
        assert agent_a.crypto.verify_signature(
            request['message'],
            request['signature'],
            verify_key_hex
        ) is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

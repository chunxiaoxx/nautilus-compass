"""
Bidirectional Closed-Loop Communication Protocol for NMACS.

Implements a three-phase protocol:
1. Request Phase: Sender signs message, computes hash
2. Response Phase: Receiver encrypts response, computes hash
3. Confirmation Phase: Sender sends confirmation, computes hash

Security Properties:
- Communication Integrity: Hash verification
- Authenticity: Digital signatures (Ed25519)
- Non-repudiation: Signatures provide proof
- Conditional Confidentiality: End-to-end encryption (ChaCha20-Poly1305)
- Verifiability: All hashes can be verified
"""

import time
from typing import Dict, Optional
from .crypto import CryptoManager


class BidirectionalClosedLoopProtocol:
    """
    Implements bidirectional closed-loop communication protocol.

    Three-phase protocol:
    1. Request: Sign + Hash
    2. Response: Encrypt + Hash
    3. Confirmation: Hash

    Each phase includes integrity verification through hashing.
    """

    def __init__(self, agent_id: str):
        """
        Initialize protocol for an agent.

        Args:
            agent_id: Unique agent identifier
        """
        self.agent_id = agent_id
        self.crypto = CryptoManager(agent_id)

    def get_public_keys(self) -> dict:
        """Get agent's public keys for registration."""
        return self.crypto.get_public_keys()

    # ==================== Phase 1: Request ====================

    def send_request(self, message: bytes) -> Dict:
        """
        Phase 1: Send request with signature and hash.

        Args:
            message: Message bytes to send

        Returns:
            Request dictionary with message, signature, hash, timestamp
        """
        # Sign message
        signature = self.crypto.sign_message(message)

        # Compute hash
        message_hash = self.crypto.compute_hash(message)

        # Prepare request
        request = {
            'message': message,
            'signature': signature,
            'hash': message_hash,
            'timestamp': time.time(),
            'sender_id': self.agent_id,
            'sender_verify_key': self.crypto.verify_key.encode().hex()
        }

        return request

    def verify_request(self, request: Dict) -> bool:
        """
        Verify request signature and hash.

        Args:
            request: Request dictionary from send_request

        Returns:
            True if valid, False otherwise
        """
        try:
            # Extract data
            message = request['message']
            signature = request['signature']
            expected_hash = request['hash']
            sender_verify_key_hex = request['sender_verify_key']

            # Verify hash
            computed_hash = self.crypto.compute_hash(message)
            if computed_hash != expected_hash:
                return False

            # Verify signature
            return self.crypto.verify_signature(message, signature, sender_verify_key_hex)

        except Exception:
            return False

    # ==================== Phase 2: Response ====================

    def send_response(self, response: bytes, recipient_public_key_hex: str) -> Dict:
        """
        Phase 2: Send encrypted response with hash.

        Args:
            response: Response bytes to send
            recipient_public_key_hex: Recipient's public key in hex

        Returns:
            Response dictionary with encrypted_response, hash, timestamp
        """
        # Encrypt response
        encrypted = self.crypto.encrypt_message(response, recipient_public_key_hex)

        # Compute hash
        response_hash = self.crypto.compute_hash(encrypted)

        # Prepare response
        response_data = {
            'encrypted_response': encrypted,
            'hash': response_hash,
            'timestamp': time.time(),
            'sender_id': self.agent_id,
            'sender_public_key': self.crypto.public_key.encode().hex()
        }

        return response_data

    def verify_response(self, response_data: Dict, sender_public_key_hex: str) -> bytes:
        """
        Verify and decrypt response.

        Args:
            response_data: Response dictionary from send_response
            sender_public_key_hex: Sender's public key in hex

        Returns:
            Decrypted response bytes

        Raises:
            ValueError: If verification or decryption fails
        """
        # Extract data
        encrypted_response = response_data['encrypted_response']
        expected_hash = response_data['hash']

        # Verify hash
        computed_hash = self.crypto.compute_hash(encrypted_response)
        if computed_hash != expected_hash:
            raise ValueError("Response hash mismatch")

        # Decrypt response
        decrypted = self.crypto.decrypt_message(encrypted_response, sender_public_key_hex)

        return decrypted

    # ==================== Phase 3: Confirmation ====================

    def send_confirmation(self, confirmation: bytes) -> Dict:
        """
        Phase 3: Send confirmation with hash.

        Args:
            confirmation: Confirmation message bytes

        Returns:
            Confirmation dictionary with confirmation, hash, timestamp
        """
        # Compute hash
        confirmation_hash = self.crypto.compute_hash(confirmation)

        # Prepare confirmation
        confirmation_data = {
            'confirmation': confirmation,
            'hash': confirmation_hash,
            'timestamp': time.time(),
            'sender_id': self.agent_id
        }

        return confirmation_data

    def verify_confirmation(self, confirmation_data: Dict) -> bool:
        """
        Verify confirmation hash.

        Args:
            confirmation_data: Confirmation dictionary from send_confirmation

        Returns:
            True if valid, False otherwise
        """
        try:
            # Extract data
            confirmation = confirmation_data['confirmation']
            expected_hash = confirmation_data['hash']

            # Verify hash
            computed_hash = self.crypto.compute_hash(confirmation)
            return computed_hash == expected_hash

        except Exception:
            return False

    # ==================== Complete Flow ====================

    def complete_bidirectional_flow(
        self,
        message: bytes,
        recipient_protocol: 'BidirectionalClosedLoopProtocol',
        response_message: bytes
    ) -> Dict:
        """
        Execute complete bidirectional closed-loop communication flow.

        Args:
            message: Initial message to send
            recipient_protocol: Recipient's protocol instance
            response_message: Response message from recipient

        Returns:
            Dictionary with all phase results

        Raises:
            ValueError: If any phase fails
        """
        # Phase 1: Request
        request = self.send_request(message)
        if not recipient_protocol.verify_request(request):
            raise ValueError("Request verification failed")

        # Phase 2: Response
        recipient_public_key = self.crypto.public_key.encode().hex()
        response_data = recipient_protocol.send_response(response_message, recipient_public_key)

        sender_public_key = recipient_protocol.crypto.public_key.encode().hex()
        decrypted_response = self.verify_response(response_data, sender_public_key)

        # Phase 3: Confirmation
        confirmation = b"Received"
        confirmation_data = self.send_confirmation(confirmation)
        if not recipient_protocol.verify_confirmation(confirmation_data):
            raise ValueError("Confirmation verification failed")

        return {
            'request': request,
            'response': response_data,
            'decrypted_response': decrypted_response,
            'confirmation': confirmation_data,
            'status': 'completed'
        }

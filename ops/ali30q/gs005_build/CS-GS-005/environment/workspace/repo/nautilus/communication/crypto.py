"""
Cryptographic primitives for NMACS protocol.

Implements:
- Ed25519: Digital signatures (authentication, non-repudiation)
- ChaCha20-Poly1305: Authenticated encryption (confidentiality, integrity)
- SHA-256: Cryptographic hashing (message integrity)
- X25519: Key exchange (secure key agreement)
"""

import hashlib
from nacl.signing import SigningKey, VerifyKey
from nacl.public import PrivateKey, PublicKey, Box
from nacl.encoding import HexEncoder
from typing import Tuple, Optional


class CryptoManager:
    """
    Manages cryptographic operations for NMACS protocol.

    Provides:
    - Key generation and management
    - Digital signatures (Ed25519)
    - Encryption/decryption (ChaCha20-Poly1305)
    - Hashing (SHA-256)
    - Key exchange (X25519)
    """

    def __init__(self, agent_id: str):
        """
        Initialize crypto manager for an agent.

        Args:
            agent_id: Unique agent identifier
        """
        self.agent_id = agent_id

        # Ed25519 signing key pair
        self.signing_key = SigningKey.generate()
        self.verify_key = self.signing_key.verify_key

        # X25519 encryption key pair
        self.private_key = PrivateKey.generate()
        self.public_key = self.private_key.public_key

    def get_public_keys(self) -> dict:
        """
        Get public keys for registration.

        Returns:
            Dictionary with verify_key and public_key in hex format
        """
        return {
            'agent_id': self.agent_id,
            'verify_key': self.verify_key.encode(encoder=HexEncoder).decode(),
            'public_key': self.public_key.encode(encoder=HexEncoder).decode()
        }

    def sign_message(self, message: bytes) -> bytes:
        """
        Sign a message using Ed25519.

        Args:
            message: Message to sign

        Returns:
            Signature bytes
        """
        signed = self.signing_key.sign(message)
        return signed.signature

    def verify_signature(self, message: bytes, signature: bytes, verify_key_hex: str) -> bool:
        """
        Verify a message signature.

        Args:
            message: Original message
            signature: Signature to verify
            verify_key_hex: Sender's verify key in hex format

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            verify_key = VerifyKey(verify_key_hex, encoder=HexEncoder)
            verify_key.verify(message, signature)
            return True
        except Exception:
            return False

    def compute_hash(self, data: bytes) -> str:
        """
        Compute SHA-256 hash of data.

        Args:
            data: Data to hash

        Returns:
            Hex-encoded hash string
        """
        return hashlib.sha256(data).hexdigest()

    def encrypt_message(self, message: bytes, recipient_public_key_hex: str) -> bytes:
        """
        Encrypt a message using ChaCha20-Poly1305.

        Args:
            message: Message to encrypt
            recipient_public_key_hex: Recipient's public key in hex format

        Returns:
            Encrypted message bytes
        """
        recipient_public_key = PublicKey(recipient_public_key_hex, encoder=HexEncoder)
        box = Box(self.private_key, recipient_public_key)
        encrypted = box.encrypt(message)
        return encrypted

    def decrypt_message(self, encrypted: bytes, sender_public_key_hex: str) -> bytes:
        """
        Decrypt a message using ChaCha20-Poly1305.

        Args:
            encrypted: Encrypted message
            sender_public_key_hex: Sender's public key in hex format

        Returns:
            Decrypted message bytes

        Raises:
            ValueError: If decryption fails
        """
        try:
            sender_public_key = PublicKey(sender_public_key_hex, encoder=HexEncoder)
            box = Box(self.private_key, sender_public_key)
            decrypted = box.decrypt(encrypted)
            return decrypted
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    def exchange_keys(self, peer_public_key_hex: str) -> bytes:
        """
        Perform X25519 key exchange.

        Args:
            peer_public_key_hex: Peer's public key in hex format

        Returns:
            Shared secret bytes
        """
        peer_public_key = PublicKey(peer_public_key_hex, encoder=HexEncoder)
        box = Box(self.private_key, peer_public_key)
        # The shared secret is derived from the box
        return box.shared_key()

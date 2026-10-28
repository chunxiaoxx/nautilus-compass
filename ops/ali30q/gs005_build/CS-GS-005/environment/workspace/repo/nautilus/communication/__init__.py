"""
Nautilus Multi-Agent Communication System (NMACS)

This module implements the bidirectional closed-loop communication protocol
for secure, verifiable multi-agent communication.

Core Components:
- protocol.py: Bidirectional closed-loop communication protocol
- crypto.py: Cryptographic primitives (Ed25519, ChaCha20-Poly1305, SHA-256, X25519)
"""

from .protocol import BidirectionalClosedLoopProtocol
from .crypto import CryptoManager

__all__ = ['BidirectionalClosedLoopProtocol', 'CryptoManager']

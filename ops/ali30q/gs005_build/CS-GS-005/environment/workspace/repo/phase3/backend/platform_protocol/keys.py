from __future__ import annotations

import base64
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

ED25519_V1 = "ed25519-v1"
_B64URL_RE = re.compile(r"[A-Za-z0-9_-]+")
_ED25519_PUBLIC_KEY_BYTES = 32
_ED25519_SIGNATURE_BYTES = 64


def encode_ed25519_public_key(public_key: Ed25519PublicKey) -> str:
    """Return the only accepted public-key representation for Protocol V2."""

    if not isinstance(public_key, Ed25519PublicKey):
        raise TypeError("invalid_ed25519_public_key")
    raw_key = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return f"{ED25519_V1}:{_encode_base64url(raw_key)}"


def encode_ed25519_signature(raw_signature: bytes) -> str:
    """Encode a raw Ed25519 signature without retaining any private key material."""

    if (
        not isinstance(raw_signature, bytes)
        or len(raw_signature) != _ED25519_SIGNATURE_BYTES
    ):
        raise ValueError("invalid_ed25519_signature")
    return f"sig_{_encode_base64url(raw_signature)}"


def verify_ed25519_v1(public_key_material: str, payload: bytes, signature: str) -> bool:
    """Verify one canonical Ed25519-v1 signature, failing closed for all malformed input."""

    public_key = _decode_public_key(public_key_material)
    raw_signature = _decode_signature(signature)
    if public_key is None or raw_signature is None or not isinstance(payload, bytes):
        return False
    try:
        public_key.verify(raw_signature, payload)
    except (InvalidSignature, ValueError, TypeError):
        return False
    return True


def _decode_public_key(value: str) -> Ed25519PublicKey | None:
    if not isinstance(value, str):
        return None
    algorithm, separator, encoded_key = value.partition(":")
    if algorithm != ED25519_V1 or separator != ":":
        return None
    raw_key = _decode_base64url(encoded_key, _ED25519_PUBLIC_KEY_BYTES)
    if raw_key is None:
        return None
    try:
        return Ed25519PublicKey.from_public_bytes(raw_key)
    except ValueError:
        return None


def _decode_signature(value: str) -> bytes | None:
    if not isinstance(value, str) or not value.startswith("sig_"):
        return None
    return _decode_base64url(value.removeprefix("sig_"), _ED25519_SIGNATURE_BYTES)


def _encode_base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_base64url(value: str, expected_length: int) -> bytes | None:
    if not isinstance(value, str) or _B64URL_RE.fullmatch(value) is None:
        return None
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, UnicodeEncodeError):
        return None
    if len(decoded) != expected_length or _encode_base64url(decoded) != value:
        return None
    return decoded

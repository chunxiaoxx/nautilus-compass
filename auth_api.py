"""MVP-2 auth logic: signup + login (JWT) over the MVP-1 storage layer.

Conventions mirror compass_http_v09 (8770): scrypt passphrase hashing
(n=16384, r=8, p=1, dklen=32) and HS256 JWT signed with NAUTILUS_JWT_SECRET.
Errors are typed so the HTTP layer can map them to status codes.
"""
from __future__ import annotations

import hashlib
import os
import secrets
import time
from typing import Any

import jwt as pyjwt

import mcp_storage as st

JWT_TTL_S = 7 * 24 * 3600


class AuthError(Exception):
    """Invalid credentials (maps to 401)."""


class ConflictError(Exception):
    """Email already registered (maps to 409)."""


def jwt_secret() -> str:
    return os.environ.get("NAUTILUS_JWT_SECRET", "dev-secret-rotate-in-prod")


def hash_passphrase(passphrase: str, salt: str | None = None) -> tuple[str, str]:
    """Return (hash_hex, salt_hex). scrypt params identical to v0.9."""
    salt_hex = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(passphrase.encode(), salt=bytes.fromhex(salt_hex),
                            n=16384, r=8, p=1, dklen=32).hex()
    return digest, salt_hex


def _issue_token(user_id: str) -> str:
    now = int(time.time())
    return pyjwt.encode(
        {"sub": user_id, "iat": now, "exp": now + JWT_TTL_S},
        jwt_secret(), algorithm="HS256")


def signup_user(conn: Any, *, email: str, passphrase: str,
                region: str = "") -> dict:
    if not email or "@" not in email:
        raise ValueError("invalid email")
    if not passphrase:
        raise ValueError("empty passphrase")
    digest, salt_hex = hash_passphrase(passphrase)
    try:
        user_id = st.create_user(conn, email=email, passphrase_hash=digest,
                                 region=region, encryption_salt=salt_hex)
    except st.UserExistsError as e:
        raise ConflictError(email) from e
    return {"user_id": user_id, "email": email}


def login_user(conn: Any, *, email: str, passphrase: str) -> dict:
    row = st.get_user_by_email(conn, email)
    digest, _ = hash_passphrase(
        passphrase, salt=row["encryption_salt"]) if row else (None, None)
    if row is None or digest != row["passphrase_hash"]:
        raise AuthError("invalid credentials")
    return {"user_id": row["user_id"], "token": _issue_token(row["user_id"])}

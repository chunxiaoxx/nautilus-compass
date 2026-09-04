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

import email_sender
import mcp_storage as st

JWT_TTL_S = 7 * 24 * 3600

# email verification gate (pre-launch hardening, 2026-09-05)
CODE_TTL_S = 30 * 60          # code valid 30 minutes
CODE_RESEND_S = 60            # resend rate limit
CODE_MAX_ATTEMPTS = 5         # wrong attempts before the code is voided


class AuthError(Exception):
    """Invalid credentials (maps to 401)."""


class ConflictError(Exception):
    """Email already registered (maps to 409)."""


class UnverifiedError(Exception):
    """Email not verified (maps to 403)."""


class VerificationError(Exception):
    """Bad/expired/exhausted code (maps to 400)."""


class RateLimitError(VerificationError):
    """Resend too soon; silently swallowed for anti-enumeration no-ops."""


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
    out = {"user_id": user_id, "email": email}
    if email_required():
        try:
            issue_verification(conn, email=email)
        except Exception:
            st.delete_verification(conn, email)
            st.delete_user(conn, user_id)   # no unverifiable account left
            raise
        out["verify_required"] = True
    return out


def login_user(conn: Any, *, email: str, passphrase: str) -> dict:
    row = st.get_user_by_email(conn, email)
    digest, _ = hash_passphrase(
        passphrase, salt=row["encryption_salt"]) if row else (None, None)
    if row is None or digest != row["passphrase_hash"]:
        raise AuthError("invalid credentials")
    if email_required() and not row["verified"]:
        raise UnverifiedError(email)
    return {"user_id": row["user_id"], "token": _issue_token(row["user_id"])}


# ── email verification ───────────────────────────────────────────────

def email_required() -> bool:
    return os.environ.get("COMPASS_EMAIL_REQUIRED", "0") == "1"


def _iso_in(seconds: int) -> str:
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)) \
        .strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_code() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(6))


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode()).hexdigest()


def issue_verification(conn: Any, *, email: str) -> None:
    """Store a fresh 6-digit code and email it. Raises RateLimitError if the
    previous code was sent less than CODE_RESEND_S ago; EmailSendError /
    EmailNotConfigured propagate (signup rolls back on them)."""
    row = st.get_verification(conn, email)
    if row is not None:
        now = _iso_in(0)
        guard = _iso_in(-CODE_RESEND_S)      # strings compare as timestamps
        if row["last_sent_ts"] > guard:
            raise RateLimitError(
                "code already sent — wait a minute before requesting another")
    code = _generate_code()
    st.store_verification_code(conn, email=email, code_hash=_hash_code(code),
                               expires_ts=_iso_in(CODE_TTL_S))
    email_sender.send_verification_email(email, code)


def resend_verification(conn: Any, *, email: str) -> None:
    """Silent no-op for unknown/already-verified emails (anti-enumeration);
    RateLimitError is also swallowed so response shape never reveals which."""
    user = st.get_user_by_email(conn, email)
    if user is None or user["verified"]:
        return
    try:
        issue_verification(conn, email=email)
    except RateLimitError:
        pass


def verify_email(conn: Any, *, email: str, code: str) -> bool:
    """True once verified. Generic VerificationError for unknown emails,
    wrong/expired codes and exhausted attempts (no oracle differences)."""
    user = st.get_user_by_email(conn, email)
    generic = "invalid or expired code"
    if user is None:
        raise VerificationError(generic)     # no oracle vs wrong-code case
    if user["verified"]:
        return True                          # idempotent no-op
    row = st.get_verification(conn, email)
    if row is None:
        raise VerificationError(generic)
    if row["expires_ts"] < _iso_in(0):
        st.delete_verification(conn, email)
        raise VerificationError("code expired — request a new one")
    if row["code_hash"] == _hash_code(code):
        st.mark_verified(conn, email)
        st.delete_verification(conn, email)
        return True
    attempts = row["attempts"] + 1
    if attempts >= CODE_MAX_ATTEMPTS:
        st.delete_verification(conn, email)
        raise VerificationError("too many attempts — request a new code")
    st.bump_verification_attempts(conn, email, attempts)
    raise VerificationError(generic)


def require_user(authorization: str) -> str:
    """Return user_id from 'Bearer <jwt>', or raise AuthError (→401)."""
    if not authorization.lower().startswith("bearer "):
        raise AuthError("missing bearer token")
    try:
        claims = pyjwt.decode(authorization[7:], jwt_secret(),
                              algorithms=["HS256"])
    except pyjwt.PyJWTError as e:
        raise AuthError("invalid token") from e
    return claims["sub"]


def issue_api_token(conn: Any, *, user_id: str, name: str = "") -> dict:
    """Create a self-service MCP token. Plaintext is returned once, only the
    sha256 is stored. Scope is bounded to the owner's own space, read+write
    (HANDOFF step-3: server-side scope, client value never trusted)."""
    raw = "cmp_live_" + secrets.token_hex(16)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    scopes = f"read:{user_id},write:{user_id}"
    token_id = st.create_token(conn, user_id=user_id, token_hash=token_hash,
                               prefix=raw[:12], name=name, scopes=scopes)
    return {"token_id": token_id, "token": raw, "scopes": scopes}


def list_api_tokens(conn: Any, user_id: str) -> list[dict]:
    return [{"token_id": r["token_id"], "name": r["name"],
             "prefix": r["prefix"], "scopes": r["scopes"],
             "created_ts": r["created_ts"], "revoked": r["revoked_ts"] is not None}
            for r in st.list_tokens(conn, user_id)]

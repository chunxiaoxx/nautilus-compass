from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_protocol.contracts import (
    IDENTITY_ROLES_V1,
    ProtocolViolation,
    _require_identifier,
    _require_sha256,
    _require_signature,
    _require_utc,
)
from platform_protocol.keys import ED25519_V1, verify_ed25519_v1
from platform_protocol.models import ProtocolIdentity, ProtocolIdentityKey

CALLER_CREDENTIAL_VERSION_V2 = "caller-credential-v2"
CALLER_CREDENTIAL_AUDIENCE_V2 = "nautilus-platform-protocol-v2"


@dataclass(frozen=True, slots=True)
class CallerCredentialV2:
    """A short-lived caller assertion that binds one service key to one request hash."""

    credential_version: str
    audience: str
    caller_id: str
    caller_release: str
    key_id: str
    request_hash: str
    issued_at: datetime
    expires_at: datetime
    signature: str

    def __post_init__(self) -> None:
        _require_identifier(self.caller_id, "caller_id", "svc_")
        _require_identifier(self.caller_release, "caller_release", "rel_")
        _require_identifier(self.key_id, "caller_key_id", "key_")
        _require_sha256(self.request_hash, "caller_credential_request_hash")
        _require_utc(self.issued_at, "caller_credential_issued_at")
        _require_utc(self.expires_at, "caller_credential_expires_at")
        _require_signature(self.signature, "caller_credential_signature")

    @property
    def canonical_signing_bytes(self) -> bytes:
        return _canonical_json_bytes(
            {
                "audience": self.audience,
                "caller_id": self.caller_id,
                "caller_release": self.caller_release,
                "credential_version": self.credential_version,
                "expires_at": _utc_text(self.expires_at),
                "issued_at": _utc_text(self.issued_at),
                "key_id": self.key_id,
                "request_hash": self.request_hash,
            }
        )

    @property
    def credential_hash(self) -> str:
        return hashlib.sha256(
            _canonical_json_bytes(
                {
                    "audience": self.audience,
                    "caller_id": self.caller_id,
                    "caller_release": self.caller_release,
                    "credential_version": self.credential_version,
                    "expires_at": _utc_text(self.expires_at),
                    "issued_at": _utc_text(self.issued_at),
                    "key_id": self.key_id,
                    "request_hash": self.request_hash,
                    "signature": self.signature,
                }
            )
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class RegisteredIdentityKeySnapshotV2:
    identity_id: str
    principal_id: str
    release: str
    role: str
    key_id: str
    algorithm: str
    public_key_material: str


class DatabaseIdentityRegistryV2:
    """Transaction-scoped trust registry backed only by Platform identity tables."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def verify_caller_credential(
        self,
        *,
        credential: CallerCredentialV2,
        request_hash: str,
        now: datetime,
    ) -> RegisteredIdentityKeySnapshotV2:
        _require_utc(now, "now")
        _require_sha256(request_hash, "request_hash")
        if credential.credential_version != CALLER_CREDENTIAL_VERSION_V2:
            raise ProtocolViolation("caller_credential_version_mismatch")
        if credential.audience != CALLER_CREDENTIAL_AUDIENCE_V2:
            raise ProtocolViolation("caller_credential_audience_mismatch")
        if credential.request_hash != request_hash:
            raise ProtocolViolation("caller_credential_request_mismatch")
        if credential.issued_at > now:
            raise ProtocolViolation("caller_credential_not_yet_valid")
        if credential.expires_at <= now:
            raise ProtocolViolation("caller_credential_expired")
        snapshot = self.resolve_key(
            identity_id=credential.caller_id,
            release=credential.caller_release,
            role="caller",
            key_id=credential.key_id,
            now=now,
        )
        if not verify_ed25519_v1(
            snapshot.public_key_material,
            credential.canonical_signing_bytes,
            credential.signature,
        ):
            raise ProtocolViolation("invalid_caller_credential_signature")
        return snapshot

    def verify_signature(
        self,
        *,
        identity_id: str,
        release: str,
        role: str,
        key_id: str,
        payload: bytes,
        signature: str,
        now: datetime,
        failure_code: str,
    ) -> RegisteredIdentityKeySnapshotV2:
        snapshot = self.resolve_key(
            identity_id=identity_id,
            release=release,
            role=role,
            key_id=key_id,
            now=now,
        )
        if not verify_ed25519_v1(snapshot.public_key_material, payload, signature):
            raise ProtocolViolation(failure_code)
        return snapshot

    def resolve_key(
        self,
        *,
        identity_id: str,
        release: str,
        role: str,
        key_id: str,
        now: datetime,
    ) -> RegisteredIdentityKeySnapshotV2:
        _require_utc(now, "now")
        _require_known_role(role)
        identity = self._identity(identity_id, role)
        if identity.release != release:
            raise ProtocolViolation(f"{role}_release_mismatch")
        if _utc(identity.registered_at) > now:
            raise ProtocolViolation(f"{role}_identity_inactive")
        key = self._session.get(ProtocolIdentityKey, key_id)
        if key is None or key.identity_id != identity_id:
            raise ProtocolViolation(f"{role}_key_mismatch")
        if key.algorithm != ED25519_V1:
            raise ProtocolViolation(f"{role}_key_algorithm_mismatch")
        if not _active_key(key, now):
            raise ProtocolViolation(f"{role}_key_inactive")
        return RegisteredIdentityKeySnapshotV2(
            identity_id=identity.identity_id,
            principal_id=identity.principal_id,
            release=identity.release,
            role=identity.role,
            key_id=key.key_id,
            algorithm=key.algorithm,
            public_key_material=key.public_key_material,
        )

    def resolve_active_identity(
        self,
        *,
        identity_id: str,
        release: str,
        role: str,
        now: datetime,
    ) -> RegisteredIdentityKeySnapshotV2:
        _require_utc(now, "now")
        _require_known_role(role)
        identity = self._identity(identity_id, role)
        if identity.release != release:
            raise ProtocolViolation(f"{role}_release_mismatch")
        if _utc(identity.registered_at) > now:
            raise ProtocolViolation(f"{role}_identity_inactive")
        keys = self._session.scalars(
            select(ProtocolIdentityKey)
            .where(ProtocolIdentityKey.identity_id == identity_id)
            .order_by(ProtocolIdentityKey.key_id)
        )
        key = next(
            (
                candidate
                for candidate in keys
                if candidate.algorithm == ED25519_V1 and _active_key(candidate, now)
            ),
            None,
        )
        if key is None:
            raise ProtocolViolation(f"{role}_key_inactive")
        return RegisteredIdentityKeySnapshotV2(
            identity_id=identity.identity_id,
            principal_id=identity.principal_id,
            release=identity.release,
            role=identity.role,
            key_id=key.key_id,
            algorithm=key.algorithm,
            public_key_material=key.public_key_material,
        )

    def _identity(self, identity_id: str, role: str) -> ProtocolIdentity:
        identity = self._session.get(ProtocolIdentity, identity_id)
        if identity is None or identity.role != role:
            raise ProtocolViolation(f"unregistered_{role}_identity")
        return identity


def _active_key(key: ProtocolIdentityKey, now: datetime) -> bool:
    return (
        key.status == "active"
        and key.revoked_at is None
        and _utc(key.registered_at) <= now
    )


def _require_known_role(role: str) -> None:
    if role not in IDENTITY_ROLES_V1:
        raise ProtocolViolation("invalid_identity_role")


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _utc_text(value: datetime) -> str:
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

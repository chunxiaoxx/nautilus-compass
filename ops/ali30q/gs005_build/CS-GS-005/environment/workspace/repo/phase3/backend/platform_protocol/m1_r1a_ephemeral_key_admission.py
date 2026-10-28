"""Pure admission for one Platform-challenged ephemeral R1a executor key."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from platform_protocol.contracts import ProtocolViolation
from platform_protocol.keys import ED25519_V1, verify_ed25519_v1
from platform_protocol.m1_r1a_runtime_admission import R1aRuntimeAdmissionDecision

PLATFORM_CHALLENGE_VERSION = "m1-r1a-platform-announce-challenge-v1"
ANNOUNCEMENT_VERSION = "m1-r1a-ephemeral-signer-announcement-v3"
EPHEMERAL_EXECUTOR_ID = "exec_r1a_synthetic_01"
EPHEMERAL_EXECUTOR_RELEASE = "rel_r1a_ephemeral_v3"
EPHEMERAL_EXECUTOR_KEY_ID = "key_r1a_ephemeral_v3"
MAX_CHALLENGE_TTL_SECONDS = 120

_ADMITTED = R1aRuntimeAdmissionDecision(
    status="admitted_for_local_r1a_synthetic_repair",
    reason_codes=(),
)
_UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
_NONCE_RE = re.compile(r"nonce_[0-9a-f]{64}\Z")
_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
_CHALLENGE_FIELDS = frozenset(
    {"expires_at", "issued_at", "schema_version", "session_nonce", "session_nonce_hash"}
)
_ANNOUNCEMENT_FIELDS = frozenset(
    {
        "executor_id",
        "executor_key_id",
        "executor_release",
        "expires_at",
        "issued_at",
        "platform_challenge_hash",
        "proof_signature",
        "public_key_material",
        "schema_version",
        "session_nonce",
        "session_nonce_hash",
        "signature_algorithm",
    }
)


@dataclass(frozen=True, slots=True)
class PlatformAnnounceChallengeV1:
    schema_version: str
    session_nonce: str
    session_nonce_hash: str
    issued_at: str
    expires_at: str

    @property
    def canonical_bytes(self) -> bytes:
        return _canonical_json_bytes(
            {
                "expires_at": self.expires_at,
                "issued_at": self.issued_at,
                "schema_version": self.schema_version,
                "session_nonce": self.session_nonce,
                "session_nonce_hash": self.session_nonce_hash,
            }
        )

    @property
    def challenge_hash(self) -> str:
        return _sha256(self.canonical_bytes)


@dataclass(frozen=True, slots=True)
class R1aEphemeralExecutorAdmissionV1:
    executor_id: str
    executor_release: str
    executor_key_id: str
    public_key_material: str
    challenge_hash: str
    announcement_hash: str
    issued_at: datetime
    expires_at: datetime


def create_platform_announce_challenge(
    *,
    session_nonce: str,
    issued_at: datetime,
    expires_at: datetime,
    now: datetime,
) -> PlatformAnnounceChallengeV1:
    """Create the only challenge shape accepted by the isolated V5 signer."""
    current = _require_utc(now, "invalid_current_time")
    issued = _require_utc(issued_at, "invalid_challenge_issued_at")
    expires = _require_utc(expires_at, "invalid_challenge_expires_at")
    _require_nonce(session_nonce)
    if issued >= expires:
        raise ProtocolViolation("invalid_challenge_window")
    if (expires - issued).total_seconds() > MAX_CHALLENGE_TTL_SECONDS:
        raise ProtocolViolation("challenge_ttl_too_long")
    if current < issued:
        raise ProtocolViolation("challenge_not_yet_valid")
    if current >= expires:
        raise ProtocolViolation("challenge_expired")
    return PlatformAnnounceChallengeV1(
        schema_version=PLATFORM_CHALLENGE_VERSION,
        session_nonce=session_nonce,
        session_nonce_hash=_sha256(session_nonce.encode("ascii")),
        issued_at=_format_utc(issued),
        expires_at=_format_utc(expires),
    )


def admit_ephemeral_executor_announcement(
    data: bytes,
    *,
    expected_challenge: PlatformAnnounceChallengeV1,
    runtime_admission: R1aRuntimeAdmissionDecision,
    now: datetime,
) -> R1aEphemeralExecutorAdmissionV1:
    """Verify one V5 announcement and return its immutable public admission."""
    if runtime_admission != _ADMITTED:
        raise ProtocolViolation("r1a_admission_required")
    current = _require_utc(now, "invalid_current_time")
    _validate_challenge(expected_challenge, current)
    document = _parse_json_object(data)
    if frozenset(document) != _ANNOUNCEMENT_FIELDS:
        raise ProtocolViolation("unexpected_announcement_fields")
    expected = {
        "executor_id": EPHEMERAL_EXECUTOR_ID,
        "executor_key_id": EPHEMERAL_EXECUTOR_KEY_ID,
        "executor_release": EPHEMERAL_EXECUTOR_RELEASE,
        "expires_at": expected_challenge.expires_at,
        "issued_at": expected_challenge.issued_at,
        "platform_challenge_hash": expected_challenge.challenge_hash,
        "schema_version": ANNOUNCEMENT_VERSION,
        "session_nonce": expected_challenge.session_nonce,
        "session_nonce_hash": expected_challenge.session_nonce_hash,
        "signature_algorithm": ED25519_V1,
    }
    for field, expected_value in expected.items():
        if document[field] != expected_value:
            code = (
                "announcement_challenge_mismatch"
                if field.startswith(("platform_challenge", "session_"))
                else "announcement_binding_mismatch"
            )
            raise ProtocolViolation(code)
    expires_at = _parse_utc(
        expected_challenge.expires_at, "invalid_challenge_expires_at"
    )
    if current >= expires_at:
        raise ProtocolViolation("announcement_expired")
    signing_document = dict(document)
    proof_signature = signing_document.pop("proof_signature")
    public_key_material = document["public_key_material"]
    if not verify_ed25519_v1(
        public_key_material,
        _canonical_json_bytes(signing_document),
        proof_signature,
    ):
        raise ProtocolViolation("invalid_announcement_proof")
    return R1aEphemeralExecutorAdmissionV1(
        executor_id=EPHEMERAL_EXECUTOR_ID,
        executor_release=EPHEMERAL_EXECUTOR_RELEASE,
        executor_key_id=EPHEMERAL_EXECUTOR_KEY_ID,
        public_key_material=public_key_material,
        challenge_hash=expected_challenge.challenge_hash,
        announcement_hash=_sha256(data),
        issued_at=_parse_utc(
            expected_challenge.issued_at, "invalid_challenge_issued_at"
        ),
        expires_at=expires_at,
    )


def _validate_challenge(
    challenge: PlatformAnnounceChallengeV1,
    now: datetime,
) -> None:
    if not isinstance(challenge, PlatformAnnounceChallengeV1):
        raise ProtocolViolation("invalid_platform_challenge")
    document = _parse_challenge_bytes(challenge.canonical_bytes)
    if document != {
        "expires_at": challenge.expires_at,
        "issued_at": challenge.issued_at,
        "schema_version": PLATFORM_CHALLENGE_VERSION,
        "session_nonce": challenge.session_nonce,
        "session_nonce_hash": challenge.session_nonce_hash,
    }:
        raise ProtocolViolation("invalid_platform_challenge")
    issued = _parse_utc(challenge.issued_at, "invalid_challenge_issued_at")
    expires = _parse_utc(challenge.expires_at, "invalid_challenge_expires_at")
    if issued >= expires:
        raise ProtocolViolation("invalid_challenge_window")
    if (expires - issued).total_seconds() > MAX_CHALLENGE_TTL_SECONDS:
        raise ProtocolViolation("challenge_ttl_too_long")
    if now < issued:
        raise ProtocolViolation("challenge_not_yet_valid")
    if now >= expires:
        raise ProtocolViolation("announcement_expired")


def _parse_challenge_bytes(data: bytes) -> Mapping[str, Any]:
    document = _parse_json_object(data, label="platform_challenge")
    if frozenset(document) != _CHALLENGE_FIELDS:
        raise ProtocolViolation("unexpected_platform_challenge_fields")
    if document["schema_version"] != PLATFORM_CHALLENGE_VERSION:
        raise ProtocolViolation("invalid_challenge_version")
    _require_nonce(document["session_nonce"])
    nonce_hash = document["session_nonce_hash"]
    if not isinstance(nonce_hash, str) or _HASH_RE.fullmatch(nonce_hash) is None:
        raise ProtocolViolation("invalid_session_nonce_hash")
    if nonce_hash != _sha256(document["session_nonce"].encode("ascii")):
        raise ProtocolViolation("session_nonce_hash_mismatch")
    return document


def _parse_json_object(
    data: bytes,
    *,
    label: str = "announcement",
) -> Mapping[str, Any]:
    if not isinstance(data, bytes):
        raise ProtocolViolation(f"invalid_{label}_bytes")

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ProtocolViolation(f"duplicate_{label}_field")
            result[key] = value
        return result

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtocolViolation(f"invalid_{label}_json") from error
    if not isinstance(value, Mapping):
        raise ProtocolViolation(f"invalid_{label}_json")
    if _canonical_json_bytes(value) != data:
        raise ProtocolViolation(f"noncanonical_{label}")
    return value


def _require_nonce(value: object) -> None:
    if not isinstance(value, str) or _NONCE_RE.fullmatch(value) is None:
        raise ProtocolViolation("invalid_session_nonce")
    if len(set(value.removeprefix("nonce_"))) < 2:
        raise ProtocolViolation("invalid_session_nonce")


def _require_utc(value: datetime, code: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ProtocolViolation(code)
    normalized = value.astimezone(UTC)
    if value.utcoffset() != normalized.utcoffset():
        raise ProtocolViolation(code)
    return normalized


def _parse_utc(value: object, code: str) -> datetime:
    if not isinstance(value, str):
        raise ProtocolViolation(code)
    try:
        parsed = datetime.strptime(value, _UTC_FORMAT).replace(tzinfo=UTC)
    except ValueError as error:
        raise ProtocolViolation(code) from error
    if _format_utc(parsed) != value:
        raise ProtocolViolation(code)
    return parsed


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).strftime(_UTC_FORMAT)


def _canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

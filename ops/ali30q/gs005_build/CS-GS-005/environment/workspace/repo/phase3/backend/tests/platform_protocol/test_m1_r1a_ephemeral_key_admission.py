from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from platform_protocol.contracts import ProtocolViolation
from platform_protocol.keys import (
    ED25519_V1,
    encode_ed25519_public_key,
    encode_ed25519_signature,
)
from platform_protocol.m1_r1a_ephemeral_key_admission import (
    ANNOUNCEMENT_VERSION,
    EPHEMERAL_EXECUTOR_ID,
    EPHEMERAL_EXECUTOR_KEY_ID,
    EPHEMERAL_EXECUTOR_RELEASE,
    PLATFORM_CHALLENGE_VERSION,
    R1aEphemeralExecutorAdmissionV1,
    admit_ephemeral_executor_announcement,
    create_platform_announce_challenge,
)
from platform_protocol.m1_r1a_runtime_admission import R1aRuntimeAdmissionDecision

_NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
_NONCE = "nonce_" + "ab" * 32
_ADMITTED = R1aRuntimeAdmissionDecision(
    status="admitted_for_local_r1a_synthetic_repair",
    reason_codes=(),
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _announcement_bytes(challenge, private_key: Ed25519PrivateKey) -> bytes:
    document = {
        "executor_id": EPHEMERAL_EXECUTOR_ID,
        "executor_key_id": EPHEMERAL_EXECUTOR_KEY_ID,
        "executor_release": EPHEMERAL_EXECUTOR_RELEASE,
        "expires_at": challenge.expires_at,
        "issued_at": challenge.issued_at,
        "platform_challenge_hash": challenge.challenge_hash,
        "public_key_material": encode_ed25519_public_key(private_key.public_key()),
        "schema_version": ANNOUNCEMENT_VERSION,
        "session_nonce": challenge.session_nonce,
        "session_nonce_hash": challenge.session_nonce_hash,
        "signature_algorithm": ED25519_V1,
    }
    document["proof_signature"] = encode_ed25519_signature(
        private_key.sign(_canonical_bytes(document))
    )
    return _canonical_bytes(document)


def _challenge(*, ttl_seconds: int = 60):
    return create_platform_announce_challenge(
        session_nonce=_NONCE,
        issued_at=_NOW,
        expires_at=_NOW + timedelta(seconds=ttl_seconds),
        now=_NOW,
    )


def test_platform_challenge_and_live_announcement_produce_frozen_admission() -> None:
    challenge = _challenge()
    private_key = Ed25519PrivateKey.generate()

    admission = admit_ephemeral_executor_announcement(
        _announcement_bytes(challenge, private_key),
        expected_challenge=challenge,
        runtime_admission=_ADMITTED,
        now=_NOW,
    )

    assert isinstance(admission, R1aEphemeralExecutorAdmissionV1)
    assert ANNOUNCEMENT_VERSION == "m1-r1a-ephemeral-signer-announcement-v3"
    assert EPHEMERAL_EXECUTOR_RELEASE == "rel_r1a_ephemeral_v3"
    assert EPHEMERAL_EXECUTOR_KEY_ID == "key_r1a_ephemeral_v3"
    assert challenge.schema_version == PLATFORM_CHALLENGE_VERSION
    assert challenge.canonical_bytes == _canonical_bytes(
        json.loads(challenge.canonical_bytes)
    )
    assert admission.executor_id == EPHEMERAL_EXECUTOR_ID
    assert admission.executor_release == EPHEMERAL_EXECUTOR_RELEASE
    assert admission.executor_key_id == EPHEMERAL_EXECUTOR_KEY_ID
    assert admission.public_key_material == encode_ed25519_public_key(
        private_key.public_key()
    )
    assert admission.challenge_hash == challenge.challenge_hash
    assert (
        admission.announcement_hash
        == hashlib.sha256(_announcement_bytes(challenge, private_key)).hexdigest()
    )
    assert admission.issued_at == _NOW
    assert admission.expires_at == _NOW + timedelta(seconds=60)


@pytest.mark.parametrize(
    ("issued_at", "expires_at", "now", "error"),
    [
        (_NOW, _NOW + timedelta(seconds=121), _NOW, "challenge_ttl_too_long"),
        (_NOW, _NOW, _NOW, "invalid_challenge_window"),
        (
            _NOW + timedelta(seconds=1),
            _NOW + timedelta(seconds=60),
            _NOW,
            "challenge_not_yet_valid",
        ),
        (_NOW - timedelta(seconds=60), _NOW, _NOW, "challenge_expired"),
    ],
)
def test_platform_challenge_rejects_invalid_time_windows(
    issued_at: datetime,
    expires_at: datetime,
    now: datetime,
    error: str,
) -> None:
    with pytest.raises(ProtocolViolation, match=error):
        create_platform_announce_challenge(
            session_nonce=_NONCE,
            issued_at=issued_at,
            expires_at=expires_at,
            now=now,
        )


@pytest.mark.parametrize("nonce", ["nonce_" + "0" * 64, "bad", "nonce_" + "A" * 64])
def test_platform_challenge_rejects_noncanonical_nonce(nonce: str) -> None:
    with pytest.raises(ProtocolViolation, match="invalid_session_nonce"):
        create_platform_announce_challenge(
            session_nonce=nonce,
            issued_at=_NOW,
            expires_at=_NOW + timedelta(seconds=60),
            now=_NOW,
        )


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("executor_id", "exec_other_01", "announcement_binding_mismatch"),
        ("executor_release", "rel_other_01", "announcement_binding_mismatch"),
        ("executor_key_id", "key_other_01", "announcement_binding_mismatch"),
        ("signature_algorithm", "rsa-v1", "announcement_binding_mismatch"),
        ("platform_challenge_hash", "0" * 64, "announcement_challenge_mismatch"),
        ("session_nonce_hash", "0" * 64, "announcement_challenge_mismatch"),
    ],
)
def test_announcement_rejects_changed_bindings(
    field: str, value: object, error: str
) -> None:
    challenge = _challenge()
    private_key = Ed25519PrivateKey.generate()
    document = json.loads(_announcement_bytes(challenge, private_key))
    document[field] = value

    with pytest.raises(ProtocolViolation, match=error):
        admit_ephemeral_executor_announcement(
            _canonical_bytes(document),
            expected_challenge=challenge,
            runtime_admission=_ADMITTED,
            now=_NOW,
        )


def test_announcement_rejects_invalid_proof_duplicate_extra_and_noncanonical_bytes() -> (
    None
):
    challenge = _challenge()
    private_key = Ed25519PrivateKey.generate()
    raw = _announcement_bytes(challenge, private_key)
    document = json.loads(raw)
    document["proof_signature"] = "sig_" + "A" * 86
    with pytest.raises(ProtocolViolation, match="invalid_announcement_proof"):
        admit_ephemeral_executor_announcement(
            _canonical_bytes(document),
            expected_challenge=challenge,
            runtime_admission=_ADMITTED,
            now=_NOW,
        )

    duplicate = raw.replace(
        b'{"executor_id"', b'{"executor_id":"exec_other_01","executor_id"'
    )
    with pytest.raises(ProtocolViolation, match="duplicate_announcement_field"):
        admit_ephemeral_executor_announcement(
            duplicate,
            expected_challenge=challenge,
            runtime_admission=_ADMITTED,
            now=_NOW,
        )

    document = json.loads(raw)
    document["raw_prompt"] = "forbidden"
    with pytest.raises(ProtocolViolation, match="unexpected_announcement_fields"):
        admit_ephemeral_executor_announcement(
            _canonical_bytes(document),
            expected_challenge=challenge,
            runtime_admission=_ADMITTED,
            now=_NOW,
        )

    with pytest.raises(ProtocolViolation, match="noncanonical_announcement"):
        admit_ephemeral_executor_announcement(
            json.dumps(json.loads(raw), indent=2).encode(),
            expected_challenge=challenge,
            runtime_admission=_ADMITTED,
            now=_NOW,
        )


def test_announcement_rejects_wrong_or_expired_challenge_and_blocked_runtime() -> None:
    challenge = _challenge()
    private_key = Ed25519PrivateKey.generate()
    raw = _announcement_bytes(challenge, private_key)
    other_challenge = create_platform_announce_challenge(
        session_nonce="nonce_" + "cd" * 32,
        issued_at=_NOW,
        expires_at=_NOW + timedelta(seconds=60),
        now=_NOW,
    )

    with pytest.raises(ProtocolViolation, match="announcement_challenge_mismatch"):
        admit_ephemeral_executor_announcement(
            raw,
            expected_challenge=other_challenge,
            runtime_admission=_ADMITTED,
            now=_NOW,
        )
    with pytest.raises(ProtocolViolation, match="announcement_expired"):
        admit_ephemeral_executor_announcement(
            raw,
            expected_challenge=challenge,
            runtime_admission=_ADMITTED,
            now=_NOW + timedelta(seconds=60),
        )
    with pytest.raises(ProtocolViolation, match="r1a_admission_required"):
        admit_ephemeral_executor_announcement(
            raw,
            expected_challenge=challenge,
            runtime_admission=replace(_ADMITTED, status="blocked"),
            now=_NOW,
        )

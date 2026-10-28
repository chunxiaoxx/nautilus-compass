"""Pure canonical contract tests for executor-authenticated R1a evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from platform_protocol.contracts import ProtocolViolation
from platform_protocol.keys import (
    ED25519_V1,
    encode_ed25519_public_key,
    encode_ed25519_signature,
    verify_ed25519_v1,
)
from platform_protocol.m1_r1a_execution_evidence import (
    EVIDENCE_CONTRACT_VERSION,
    EVIDENCE_VECTOR_SET_VERSION,
    ExecutorExecutionEvidenceV1,
    parse_executor_execution_evidence_bytes,
)

_PACKAGE = Path(__file__).resolve().parents[2] / "platform_protocol"
_VECTOR_PATH = _PACKAGE / "m1_r1a_execution_evidence_vectors_v1.json"
_HASH_PATH = _PACKAGE / "m1_r1a_execution_evidence_vectors_v1.sha256"


def _unsigned_evidence() -> ExecutorExecutionEvidenceV1:
    return ExecutorExecutionEvidenceV1(
        evidence_version=EVIDENCE_CONTRACT_VERSION,
        operation_id="op_r1a_synthetic_01",
        attempt_id="att_r1a_synthetic_01",
        input_ref_hash="1" * 64,
        executor_id="exec_r1a_synthetic_01",
        executor_release="rel_r1a_synthetic_01",
        executor_key_id="key_r1a_synthetic_01",
        bound_capsule_hash="2" * 64,
        fixture_hash="3" * 64,
        tool_policy_hash="4" * 64,
        artifact_hash="5" * 64,
        result_state="completed",
        produced_at=datetime(2026, 8, 9, 12, 30, tzinfo=timezone.utc),
        signature_algorithm=ED25519_V1,
        executor_signature="sig_" + "A" * 86,
    )


def _signed_evidence():
    private_key = Ed25519PrivateKey.generate()
    public_key_material = encode_ed25519_public_key(private_key.public_key())
    unsigned = _unsigned_evidence()
    signature = encode_ed25519_signature(
        private_key.sign(unsigned.canonical_signing_bytes)
    )
    return replace(unsigned, executor_signature=signature), public_key_material


def test_canonical_signing_bytes_exclude_only_signature() -> None:
    evidence, public_key_material = _signed_evidence()
    signing_document = json.loads(evidence.canonical_signing_bytes)
    serialized_document = json.loads(evidence.canonical_bytes)

    assert "executor_signature" not in signing_document
    assert serialized_document == {
        **signing_document,
        "executor_signature": evidence.executor_signature,
    }
    assert verify_ed25519_v1(
        public_key_material,
        evidence.canonical_signing_bytes,
        evidence.executor_signature,
    )
    assert parse_executor_execution_evidence_bytes(evidence.canonical_bytes) == evidence


@pytest.mark.parametrize(
    ("field", "changed"),
    [
        ("operation_id", "op_r1a_synthetic_02"),
        ("attempt_id", "att_r1a_synthetic_02"),
        ("input_ref_hash", "a" * 64),
        ("executor_id", "exec_r1a_synthetic_02"),
        ("executor_release", "rel_r1a_synthetic_02"),
        ("executor_key_id", "key_r1a_synthetic_02"),
        ("bound_capsule_hash", "b" * 64),
        ("fixture_hash", "c" * 64),
        ("tool_policy_hash", "d" * 64),
        ("artifact_hash", "e" * 64),
        ("result_state", "review_required"),
        ("produced_at", datetime(2026, 8, 9, 12, 31, tzinfo=timezone.utc)),
    ],
)
def test_every_changed_binding_invalidates_the_executor_signature(
    field: str, changed: object
) -> None:
    evidence, public_key_material = _signed_evidence()
    changed_evidence = replace(evidence, **{field: changed})

    assert not verify_ed25519_v1(
        public_key_material,
        changed_evidence.canonical_signing_bytes,
        evidence.executor_signature,
    )


@pytest.mark.parametrize(
    "extra_field",
    [
        "unknown",
        "raw_patch",
        "raw_evidence",
        "path",
        "prompt",
        "token",
        "private_key",
    ],
)
def test_unknown_or_raw_fields_fail_closed(extra_field: str) -> None:
    evidence, _ = _signed_evidence()
    document = json.loads(evidence.canonical_bytes)
    document[extra_field] = "prohibited-marker"

    with pytest.raises(ProtocolViolation, match="unexpected_evidence_fields"):
        parse_executor_execution_evidence_bytes(json.dumps(document).encode())


def test_duplicate_field_fails_closed() -> None:
    evidence, _ = _signed_evidence()
    duplicated = evidence.canonical_bytes.replace(
        b'{"artifact_hash"',
        b'{"artifact_hash":"f' + b"f" * 63 + b'","artifact_hash"',
        1,
    )

    with pytest.raises(ProtocolViolation, match="duplicate_evidence_field"):
        parse_executor_execution_evidence_bytes(duplicated)


@pytest.mark.parametrize(
    "changes",
    [
        {"evidence_version": "m1-r1a-executor-execution-evidence-v2"},
        {"executor_key_id": "bad-key"},
        {"signature_algorithm": "rsa-v1"},
        {"executor_signature": "sig_bad"},
        {"input_ref_hash": "A" * 64},
        {
            "produced_at": datetime(2026, 8, 9, 12, 30, tzinfo=timezone.utc).replace(
                tzinfo=None
            )
        },
        {
            "produced_at": datetime(
                2026, 8, 9, 12, 30, tzinfo=timezone(timedelta(hours=8))
            )
        },
    ],
)
def test_invalid_shape_algorithm_hash_signature_or_time_fails_closed(
    changes: dict[str, object],
) -> None:
    with pytest.raises(ProtocolViolation):
        replace(_unsigned_evidence(), **changes)


def test_noncanonical_serialized_utc_time_fails_closed() -> None:
    evidence, _ = _signed_evidence()
    document = json.loads(evidence.canonical_bytes)
    document["produced_at"] = "2026-08-09T12:30:00+00:00"

    with pytest.raises(ProtocolViolation, match="invalid_produced_at"):
        parse_executor_execution_evidence_bytes(json.dumps(document).encode())


def test_published_vectors_and_lf_hash_are_byte_exact() -> None:
    vector_bytes = _VECTOR_PATH.read_bytes()
    published_hash = _HASH_PATH.read_text(encoding="ascii").strip()
    vectors = json.loads(vector_bytes)

    assert b"\r" not in vector_bytes
    assert vector_bytes.endswith(b"\n")
    assert hashlib.sha256(vector_bytes).hexdigest() == published_hash
    assert vectors["evidence_contract_version"] == EVIDENCE_CONTRACT_VERSION
    assert vectors["vector_set_version"] == EVIDENCE_VECTOR_SET_VERSION
    vector = vectors["vectors"][0]
    evidence = parse_executor_execution_evidence_bytes(
        json.dumps(vector["evidence"], separators=(",", ":"), sort_keys=True).encode()
    )
    assert (
        hashlib.sha256(evidence.canonical_signing_bytes).hexdigest()
        == vector["expected"]["canonical_signing_sha256"]
    )
    assert (
        hashlib.sha256(evidence.canonical_bytes).hexdigest()
        == vector["expected"]["canonical_evidence_sha256"]
    )

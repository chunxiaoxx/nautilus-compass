"""Independent, test-only verifier for the bounded R1a synthetic repair."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_protocol.contracts import (
    ExecutionAttemptV2,
    IndependentReceiptV2,
    ManifestV2,
    OperationEnvelopeV2,
    ProtocolViolation,
)
from platform_protocol.keys import encode_ed25519_signature
from platform_protocol.m1_r1a_execution_evidence import ExecutorExecutionEvidenceV1
from platform_protocol.models import ProtocolExecutorEvidence, ProtocolManifest
from platform_protocol.registry import DatabaseIdentityRegistryV2
from platform_protocol.repository import executor_execution_evidence

MANIFEST_READ_GRANT_VERSION = "m1-r1a-manifest-read-grant-v1"
REQUIRED_SCOPE_EVIDENCE = (
    "integrity:fixed-patch-sha256",
    "scope:disposable-synthetic-module-only",
)
INTEGRITY_ONLY_SCOPE_EVIDENCE = ("integrity:fixed-patch-sha256",)
FIXED_FIXTURE_BYTES = (
    b"def clamp_int(value: int, lower: int, upper: int) -> int:\n"
    b"    if lower > upper:\n"
    b'        raise ValueError("lower must not exceed upper")\n'
    b"    return value\n"
)
FIXED_PATCH_BYTES = (
    b"--- a/synthetic_clamp.py\n"
    b"+++ b/synthetic_clamp.py\n"
    b"@@ -1,4 +1,6 @@\n"
    b" def clamp_int(value: int, lower: int, upper: int) -> int:\n"
    b"     if lower > upper:\n"
    b'         raise ValueError("lower must not exceed upper")\n'
    b"-    return value\n"
    b"+    if value < lower:\n"
    b"+        return lower\n"
    b"+    return min(value, upper)\n"
)
FIXED_REPAIRED_BYTES = (
    b"def clamp_int(value: int, lower: int, upper: int) -> int:\n"
    b"    if lower > upper:\n"
    b'        raise ValueError("lower must not exceed upper")\n'
    b"    if value < lower:\n"
    b"        return lower\n"
    b"    return min(value, upper)\n"
)

_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
_NONCE_RE = re.compile(r"nonce_[0-9a-f]{64}\Z")


def _canonical_bytes(value: dict[str, object]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ProtocolViolation("invalid_grant_time")
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass(frozen=True, slots=True)
class ManifestReadGrantV1:
    operation_id: str
    attempt_id: str
    manifest_hash: str
    artifact_id: str
    artifact_hash: str
    storage_ref: str
    verifier_id: str
    verifier_release: str
    platform_identity_id: str
    platform_release: str
    platform_key_id: str
    nonce: str
    issued_at: datetime
    expires_at: datetime
    signature: str
    schema_version: str = MANIFEST_READ_GRANT_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != MANIFEST_READ_GRANT_VERSION:
            raise ProtocolViolation("invalid_manifest_read_grant_version")
        if _HASH_RE.fullmatch(self.manifest_hash) is None:
            raise ProtocolViolation("invalid_manifest_read_grant_hash")
        if _HASH_RE.fullmatch(self.artifact_hash) is None:
            raise ProtocolViolation("invalid_manifest_read_grant_hash")
        if _NONCE_RE.fullmatch(self.nonce) is None:
            raise ProtocolViolation("invalid_manifest_read_grant_nonce")
        if self.issued_at >= self.expires_at:
            raise ProtocolViolation("invalid_manifest_read_grant_window")
        _utc_text(self.issued_at)
        _utc_text(self.expires_at)

    @property
    def canonical_signing_bytes(self) -> bytes:
        return _canonical_bytes(self._data(include_signature=False))

    def _data(self, *, include_signature: bool) -> dict[str, object]:
        data: dict[str, object] = {
            "artifact_hash": self.artifact_hash,
            "artifact_id": self.artifact_id,
            "attempt_id": self.attempt_id,
            "expires_at": _utc_text(self.expires_at),
            "issued_at": _utc_text(self.issued_at),
            "manifest_hash": self.manifest_hash,
            "nonce": self.nonce,
            "operation_id": self.operation_id,
            "platform_identity_id": self.platform_identity_id,
            "platform_key_id": self.platform_key_id,
            "platform_release": self.platform_release,
            "schema_version": self.schema_version,
            "storage_ref": self.storage_ref,
            "verifier_id": self.verifier_id,
            "verifier_release": self.verifier_release,
        }
        if include_signature:
            data["signature"] = self.signature
        return data


@dataclass(frozen=True, slots=True)
class IndependentVerificationResultV1:
    receipt: IndependentReceiptV2
    temporary_fixture_removed: bool
    outcome: str


class TestOnlyProtectedArtifactStore:
    """In-memory artifact bytes readable only through one signed grant."""

    def __init__(self) -> None:
        self._artifacts: dict[str, bytes] = {}
        self._consumed_nonces: set[str] = set()

    def put(self, storage_ref: str, artifact: bytes) -> None:
        if storage_ref in self._artifacts:
            raise ProtocolViolation("artifact_storage_conflict")
        self._artifacts[storage_ref] = bytes(artifact)

    def read_once(
        self,
        grant: ManifestReadGrantV1,
        *,
        registry: DatabaseIdentityRegistryV2,
        now: datetime,
    ) -> bytes:
        if now < grant.issued_at or now >= grant.expires_at:
            raise ProtocolViolation("manifest_read_grant_expired")
        if grant.nonce in self._consumed_nonces:
            raise ProtocolViolation("manifest_read_grant_replayed")
        registry.verify_signature(
            identity_id=grant.platform_identity_id,
            release=grant.platform_release,
            role="platform",
            key_id=grant.platform_key_id,
            payload=grant.canonical_signing_bytes,
            signature=grant.signature,
            now=now,
            failure_code="invalid_manifest_read_grant_signature",
        )
        artifact = self._artifacts.get(grant.storage_ref)
        if (
            artifact is None
            or hashlib.sha256(artifact).hexdigest() != grant.artifact_hash
        ):
            raise ProtocolViolation("manifest_read_grant_artifact_mismatch")
        self._consumed_nonces.add(grant.nonce)
        return artifact


def create_manifest_read_grant(
    *,
    operation: OperationEnvelopeV2,
    attempt: ExecutionAttemptV2,
    manifest: ManifestV2,
    verifier_id: str,
    verifier_release: str,
    nonce: str,
    issued_at: datetime,
    expires_at: datetime,
    platform_private_key: Ed25519PrivateKey,
) -> ManifestReadGrantV1:
    artifact = manifest.artifacts[0]
    unsigned = ManifestReadGrantV1(
        operation_id=operation.operation_id,
        attempt_id=attempt.attempt_id,
        manifest_hash=manifest.manifest_hash,
        artifact_id=artifact.artifact_id,
        artifact_hash=artifact.sha256,
        storage_ref=artifact.storage_ref,
        verifier_id=verifier_id,
        verifier_release=verifier_release,
        platform_identity_id=operation.platform_identity_id,
        platform_release=operation.platform_release,
        platform_key_id=operation.platform_key_id,
        nonce=nonce,
        issued_at=issued_at,
        expires_at=expires_at,
        signature="sig_" + "A" * 86,
    )
    return replace(
        unsigned,
        signature=encode_ed25519_signature(
            platform_private_key.sign(unsigned.canonical_signing_bytes)
        ),
    )


def require_persisted_verifier_inputs(
    *,
    session: Session,
    evidence: ExecutorExecutionEvidenceV1,
    manifest: ManifestV2,
) -> ExecutorExecutionEvidenceV1:
    """Load the atomic DB result and reject any substituted in-memory outcome."""
    evidence_row = session.scalar(
        select(ProtocolExecutorEvidence).where(
            ProtocolExecutorEvidence.operation_id == evidence.operation_id,
            ProtocolExecutorEvidence.attempt_id == evidence.attempt_id,
        )
    )
    if evidence_row is None:
        raise ProtocolViolation("persisted_executor_evidence_missing")
    persisted_evidence = executor_execution_evidence(evidence_row)
    if (
        evidence_row.evidence_hash
        != hashlib.sha256(persisted_evidence.canonical_bytes).hexdigest()
        or persisted_evidence != evidence
    ):
        raise ProtocolViolation("persisted_executor_evidence_mismatch")
    manifest_row = session.scalar(
        select(ProtocolManifest).where(
            ProtocolManifest.operation_id == manifest.operation_id,
            ProtocolManifest.attempt_id == manifest.attempt_id,
        )
    )
    if (
        manifest_row is None
        or manifest_row.manifest_hash != manifest.manifest_hash
        or manifest_row.operation_id != manifest.operation_id
        or manifest_row.attempt_id != manifest.attempt_id
        or manifest_row.executor_id != manifest.executor_id
        or manifest_row.executor_release != manifest.executor_release
    ):
        raise ProtocolViolation("persisted_manifest_mismatch")
    return persisted_evidence


def verify_and_sign_receipt(
    *,
    session: Session,
    store: TestOnlyProtectedArtifactStore,
    grant: ManifestReadGrantV1,
    operation: OperationEnvelopeV2,
    attempt: ExecutionAttemptV2,
    manifest: ManifestV2,
    evidence: ExecutorExecutionEvidenceV1,
    verifier_id: str,
    verifier_release: str,
    verifier_key_id: str,
    verifier_private_key: Ed25519PrivateKey,
    now: datetime,
) -> IndependentVerificationResultV1:
    """Re-verify every binding, run the fixed oracle, and sign one receipt."""
    evidence = require_persisted_verifier_inputs(
        session=session,
        evidence=evidence,
        manifest=manifest,
    )
    expected_scope_by_result = {
        "completed": REQUIRED_SCOPE_EVIDENCE,
        "review_required": INTEGRITY_ONLY_SCOPE_EVIDENCE,
    }
    if evidence.result_state not in expected_scope_by_result:
        raise ProtocolViolation("scope_evidence_outcome_mismatch")
    artifact = manifest.artifacts[0]
    if (
        evidence.operation_id != operation.operation_id
        or evidence.attempt_id != attempt.attempt_id
        or evidence.input_ref_hash != attempt.input_ref_hash
        or evidence.executor_id != attempt.executor_id
        or evidence.executor_release != attempt.executor_release
        or evidence.tool_policy_hash != attempt.tool_policy_hash
        or evidence.artifact_hash != artifact.sha256
        or manifest.operation_id != operation.operation_id
        or manifest.attempt_id != attempt.attempt_id
        or manifest.executor_id != attempt.executor_id
        or manifest.executor_release != attempt.executor_release
        or grant.operation_id != operation.operation_id
        or grant.attempt_id != attempt.attempt_id
        or grant.manifest_hash != manifest.manifest_hash
        or grant.artifact_id != artifact.artifact_id
        or grant.artifact_hash != artifact.sha256
        or grant.storage_ref != artifact.storage_ref
        or grant.verifier_id != verifier_id
        or grant.verifier_release != verifier_release
    ):
        raise ProtocolViolation("independent_verifier_binding_mismatch")

    registry = DatabaseIdentityRegistryV2(session)
    executor = registry.verify_signature(
        identity_id=evidence.executor_id,
        release=evidence.executor_release,
        role="executor",
        key_id=evidence.executor_key_id,
        payload=evidence.canonical_signing_bytes,
        signature=evidence.executor_signature,
        now=now,
        failure_code="invalid_executor_evidence_signature",
    )
    verifier = registry.resolve_key(
        identity_id=verifier_id,
        release=verifier_release,
        role="verifier",
        key_id=verifier_key_id,
        now=now,
    )
    if (
        executor.principal_id == verifier.principal_id
        or executor.public_key_material == verifier.public_key_material
    ):
        raise ProtocolViolation("executor_verifier_conflict")

    candidate = store.read_once(grant, registry=registry, now=now)
    if candidate != FIXED_PATCH_BYTES:
        raise ProtocolViolation("unexpected_synthetic_patch")
    fixture_hash = hashlib.sha256(FIXED_FIXTURE_BYTES).hexdigest()
    if evidence.fixture_hash != fixture_hash:
        raise ProtocolViolation("fixture_hash_mismatch")

    if evidence.result_state == "completed":
        fixture_path: Path | None = None
        with tempfile.TemporaryDirectory(prefix="nautilus_r1a_fixture_") as directory:
            fixture_path = Path(directory) / "synthetic_clamp.py"
            fixture_path.write_bytes(FIXED_FIXTURE_BYTES)
            if hashlib.sha256(fixture_path.read_bytes()).hexdigest() != fixture_hash:
                raise ProtocolViolation("fixture_hash_mismatch")
            fixture_path.write_bytes(
                _apply_fixed_patch(fixture_path.read_bytes(), candidate)
            )
            _run_fixed_oracle(fixture_path.read_bytes())
        temporary_fixture_removed = (
            fixture_path is not None and not fixture_path.exists()
        )
        if not temporary_fixture_removed:
            raise ProtocolViolation("temporary_fixture_not_removed")
    else:
        temporary_fixture_removed = True

    unsigned = IndependentReceiptV2(
        operation_id=operation.operation_id,
        attempt_id=attempt.attempt_id,
        manifest_hash=manifest.manifest_hash,
        verifier_id=verifier_id,
        verifier_release=verifier_release,
        policy_version=operation.policy_version,
        decision="accepted",
        decision_vocabulary_version="protocol-v2-decisions-v1",
        reason_codes=("policy_satisfied",),
        reason_code_vocabulary_version="protocol-v2-reason-codes-v1",
        issued_at=now,
        key_id=verifier_key_id,
        signature="sig_" + "A" * 86,
    )
    receipt = replace(
        unsigned,
        signature=encode_ed25519_signature(
            verifier_private_key.sign(unsigned.canonical_signing_bytes)
        ),
    )
    return IndependentVerificationResultV1(
        receipt=receipt,
        temporary_fixture_removed=temporary_fixture_removed,
        outcome=evidence.result_state,
    )


def _apply_fixed_patch(fixture: bytes, patch: bytes) -> bytes:
    if fixture != FIXED_FIXTURE_BYTES or patch != FIXED_PATCH_BYTES:
        raise ProtocolViolation("unexpected_synthetic_patch")
    return FIXED_REPAIRED_BYTES


def _run_fixed_oracle(source: bytes) -> None:
    namespace: dict[str, object] = {}
    exec(compile(source, "synthetic_clamp.py", "exec"), namespace)  # noqa: S102
    clamp = namespace["clamp_int"]
    if not callable(clamp):
        raise ProtocolViolation("synthetic_oracle_failed")
    for value, lower, upper, expected in (
        (-1, 0, 10, 0),
        (11, 0, 10, 10),
        (7, 0, 10, 7),
    ):
        if clamp(value, lower, upper) != expected:
            raise ProtocolViolation("synthetic_oracle_failed")
    try:
        clamp(1, 2, 1)
    except ValueError:
        return
    raise ProtocolViolation("synthetic_oracle_failed")

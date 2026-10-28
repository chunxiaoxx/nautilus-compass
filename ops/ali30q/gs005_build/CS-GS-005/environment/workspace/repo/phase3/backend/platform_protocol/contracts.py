from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

PROTOCOL_CONTRACT_VERSION = "protocol-v2-contracts-v1"
DECISION_VOCABULARY_VERSION = "protocol-v2-decisions-v1"
REASON_CODE_VOCABULARY_VERSION = "protocol-v2-reason-codes-v1"
RECEIPT_DECISIONS_V1 = ("accepted", "rejected", "blocked")
REASON_CODES_V1 = (
    "binding_mismatch",
    "input_unavailable",
    "lease_expired",
    "manifest_tampered",
    "policy_denied",
    "policy_satisfied",
    "signature_invalid",
    "verifier_unavailable",
)
OPERATION_KINDS_V1 = frozenset({"bounded_execution", "bounded_verification"})
IDENTITY_ROLES_V1 = frozenset({"caller", "platform", "executor", "verifier"})

SignatureSigner = Callable[[str, bytes], str]
SignatureVerifier = Callable[[str, bytes, str], bool]

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_MEDIA_TYPE_RE = re.compile(
    r"[a-z0-9][a-z0-9!#$&^_.+-]{0,63}/[a-z0-9][a-z0-9!#$&^_.+-]{0,63}"
)
_STORAGE_REF_RE = re.compile(r"vault://artifact/[a-z0-9][a-z0-9_-]{2,63}")
_SIGNATURE_RE = re.compile(r"sig_[A-Za-z0-9_-]{16,512}")


class ProtocolViolation(ValueError):
    """A fixed protocol validation reason code."""


def _violate(code: str) -> None:
    raise ProtocolViolation(code)


def _require_identifier(value: str, field_name: str, prefix: str) -> None:
    expression = re.compile(rf"{re.escape(prefix)}[a-z0-9][a-z0-9_-]{{1,60}}")
    if not isinstance(value, str) or expression.fullmatch(value) is None:
        _violate(f"invalid_{field_name}")


def _require_agent_identity(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        _violate(f"invalid_{field_name}")
    prefixes = ("agent_", "exec_", "ver_")
    if not any(
        re.fullmatch(rf"{prefix}[a-z0-9][a-z0-9_-]{{1,60}}", value)
        for prefix in prefixes
    ):
        _violate(f"invalid_{field_name}")


def _require_utc(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        _violate(f"invalid_{field_name}")
    if value.utcoffset() != timedelta(0):
        _violate(f"invalid_{field_name}")


def _utc_text(value: datetime) -> str:
    _require_utc(value, "timestamp")
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _operation_request_payload(
    *,
    source_ref_hash: str,
    source_version: str,
    operation_kind: str,
    policy_version: str,
    idempotency_key: str,
    expires_at: datetime,
) -> Mapping[str, str]:
    return {
        "expires_at": _utc_text(expires_at),
        "idempotency_key": idempotency_key,
        "operation_kind": operation_kind,
        "policy_version": policy_version,
        "source_ref_hash": source_ref_hash,
        "source_version": source_version,
    }


def _require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _violate(f"invalid_{field_name}")


def _require_signature(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _SIGNATURE_RE.fullmatch(value) is None:
        _violate(f"invalid_{field_name}")


def _verify_signature(
    *,
    key_id: str,
    payload: bytes,
    signature: str,
    signature_verifier: SignatureVerifier,
    failure_code: str,
) -> None:
    valid = signature_verifier(key_id, payload, signature)
    if valid is not True:
        _violate(failure_code)


@dataclass(frozen=True, slots=True)
class RegisteredIdentityV2:
    """A Platform registration that binds an opaque identity to one principal and key."""

    identity_id: str
    principal_id: str
    release: str
    key_id: str
    role: str

    def __post_init__(self) -> None:
        prefix = {
            "caller": "svc_",
            "platform": "plt_",
            "executor": "exec_",
            "verifier": "ver_",
        }.get(self.role)
        if prefix is None:
            _violate("invalid_identity_role")
        _require_identifier(self.identity_id, "identity_id", prefix)
        _require_identifier(self.principal_id, "principal_id", "prn_")
        _require_identifier(self.release, "identity_release", "rel_")
        _require_identifier(self.key_id, "identity_key_id", "key_")


@dataclass(frozen=True, slots=True)
class IdentityRegistryV2:
    """Read-only Platform registration snapshot used by all trust-boundary validators."""

    identities: tuple[RegisteredIdentityV2, ...]

    def __post_init__(self) -> None:
        identities = tuple(self.identities)
        if not identities or not all(
            isinstance(identity, RegisteredIdentityV2) for identity in identities
        ):
            _violate("invalid_identity_registry")
        if len({identity.identity_id for identity in identities}) != len(identities):
            _violate("duplicate_registered_identity")
        if len({identity.key_id for identity in identities}) != len(identities):
            _violate("duplicate_registered_key")
        object.__setattr__(self, "identities", identities)

    def resolve(self, identity_id: str) -> RegisteredIdentityV2:
        for identity in self.identities:
            if identity.identity_id == identity_id:
                return identity
        _violate("unregistered_identity")


def _require_registered_identity(
    *,
    registry: IdentityRegistryV2,
    identity_id: str,
    release: str,
    key_id: str,
    role: str,
) -> RegisteredIdentityV2:
    identity = registry.resolve(identity_id)
    if identity.role != role:
        _violate(f"unregistered_{role}_identity")
    if identity.release != release:
        _violate(f"{role}_release_mismatch")
    if identity.key_id != key_id:
        _violate(f"{role}_key_mismatch")
    return identity


@dataclass(frozen=True, slots=True)
class OperationRequestV2:
    """Untrusted request data that cannot choose a Platform operation identity."""

    source_ref_hash: str
    source_version: str
    operation_kind: str
    policy_version: str
    idempotency_key: str
    expires_at: datetime

    def __post_init__(self) -> None:
        _require_sha256(self.source_ref_hash, "source_ref_hash")
        _require_identifier(self.source_version, "source_version", "srcv_")
        if self.operation_kind not in OPERATION_KINDS_V1:
            _violate("invalid_operation_kind")
        _require_identifier(self.policy_version, "policy_version", "pol_")
        _require_identifier(self.idempotency_key, "idempotency_key", "idem_")
        _require_utc(self.expires_at, "expires_at")

    @property
    def canonical_request_hash(self) -> str:
        return hashlib.sha256(self.canonical_request_bytes).hexdigest()

    @property
    def canonical_request_bytes(self) -> bytes:
        return _canonical_json_bytes(
            _operation_request_payload(
                source_ref_hash=self.source_ref_hash,
                source_version=self.source_version,
                operation_kind=self.operation_kind,
                policy_version=self.policy_version,
                idempotency_key=self.idempotency_key,
                expires_at=self.expires_at,
            )
        )


@dataclass(frozen=True, slots=True)
class OperationEnvelopeV2:
    operation_id: str
    caller_id: str
    source_ref_hash: str
    source_version: str
    operation_kind: str
    policy_version: str
    idempotency_key: str
    expires_at: datetime
    platform_identity_id: str
    platform_release: str
    platform_key_id: str
    platform_signature: str

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id", "op_")
        _require_identifier(self.caller_id, "caller_id", "svc_")
        _require_sha256(self.source_ref_hash, "source_ref_hash")
        _require_identifier(self.source_version, "source_version", "srcv_")
        if self.operation_kind not in OPERATION_KINDS_V1:
            _violate("invalid_operation_kind")
        _require_identifier(self.policy_version, "policy_version", "pol_")
        _require_identifier(self.idempotency_key, "idempotency_key", "idem_")
        _require_utc(self.expires_at, "expires_at")
        _require_identifier(self.platform_identity_id, "platform_identity_id", "plt_")
        _require_identifier(self.platform_release, "platform_release", "rel_")
        _require_identifier(self.platform_key_id, "platform_key_id", "key_")
        _require_signature(self.platform_signature, "platform_signature")

    @property
    def idempotency_payload_hash(self) -> str:
        return hashlib.sha256(
            _canonical_json_bytes(self._idempotency_payload)
        ).hexdigest()

    @property
    def _idempotency_payload(self) -> Mapping[str, str]:
        return {
            "source_ref_hash": self.source_ref_hash,
            "source_version": self.source_version,
            "operation_kind": self.operation_kind,
            "policy_version": self.policy_version,
            "expires_at": _utc_text(self.expires_at),
        }

    @property
    def canonical_request_hash(self) -> str:
        return hashlib.sha256(self.canonical_request_bytes).hexdigest()

    @property
    def canonical_request_bytes(self) -> bytes:
        return _canonical_json_bytes(
            _operation_request_payload(
                source_ref_hash=self.source_ref_hash,
                source_version=self.source_version,
                operation_kind=self.operation_kind,
                policy_version=self.policy_version,
                idempotency_key=self.idempotency_key,
                expires_at=self.expires_at,
            )
        )

    @property
    def canonical_issuance_bytes(self) -> bytes:
        return _canonical_json_bytes(
            {
                "caller_id": self.caller_id,
                "expires_at": _utc_text(self.expires_at),
                "idempotency_key": self.idempotency_key,
                "operation_id": self.operation_id,
                "operation_kind": self.operation_kind,
                "platform_identity_id": self.platform_identity_id,
                "platform_key_id": self.platform_key_id,
                "platform_release": self.platform_release,
                "policy_version": self.policy_version,
                "source_ref_hash": self.source_ref_hash,
                "source_version": self.source_version,
            }
        )


def create_operation_envelope(
    *,
    authenticated_caller: str,
    operation_id: str,
    request: OperationRequestV2,
    platform_identity: RegisteredIdentityV2,
    signature_signer: SignatureSigner,
) -> OperationEnvelopeV2:
    """Platform-only issuance: authenticated caller and operation ID are signed together."""

    if not isinstance(request, OperationRequestV2):
        _violate("invalid_operation_request")
    if (
        not isinstance(platform_identity, RegisteredIdentityV2)
        or platform_identity.role != "platform"
    ):
        _violate("invalid_platform_identity")
    unsigned = OperationEnvelopeV2(
        operation_id=operation_id,
        caller_id=authenticated_caller,
        source_ref_hash=request.source_ref_hash,
        source_version=request.source_version,
        operation_kind=request.operation_kind,
        policy_version=request.policy_version,
        idempotency_key=request.idempotency_key,
        expires_at=request.expires_at,
        platform_identity_id=platform_identity.identity_id,
        platform_release=platform_identity.release,
        platform_key_id=platform_identity.key_id,
        platform_signature="sig_0000000000000000",
    )
    try:
        signature = signature_signer(
            platform_identity.key_id, unsigned.canonical_issuance_bytes
        )
    except Exception as error:
        raise ProtocolViolation("invalid_platform_signature") from error
    _require_signature(signature, "platform_signature")
    return replace(unsigned, platform_signature=signature)


def validate_operation_envelope(
    *,
    envelope: OperationEnvelopeV2,
    registry: IdentityRegistryV2,
    signature_verifier: SignatureVerifier,
) -> OperationEnvelopeV2:
    _require_registered_identity(
        registry=registry,
        identity_id=envelope.platform_identity_id,
        release=envelope.platform_release,
        key_id=envelope.platform_key_id,
        role="platform",
    )
    _verify_signature(
        key_id=envelope.platform_key_id,
        payload=envelope.canonical_issuance_bytes,
        signature=envelope.platform_signature,
        signature_verifier=signature_verifier,
        failure_code="invalid_platform_signature",
    )
    return envelope


@dataclass(frozen=True, slots=True)
class ExecutionAttemptV2:
    operation_id: str
    attempt_id: str
    executor_id: str
    executor_release: str
    lease_expires_at: datetime
    tool_policy_hash: str
    input_ref_hash: str | None = None
    execution_grant_hash: str | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id", "op_")
        _require_identifier(self.attempt_id, "attempt_id", "att_")
        _require_agent_identity(self.executor_id, "executor_id")
        _require_identifier(self.executor_release, "executor_release", "rel_")
        _require_utc(self.lease_expires_at, "lease_expires_at")
        _require_sha256(self.tool_policy_hash, "tool_policy_hash")
        bindings = (self.input_ref_hash, self.execution_grant_hash)
        if sum(value is not None for value in bindings) != 1:
            _violate("invalid_attempt_input_binding")
        if self.input_ref_hash is not None:
            _require_sha256(self.input_ref_hash, "input_ref_hash")
        if self.execution_grant_hash is not None:
            _require_sha256(self.execution_grant_hash, "execution_grant_hash")


def validate_attempt_binding(
    *,
    envelope: OperationEnvelopeV2,
    attempt: ExecutionAttemptV2,
    registry: IdentityRegistryV2,
    signature_verifier: SignatureVerifier,
) -> ExecutionAttemptV2:
    validate_operation_envelope(
        envelope=envelope,
        registry=registry,
        signature_verifier=signature_verifier,
    )
    if attempt.operation_id != envelope.operation_id:
        _violate("attempt_operation_mismatch")
    if attempt.lease_expires_at > envelope.expires_at:
        _violate("attempt_expiry_exceeds_operation")
    _require_registered_identity(
        registry=registry,
        identity_id=attempt.executor_id,
        release=attempt.executor_release,
        key_id=registry.resolve(attempt.executor_id).key_id,
        role="executor",
    )
    return attempt


@dataclass(frozen=True, slots=True)
class ArtifactV2:
    artifact_id: str
    media_type: str
    sha256: str
    byte_size: int
    storage_ref: str

    def __post_init__(self) -> None:
        _require_identifier(self.artifact_id, "artifact_id", "art_")
        if (
            not isinstance(self.media_type, str)
            or _MEDIA_TYPE_RE.fullmatch(self.media_type) is None
        ):
            _violate("invalid_media_type")
        _require_sha256(self.sha256, "artifact_sha256")
        if (
            not isinstance(self.byte_size, int)
            or isinstance(self.byte_size, bool)
            or self.byte_size < 0
        ):
            _violate("invalid_byte_size")
        if (
            not isinstance(self.storage_ref, str)
            or _STORAGE_REF_RE.fullmatch(self.storage_ref) is None
        ):
            _violate("invalid_storage_ref")

    @property
    def canonical_data(self) -> Mapping[str, str | int]:
        return {
            "artifact_id": self.artifact_id,
            "byte_size": self.byte_size,
            "media_type": self.media_type,
            "sha256": self.sha256,
            "storage_ref": self.storage_ref,
        }


@dataclass(frozen=True, slots=True)
class ManifestV2:
    operation_id: str
    attempt_id: str
    executor_id: str
    executor_release: str
    artifacts: tuple[ArtifactV2, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id", "op_")
        _require_identifier(self.attempt_id, "attempt_id", "att_")
        _require_agent_identity(self.executor_id, "executor_id")
        _require_identifier(self.executor_release, "executor_release", "rel_")
        artifacts = tuple(self.artifacts)
        if not artifacts or not all(
            isinstance(artifact, ArtifactV2) for artifact in artifacts
        ):
            _violate("invalid_artifacts")
        canonical_artifacts = tuple(
            sorted(artifacts, key=lambda artifact: artifact.artifact_id)
        )
        if len({artifact.artifact_id for artifact in canonical_artifacts}) != len(
            canonical_artifacts
        ):
            _violate("duplicate_artifact_id")
        object.__setattr__(self, "artifacts", canonical_artifacts)

    @property
    def canonical_bytes(self) -> bytes:
        return _canonical_json_bytes(
            {
                "artifacts": [artifact.canonical_data for artifact in self.artifacts],
                "attempt_id": self.attempt_id,
                "executor_id": self.executor_id,
                "executor_release": self.executor_release,
                "operation_id": self.operation_id,
            }
        )

    @property
    def manifest_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes).hexdigest()


def validate_manifest_binding(
    *,
    attempt: ExecutionAttemptV2,
    manifest: ManifestV2,
) -> ManifestV2:
    if manifest.operation_id != attempt.operation_id:
        _violate("manifest_operation_mismatch")
    if manifest.attempt_id != attempt.attempt_id:
        _violate("manifest_attempt_mismatch")
    if manifest.executor_id != attempt.executor_id:
        _violate("manifest_executor_mismatch")
    if manifest.executor_release != attempt.executor_release:
        _violate("manifest_executor_release_mismatch")
    return manifest


@dataclass(frozen=True, slots=True)
class IndependentReceiptV2:
    operation_id: str
    attempt_id: str
    manifest_hash: str
    verifier_id: str
    verifier_release: str
    policy_version: str
    decision: str
    decision_vocabulary_version: str
    reason_codes: tuple[str, ...]
    reason_code_vocabulary_version: str
    issued_at: datetime
    key_id: str
    signature: str

    def __post_init__(self) -> None:
        _require_identifier(self.operation_id, "operation_id", "op_")
        _require_identifier(self.attempt_id, "attempt_id", "att_")
        _require_sha256(self.manifest_hash, "manifest_hash")
        _require_agent_identity(self.verifier_id, "verifier_id")
        _require_identifier(self.verifier_release, "verifier_release", "rel_")
        _require_identifier(self.policy_version, "policy_version", "pol_")
        if self.decision not in RECEIPT_DECISIONS_V1:
            _violate("invalid_receipt_decision")
        if self.decision_vocabulary_version != DECISION_VOCABULARY_VERSION:
            _violate("invalid_decision_vocabulary_version")
        if self.reason_code_vocabulary_version != REASON_CODE_VOCABULARY_VERSION:
            _violate("invalid_reason_code_vocabulary_version")
        if not isinstance(self.reason_codes, tuple) or not self.reason_codes:
            _violate("invalid_reason_codes")
        if any(code not in REASON_CODES_V1 for code in self.reason_codes):
            _violate("invalid_reason_codes")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            _violate("duplicate_reason_code")
        if (
            tuple(sorted(self.reason_codes, key=REASON_CODES_V1.index))
            != self.reason_codes
        ):
            _violate("noncanonical_reason_codes")
        _require_utc(self.issued_at, "issued_at")
        _require_identifier(self.key_id, "key_id", "key_")
        _require_signature(self.signature, "signature")

    @property
    def canonical_signing_bytes(self) -> bytes:
        return _canonical_json_bytes(
            {
                "attempt_id": self.attempt_id,
                "decision": self.decision,
                "decision_vocabulary_version": self.decision_vocabulary_version,
                "issued_at": _utc_text(self.issued_at),
                "key_id": self.key_id,
                "manifest_hash": self.manifest_hash,
                "operation_id": self.operation_id,
                "policy_version": self.policy_version,
                "reason_code_vocabulary_version": self.reason_code_vocabulary_version,
                "reason_codes": list(self.reason_codes),
                "verifier_id": self.verifier_id,
                "verifier_release": self.verifier_release,
            }
        )


def accept_operation(
    *,
    caller: str,
    envelope: OperationEnvelopeV2,
    now: datetime,
    registry: IdentityRegistryV2,
    signature_verifier: SignatureVerifier,
) -> OperationEnvelopeV2:
    _require_identifier(caller, "caller", "svc_")
    _require_utc(now, "now")
    validate_operation_envelope(
        envelope=envelope,
        registry=registry,
        signature_verifier=signature_verifier,
    )
    if caller != envelope.caller_id:
        _violate("caller_envelope_mismatch")
    if now >= envelope.expires_at:
        _violate("operation_expired")
    return envelope


def assert_idempotency_replay_matches(
    *,
    existing: OperationEnvelopeV2,
    incoming: OperationEnvelopeV2,
) -> OperationEnvelopeV2:
    if existing.caller_id != incoming.caller_id:
        _violate("idempotency_caller_mismatch")
    if existing.idempotency_key != incoming.idempotency_key:
        _violate("idempotency_key_mismatch")
    if existing.idempotency_payload_hash != incoming.idempotency_payload_hash:
        _violate("idempotency_payload_conflict")
    return existing


def validate_receipt_binding(
    *,
    envelope: OperationEnvelopeV2,
    attempt: ExecutionAttemptV2,
    manifest: ManifestV2,
    receipt: IndependentReceiptV2,
    registry: IdentityRegistryV2,
    signature_verifier: SignatureVerifier,
) -> IndependentReceiptV2:
    validate_attempt_binding(
        envelope=envelope,
        attempt=attempt,
        registry=registry,
        signature_verifier=signature_verifier,
    )
    validate_manifest_binding(attempt=attempt, manifest=manifest)
    if receipt.operation_id != envelope.operation_id:
        _violate("receipt_operation_mismatch")
    if receipt.attempt_id != manifest.attempt_id:
        _violate("receipt_attempt_mismatch")
    if receipt.policy_version != envelope.policy_version:
        _violate("receipt_policy_mismatch")
    if receipt.manifest_hash != manifest.manifest_hash:
        _violate("receipt_manifest_mismatch")
    executor = registry.resolve(attempt.executor_id)
    verifier = _require_registered_identity(
        registry=registry,
        identity_id=receipt.verifier_id,
        release=receipt.verifier_release,
        key_id=receipt.key_id,
        role="verifier",
    )
    if verifier.principal_id == executor.principal_id:
        _violate("executor_verifier_conflict")
    _verify_signature(
        key_id=receipt.key_id,
        payload=receipt.canonical_signing_bytes,
        signature=receipt.signature,
        signature_verifier=signature_verifier,
        failure_code="invalid_receipt_signature",
    )
    return receipt

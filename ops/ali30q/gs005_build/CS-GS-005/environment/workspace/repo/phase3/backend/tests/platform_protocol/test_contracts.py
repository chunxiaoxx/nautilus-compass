from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from platform_protocol.contracts import (
    ArtifactV2,
    ExecutionAttemptV2,
    IdentityRegistryV2,
    IndependentReceiptV2,
    ManifestV2,
    OperationRequestV2,
    ProtocolViolation,
    RegisteredIdentityV2,
    accept_operation,
    assert_idempotency_replay_matches,
    create_operation_envelope,
    validate_attempt_binding,
    validate_receipt_binding,
)

NOW = datetime(2026, 8, 3, 18, 0, tzinfo=timezone.utc)


def signature_for(key_id: str, payload: bytes) -> str:
    return "sig_" + hashlib.sha256(key_id.encode("ascii") + payload).hexdigest()


def signature_is_valid(key_id: str, payload: bytes, signature: str) -> bool:
    return signature == signature_for(key_id, payload)


def registry(*, same_principal: bool = False) -> IdentityRegistryV2:
    verifier_principal = "prn_executor_01" if same_principal else "prn_verifier_01"
    return IdentityRegistryV2(
        identities=(
            RegisteredIdentityV2(
                identity_id="plt_platform_01",
                principal_id="prn_platform_01",
                release="rel_platform_01",
                key_id="key_platform_01",
                role="platform",
            ),
            RegisteredIdentityV2(
                identity_id="exec_worker_01",
                principal_id="prn_executor_01",
                release="rel_worker_01",
                key_id="key_worker_01",
                role="executor",
            ),
            RegisteredIdentityV2(
                identity_id="ver_auditor_01",
                principal_id=verifier_principal,
                release="rel_verifier_01",
                key_id="key_verifier_01",
                role="verifier",
            ),
        )
    )


def operation_request(
    *, key: str = "idem_retry_01", policy: str = "pol_v1"
) -> OperationRequestV2:
    return OperationRequestV2(
        source_ref_hash="a" * 64,
        source_version="srcv_readback_01",
        operation_kind="bounded_execution",
        policy_version=policy,
        idempotency_key=key,
        expires_at=NOW + timedelta(minutes=5),
    )


def operation(*, key: str = "idem_retry_01", policy: str = "pol_v1"):
    trusted_registry = registry()
    return create_operation_envelope(
        authenticated_caller="svc_source_01",
        operation_id="op_alpha_01",
        request=operation_request(key=key, policy=policy),
        platform_identity=trusted_registry.identities[0],
        signature_signer=signature_for,
    )


def attempt() -> ExecutionAttemptV2:
    return ExecutionAttemptV2(
        operation_id="op_alpha_01",
        attempt_id="att_executor_01",
        executor_id="exec_worker_01",
        executor_release="rel_worker_01",
        lease_expires_at=NOW + timedelta(minutes=3),
        tool_policy_hash="b" * 64,
        input_ref_hash="c" * 64,
    )


def manifest() -> ManifestV2:
    return ManifestV2(
        operation_id="op_alpha_01",
        attempt_id="att_executor_01",
        executor_id="exec_worker_01",
        executor_release="rel_worker_01",
        artifacts=(
            ArtifactV2(
                artifact_id="art_blob_b1",
                media_type="application/json",
                sha256="b" * 64,
                byte_size=21,
                storage_ref="vault://artifact/artifact_b1",
            ),
            ArtifactV2(
                artifact_id="art_blob_a1",
                media_type="text/plain",
                sha256="a" * 64,
                byte_size=8,
                storage_ref="vault://artifact/artifact_a1",
            ),
        ),
    )


def receipt(
    *, manifest_hash: str, verifier_id: str = "ver_auditor_01"
) -> IndependentReceiptV2:
    unsigned = IndependentReceiptV2(
        operation_id="op_alpha_01",
        attempt_id="att_executor_01",
        manifest_hash=manifest_hash,
        verifier_id=verifier_id,
        verifier_release="rel_verifier_01",
        policy_version="pol_v1",
        decision="accepted",
        decision_vocabulary_version="protocol-v2-decisions-v1",
        reason_codes=("policy_satisfied",),
        reason_code_vocabulary_version="protocol-v2-reason-codes-v1",
        issued_at=NOW,
        key_id="key_verifier_01",
        signature="sig_0123456789abcdef",
    )
    return IndependentReceiptV2(
        operation_id=unsigned.operation_id,
        attempt_id=unsigned.attempt_id,
        manifest_hash=unsigned.manifest_hash,
        verifier_id=unsigned.verifier_id,
        verifier_release=unsigned.verifier_release,
        policy_version=unsigned.policy_version,
        decision=unsigned.decision,
        decision_vocabulary_version=unsigned.decision_vocabulary_version,
        reason_codes=unsigned.reason_codes,
        reason_code_vocabulary_version=unsigned.reason_code_vocabulary_version,
        issued_at=unsigned.issued_at,
        key_id=unsigned.key_id,
        signature=signature_for(unsigned.key_id, unsigned.canonical_signing_bytes),
    )


def test_valid_operation_envelope_is_accepted_before_expiry() -> None:
    envelope = operation()

    accepted = accept_operation(
        caller="svc_source_01",
        envelope=envelope,
        now=NOW,
        registry=registry(),
        signature_verifier=signature_is_valid,
    )

    assert accepted == envelope


def test_manifest_hash_is_canonical_for_same_artifacts_in_different_input_order() -> (
    None
):
    first = manifest()
    second = ManifestV2(
        operation_id=first.operation_id,
        attempt_id=first.attempt_id,
        executor_id=first.executor_id,
        executor_release=first.executor_release,
        artifacts=tuple(reversed(first.artifacts)),
    )

    assert first.manifest_hash == second.manifest_hash
    assert first.manifest_hash == hashlib.sha256(first.canonical_bytes).hexdigest()
    assert [artifact.artifact_id for artifact in first.artifacts] == [
        "art_blob_a1",
        "art_blob_b1",
    ]


def test_changed_payload_reusing_idempotency_key_is_rejected() -> None:
    first = operation()
    changed = operation(policy="pol_v2")

    with pytest.raises(ProtocolViolation, match="idempotency_payload_conflict"):
        assert_idempotency_replay_matches(existing=first, incoming=changed)


def test_expired_operation_is_rejected() -> None:
    trusted_registry = registry()
    expired = create_operation_envelope(
        authenticated_caller="svc_source_01",
        operation_id="op_expired_01",
        request=OperationRequestV2(
            source_ref_hash="a" * 64,
            source_version="srcv_readback_01",
            operation_kind="bounded_execution",
            policy_version="pol_v1",
            idempotency_key="idem_expired_01",
            expires_at=NOW,
        ),
        platform_identity=trusted_registry.identities[0],
        signature_signer=signature_for,
    )

    with pytest.raises(ProtocolViolation, match="operation_expired"):
        accept_operation(
            caller="svc_source_01",
            envelope=expired,
            now=NOW,
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )


def test_executor_cannot_also_be_receipt_verifier() -> None:
    envelope = operation()
    execution_attempt = attempt()
    submitted_manifest = manifest()
    trusted_registry = registry(same_principal=True)
    validate_attempt_binding(
        envelope=envelope,
        attempt=execution_attempt,
        registry=trusted_registry,
        signature_verifier=signature_is_valid,
    )

    with pytest.raises(ProtocolViolation, match="executor_verifier_conflict"):
        validate_receipt_binding(
            envelope=envelope,
            manifest=submitted_manifest,
            receipt=receipt(manifest_hash=submitted_manifest.manifest_hash),
            attempt=execution_attempt,
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )


def test_receipt_manifest_binding_mismatch_is_rejected() -> None:
    envelope = operation()
    execution_attempt = attempt()
    submitted_manifest = manifest()
    trusted_registry = registry()

    with pytest.raises(ProtocolViolation, match="receipt_manifest_mismatch"):
        validate_receipt_binding(
            envelope=envelope,
            manifest=submitted_manifest,
            receipt=receipt(manifest_hash="c" * 64),
            attempt=execution_attempt,
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )

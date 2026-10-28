from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from platform_protocol.contracts import (
    ArtifactV2,
    ExecutionAttemptV2,
    IdentityRegistryV2,
    IndependentReceiptV2,
    ManifestV2,
    OperationEnvelopeV2,
    OperationRequestV2,
    ProtocolViolation,
    RegisteredIdentityV2,
    assert_idempotency_replay_matches,
    create_operation_envelope,
    validate_attempt_binding,
    validate_manifest_binding,
    validate_operation_envelope,
    validate_receipt_binding,
)

NOW = datetime(2026, 8, 4, 18, 0, tzinfo=timezone.utc)
VECTOR_PATH = (
    Path(__file__).parents[2] / "platform_protocol" / "conformance_vectors_v2.json"
)
VECTOR_HASH_PATH = VECTOR_PATH.with_suffix(".sha256")


def request(*, key: str = "idem_retry_01") -> OperationRequestV2:
    return OperationRequestV2(
        source_ref_hash="a" * 64,
        source_version="srcv_readback_01",
        operation_kind="bounded_execution",
        policy_version="pol_v1",
        idempotency_key=key,
        expires_at=NOW + timedelta(minutes=5),
    )


def envelope():
    trusted_registry = registry()
    return create_operation_envelope(
        authenticated_caller="svc_source_01",
        operation_id="op_alpha_01",
        request=request(),
        platform_identity=trusted_registry.identities[0],
        signature_signer=signature_for,
    )


def attempt(**overrides: object) -> ExecutionAttemptV2:
    values: dict[str, object] = {
        "operation_id": "op_alpha_01",
        "attempt_id": "att_executor_01",
        "executor_id": "exec_worker_01",
        "executor_release": "rel_worker_01",
        "lease_expires_at": NOW + timedelta(minutes=3),
        "tool_policy_hash": "b" * 64,
        "input_ref_hash": "c" * 64,
        "execution_grant_hash": None,
    }
    values.update(overrides)
    return ExecutionAttemptV2(**values)


def artifact(**overrides: object) -> ArtifactV2:
    values: dict[str, object] = {
        "artifact_id": "art_blob_a1",
        "media_type": "application/json",
        "sha256": "d" * 64,
        "byte_size": 12,
        "storage_ref": "vault://artifact/artifact_a1",
    }
    values.update(overrides)
    return ArtifactV2(**values)


def manifest(**overrides: object) -> ManifestV2:
    values: dict[str, object] = {
        "operation_id": "op_alpha_01",
        "attempt_id": "att_executor_01",
        "executor_id": "exec_worker_01",
        "executor_release": "rel_worker_01",
        "artifacts": (artifact(),),
    }
    values.update(overrides)
    return ManifestV2(**values)


def receipt(**overrides: object) -> IndependentReceiptV2:
    values: dict[str, object] = {
        "operation_id": "op_alpha_01",
        "attempt_id": "att_executor_01",
        "manifest_hash": manifest().manifest_hash,
        "verifier_id": "ver_auditor_01",
        "verifier_release": "rel_verifier_01",
        "policy_version": "pol_v1",
        "decision": "accepted",
        "decision_vocabulary_version": "protocol-v2-decisions-v1",
        "reason_codes": ("policy_satisfied",),
        "reason_code_vocabulary_version": "protocol-v2-reason-codes-v1",
        "issued_at": NOW,
        "key_id": "key_verifier_01",
        "signature": "sig_0123456789abcdef",
    }
    values.update(overrides)
    return IndependentReceiptV2(**values)


def signature_for(key_id: str, payload: bytes) -> str:
    return "sig_" + hashlib.sha256(key_id.encode("ascii") + payload).hexdigest()


def signature_is_valid(key_id: str, payload: bytes, signature: str) -> bool:
    return signature == signature_for(key_id, payload)


def registry(
    *,
    same_principal: bool = False,
    shared_executor_verifier_key: bool = False,
) -> IdentityRegistryV2:
    verifier_principal = "prn_executor_01" if same_principal else "prn_verifier_01"
    verifier_key = (
        "key_worker_01" if shared_executor_verifier_key else "key_verifier_01"
    )
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
                key_id=verifier_key,
                role="verifier",
            ),
        )
    )


def test_request_cannot_supply_platform_operation_or_authenticated_caller() -> None:
    operation = envelope()

    assert operation.operation_id == "op_alpha_01"
    assert operation.caller_id == "svc_source_01"
    with pytest.raises(TypeError):
        OperationRequestV2(
            source_ref_hash="a" * 64,
            source_version="srcv_readback_01",
            operation_kind="bounded_execution",
            policy_version="pol_v1",
            idempotency_key="idem_retry_01",
            expires_at=NOW + timedelta(minutes=5),
            operation_id="op_untrusted_01",
        )


def test_attempt_requires_one_opaque_input_binding_and_a_bounded_lease() -> None:
    valid = attempt()
    trusted_registry = registry()

    assert (
        validate_attempt_binding(
            envelope=envelope(),
            attempt=valid,
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )
        == valid
    )
    with pytest.raises(ProtocolViolation, match="invalid_attempt_input_binding"):
        attempt(input_ref_hash=None, execution_grant_hash=None)
    with pytest.raises(ProtocolViolation, match="invalid_attempt_input_binding"):
        attempt(execution_grant_hash="e" * 64)
    with pytest.raises(ProtocolViolation, match="attempt_expiry_exceeds_operation"):
        validate_attempt_binding(
            envelope=envelope(),
            attempt=attempt(lease_expires_at=NOW + timedelta(minutes=6)),
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )


def test_manifest_binds_executor_release_and_rejects_duplicate_or_raw_refs() -> None:
    submitted = manifest()

    assert validate_manifest_binding(attempt=attempt(), manifest=submitted) == submitted
    with pytest.raises(ProtocolViolation, match="manifest_executor_release_mismatch"):
        validate_manifest_binding(
            attempt=attempt(),
            manifest=manifest(executor_release="rel_worker_02"),
        )
    with pytest.raises(ProtocolViolation, match="duplicate_artifact_id"):
        manifest(artifacts=(artifact(), artifact()))
    with pytest.raises(ProtocolViolation, match="invalid_storage_ref"):
        artifact(storage_ref="file:///private/raw-evidence.txt")


def test_receipt_signing_bytes_exclude_signature_and_bind_an_independent_verifier() -> (
    None
):
    submitted = manifest()
    unsigned = receipt(manifest_hash=submitted.manifest_hash)
    signed = replace(
        unsigned,
        signature=signature_for(unsigned.key_id, unsigned.canonical_signing_bytes),
    )
    trusted_registry = registry()
    expected_payload = {
        "attempt_id": "att_executor_01",
        "decision": "accepted",
        "decision_vocabulary_version": "protocol-v2-decisions-v1",
        "issued_at": "2026-08-04T18:00:00.000000Z",
        "key_id": "key_verifier_01",
        "manifest_hash": submitted.manifest_hash,
        "operation_id": "op_alpha_01",
        "policy_version": "pol_v1",
        "reason_code_vocabulary_version": "protocol-v2-reason-codes-v1",
        "reason_codes": ["policy_satisfied"],
        "verifier_id": "ver_auditor_01",
        "verifier_release": "rel_verifier_01",
    }
    expected_bytes = json.dumps(
        expected_payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    assert b"sig_0123456789abcdef" not in signed.canonical_signing_bytes
    assert signed.canonical_signing_bytes == expected_bytes
    assert hashlib.sha256(signed.canonical_signing_bytes).hexdigest() == (
        "7340a94b3e3104a6bb1a6658d5461308dadba2061285a0bb983ad47fde8a675d"
    )
    assert (
        validate_receipt_binding(
            envelope=envelope(),
            attempt=attempt(),
            manifest=submitted,
            receipt=signed,
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )
        == signed
    )
    with pytest.raises(ProtocolViolation, match="executor_verifier_conflict"):
        validate_receipt_binding(
            envelope=envelope(),
            attempt=attempt(),
            manifest=submitted,
            receipt=signed,
            registry=registry(same_principal=True),
            signature_verifier=signature_is_valid,
        )


def test_receipt_rejects_mis_split_or_unknown_versioned_reason_codes() -> None:
    with pytest.raises(ProtocolViolation, match="invalid_reason_codes"):
        receipt(reason_codes="policy_satisfied")
    with pytest.raises(ProtocolViolation, match="invalid_reason_codes"):
        receipt(reason_codes=("invented_story",))
    with pytest.raises(
        ProtocolViolation, match="invalid_reason_code_vocabulary_version"
    ):
        receipt(reason_code_vocabulary_version="protocol-v2-reason-codes-v0")
    with pytest.raises(ProtocolViolation, match="invalid_receipt_decision"):
        receipt(decision="approved")
    with pytest.raises(ProtocolViolation, match="invalid_decision_vocabulary_version"):
        receipt(decision_vocabulary_version="protocol-v2-decisions-v0")
    with pytest.raises(ProtocolViolation, match="duplicate_reason_code"):
        receipt(reason_codes=("policy_satisfied", "policy_satisfied"))
    with pytest.raises(ProtocolViolation, match="noncanonical_reason_codes"):
        receipt(reason_codes=("policy_satisfied", "policy_denied"))


def test_idempotency_returns_original_operation_for_same_authenticated_caller() -> None:
    original = envelope()
    trusted_registry = registry()
    replay = create_operation_envelope(
        authenticated_caller="svc_source_01",
        operation_id="op_retry_01",
        request=request(),
        platform_identity=trusted_registry.identities[0],
        signature_signer=signature_for,
    )

    from platform_protocol.contracts import assert_idempotency_replay_matches

    assert (
        assert_idempotency_replay_matches(existing=original, incoming=replay)
        == original
    )


def test_conformance_vectors_are_canonical_and_have_a_published_hash() -> None:
    document = json.loads(VECTOR_PATH.read_bytes())
    expected_bytes = (
        json.dumps(
            document,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )

    assert VECTOR_PATH.read_bytes() == expected_bytes
    assert VECTOR_HASH_PATH.read_text(encoding="ascii") == (
        f"sha256:{hashlib.sha256(expected_bytes).hexdigest()}\n"
    )
    assert document["vector_set_version"] == "protocol-v2-conformance-v1"
    assert document["protocol_contract_version"] == "protocol-v2-contracts-v1"
    assert document["decision_vocabulary_version"] == "protocol-v2-decisions-v1"
    assert document["reason_code_vocabulary_version"] == "protocol-v2-reason-codes-v1"
    assert [vector["id"] for vector in document["vectors"]] == [
        "valid_chain",
        "changed_replay",
        "non_independent_verifier",
        "shared_executor_verifier_key",
    ]


def _vector_registry(vector: dict[str, object]) -> IdentityRegistryV2:
    return IdentityRegistryV2(
        identities=tuple(
            RegisteredIdentityV2(**item) for item in vector["registrations"]
        )
    )


def _vector_operation(data: dict[str, object]) -> OperationEnvelopeV2:
    return OperationEnvelopeV2(
        **{
            **data,
            "expires_at": datetime.fromisoformat(
                data["expires_at"].replace("Z", "+00:00")
            ),
        }
    )


def _vector_request(data: dict[str, object]) -> OperationRequestV2:
    return OperationRequestV2(
        **{
            **data,
            "expires_at": datetime.fromisoformat(
                data["expires_at"].replace("Z", "+00:00")
            ),
        }
    )


def _vector_chain(
    vector: dict[str, object],
) -> tuple[
    IdentityRegistryV2,
    OperationEnvelopeV2,
    ExecutionAttemptV2,
    ManifestV2,
    IndependentReceiptV2,
]:
    attempt_data = vector["attempt"]
    manifest_data = vector["manifest"]
    receipt_data = vector["receipt"]
    return (
        _vector_registry(vector),
        _vector_operation(vector["operation"]),
        ExecutionAttemptV2(
            **{
                **attempt_data,
                "lease_expires_at": datetime.fromisoformat(
                    attempt_data["lease_expires_at"].replace("Z", "+00:00")
                ),
            }
        ),
        ManifestV2(
            **{
                **manifest_data,
                "artifacts": tuple(
                    ArtifactV2(**item) for item in manifest_data["artifacts"]
                ),
            }
        ),
        IndependentReceiptV2(
            **{
                **receipt_data,
                "issued_at": datetime.fromisoformat(
                    receipt_data["issued_at"].replace("Z", "+00:00")
                ),
                "reason_codes": tuple(receipt_data["reason_codes"]),
            }
        ),
    )


def test_conformance_vectors_replay_positive_and_negative_contracts() -> None:
    vector_set = json.loads(VECTOR_PATH.read_bytes())
    valid, changed_replay, non_independent_verifier, shared_executor_verifier_key = (
        vector_set["vectors"]
    )
    trusted_registry, operation, execution_attempt, submitted_manifest, signed = (
        _vector_chain(valid)
    )

    assert (
        create_operation_envelope(
            authenticated_caller=operation.caller_id,
            operation_id=operation.operation_id,
            request=_vector_request(valid["request"]),
            platform_identity=trusted_registry.identities[0],
            signature_signer=signature_for,
        )
        == operation
    )
    assert submitted_manifest.manifest_hash == valid["expected"]["manifest_hash"]
    assert (
        hashlib.sha256(signed.canonical_signing_bytes).hexdigest()
        == valid["expected"]["receipt_signing_sha256"]
    )
    assert (
        validate_receipt_binding(
            envelope=operation,
            attempt=execution_attempt,
            manifest=submitted_manifest,
            receipt=signed,
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )
        == signed
    )

    replay_registry = _vector_registry(changed_replay)
    original = _vector_operation(changed_replay["original"]["operation"])
    incoming = _vector_operation(changed_replay["incoming"]["operation"])
    assert (
        validate_operation_envelope(
            envelope=original,
            registry=replay_registry,
            signature_verifier=signature_is_valid,
        )
        == original
    )
    assert (
        validate_operation_envelope(
            envelope=incoming,
            registry=replay_registry,
            signature_verifier=signature_is_valid,
        )
        == incoming
    )
    with pytest.raises(
        ProtocolViolation, match=changed_replay["expected"]["violation"]
    ):
        assert_idempotency_replay_matches(existing=original, incoming=incoming)

    (
        non_independent_registry,
        operation,
        execution_attempt,
        submitted_manifest,
        signed,
    ) = _vector_chain(non_independent_verifier)
    with pytest.raises(
        ProtocolViolation,
        match=non_independent_verifier["expected"]["violation"],
    ):
        validate_receipt_binding(
            envelope=operation,
            attempt=execution_attempt,
            manifest=submitted_manifest,
            receipt=signed,
            registry=non_independent_registry,
            signature_verifier=signature_is_valid,
        )

    with pytest.raises(
        ProtocolViolation,
        match=shared_executor_verifier_key["expected"]["violation"],
    ):
        _vector_registry(shared_executor_verifier_key)


def test_platform_signature_and_registered_independent_principals_are_required() -> (
    None
):
    trusted_registry = registry()
    issued = create_operation_envelope(
        authenticated_caller="svc_source_01",
        operation_id="op_alpha_01",
        request=request(),
        platform_identity=trusted_registry.identities[0],
        signature_signer=signature_for,
    )
    signed = receipt(manifest_hash=manifest().manifest_hash)
    signed = replace(
        signed, signature=signature_for(signed.key_id, signed.canonical_signing_bytes)
    )

    assert (
        validate_operation_envelope(
            envelope=issued,
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )
        == issued
    )
    assert (
        validate_attempt_binding(
            envelope=issued,
            attempt=attempt(),
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )
        == attempt()
    )
    with pytest.raises(ProtocolViolation, match="executor_release_mismatch"):
        validate_attempt_binding(
            envelope=issued,
            attempt=attempt(executor_release="rel_worker_02"),
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )
    assert (
        validate_receipt_binding(
            envelope=issued,
            attempt=attempt(),
            manifest=manifest(),
            receipt=signed,
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )
        == signed
    )

    with pytest.raises(ProtocolViolation, match="invalid_platform_signature"):
        validate_operation_envelope(
            envelope=replace(issued, caller_id="svc_forged_01"),
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )
    with pytest.raises(ProtocolViolation, match="executor_verifier_conflict"):
        validate_receipt_binding(
            envelope=issued,
            attempt=attempt(),
            manifest=manifest(),
            receipt=signed,
            registry=registry(same_principal=True),
            signature_verifier=signature_is_valid,
        )
    with pytest.raises(ProtocolViolation, match="invalid_receipt_signature"):
        validate_receipt_binding(
            envelope=issued,
            attempt=attempt(),
            manifest=manifest(),
            receipt=replace(signed, signature="sig_0123456789abcdef"),
            registry=trusted_registry,
            signature_verifier=signature_is_valid,
        )
    with pytest.raises(ProtocolViolation, match="duplicate_registered_key"):
        registry(shared_executor_verifier_key=True)

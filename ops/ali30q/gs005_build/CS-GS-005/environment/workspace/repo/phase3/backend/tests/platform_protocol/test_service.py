from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from threading import Barrier
from typing import Callable

import pytest
import sqlalchemy as sa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

import platform_protocol.service as service_module
from platform_protocol.contracts import (
    ArtifactV2,
    ExecutionAttemptV2,
    IndependentReceiptV2,
    ManifestV2,
    OperationEnvelopeV2,
    OperationRequestV2,
    ProtocolViolation,
    RegisteredIdentityV2,
    create_operation_envelope,
)
from platform_protocol.keys import encode_ed25519_public_key, encode_ed25519_signature
from platform_protocol.m1_r1a_admission import AdmissionViolation
from platform_protocol.m1_r1a_ephemeral_key_admission import (
    ANNOUNCEMENT_VERSION,
    create_platform_announce_challenge,
)
from platform_protocol.m1_r1a_execution_evidence import (
    EVIDENCE_CONTRACT_VERSION,
    ExecutorExecutionEvidenceV1,
)
from platform_protocol.m1_r1a_routing import (
    R1A_CAPABILITY,
    R1A_EXECUTOR_ID,
    R1A_EXECUTOR_KEY_ID,
    R1A_EXECUTOR_RELEASE,
    R1A_POLICY_VERSION,
    R1A_TOOL_POLICY_HASH,
    R1aExecutorCandidateV1,
    R1aExecutorSelectionV1,
)
from platform_protocol.m1_r1a_runtime_admission import R1aRuntimeAdmissionDecision
from platform_protocol.migrations import (
    downgrade_platform_database,
    upgrade_platform_database,
)
from platform_protocol.models import (
    ProtocolAttempt,
    ProtocolAuditEvent,
    ProtocolExecutorEvidence,
    ProtocolIdentity,
    ProtocolIdentityKey,
    ProtocolManifest,
    ProtocolOperation,
    ProtocolOutbox,
    ProtocolReceipt,
)
from platform_protocol.registry import (
    CALLER_CREDENTIAL_AUDIENCE_V2,
    CALLER_CREDENTIAL_VERSION_V2,
    CallerCredentialV2,
)
from platform_protocol.repository import ProtocolRepository
from platform_protocol.service import ProtocolService

NOW = datetime(2026, 8, 4, 16, 0, tzinfo=timezone.utc)
R1A_PRODUCED_AT = NOW + timedelta(seconds=30)
R1A_OPERATION_ID = "op_r1a_synthetic_01"
R1A_INPUT_REF_HASH = "2e4fb6379b2defc90671f993b6264f395e64548101a4e3dba13ba846bbff150d"
R1A_CAPSULE_HASH = "1387d4d12edddbe2a8b83e54160ac864760d33d8b9372010976df1279a5f53d0"
R1A_FIXTURE_HASH = "340c7baf9e908ec8349bee450e87671b963f38d52440e743d88e717948724318"
R1A_ARTIFACT_HASH = "ca32fce8c78684df61d5fdf4e8a101615181ab39978d3c29683b37492c2ef21e"


@pytest.fixture(scope="session")
def database_url() -> str:
    configured = os.environ.get("NAUTILUS_PLATFORM_DATABASE_URL")
    if configured is None:
        pytest.skip("requires an explicit disposable NAUTILUS_PLATFORM_DATABASE_URL")
    return configured


@pytest.fixture(scope="session", autouse=True)
def migrated_database(database_url: str) -> None:
    upgrade_platform_database()
    yield
    downgrade_platform_database()


@pytest.fixture
def session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(database_url)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        engine.dispose()


@pytest.fixture
def session(session_factory: sessionmaker[Session]) -> Session:
    with session_factory() as current:
        _truncate(current)
        yield current
        _truncate(current)


@pytest.fixture
def private_keys(session: Session) -> dict[str, Ed25519PrivateKey]:
    keys = {
        "key_caller_01": Ed25519PrivateKey.generate(),
        "key_platform_01": Ed25519PrivateKey.generate(),
        "key_executor_01": Ed25519PrivateKey.generate(),
        "key_verifier_01": Ed25519PrivateKey.generate(),
        R1A_EXECUTOR_KEY_ID: Ed25519PrivateKey.generate(),
    }
    registrations = (
        ("svc_source_01", "prn_caller_01", "caller", "rel_caller_01", "key_caller_01"),
        (
            "plt_platform_01",
            "prn_platform_01",
            "platform",
            "rel_platform_01",
            "key_platform_01",
        ),
        (
            "exec_executor_01",
            "prn_executor_01",
            "executor",
            "rel_executor_01",
            "key_executor_01",
        ),
        (
            "ver_verifier_01",
            "prn_verifier_01",
            "verifier",
            "rel_verifier_01",
            "key_verifier_01",
        ),
    )
    for identity_id, principal_id, role, release, key_id in registrations:
        session.add(
            ProtocolIdentity(
                identity_id=identity_id,
                principal_id=principal_id,
                role=role,
                release=release,
                registered_at=NOW,
            )
        )
        session.add(
            ProtocolIdentityKey(
                key_id=key_id,
                identity_id=identity_id,
                algorithm="ed25519-v1",
                public_key_material=encode_ed25519_public_key(
                    keys[key_id].public_key()
                ),
                status="active",
                registered_at=NOW,
                revoked_at=None,
            )
        )
    session.commit()
    return keys


@pytest.fixture
def service(
    monkeypatch: pytest.MonkeyPatch,
    session_factory: sessionmaker[Session],
    private_keys: dict[str, Ed25519PrivateKey],
) -> ProtocolService:
    monkeypatch.setattr(
        service_module,
        "evaluate_r1a_runtime_admission_bytes",
        lambda _data, *, source_readback: R1aRuntimeAdmissionDecision(
            status="admitted_for_local_r1a_synthetic_repair", reason_codes=()
        ),
    )
    challenge = create_platform_announce_challenge(
        session_nonce="nonce_" + "ab" * 32,
        issued_at=NOW,
        expires_at=NOW + timedelta(seconds=120),
        now=NOW,
    )
    current = ProtocolService(
        session_factory=session_factory,
        r1a_admission_bytes=b"test-only-source-bound-admission",
        r1a_source_readback=_R1aSourceReadbackStub(),
        r1a_executor_candidates=(_r1a_candidate(),),
        r1a_ephemeral_challenge=challenge,
        r1a_ephemeral_announcement_bytes=_ephemeral_announcement_bytes(
            challenge, private_keys[R1A_EXECUTOR_KEY_ID]
        ),
    )
    current.register_r1a_ephemeral_executor_key(now=NOW)
    return current


@pytest.fixture
def operation(
    private_keys: dict[str, Ed25519PrivateKey],
) -> Callable[..., OperationEnvelopeV2]:
    def build(
        *,
        operation_id: str = "op_operation_01",
        source_ref_hash: str = "a" * 64,
        idempotency_key: str = "idem_operation_01",
        expires_at: datetime = NOW + timedelta(minutes=30),
        policy_version: str = "pol_policy_01",
    ):
        return create_operation_envelope(
            authenticated_caller="svc_source_01",
            operation_id=operation_id,
            request=OperationRequestV2(
                source_ref_hash=source_ref_hash,
                source_version="srcv_source_01",
                operation_kind="bounded_execution",
                policy_version=policy_version,
                idempotency_key=idempotency_key,
                expires_at=expires_at,
            ),
            platform_identity=RegisteredIdentityV2(
                identity_id="plt_platform_01",
                principal_id="prn_platform_01",
                release="rel_platform_01",
                key_id="key_platform_01",
                role="platform",
            ),
            signature_signer=lambda _key_id, payload: encode_ed25519_signature(
                private_keys["key_platform_01"].sign(payload)
            ),
        )

    return build


@pytest.fixture
def attempt() -> ExecutionAttemptV2:
    return ExecutionAttemptV2(
        operation_id="op_operation_01",
        attempt_id="att_attempt_01",
        executor_id="exec_executor_01",
        executor_release="rel_executor_01",
        lease_expires_at=NOW + timedelta(minutes=10),
        tool_policy_hash="b" * 64,
        input_ref_hash="c" * 64,
    )


@pytest.fixture
def manifest() -> ManifestV2:
    return ManifestV2(
        operation_id="op_operation_01",
        attempt_id="att_attempt_01",
        executor_id="exec_executor_01",
        executor_release="rel_executor_01",
        artifacts=(
            ArtifactV2(
                artifact_id="art_item_01",
                media_type="application/json",
                sha256="d" * 64,
                byte_size=17,
                storage_ref="vault://artifact/item_01",
            ),
        ),
    )


@pytest.fixture
def receipt(
    manifest: ManifestV2, private_keys: dict[str, Ed25519PrivateKey]
) -> IndependentReceiptV2:
    unsigned = IndependentReceiptV2(
        operation_id="op_operation_01",
        attempt_id="att_attempt_01",
        manifest_hash=manifest.manifest_hash,
        verifier_id="ver_verifier_01",
        verifier_release="rel_verifier_01",
        policy_version="pol_policy_01",
        decision="accepted",
        decision_vocabulary_version="protocol-v2-decisions-v1",
        reason_codes=("policy_satisfied",),
        reason_code_vocabulary_version="protocol-v2-reason-codes-v1",
        issued_at=NOW + timedelta(minutes=1),
        key_id="key_verifier_01",
        signature="sig_0000000000000000",
    )
    return _signed_receipt(private_keys, unsigned)


@pytest.fixture
def caller_credential(
    private_keys: dict[str, Ed25519PrivateKey],
) -> Callable[..., CallerCredentialV2]:
    def build(
        request: OperationEnvelopeV2 | OperationRequestV2, **changes: object
    ) -> CallerCredentialV2:
        unsigned = CallerCredentialV2(
            credential_version=CALLER_CREDENTIAL_VERSION_V2,
            audience=CALLER_CREDENTIAL_AUDIENCE_V2,
            caller_id="svc_source_01",
            caller_release="rel_caller_01",
            key_id="key_caller_01",
            request_hash=request.canonical_request_hash,
            issued_at=NOW - timedelta(minutes=1),
            expires_at=NOW + timedelta(minutes=5),
            signature="sig_0000000000000000",
        )
        unsigned = replace(unsigned, **changes)
        return replace(
            unsigned,
            signature=encode_ed25519_signature(
                private_keys["key_caller_01"].sign(unsigned.canonical_signing_bytes)
            ),
        )

    return build


def lifecycle_counts(session: Session) -> dict[str, int]:
    models = {
        "operations": ProtocolOperation,
        "attempts": ProtocolAttempt,
        "manifests": ProtocolManifest,
        "receipts": ProtocolReceipt,
        "audit": ProtocolAuditEvent,
        "outbox": ProtocolOutbox,
    }
    return {
        name: session.scalar(select(sa.func.count()).select_from(model)) or 0
        for name, model in models.items()
    }


def advance_to_manifest(
    service: ProtocolService,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
    attempt: ExecutionAttemptV2,
    manifest: ManifestV2,
) -> None:
    envelope = operation()
    service.accept_operation(
        caller_credential=caller_credential(envelope),
        envelope=envelope,
        now=NOW,
    )
    service.record_attempt(attempt=attempt, now=NOW)
    service.record_manifest(manifest=manifest, now=NOW)


def _accept_operation(
    service: ProtocolService,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
    **operation_changes: object,
) -> OperationEnvelopeV2:
    envelope = operation(**operation_changes)
    return service.accept_operation(
        caller_credential=caller_credential(envelope),
        envelope=envelope,
        now=NOW,
    )


def _signed_receipt(
    private_keys: dict[str, Ed25519PrivateKey], receipt: IndependentReceiptV2
) -> IndependentReceiptV2:
    return replace(
        receipt,
        signature=encode_ed25519_signature(
            private_keys[receipt.key_id].sign(receipt.canonical_signing_bytes)
        ),
    )


def _r1a_attempt() -> ExecutionAttemptV2:
    return ExecutionAttemptV2(
        operation_id=R1A_OPERATION_ID,
        attempt_id="att_r1a_synthetic_01",
        executor_id=R1A_EXECUTOR_ID,
        executor_release=R1A_EXECUTOR_RELEASE,
        lease_expires_at=NOW + timedelta(seconds=90),
        tool_policy_hash=R1A_TOOL_POLICY_HASH,
        input_ref_hash=R1A_INPUT_REF_HASH,
    )


class _R1aSourceReadbackStub:
    """Test trust-boundary object; the evaluator is replaced by the fixture."""


def _ephemeral_announcement_bytes(challenge, private_key: Ed25519PrivateKey) -> bytes:
    document = {
        "executor_id": R1A_EXECUTOR_ID,
        "executor_key_id": R1A_EXECUTOR_KEY_ID,
        "executor_release": R1A_EXECUTOR_RELEASE,
        "expires_at": challenge.expires_at,
        "issued_at": challenge.issued_at,
        "platform_challenge_hash": challenge.challenge_hash,
        "public_key_material": encode_ed25519_public_key(private_key.public_key()),
        "schema_version": ANNOUNCEMENT_VERSION,
        "session_nonce": challenge.session_nonce,
        "session_nonce_hash": challenge.session_nonce_hash,
        "signature_algorithm": "ed25519-v1",
    }
    signing_bytes = json.dumps(
        document,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    document["proof_signature"] = encode_ed25519_signature(
        private_key.sign(signing_bytes)
    )
    return json.dumps(
        document,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _r1a_candidate() -> R1aExecutorCandidateV1:
    return R1aExecutorCandidateV1(
        identity_id=R1A_EXECUTOR_ID,
        release=R1A_EXECUTOR_RELEASE,
        role="executor",
        key_id=R1A_EXECUTOR_KEY_ID,
        capability=R1A_CAPABILITY,
        policy_version=R1A_POLICY_VERSION,
        tool_policy_hash=R1A_TOOL_POLICY_HASH,
        active=True,
    )


def _r1a_selection() -> R1aExecutorSelectionV1:
    return R1aExecutorSelectionV1(
        executor_id=R1A_EXECUTOR_ID,
        executor_release=R1A_EXECUTOR_RELEASE,
        executor_key_id=R1A_EXECUTOR_KEY_ID,
        capability=R1A_CAPABILITY,
        policy_version=R1A_POLICY_VERSION,
        tool_policy_hash=R1A_TOOL_POLICY_HASH,
    )


def _issue_r1a_operation(
    service: ProtocolService,
    private_keys: dict[str, Ed25519PrivateKey],
    caller_credential: Callable[..., CallerCredentialV2],
) -> OperationEnvelopeV2:
    request = OperationRequestV2(
        source_ref_hash="a" * 64,
        source_version="srcv_source_01",
        operation_kind="bounded_execution",
        policy_version=R1A_POLICY_VERSION,
        idempotency_key="idem_operation_01",
        expires_at=NOW + timedelta(seconds=120),
    )
    return service.issue_and_accept_r1a_operation(
        authenticated_caller="svc_source_01",
        operation_id=R1A_OPERATION_ID,
        request=request,
        platform_identity=RegisteredIdentityV2(
            identity_id="plt_platform_01",
            principal_id="prn_platform_01",
            release="rel_platform_01",
            key_id="key_platform_01",
            role="platform",
        ),
        signature_signer=lambda _key_id, payload: encode_ed25519_signature(
            private_keys["key_platform_01"].sign(payload)
        ),
        caller_credential=caller_credential(request),
        now=NOW,
    )


def _r1a_manifest() -> ManifestV2:
    return ManifestV2(
        operation_id=R1A_OPERATION_ID,
        attempt_id="att_r1a_synthetic_01",
        executor_id=R1A_EXECUTOR_ID,
        executor_release=R1A_EXECUTOR_RELEASE,
        artifacts=(
            ArtifactV2(
                artifact_id="art_r1a_patch_01",
                media_type="text/x-diff",
                sha256=R1A_ARTIFACT_HASH,
                byte_size=241,
                storage_ref="vault://artifact/r1a_patch_01",
            ),
        ),
    )


def _r1a_evidence(
    private_keys: dict[str, Ed25519PrivateKey],
) -> ExecutorExecutionEvidenceV1:
    unsigned = ExecutorExecutionEvidenceV1(
        evidence_version=EVIDENCE_CONTRACT_VERSION,
        operation_id=R1A_OPERATION_ID,
        attempt_id="att_r1a_synthetic_01",
        input_ref_hash=R1A_INPUT_REF_HASH,
        executor_id=R1A_EXECUTOR_ID,
        executor_release=R1A_EXECUTOR_RELEASE,
        executor_key_id=R1A_EXECUTOR_KEY_ID,
        bound_capsule_hash=R1A_CAPSULE_HASH,
        fixture_hash=R1A_FIXTURE_HASH,
        tool_policy_hash=R1A_TOOL_POLICY_HASH,
        artifact_hash=R1A_ARTIFACT_HASH,
        result_state="completed",
        produced_at=R1A_PRODUCED_AT,
        signature_algorithm="ed25519-v1",
        executor_signature="sig_" + "A" * 86,
    )
    return replace(
        unsigned,
        executor_signature=encode_ed25519_signature(
            private_keys[R1A_EXECUTOR_KEY_ID].sign(unsigned.canonical_signing_bytes)
        ),
    )


def _advance_r1a_to_dispatched(
    service: ProtocolService,
    private_keys: dict[str, Ed25519PrivateKey],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    _issue_r1a_operation(service, private_keys, caller_credential)
    service.claim_r1a_attempt(attempt=_r1a_attempt(), now=NOW)


def _truncate(session: Session) -> None:
    session.execute(
        sa.text(
            "TRUNCATE TABLE protocol_audit_events, protocol_outbox, protocol_receipts, "
            "protocol_executor_evidence, protocol_manifests, protocol_attempts, "
            "protocol_operations, "
            "protocol_identity_keys, protocol_identities"
        )
    )
    session.commit()


def test_accept_operation_is_atomic_idempotent_and_rejects_changed_replay(
    service: ProtocolService,
    session: Session,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    first = _accept_operation(service, operation, caller_credential)
    replay = _accept_operation(
        service, operation, caller_credential, operation_id="op_operation_02"
    )

    assert replay.operation_id == first.operation_id == "op_operation_01"
    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 0,
        "manifests": 0,
        "receipts": 0,
        "audit": 1,
        "outbox": 0,
    }

    with pytest.raises(ProtocolViolation, match="idempotency_payload_conflict"):
        _accept_operation(
            service,
            operation,
            caller_credential,
            operation_id="op_operation_03",
            source_ref_hash="e" * 64,
        )

    assert lifecycle_counts(session)["operations"] == 1
    assert lifecycle_counts(session)["audit"] == 1


def test_attempt_and_manifest_replays_preserve_one_immutable_binding(
    service: ProtocolService,
    session: Session,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
    attempt: ExecutionAttemptV2,
    manifest: ManifestV2,
) -> None:
    _accept_operation(service, operation, caller_credential)

    assert service.record_attempt(attempt=attempt, now=NOW) == attempt
    assert service.record_attempt(attempt=attempt, now=NOW) == attempt
    with pytest.raises(ProtocolViolation, match="attempt_binding_conflict"):
        service.record_attempt(
            attempt=replace(attempt, tool_policy_hash="f" * 64), now=NOW
        )

    assert service.record_manifest(manifest=manifest, now=NOW) == manifest
    assert service.record_manifest(manifest=manifest, now=NOW) == manifest
    tampered = ManifestV2(
        operation_id=manifest.operation_id,
        attempt_id=manifest.attempt_id,
        executor_id=manifest.executor_id,
        executor_release=manifest.executor_release,
        artifacts=(replace(manifest.artifacts[0], sha256="1" * 64),),
    )
    with pytest.raises(ProtocolViolation, match="manifest_binding_conflict"):
        service.record_manifest(manifest=tampered, now=NOW)

    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 1,
        "manifests": 1,
        "receipts": 0,
        "audit": 3,
        "outbox": 1,
    }


def test_r1a_attempt_claim_cannot_use_a_manually_constructed_selection(
    service: ProtocolService,
    session: Session,
    private_keys: dict[str, Ed25519PrivateKey],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    _issue_r1a_operation(service, private_keys, caller_credential)
    attempt = _r1a_attempt()

    with pytest.raises(ProtocolViolation, match="r1a_claim_required"):
        service.record_attempt(
            attempt=attempt,
            selection=_r1a_selection(),
            now=NOW,
        )

    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 0,
        "manifests": 0,
        "receipts": 0,
        "audit": 1,
        "outbox": 0,
    }
    assert session.get(ProtocolOperation, R1A_OPERATION_ID).state == "accepted"

    assert service.claim_r1a_attempt(attempt=attempt, now=NOW) == attempt


def test_r1a_ephemeral_executor_registration_is_exact_and_idempotent(
    service: ProtocolService,
    session: Session,
) -> None:
    first = service.register_r1a_ephemeral_executor_key(now=NOW)
    replay = service.register_r1a_ephemeral_executor_key(now=NOW + timedelta(seconds=1))

    assert first == replay
    identity = session.get(ProtocolIdentity, R1A_EXECUTOR_ID)
    key = session.get(ProtocolIdentityKey, R1A_EXECUTOR_KEY_ID)
    assert identity.principal_id == "prn_r1a_synthetic_01"
    assert identity.release == R1A_EXECUTOR_RELEASE
    assert key.identity_id == R1A_EXECUTOR_ID
    assert key.public_key_material == first.public_key_material
    assert key.status == "active"
    assert (
        session.scalar(
            select(sa.func.count())
            .select_from(ProtocolIdentity)
            .where(ProtocolIdentity.identity_id == R1A_EXECUTOR_ID)
        )
        == 1
    )
    assert (
        session.scalar(
            select(sa.func.count())
            .select_from(ProtocolIdentityKey)
            .where(ProtocolIdentityKey.key_id == R1A_EXECUTOR_KEY_ID)
        )
        == 1
    )


def test_r1a_changed_ephemeral_key_conflicts_without_protocol_writes(
    service: ProtocolService,
    session_factory: sessionmaker[Session],
    session: Session,
) -> None:
    other_key = Ed25519PrivateKey.generate()
    changed = ProtocolService(
        session_factory=session_factory,
        r1a_admission_bytes=service._r1a_admission_bytes,
        r1a_source_readback=service._r1a_source_readback,
        r1a_executor_candidates=service._r1a_executor_candidates,
        r1a_ephemeral_challenge=service._r1a_ephemeral_challenge,
        r1a_ephemeral_announcement_bytes=_ephemeral_announcement_bytes(
            service._r1a_ephemeral_challenge, other_key
        ),
    )

    with pytest.raises(
        ProtocolViolation, match="r1a_ephemeral_key_registration_conflict"
    ):
        changed.register_r1a_ephemeral_executor_key(now=NOW)

    assert lifecycle_counts(session) == {
        "operations": 0,
        "attempts": 0,
        "manifests": 0,
        "receipts": 0,
        "audit": 0,
        "outbox": 0,
    }


def test_r1a_operation_expiry_cannot_exceed_ephemeral_key(
    service: ProtocolService,
    session: Session,
    private_keys: dict[str, Ed25519PrivateKey],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    request = OperationRequestV2(
        source_ref_hash="a" * 64,
        source_version="srcv_source_01",
        operation_kind="bounded_execution",
        policy_version=R1A_POLICY_VERSION,
        idempotency_key="idem_operation_01",
        expires_at=NOW + timedelta(seconds=121),
    )
    signer_calls = 0

    def signer(_key_id: str, payload: bytes) -> str:
        nonlocal signer_calls
        signer_calls += 1
        return encode_ed25519_signature(private_keys["key_platform_01"].sign(payload))

    with pytest.raises(
        ProtocolViolation, match="operation_expiry_exceeds_ephemeral_key"
    ):
        service.issue_and_accept_r1a_operation(
            authenticated_caller="svc_source_01",
            operation_id=R1A_OPERATION_ID,
            request=request,
            platform_identity=RegisteredIdentityV2(
                identity_id="plt_platform_01",
                principal_id="prn_platform_01",
                release="rel_platform_01",
                key_id="key_platform_01",
                role="platform",
            ),
            signature_signer=signer,
            caller_credential=caller_credential(request),
            now=NOW,
        )

    assert signer_calls == 0
    assert lifecycle_counts(session)["operations"] == 0


def test_r1a_attempt_lease_cannot_exceed_ephemeral_key(
    service: ProtocolService,
    session: Session,
    private_keys: dict[str, Ed25519PrivateKey],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    _issue_r1a_operation(service, private_keys, caller_credential)
    attempt = replace(_r1a_attempt(), lease_expires_at=NOW + timedelta(seconds=121))

    with pytest.raises(ProtocolViolation, match="executor_selection_required"):
        service.claim_r1a_attempt(attempt=attempt, now=NOW)

    assert lifecycle_counts(session)["attempts"] == 0
    assert session.get(ProtocolOperation, R1A_OPERATION_ID).state == "accepted"


def test_r1a_generic_accept_operation_fails_before_any_protocol_write(
    service: ProtocolService,
    session: Session,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    envelope = operation(
        operation_id=R1A_OPERATION_ID,
        policy_version=R1A_POLICY_VERSION,
        expires_at=NOW + timedelta(seconds=120),
    )

    with pytest.raises(ProtocolViolation, match="r1a_admission_required"):
        service.accept_operation(
            caller_credential=caller_credential(envelope),
            envelope=envelope,
            now=NOW,
        )

    assert lifecycle_counts(session) == {
        "operations": 0,
        "attempts": 0,
        "manifests": 0,
        "receipts": 0,
        "audit": 0,
        "outbox": 0,
    }


def test_r1a_source_admission_failure_happens_before_envelope_signing_or_writes(
    monkeypatch: pytest.MonkeyPatch,
    service: ProtocolService,
    session: Session,
    private_keys: dict[str, Ed25519PrivateKey],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    request = OperationRequestV2(
        source_ref_hash="a" * 64,
        source_version="srcv_source_01",
        operation_kind="bounded_execution",
        policy_version=R1A_POLICY_VERSION,
        idempotency_key="idem_operation_01",
        expires_at=NOW + timedelta(seconds=120),
    )
    signer_calls = 0

    def fail_source_admission(_data: bytes, *, source_readback: object) -> None:
        raise AdmissionViolation("r1a_source_readback_failed")

    def platform_signer(_key_id: str, _payload: bytes) -> str:
        nonlocal signer_calls
        signer_calls += 1
        return "sig_" + "A" * 86

    monkeypatch.setattr(
        service_module,
        "evaluate_r1a_runtime_admission_bytes",
        fail_source_admission,
    )

    with pytest.raises(ProtocolViolation, match="r1a_admission_required"):
        service.issue_and_accept_r1a_operation(
            authenticated_caller="svc_source_01",
            operation_id=R1A_OPERATION_ID,
            request=request,
            platform_identity=RegisteredIdentityV2(
                identity_id="plt_platform_01",
                principal_id="prn_platform_01",
                release="rel_platform_01",
                key_id="key_platform_01",
                role="platform",
            ),
            signature_signer=platform_signer,
            caller_credential=caller_credential(request),
            now=NOW,
        )

    assert signer_calls == 0
    assert lifecycle_counts(session) == {
        "operations": 0,
        "attempts": 0,
        "manifests": 0,
        "receipts": 0,
        "audit": 0,
        "outbox": 0,
    }


def test_r1a_inactive_executor_key_fails_before_envelope_signing_or_writes(
    service: ProtocolService,
    session: Session,
    private_keys: dict[str, Ed25519PrivateKey],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    key = session.get(ProtocolIdentityKey, R1A_EXECUTOR_KEY_ID)
    key.status = "revoked"
    key.revoked_at = NOW
    session.commit()
    request = OperationRequestV2(
        source_ref_hash="a" * 64,
        source_version="srcv_source_01",
        operation_kind="bounded_execution",
        policy_version=R1A_POLICY_VERSION,
        idempotency_key="idem_operation_01",
        expires_at=NOW + timedelta(seconds=120),
    )
    signer_calls = 0

    def platform_signer(_key_id: str, payload: bytes) -> str:
        nonlocal signer_calls
        signer_calls += 1
        return encode_ed25519_signature(private_keys["key_platform_01"].sign(payload))

    with pytest.raises(ProtocolViolation, match="executor_selection_required"):
        service.issue_and_accept_r1a_operation(
            authenticated_caller="svc_source_01",
            operation_id=R1A_OPERATION_ID,
            request=request,
            platform_identity=RegisteredIdentityV2(
                identity_id="plt_platform_01",
                principal_id="prn_platform_01",
                release="rel_platform_01",
                key_id="key_platform_01",
                role="platform",
            ),
            signature_signer=platform_signer,
            caller_credential=caller_credential(request),
            now=NOW,
        )

    assert signer_calls == 0
    assert lifecycle_counts(session) == {
        "operations": 0,
        "attempts": 0,
        "manifests": 0,
        "receipts": 0,
        "audit": 0,
        "outbox": 0,
    }


def test_r1a_legacy_record_manifest_requires_execution_evidence(
    service: ProtocolService,
    session: Session,
    private_keys: dict[str, Ed25519PrivateKey],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    _issue_r1a_operation(service, private_keys, caller_credential)
    service.claim_r1a_attempt(attempt=_r1a_attempt(), now=NOW)

    with pytest.raises(ProtocolViolation, match="executor_evidence_required"):
        service.record_manifest(manifest=_r1a_manifest(), now=NOW)

    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 1,
        "manifests": 0,
        "receipts": 0,
        "audit": 2,
        "outbox": 1,
    }
    assert session.get(ProtocolOperation, R1A_OPERATION_ID).state == "dispatched"


def test_r1a_two_session_attempt_claim_has_exactly_one_winner(
    monkeypatch: pytest.MonkeyPatch,
    service: ProtocolService,
    session: Session,
    private_keys: dict[str, Ed25519PrivateKey],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    _issue_r1a_operation(service, private_keys, caller_credential)
    barrier = Barrier(2, timeout=10)
    original_require_state = ProtocolService._require_state

    def synchronized_require_state(
        operation_row: ProtocolOperation, expected: str
    ) -> None:
        original_require_state(operation_row, expected)
        if expected == "accepted":
            barrier.wait()

    monkeypatch.setattr(
        ProtocolService,
        "_require_state",
        staticmethod(synchronized_require_state),
    )
    attempts = (
        _r1a_attempt(),
        replace(_r1a_attempt(), attempt_id="att_r1a_synthetic_02"),
    )

    def submit(candidate: ExecutionAttemptV2) -> ExecutionAttemptV2 | Exception:
        try:
            return service.claim_r1a_attempt(attempt=candidate, now=NOW)
        except Exception as error:  # noqa: BLE001 - result is asserted below
            return error

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(submit, attempts))

    diagnostic = tuple((type(result).__name__, str(result)) for result in results)
    assert sum(isinstance(result, ExecutionAttemptV2) for result in results) == 1, (
        diagnostic
    )
    assert (
        sum(
            isinstance(result, ProtocolViolation)
            and str(result) == "attempt_claim_conflict"
            for result in results
        )
        == 1
    ), diagnostic
    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 1,
        "manifests": 0,
        "receipts": 0,
        "audit": 2,
        "outbox": 1,
    }
    assert (
        session.scalar(
            select(sa.func.count())
            .select_from(ProtocolAuditEvent)
            .where(ProtocolAuditEvent.event_type == "dispatched")
        )
        == 1
    )
    assert (
        session.scalar(
            select(sa.func.count())
            .select_from(ProtocolOutbox)
            .where(ProtocolOutbox.event_type == "dispatched")
        )
        == 1
    )


def test_r1a_execution_evidence_and_manifest_are_atomic_and_replay_safe(
    service: ProtocolService,
    session: Session,
    private_keys: dict[str, Ed25519PrivateKey],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    _advance_r1a_to_dispatched(service, private_keys, caller_credential)
    evidence = _r1a_evidence(private_keys)
    manifest = _r1a_manifest()

    first = service.record_execution_evidence_and_manifest(
        evidence=evidence,
        manifest=manifest,
        now=R1A_PRODUCED_AT + timedelta(seconds=20),
    )
    replay = service.record_execution_evidence_and_manifest(
        evidence=evidence,
        manifest=manifest,
        now=R1A_PRODUCED_AT + timedelta(seconds=30),
    )

    assert first == replay == (evidence, manifest)
    row = session.scalar(select(ProtocolExecutorEvidence))
    assert row.evidence_hash == hashlib.sha256(evidence.canonical_bytes).hexdigest()
    assert row.executor_signature == evidence.executor_signature
    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 1,
        "manifests": 1,
        "receipts": 0,
        "audit": 3,
        "outbox": 2,
    }
    assert (
        session.scalar(select(sa.func.count()).select_from(ProtocolExecutorEvidence))
        == 1
    )
    assert session.get(ProtocolOperation, R1A_OPERATION_ID).state == "manifest_received"

    changed_manifest = replace(
        manifest,
        artifacts=(
            replace(manifest.artifacts[0], storage_ref="vault://artifact/changed"),
        ),
    )
    with pytest.raises(ProtocolViolation, match="executor_evidence_binding_conflict"):
        service.record_execution_evidence_and_manifest(
            evidence=evidence,
            manifest=changed_manifest,
            now=R1A_PRODUCED_AT + timedelta(seconds=40),
        )
    assert lifecycle_counts(session)["manifests"] == 1
    assert (
        session.scalar(select(sa.func.count()).select_from(ProtocolExecutorEvidence))
        == 1
    )


@pytest.mark.parametrize(
    ("case", "expected_code"),
    [
        ("forged_signature", "invalid_executor_evidence_signature"),
        ("substituted_artifact", "executor_evidence_artifact_mismatch"),
        ("wrong_key", "executor_evidence_binding_mismatch"),
        ("wrong_release", "executor_evidence_binding_mismatch"),
        ("changed_input", "executor_evidence_binding_mismatch"),
        ("changed_capsule", "executor_evidence_binding_mismatch"),
        ("changed_fixture", "executor_evidence_binding_mismatch"),
        ("changed_tool_policy", "executor_evidence_binding_mismatch"),
        ("changed_artifact_evidence", "executor_evidence_binding_mismatch"),
        ("revoked_key", "executor_key_inactive"),
        ("expired_attempt", "attempt_expired"),
    ],
)
def test_r1a_invalid_execution_evidence_rolls_back_without_partial_rows(
    case: str,
    expected_code: str,
    service: ProtocolService,
    session: Session,
    private_keys: dict[str, Ed25519PrivateKey],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    _advance_r1a_to_dispatched(service, private_keys, caller_credential)
    evidence = _r1a_evidence(private_keys)
    manifest = _r1a_manifest()
    now = R1A_PRODUCED_AT + timedelta(seconds=20)
    if case == "forged_signature":
        evidence = replace(evidence, executor_signature="sig_" + "A" * 86)
    elif case == "substituted_artifact":
        manifest = replace(
            manifest,
            artifacts=(replace(manifest.artifacts[0], sha256="d" * 64),),
        )
    elif case == "wrong_key":
        evidence = replace(evidence, executor_key_id="key_executor_01")
    elif case == "wrong_release":
        evidence = replace(evidence, executor_release="rel_r1a_synthetic_02")
    elif case == "changed_input":
        evidence = replace(evidence, input_ref_hash="e" * 64)
    elif case == "changed_capsule":
        evidence = replace(evidence, bound_capsule_hash="e" * 64)
    elif case == "changed_fixture":
        evidence = replace(evidence, fixture_hash="e" * 64)
    elif case == "changed_tool_policy":
        evidence = replace(evidence, tool_policy_hash="e" * 64)
    elif case == "changed_artifact_evidence":
        evidence = replace(evidence, artifact_hash="e" * 64)
    elif case == "revoked_key":
        key = session.get(ProtocolIdentityKey, R1A_EXECUTOR_KEY_ID)
        key.status = "revoked"
        key.revoked_at = R1A_PRODUCED_AT
        session.commit()
    elif case == "expired_attempt":
        now = NOW + timedelta(seconds=90)

    with pytest.raises(ProtocolViolation, match=expected_code):
        service.record_execution_evidence_and_manifest(
            evidence=evidence,
            manifest=manifest,
            now=now,
        )

    assert (
        session.scalar(select(sa.func.count()).select_from(ProtocolExecutorEvidence))
        == 0
    )
    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 1,
        "manifests": 0,
        "receipts": 0,
        "audit": 2,
        "outbox": 1,
    }
    assert session.get(ProtocolOperation, R1A_OPERATION_ID).state == "dispatched"


@pytest.mark.parametrize("failure_point", ["manifest_insert", "audit_append"])
def test_r1a_injected_failure_rolls_back_executor_evidence_and_manifest(
    failure_point: str,
    monkeypatch: pytest.MonkeyPatch,
    service: ProtocolService,
    session: Session,
    private_keys: dict[str, Ed25519PrivateKey],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    _advance_r1a_to_dispatched(service, private_keys, caller_credential)

    def fail_manifest(_repository: ProtocolRepository, _row: ProtocolManifest) -> None:
        raise RuntimeError("injected_manifest_failure")

    def fail_audit(_repository: ProtocolRepository, _row: ProtocolAuditEvent) -> None:
        raise RuntimeError("injected_audit_failure")

    if failure_point == "manifest_insert":
        monkeypatch.setattr(ProtocolRepository, "insert_manifest", fail_manifest)
        expected = "injected_manifest_failure"
    else:
        monkeypatch.setattr(ProtocolRepository, "append_audit_event", fail_audit)
        expected = "injected_audit_failure"
    with pytest.raises(RuntimeError, match=expected):
        service.record_execution_evidence_and_manifest(
            evidence=_r1a_evidence(private_keys),
            manifest=_r1a_manifest(),
            now=R1A_PRODUCED_AT + timedelta(seconds=20),
        )

    assert (
        session.scalar(select(sa.func.count()).select_from(ProtocolExecutorEvidence))
        == 0
    )
    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 1,
        "manifests": 0,
        "receipts": 0,
        "audit": 2,
        "outbox": 1,
    }
    assert session.get(ProtocolOperation, R1A_OPERATION_ID).state == "dispatched"


def test_generic_protocol_v2_manifest_path_remains_compatible(
    service: ProtocolService,
    session: Session,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
    attempt: ExecutionAttemptV2,
    manifest: ManifestV2,
) -> None:
    _accept_operation(service, operation, caller_credential)

    assert service.record_attempt(attempt=attempt, now=NOW) == attempt
    assert service.record_manifest(manifest=manifest, now=NOW) == manifest
    assert lifecycle_counts(session)["manifests"] == 1


def test_receipt_requires_an_independent_registered_signature_and_one_binding(
    service: ProtocolService,
    session: Session,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
    attempt: ExecutionAttemptV2,
    manifest: ManifestV2,
    receipt: IndependentReceiptV2,
    private_keys: dict[str, Ed25519PrivateKey],
) -> None:
    advance_to_manifest(service, operation, caller_credential, attempt, manifest)

    assert (
        service.record_receipt(receipt=receipt, now=NOW + timedelta(minutes=2))
        == receipt
    )
    assert (
        service.record_receipt(receipt=receipt, now=NOW + timedelta(minutes=2))
        == receipt
    )
    changed_unsigned = replace(
        receipt,
        decision="rejected",
        signature="sig_0000000000000000",
    )
    with pytest.raises(ProtocolViolation, match="receipt_binding_conflict"):
        service.record_receipt(
            receipt=_signed_receipt(private_keys, changed_unsigned),
            now=NOW + timedelta(minutes=2),
        )
    with pytest.raises(ProtocolViolation, match="invalid_receipt_signature"):
        service.record_receipt(
            receipt=replace(receipt, signature="sig_0123456789abcdef"),
            now=NOW + timedelta(minutes=2),
        )

    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 1,
        "manifests": 1,
        "receipts": 1,
        "audit": 4,
        "outbox": 2,
    }


def test_expired_operation_and_invalid_release_fail_closed_without_new_rows(
    service: ProtocolService,
    session: Session,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
    attempt: ExecutionAttemptV2,
) -> None:
    with pytest.raises(ProtocolViolation, match="operation_expired"):
        _accept_operation(service, operation, caller_credential, expires_at=NOW)

    _accept_operation(service, operation, caller_credential)
    with pytest.raises(ProtocolViolation, match="executor_release_mismatch"):
        service.record_attempt(
            attempt=replace(attempt, executor_release="rel_executor_02"),
            now=NOW,
        )

    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 0,
        "manifests": 0,
        "receipts": 0,
        "audit": 1,
        "outbox": 0,
    }


def test_receipt_rejects_same_principal_wrong_release_key_and_expiry(
    service: ProtocolService,
    session: Session,
    private_keys: dict[str, Ed25519PrivateKey],
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
    attempt: ExecutionAttemptV2,
    manifest: ManifestV2,
    receipt: IndependentReceiptV2,
) -> None:
    advance_to_manifest(service, operation, caller_credential, attempt, manifest)
    conflicting_key = Ed25519PrivateKey.generate()
    session.add(
        ProtocolIdentity(
            identity_id="ver_conflict_01",
            principal_id="prn_executor_01",
            role="verifier",
            release="rel_conflict_01",
            registered_at=NOW,
        )
    )
    session.add(
        ProtocolIdentityKey(
            key_id="key_conflict_01",
            identity_id="ver_conflict_01",
            algorithm="ed25519-v1",
            public_key_material=encode_ed25519_public_key(conflicting_key.public_key()),
            status="active",
            registered_at=NOW,
            revoked_at=None,
        )
    )
    session.commit()
    conflicting_receipt = _signed_receipt(
        {**private_keys, "key_conflict_01": conflicting_key},
        replace(
            receipt,
            verifier_id="ver_conflict_01",
            verifier_release="rel_conflict_01",
            key_id="key_conflict_01",
            signature="sig_0000000000000000",
        ),
    )

    with pytest.raises(ProtocolViolation, match="executor_verifier_conflict"):
        service.record_receipt(
            receipt=conflicting_receipt, now=NOW + timedelta(minutes=2)
        )
    with pytest.raises(ProtocolViolation, match="verifier_release_mismatch"):
        service.record_receipt(
            receipt=replace(receipt, verifier_release="rel_verifier_02"),
            now=NOW + timedelta(minutes=2),
        )
    with pytest.raises(ProtocolViolation, match="verifier_key_mismatch"):
        service.record_receipt(
            receipt=replace(receipt, key_id="key_executor_01"),
            now=NOW + timedelta(minutes=2),
        )
    with pytest.raises(ProtocolViolation, match="operation_expired"):
        service.record_receipt(receipt=receipt, now=NOW + timedelta(minutes=31))

    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 1,
        "manifests": 1,
        "receipts": 0,
        "audit": 3,
        "outbox": 1,
    }


def test_transaction_failure_rolls_back_operation_audit_and_outbox(
    monkeypatch: pytest.MonkeyPatch,
    service: ProtocolService,
    session: Session,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
) -> None:
    def fail_after_operation(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("injected audit failure")

    monkeypatch.setattr(ProtocolRepository, "append_audit_event", fail_after_operation)

    with pytest.raises(RuntimeError, match="injected audit failure"):
        _accept_operation(service, operation, caller_credential)

    assert lifecycle_counts(session) == {
        "operations": 0,
        "attempts": 0,
        "manifests": 0,
        "receipts": 0,
        "audit": 0,
        "outbox": 0,
    }


def test_transaction_failure_rolls_back_attempt_audit_and_state(
    monkeypatch: pytest.MonkeyPatch,
    service: ProtocolService,
    session: Session,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
    attempt: ExecutionAttemptV2,
) -> None:
    _accept_operation(service, operation, caller_credential)

    def fail_after_attempt(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("injected attempt audit failure")

    monkeypatch.setattr(ProtocolRepository, "append_audit_event", fail_after_attempt)

    with pytest.raises(RuntimeError, match="injected attempt audit failure"):
        service.record_attempt(attempt=attempt, now=NOW)

    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 0,
        "manifests": 0,
        "receipts": 0,
        "audit": 1,
        "outbox": 0,
    }
    assert session.get(ProtocolOperation, "op_operation_01").state == "accepted"


def test_transaction_failure_rolls_back_manifest_audit_outbox_and_state(
    monkeypatch: pytest.MonkeyPatch,
    service: ProtocolService,
    session: Session,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
    attempt: ExecutionAttemptV2,
    manifest: ManifestV2,
) -> None:
    _accept_operation(service, operation, caller_credential)
    service.record_attempt(attempt=attempt, now=NOW)

    def fail_after_manifest(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("injected manifest outbox failure")

    monkeypatch.setattr(ProtocolRepository, "enqueue_outbox", fail_after_manifest)

    with pytest.raises(RuntimeError, match="injected manifest outbox failure"):
        service.record_manifest(manifest=manifest, now=NOW)

    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 1,
        "manifests": 0,
        "receipts": 0,
        "audit": 2,
        "outbox": 0,
    }
    assert session.get(ProtocolOperation, "op_operation_01").state == "dispatched"


def test_transaction_failure_rolls_back_receipt_audit_outbox_and_state(
    monkeypatch: pytest.MonkeyPatch,
    service: ProtocolService,
    session: Session,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
    attempt: ExecutionAttemptV2,
    manifest: ManifestV2,
    receipt: IndependentReceiptV2,
) -> None:
    advance_to_manifest(service, operation, caller_credential, attempt, manifest)

    def fail_after_receipt(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("injected receipt audit failure")

    monkeypatch.setattr(ProtocolRepository, "append_audit_event", fail_after_receipt)

    with pytest.raises(RuntimeError, match="injected receipt audit failure"):
        service.record_receipt(receipt=receipt, now=NOW + timedelta(minutes=2))

    assert lifecycle_counts(session) == {
        "operations": 1,
        "attempts": 1,
        "manifests": 1,
        "receipts": 0,
        "audit": 3,
        "outbox": 1,
    }
    assert (
        session.get(ProtocolOperation, "op_operation_01").state == "manifest_received"
    )


def test_outbox_claim_and_ack_are_retry_safe_without_network_delivery(
    service: ProtocolService,
    session: Session,
    operation: Callable[..., OperationEnvelopeV2],
    caller_credential: Callable[..., CallerCredentialV2],
    attempt: ExecutionAttemptV2,
    manifest: ManifestV2,
) -> None:
    advance_to_manifest(service, operation, caller_credential, attempt, manifest)

    claimed = service.claim_next_outbox(
        now=NOW + timedelta(minutes=2), lease=timedelta(minutes=1)
    )

    assert claimed is not None
    assert session.get(ProtocolOutbox, claimed.outbox_id).state == "claimed"
    with pytest.raises(ProtocolViolation, match="outbox_event_hash_mismatch"):
        service.ack_outbox(
            outbox_id=claimed.outbox_id,
            event_hash="0" * 64,
            claim_token=claimed.claim_token,
            now=NOW + timedelta(minutes=2),
        )
    with pytest.raises(ProtocolViolation, match="outbox_not_found"):
        service.ack_outbox(
            outbox_id="out_missing_01",
            event_hash=claimed.event_hash,
            claim_token=claimed.claim_token,
            now=NOW + timedelta(minutes=2),
        )

    first_ack = service.ack_outbox(
        outbox_id=claimed.outbox_id,
        event_hash=claimed.event_hash,
        claim_token=claimed.claim_token,
        now=NOW + timedelta(minutes=2),
    )
    replay_ack = service.ack_outbox(
        outbox_id=claimed.outbox_id,
        event_hash=claimed.event_hash,
        claim_token=claimed.claim_token,
        now=NOW + timedelta(minutes=2),
    )

    assert replay_ack == first_ack
    assert session.get(ProtocolOutbox, claimed.outbox_id).state == "delivered"
    assert lifecycle_counts(session)["outbox"] == 1

from __future__ import annotations

import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

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
from platform_protocol.migrations import (
    downgrade_platform_database,
    upgrade_platform_database,
)
from platform_protocol.models import (
    ProtocolAuditEvent,
    ProtocolIdentity,
    ProtocolIdentityKey,
    ProtocolOperation,
    ProtocolOutbox,
)
from platform_protocol.registry import (
    CALLER_CREDENTIAL_AUDIENCE_V2,
    CALLER_CREDENTIAL_VERSION_V2,
    CallerCredentialV2,
)
from platform_protocol.service import ProtocolService

NOW = datetime(2026, 8, 4, 18, 0, tzinfo=timezone.utc)


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
        "svc_caller_01": Ed25519PrivateKey.generate(),
        "plt_platform_01": Ed25519PrivateKey.generate(),
        "exec_executor_01": Ed25519PrivateKey.generate(),
        "ver_verifier_01": Ed25519PrivateKey.generate(),
    }
    registrations = (
        ("svc_caller_01", "prn_caller_01", "caller", "rel_caller_01", "key_caller_01"),
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
                registered_at=NOW - timedelta(minutes=1),
            )
        )
        session.add(
            ProtocolIdentityKey(
                key_id=key_id,
                identity_id=identity_id,
                algorithm="ed25519-v1",
                public_key_material=encode_ed25519_public_key(
                    keys[identity_id].public_key()
                ),
                status="active",
                registered_at=NOW - timedelta(minutes=1),
                revoked_at=None,
            )
        )
    session.commit()
    return keys


@pytest.fixture
def operation(private_keys: dict[str, Ed25519PrivateKey]) -> OperationEnvelopeV2:
    request = OperationRequestV2(
        source_ref_hash="a" * 64,
        source_version="srcv_source_01",
        operation_kind="bounded_execution",
        policy_version="pol_policy_01",
        idempotency_key="idem_operation_01",
        expires_at=NOW + timedelta(minutes=15),
    )
    return create_operation_envelope(
        authenticated_caller="svc_caller_01",
        operation_id="op_operation_01",
        request=request,
        platform_identity=RegisteredIdentityV2(
            identity_id="plt_platform_01",
            principal_id="prn_platform_01",
            release="rel_platform_01",
            key_id="key_platform_01",
            role="platform",
        ),
        signature_signer=lambda _key_id, payload: encode_ed25519_signature(
            private_keys["plt_platform_01"].sign(payload)
        ),
    )


def _caller_credential(
    private_keys: dict[str, Ed25519PrivateKey],
    envelope: OperationEnvelopeV2,
    **changes: object,
) -> CallerCredentialV2:
    unsigned = CallerCredentialV2(
        credential_version=CALLER_CREDENTIAL_VERSION_V2,
        audience=CALLER_CREDENTIAL_AUDIENCE_V2,
        caller_id="svc_caller_01",
        caller_release="rel_caller_01",
        key_id="key_caller_01",
        request_hash=envelope.canonical_request_hash,
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        signature="sig_0000000000000000",
    )
    unsigned = replace(unsigned, **changes)
    return replace(
        unsigned,
        signature=encode_ed25519_signature(
            private_keys["svc_caller_01"].sign(unsigned.canonical_signing_bytes)
        ),
    )


def _attempt() -> ExecutionAttemptV2:
    return ExecutionAttemptV2(
        operation_id="op_operation_01",
        attempt_id="att_attempt_01",
        executor_id="exec_executor_01",
        executor_release="rel_executor_01",
        lease_expires_at=NOW + timedelta(minutes=5),
        tool_policy_hash="b" * 64,
        input_ref_hash="c" * 64,
    )


def _manifest() -> ManifestV2:
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


def _receipt(
    private_keys: dict[str, Ed25519PrivateKey],
    manifest: ManifestV2,
    *,
    signing_key: Ed25519PrivateKey | None = None,
    **changes: object,
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
    unsigned = replace(unsigned, **changes)
    signing_key = (
        signing_key
        or private_keys[
            "ver_verifier_01"
            if unsigned.key_id == "key_verifier_01"
            else "exec_executor_01"
        ]
    )
    return replace(
        unsigned,
        signature=encode_ed25519_signature(
            signing_key.sign(unsigned.canonical_signing_bytes)
        ),
    )


def _counts(session: Session) -> dict[str, int]:
    return {
        "operations": session.scalar(
            select(sa.func.count()).select_from(ProtocolOperation)
        )
        or 0,
        "audit": session.scalar(select(sa.func.count()).select_from(ProtocolAuditEvent))
        or 0,
        "outbox": session.scalar(select(sa.func.count()).select_from(ProtocolOutbox))
        or 0,
    }


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


def test_service_accepts_only_a_db_registered_caller_credential_and_real_platform_signature(
    session: Session,
    session_factory: sessionmaker[Session],
    private_keys: dict[str, Ed25519PrivateKey],
    operation: OperationEnvelopeV2,
) -> None:
    service = ProtocolService(session_factory=session_factory)
    credential = _caller_credential(private_keys, operation)

    accepted = service.accept_operation(
        caller_credential=credential,
        envelope=operation,
        now=NOW,
    )

    stored = session.get(ProtocolOperation, accepted.operation_id)
    assert stored is not None
    assert stored.caller_id == credential.caller_id
    assert stored.caller_release == credential.caller_release
    assert stored.caller_key_id == credential.key_id
    assert stored.caller_credential_version == credential.credential_version
    assert stored.caller_credential_hash == credential.credential_hash
    assert _counts(session) == {"operations": 1, "audit": 1, "outbox": 0}


def test_service_rejects_tampered_envelope_and_unknown_caller_key_without_writes(
    session: Session,
    session_factory: sessionmaker[Session],
    private_keys: dict[str, Ed25519PrivateKey],
    operation: OperationEnvelopeV2,
) -> None:
    service = ProtocolService(session_factory=session_factory)
    tampered_envelope = replace(operation, source_version="srcv_source_02")

    with pytest.raises(ProtocolViolation, match="invalid_platform_signature"):
        service.accept_operation(
            caller_credential=_caller_credential(private_keys, tampered_envelope),
            envelope=tampered_envelope,
            now=NOW,
        )
    with pytest.raises(ProtocolViolation, match="caller_key_mismatch"):
        service.accept_operation(
            caller_credential=_caller_credential(
                private_keys,
                operation,
                key_id="key_caller_02",
            ),
            envelope=operation,
            now=NOW,
        )

    assert _counts(session) == {"operations": 0, "audit": 0, "outbox": 0}


def test_service_rejects_invalid_caller_credentials_and_platform_keys_without_writes(
    session: Session,
    session_factory: sessionmaker[Session],
    private_keys: dict[str, Ed25519PrivateKey],
    operation: OperationEnvelopeV2,
) -> None:
    service = ProtocolService(session_factory=session_factory)
    invalid_signature = replace(
        _caller_credential(private_keys, operation),
        signature="sig_" + "A" * 86,
    )
    credentials = (
        (
            _caller_credential(
                private_keys,
                operation,
                issued_at=NOW + timedelta(minutes=1),
            ),
            "caller_credential_not_yet_valid",
        ),
        (
            _caller_credential(private_keys, operation, expires_at=NOW),
            "caller_credential_expired",
        ),
        (invalid_signature, "invalid_caller_credential_signature"),
    )
    for credential, failure_code in credentials:
        with pytest.raises(ProtocolViolation, match=failure_code):
            service.accept_operation(
                caller_credential=credential,
                envelope=operation,
                now=NOW,
            )
    with pytest.raises(ProtocolViolation, match="platform_key_mismatch"):
        service.accept_operation(
            caller_credential=_caller_credential(private_keys, operation),
            envelope=replace(operation, platform_key_id="key_platform_unknown_01"),
            now=NOW,
        )

    platform_key = session.get(ProtocolIdentityKey, "key_platform_01")
    assert platform_key is not None
    platform_key.status = "revoked"
    platform_key.revoked_at = NOW
    session.commit()
    with pytest.raises(ProtocolViolation, match="platform_key_inactive"):
        service.accept_operation(
            caller_credential=_caller_credential(private_keys, operation),
            envelope=operation,
            now=NOW,
        )

    assert _counts(session) == {"operations": 0, "audit": 0, "outbox": 0}


def test_service_verifies_db_registered_independent_ed25519_receipts_without_partial_writes(
    session: Session,
    session_factory: sessionmaker[Session],
    private_keys: dict[str, Ed25519PrivateKey],
    operation: OperationEnvelopeV2,
) -> None:
    service = ProtocolService(session_factory=session_factory)
    credential = _caller_credential(private_keys, operation)
    attempt = _attempt()
    manifest = _manifest()
    receipt = _receipt(private_keys, manifest)

    service.accept_operation(caller_credential=credential, envelope=operation, now=NOW)
    service.record_attempt(attempt=attempt, now=NOW)
    service.record_manifest(manifest=manifest, now=NOW)
    assert (
        service.record_receipt(receipt=receipt, now=NOW + timedelta(minutes=2))
        == receipt
    )

    with pytest.raises(ProtocolViolation, match="verifier_key_mismatch"):
        service.record_receipt(
            receipt=_receipt(private_keys, manifest, key_id="key_executor_01"),
            now=NOW + timedelta(minutes=2),
        )
    with pytest.raises(ProtocolViolation, match="invalid_receipt_signature"):
        service.record_receipt(
            receipt=replace(receipt, decision="rejected"),
            now=NOW + timedelta(minutes=2),
        )

    assert _counts(session) == {"operations": 1, "audit": 4, "outbox": 2}


def test_service_rejects_shared_executor_verifier_public_key_without_receipt_write(
    session: Session,
    session_factory: sessionmaker[Session],
    private_keys: dict[str, Ed25519PrivateKey],
    operation: OperationEnvelopeV2,
) -> None:
    service = ProtocolService(session_factory=session_factory)
    manifest = _manifest()
    service.accept_operation(
        caller_credential=_caller_credential(private_keys, operation),
        envelope=operation,
        now=NOW,
    )
    service.record_attempt(attempt=_attempt(), now=NOW)
    service.record_manifest(manifest=manifest, now=NOW)

    session.add(
        ProtocolIdentityKey(
            key_id="key_verifier_shared_01",
            identity_id="ver_verifier_01",
            algorithm="ed25519-v1",
            public_key_material=encode_ed25519_public_key(
                private_keys["exec_executor_01"].public_key()
            ),
            status="active",
            registered_at=NOW - timedelta(minutes=1),
            revoked_at=None,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    assert _counts(session) == {"operations": 1, "audit": 3, "outbox": 1}


def test_service_rejects_invalid_verifier_registry_states_without_receipt_write(
    session: Session,
    session_factory: sessionmaker[Session],
    private_keys: dict[str, Ed25519PrivateKey],
    operation: OperationEnvelopeV2,
) -> None:
    service = ProtocolService(session_factory=session_factory)
    manifest = _manifest()
    service.accept_operation(
        caller_credential=_caller_credential(private_keys, operation),
        envelope=operation,
        now=NOW,
    )
    service.record_attempt(attempt=_attempt(), now=NOW)
    service.record_manifest(manifest=manifest, now=NOW)

    wrong_role_key = Ed25519PrivateKey.generate()
    session.add(
        ProtocolIdentity(
            identity_id="ver_wrong_role_01",
            principal_id="prn_wrong_role_01",
            role="executor",
            release="rel_wrong_role_01",
            registered_at=NOW - timedelta(minutes=1),
        )
    )
    session.add(
        ProtocolIdentityKey(
            key_id="key_wrong_role_01",
            identity_id="ver_wrong_role_01",
            algorithm="ed25519-v1",
            public_key_material=encode_ed25519_public_key(wrong_role_key.public_key()),
            status="active",
            registered_at=NOW - timedelta(minutes=1),
            revoked_at=None,
        )
    )
    session.commit()
    with pytest.raises(ProtocolViolation, match="unregistered_verifier_identity"):
        service.record_receipt(
            receipt=_receipt(
                private_keys,
                manifest,
                verifier_id="ver_wrong_role_01",
                verifier_release="rel_wrong_role_01",
                key_id="key_wrong_role_01",
                signing_key=wrong_role_key,
            ),
            now=NOW + timedelta(minutes=2),
        )
    with pytest.raises(ProtocolViolation, match="verifier_key_mismatch"):
        service.record_receipt(
            receipt=_receipt(
                private_keys,
                manifest,
                key_id="key_verifier_unknown_01",
                signing_key=private_keys["ver_verifier_01"],
            ),
            now=NOW + timedelta(minutes=2),
        )
    with pytest.raises(IntegrityError), session.begin_nested():
        session.execute(
            sa.update(ProtocolIdentityKey)
            .where(ProtocolIdentityKey.key_id == "key_verifier_01")
            .values(
                public_key_material=encode_ed25519_public_key(
                    private_keys["exec_executor_01"].public_key()
                )
            )
        )

    verifier_key = session.get(ProtocolIdentityKey, "key_verifier_01")
    assert verifier_key is not None
    verifier_key.status = "revoked"
    verifier_key.revoked_at = NOW
    session.commit()
    with pytest.raises(ProtocolViolation, match="verifier_key_inactive"):
        service.record_receipt(
            receipt=_receipt(private_keys, manifest),
            now=NOW + timedelta(minutes=2),
        )

    assert _counts(session) == {"operations": 1, "audit": 3, "outbox": 1}

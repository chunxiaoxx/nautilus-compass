from __future__ import annotations

import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import sqlalchemy as sa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine, select
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
from platform_protocol.keys import (
    encode_ed25519_public_key,
    encode_ed25519_signature,
    verify_ed25519_v1,
)
from platform_protocol.migrations import (
    PLATFORM_MIGRATION_HEAD,
    downgrade_platform_database,
    upgrade_platform_database,
)
from platform_protocol.models import (
    PLATFORM_PROTOCOL_TABLES,
    ProtocolAttempt,
    ProtocolAuditEvent,
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
from platform_protocol.service import ProtocolService

NOW = datetime(2026, 8, 4, 20, 0, tzinfo=timezone.utc)
EVIDENCE_PATH = (
    Path(__file__).parents[4]
    / "docs"
    / "plans"
    / "2026-08-04-platform-protocol-v2-vertical-slice-evidence.md"
)
EXPECTED_ROW_COUNTS = {
    "identities": 4,
    "identity_keys": 4,
    "operations": 1,
    "attempts": 1,
    "manifests": 1,
    "receipts": 1,
    "audit": 4,
    "outbox": 2,
}
PERSISTED_COLUMN_ALLOWLIST = {
    "protocol_identities": {
        "identity_id",
        "principal_id",
        "role",
        "release",
        "registered_at",
    },
    "protocol_identity_keys": {
        "key_id",
        "identity_id",
        "algorithm",
        "public_key_material",
        "status",
        "registered_at",
        "revoked_at",
    },
    "protocol_operations": {
        "operation_id",
        "caller_id",
        "caller_release",
        "caller_key_id",
        "caller_credential_version",
        "caller_credential_hash",
        "source_ref_hash",
        "source_version",
        "operation_kind",
        "policy_version",
        "idempotency_key",
        "expires_at",
        "platform_identity_id",
        "platform_release",
        "platform_key_id",
        "platform_signature",
        "state",
        "accepted_at",
    },
    "protocol_attempts": {
        "attempt_id",
        "operation_id",
        "executor_id",
        "executor_release",
        "lease_expires_at",
        "tool_policy_hash",
        "input_ref_hash",
        "execution_grant_hash",
    },
    "protocol_executor_evidence": {
        "evidence_hash",
        "evidence_version",
        "operation_id",
        "attempt_id",
        "input_ref_hash",
        "executor_id",
        "executor_release",
        "executor_key_id",
        "bound_capsule_hash",
        "fixture_hash",
        "tool_policy_hash",
        "artifact_hash",
        "result_state",
        "produced_at",
        "signature_algorithm",
        "executor_signature",
    },
    "protocol_manifests": {
        "manifest_hash",
        "operation_id",
        "attempt_id",
        "executor_id",
        "executor_release",
        "received_at",
    },
    "protocol_receipts": {
        "operation_id",
        "attempt_id",
        "manifest_hash",
        "verifier_id",
        "verifier_release",
        "policy_version",
        "decision",
        "decision_vocabulary_version",
        "reason_codes",
        "reason_code_vocabulary_version",
        "issued_at",
        "key_id",
        "signature",
    },
    "protocol_outbox": {
        "outbox_id",
        "operation_id",
        "event_type",
        "event_hash",
        "state",
        "created_at",
        "delivered_at",
        "claim_token_hash",
        "claim_expires_at",
    },
    "protocol_audit_events": {
        "audit_event_id",
        "operation_id",
        "event_type",
        "event_hash",
        "occurred_at",
    },
}


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
        "caller": Ed25519PrivateKey.generate(),
        "platform": Ed25519PrivateKey.generate(),
        "executor": Ed25519PrivateKey.generate(),
        "verifier": Ed25519PrivateKey.generate(),
    }
    public_key_materials = {
        role: encode_ed25519_public_key(private_key.public_key())
        for role, private_key in keys.items()
    }
    assert public_key_materials["executor"] != public_key_materials["verifier"]
    registrations = (
        (
            "svc_vertical_caller_01",
            "prn_vertical_caller_01",
            "caller",
            "rel_vertical_caller_01",
            "key_vertical_caller_01",
        ),
        (
            "plt_vertical_platform_01",
            "prn_vertical_platform_01",
            "platform",
            "rel_vertical_platform_01",
            "key_vertical_platform_01",
        ),
        (
            "exec_vertical_executor_01",
            "prn_vertical_executor_01",
            "executor",
            "rel_vertical_executor_01",
            "key_vertical_executor_01",
        ),
        (
            "ver_vertical_verifier_01",
            "prn_vertical_verifier_01",
            "verifier",
            "rel_vertical_verifier_01",
            "key_vertical_verifier_01",
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
                public_key_material=public_key_materials[role],
                status="active",
                registered_at=NOW - timedelta(minutes=1),
                revoked_at=None,
            )
        )
    session.commit()
    return keys


def test_deterministic_non_business_vertical_slice_replays_without_row_growth(
    session: Session,
    session_factory: sessionmaker[Session],
    private_keys: dict[str, Ed25519PrivateKey],
) -> None:
    assert EVIDENCE_PATH.is_file()
    assert (
        session.execute(
            sa.text("SELECT version_num FROM platform_schema_version")
        ).scalar_one()
        == PLATFORM_MIGRATION_HEAD
    )
    service = ProtocolService(session_factory=session_factory)
    request = OperationRequestV2(
        source_ref_hash="a" * 64,
        source_version="srcv_vertical_01",
        operation_kind="bounded_execution",
        policy_version="pol_vertical_01",
        idempotency_key="idem_vertical_01",
        expires_at=NOW + timedelta(minutes=15),
    )
    envelope = _envelope(private_keys, request)
    credential = _caller_credential(private_keys, envelope)
    attempt = ExecutionAttemptV2(
        operation_id=envelope.operation_id,
        attempt_id="att_vertical_01",
        executor_id="exec_vertical_executor_01",
        executor_release="rel_vertical_executor_01",
        lease_expires_at=NOW + timedelta(minutes=5),
        tool_policy_hash="b" * 64,
        input_ref_hash="c" * 64,
    )
    manifest = ManifestV2(
        operation_id=envelope.operation_id,
        attempt_id=attempt.attempt_id,
        executor_id=attempt.executor_id,
        executor_release=attempt.executor_release,
        artifacts=(
            ArtifactV2(
                artifact_id="art_vertical_01",
                media_type="application/json",
                sha256="d" * 64,
                byte_size=17,
                storage_ref="vault://artifact/vertical_item_01",
            ),
        ),
    )
    receipt = _receipt(private_keys, manifest)

    assert request.canonical_request_hash == envelope.canonical_request_hash
    assert credential.request_hash == request.canonical_request_hash
    assert verify_ed25519_v1(
        encode_ed25519_public_key(private_keys["verifier"].public_key()),
        receipt.canonical_signing_bytes,
        receipt.signature,
    )
    assert (
        service.accept_operation(
            caller_credential=credential,
            envelope=envelope,
            now=NOW,
        )
        == envelope
    )
    assert service.record_attempt(attempt=attempt, now=NOW) == attempt
    assert service.record_manifest(manifest=manifest, now=NOW) == manifest
    assert (
        service.record_receipt(receipt=receipt, now=NOW + timedelta(minutes=2))
        == receipt
    )

    claim = service.claim_next_outbox(
        now=NOW + timedelta(minutes=2), lease=timedelta(minutes=1)
    )
    assert claim is not None
    acknowledgement = service.ack_outbox(
        outbox_id=claim.outbox_id,
        event_hash=claim.event_hash,
        claim_token=claim.claim_token,
        now=NOW + timedelta(minutes=2),
    )
    assert acknowledgement.state == "delivered"
    assert (
        service.ack_outbox(
            outbox_id=claim.outbox_id,
            event_hash=claim.event_hash,
            claim_token=claim.claim_token,
            now=NOW + timedelta(minutes=2),
        )
        == acknowledgement
    )

    assert _row_counts(session) == EXPECTED_ROW_COUNTS
    assert _outbox_state_counts(session) == {"delivered": 1, "pending": 1}
    assert (
        service.accept_operation(
            caller_credential=credential,
            envelope=envelope,
            now=NOW + timedelta(minutes=3),
        )
        == envelope
    )
    assert (
        service.record_attempt(attempt=attempt, now=NOW + timedelta(minutes=3))
        == attempt
    )
    assert (
        service.record_manifest(manifest=manifest, now=NOW + timedelta(minutes=3))
        == manifest
    )
    assert (
        service.record_receipt(receipt=receipt, now=NOW + timedelta(minutes=3))
        == receipt
    )

    changed_request = replace(request, source_ref_hash="e" * 64)
    changed_envelope = _envelope(private_keys, changed_request)
    with pytest.raises(ProtocolViolation, match="idempotency_payload_conflict"):
        service.accept_operation(
            caller_credential=_caller_credential(private_keys, changed_envelope),
            envelope=changed_envelope,
            now=NOW + timedelta(minutes=3),
        )
    changed_receipt = _signed_receipt(
        private_keys["verifier"],
        replace(receipt, decision="rejected"),
    )
    with pytest.raises(ProtocolViolation, match="receipt_binding_conflict"):
        service.record_receipt(receipt=changed_receipt, now=NOW + timedelta(minutes=3))

    assert _row_counts(session) == EXPECTED_ROW_COUNTS
    assert _outbox_state_counts(session) == {"delivered": 1, "pending": 1}
    _assert_only_protocol_metadata_is_persisted(
        session,
        credential,
        envelope,
        receipt,
        claim,
    )


def _envelope(
    private_keys: dict[str, Ed25519PrivateKey], request: OperationRequestV2
) -> OperationEnvelopeV2:
    return create_operation_envelope(
        authenticated_caller="svc_vertical_caller_01",
        operation_id="op_vertical_01",
        request=request,
        platform_identity=RegisteredIdentityV2(
            identity_id="plt_vertical_platform_01",
            principal_id="prn_vertical_platform_01",
            release="rel_vertical_platform_01",
            key_id="key_vertical_platform_01",
            role="platform",
        ),
        signature_signer=lambda _key_id, payload: encode_ed25519_signature(
            private_keys["platform"].sign(payload)
        ),
    )


def _caller_credential(
    private_keys: dict[str, Ed25519PrivateKey], envelope: OperationEnvelopeV2
) -> CallerCredentialV2:
    unsigned = CallerCredentialV2(
        credential_version=CALLER_CREDENTIAL_VERSION_V2,
        audience=CALLER_CREDENTIAL_AUDIENCE_V2,
        caller_id="svc_vertical_caller_01",
        caller_release="rel_vertical_caller_01",
        key_id="key_vertical_caller_01",
        request_hash=envelope.canonical_request_hash,
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        signature="sig_0000000000000000",
    )
    return replace(
        unsigned,
        signature=encode_ed25519_signature(
            private_keys["caller"].sign(unsigned.canonical_signing_bytes)
        ),
    )


def _receipt(
    private_keys: dict[str, Ed25519PrivateKey], manifest: ManifestV2
) -> IndependentReceiptV2:
    unsigned = IndependentReceiptV2(
        operation_id=manifest.operation_id,
        attempt_id=manifest.attempt_id,
        manifest_hash=manifest.manifest_hash,
        verifier_id="ver_vertical_verifier_01",
        verifier_release="rel_vertical_verifier_01",
        policy_version="pol_vertical_01",
        decision="accepted",
        decision_vocabulary_version="protocol-v2-decisions-v1",
        reason_codes=("policy_satisfied",),
        reason_code_vocabulary_version="protocol-v2-reason-codes-v1",
        issued_at=NOW + timedelta(minutes=1),
        key_id="key_vertical_verifier_01",
        signature="sig_0000000000000000",
    )
    return _signed_receipt(private_keys["verifier"], unsigned)


def _signed_receipt(
    private_key: Ed25519PrivateKey, receipt: IndependentReceiptV2
) -> IndependentReceiptV2:
    return replace(
        receipt,
        signature=encode_ed25519_signature(
            private_key.sign(receipt.canonical_signing_bytes)
        ),
    )


def _row_counts(session: Session) -> dict[str, int]:
    models = {
        "identities": ProtocolIdentity,
        "identity_keys": ProtocolIdentityKey,
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


def _outbox_state_counts(session: Session) -> dict[str, int]:
    rows = session.execute(
        select(ProtocolOutbox.state, sa.func.count()).group_by(ProtocolOutbox.state)
    ).all()
    return {state: count for state, count in rows}


def _assert_only_protocol_metadata_is_persisted(
    session: Session,
    credential: CallerCredentialV2,
    envelope: OperationEnvelopeV2,
    receipt: IndependentReceiptV2,
    claim: object,
) -> None:
    inspector = sa.inspect(session.get_bind())
    assert set(inspector.get_table_names()) == {
        "platform_schema_version",
        *PLATFORM_PROTOCOL_TABLES,
    }
    protocol_columns = {
        table_name: {column["name"] for column in inspector.get_columns(table_name)}
        for table_name in PLATFORM_PROTOCOL_TABLES
    }
    assert protocol_columns == PERSISTED_COLUMN_ALLOWLIST
    all_protocol_columns = set().union(*protocol_columns.values())
    assert {
        "raw_evidence",
        "dialogue",
        "path",
        "account_id",
        "private_key",
        "private_key_material",
        "caller_credential",
        "caller_credential_signature",
    }.isdisjoint(all_protocol_columns)
    assert {"storage_ref", "artifacts"}.isdisjoint(
        protocol_columns["protocol_manifests"]
    )
    assert "platform_signature" in protocol_columns["protocol_operations"]
    assert "signature" in protocol_columns["protocol_receipts"]
    assert "executor_signature" in protocol_columns["protocol_executor_evidence"]
    assert "public_key_material" in protocol_columns["protocol_identity_keys"]
    assert "caller_credential_hash" in protocol_columns["protocol_operations"]
    assert "manifest_hash" in protocol_columns["protocol_manifests"]
    assert "event_hash" in protocol_columns["protocol_outbox"]
    assert "event_hash" in protocol_columns["protocol_audit_events"]
    stored_operation = session.get(ProtocolOperation, "op_vertical_01")
    assert stored_operation is not None
    assert stored_operation.caller_credential_version == credential.credential_version
    assert stored_operation.caller_key_id == credential.key_id
    assert stored_operation.caller_credential_hash == credential.credential_hash
    assert stored_operation.caller_credential_hash != credential.signature
    assert stored_operation.platform_signature == envelope.platform_signature
    stored_receipt = session.scalar(select(ProtocolReceipt))
    assert stored_receipt is not None
    assert stored_receipt.signature == receipt.signature
    stored_claim = session.get(ProtocolOutbox, claim.outbox_id)
    assert stored_claim is not None
    assert stored_claim.claim_token_hash != claim.claim_token


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

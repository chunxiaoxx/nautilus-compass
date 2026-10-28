from __future__ import annotations

import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from platform_protocol.contracts import OperationRequestV2, ProtocolViolation
from platform_protocol.keys import encode_ed25519_public_key, encode_ed25519_signature
from platform_protocol.migrations import (
    downgrade_platform_database,
    upgrade_platform_database,
)
from platform_protocol.models import ProtocolIdentity, ProtocolIdentityKey
from platform_protocol.registry import (
    CALLER_CREDENTIAL_AUDIENCE_V2,
    CALLER_CREDENTIAL_VERSION_V2,
    CallerCredentialV2,
    DatabaseIdentityRegistryV2,
)

NOW = datetime(2026, 8, 4, 17, 0, tzinfo=timezone.utc)


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
        current.execute(
            sa.text(
                "TRUNCATE TABLE protocol_audit_events, protocol_outbox, protocol_receipts, "
                "protocol_executor_evidence, protocol_manifests, protocol_attempts, "
                "protocol_operations, "
                "protocol_identity_keys, protocol_identities"
            )
        )
        current.commit()
        yield current
        current.execute(
            sa.text(
                "TRUNCATE TABLE protocol_audit_events, protocol_outbox, protocol_receipts, "
                "protocol_executor_evidence, protocol_manifests, protocol_attempts, "
                "protocol_operations, "
                "protocol_identity_keys, protocol_identities"
            )
        )
        current.commit()


@pytest.fixture
def caller_private_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


@pytest.fixture
def caller_request() -> OperationRequestV2:
    return OperationRequestV2(
        source_ref_hash="a" * 64,
        source_version="srcv_source_01",
        operation_kind="bounded_execution",
        policy_version="pol_policy_01",
        idempotency_key="idem_request_01",
        expires_at=NOW + timedelta(minutes=15),
    )


@pytest.fixture
def registry(
    session: Session, caller_private_key: Ed25519PrivateKey
) -> DatabaseIdentityRegistryV2:
    session.add(
        ProtocolIdentity(
            identity_id="svc_caller_01",
            principal_id="prn_caller_01",
            role="caller",
            release="rel_caller_01",
            registered_at=NOW - timedelta(minutes=1),
        )
    )
    session.add(
        ProtocolIdentityKey(
            key_id="key_caller_01",
            identity_id="svc_caller_01",
            algorithm="ed25519-v1",
            public_key_material=encode_ed25519_public_key(
                caller_private_key.public_key()
            ),
            status="active",
            registered_at=NOW - timedelta(minutes=1),
            revoked_at=None,
        )
    )
    session.commit()
    return DatabaseIdentityRegistryV2(session)


def _credential(
    private_key: Ed25519PrivateKey,
    request: OperationRequestV2,
    **changes: object,
) -> CallerCredentialV2:
    unsigned = CallerCredentialV2(
        credential_version=CALLER_CREDENTIAL_VERSION_V2,
        audience=CALLER_CREDENTIAL_AUDIENCE_V2,
        caller_id="svc_caller_01",
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
            private_key.sign(unsigned.canonical_signing_bytes)
        ),
    )


def test_database_registry_verifies_active_caller_credential_against_request_hash(
    registry: DatabaseIdentityRegistryV2,
    caller_private_key: Ed25519PrivateKey,
    caller_request: OperationRequestV2,
) -> None:
    credential = _credential(caller_private_key, caller_request)

    snapshot = registry.verify_caller_credential(
        credential=credential,
        request_hash=caller_request.canonical_request_hash,
        now=NOW,
    )

    assert snapshot.identity_id == "svc_caller_01"
    assert snapshot.release == "rel_caller_01"
    assert snapshot.role == "caller"
    assert snapshot.key_id == "key_caller_01"


@pytest.mark.parametrize(
    ("changes", "expected_code"),
    (
        ({"audience": "other-audience"}, "caller_credential_audience_mismatch"),
        (
            {"credential_version": "caller-credential-v1"},
            "caller_credential_version_mismatch",
        ),
        ({"expires_at": NOW}, "caller_credential_expired"),
    ),
)
def test_database_registry_fails_closed_for_invalid_caller_credential_metadata(
    registry: DatabaseIdentityRegistryV2,
    caller_private_key: Ed25519PrivateKey,
    caller_request: OperationRequestV2,
    changes: dict[str, object],
    expected_code: str,
) -> None:
    credential = _credential(caller_private_key, caller_request, **changes)

    with pytest.raises(ProtocolViolation, match=expected_code):
        registry.verify_caller_credential(
            credential=credential,
            request_hash=caller_request.canonical_request_hash,
            now=NOW,
        )


def test_database_registry_rejects_request_hash_replay_mismatch_and_revoked_key(
    registry: DatabaseIdentityRegistryV2,
    session: Session,
    caller_private_key: Ed25519PrivateKey,
    caller_request: OperationRequestV2,
) -> None:
    credential = _credential(caller_private_key, caller_request)
    changed_request = replace(caller_request, idempotency_key="idem_request_02")

    with pytest.raises(ProtocolViolation, match="caller_credential_request_mismatch"):
        registry.verify_caller_credential(
            credential=credential,
            request_hash=changed_request.canonical_request_hash,
            now=NOW,
        )

    key = session.get(ProtocolIdentityKey, "key_caller_01")
    assert key is not None
    key.status = "revoked"
    key.revoked_at = NOW
    session.commit()

    with pytest.raises(ProtocolViolation, match="caller_key_inactive"):
        registry.verify_caller_credential(
            credential=credential,
            request_hash=caller_request.canonical_request_hash,
            now=NOW,
        )

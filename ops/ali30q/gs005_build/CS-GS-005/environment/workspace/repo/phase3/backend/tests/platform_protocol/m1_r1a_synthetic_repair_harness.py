"""Test-only end-to-end harness for the bounded R1a synthetic repair."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import sys
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from platform_protocol.contracts import (
    ArtifactV2,
    ExecutionAttemptV2,
    ManifestV2,
    OperationRequestV2,
    RegisteredIdentityV2,
)
from platform_protocol.keys import (
    encode_ed25519_public_key,
    encode_ed25519_signature,
)
from platform_protocol.m1_r1a_ephemeral_key_admission import (
    PlatformAnnounceChallengeV1,
    create_platform_announce_challenge,
)
from platform_protocol.m1_r1a_execution_evidence import (
    ExecutorExecutionEvidenceV1,
    parse_executor_execution_evidence_bytes,
)
from platform_protocol.m1_r1a_routing import (
    R1A_CAPABILITY,
    R1A_EXECUTOR_ID,
    R1A_EXECUTOR_KEY_ID,
    R1A_EXECUTOR_RELEASE,
    R1A_POLICY_VERSION,
    R1A_TOOL_POLICY_HASH,
    R1aExecutorCandidateV1,
)
from platform_protocol.m1_r1a_runtime_admission import LocalR1aRuntimeSourceReadback
from platform_protocol.migrations import (
    PLATFORM_VERSION_TABLE,
    downgrade_platform_database,
    upgrade_platform_database,
)
from platform_protocol.models import (
    PLATFORM_PROTOCOL_TABLES,
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
from platform_protocol.service import ProtocolService
from tests.platform_protocol.m1_r1a_synthetic_repair_verifier import (
    FIXED_FIXTURE_BYTES,
    FIXED_PATCH_BYTES,
    REQUIRED_SCOPE_EVIDENCE,
    TestOnlyProtectedArtifactStore,
    create_manifest_read_grant,
    verify_and_sign_receipt,
)

_V5_EXECUTOR_COMMIT = "f3d94d32fce6316e84628c63754468ba608a1595"
_RUNTIME_EVIDENCE_PATH = "phase3/backend/docs/evidence/m1-r1a-runtime-admission-v1.json"
_BOUND_CAPSULE_HASH = "1387d4d12edddbe2a8b83e54160ac864760d33d8b9372010976df1279a5f53d0"
_OPAQUE_INPUT_ID = "in_r1a_integer_clamp_v1"
_DERIVATION_VERSION = "m1-attempt-input-hmac-v1"
_EXECUTION_REQUEST_VERSION = "m1-r1a-ephemeral-sign-request-v3"
_EXECUTION_RESULT_VERSION = "m1-r1a-ephemeral-sign-result-v3"
_OPERATION_ID = "op_r1a_vertical_01"
_ATTEMPT_ID = "att_r1a_vertical_01"
_CALLER_ID = "svc_r1a_caller_01"
_CALLER_RELEASE = "rel_r1a_caller_01"
_CALLER_KEY_ID = "key_r1a_caller_01"
_PLATFORM_ID = "plt_r1a_platform_01"
_PLATFORM_RELEASE = "rel_r1a_platform_01"
_PLATFORM_KEY_ID = "key_r1a_platform_01"
_VERIFIER_ID = "ver_r1a_verifier_01"
_VERIFIER_RELEASE = "rel_r1a_verifier_01"
_VERIFIER_KEY_ID = "key_r1a_verifier_01"

_RESULT_FIELDS = frozenset(
    {
        "artifact_b64",
        "artifact_hash",
        "execution_evidence_b64",
        "execution_evidence_hash",
        "platform_challenge_hash",
        "result_state",
        "schema_version",
        "scope_evidence_mode",
        "scope_evidence_ids",
        "session_nonce",
    }
)


@dataclass(frozen=True, slots=True)
class R1aSyntheticRepairResult:
    source_admission_status: str
    protocol_row_counts: dict[str, int]
    attempt_claim_count: int
    audit_event_types: tuple[str, ...]
    outbox_event_types: tuple[str, ...]
    outbox_state_counts: dict[str, int]
    receipt_decision: str
    receipt_reason_codes: tuple[str, ...]
    operation_state: str
    executor_principal: str
    verifier_principal: str
    executor_release: str
    verifier_release: str
    executor_public_key: str
    verifier_public_key: str
    network_delivery_count: int
    separate_database_readback: bool
    temporary_fixture_removed: bool
    executor_result_state: str
    repair_completed: bool


def run_positive_chain(
    *,
    database_url: str,
    platform_root: Path,
    v5_authority_root: Path,
    v5_executor_root: Path,
    compass_authority_root: Path,
) -> R1aSyntheticRepairResult:
    """Run the completed no-business-data chain."""
    return _run_chain(
        database_url=database_url,
        platform_root=platform_root,
        v5_authority_root=v5_authority_root,
        v5_executor_root=v5_executor_root,
        compass_authority_root=compass_authority_root,
        scope_evidence_mode="complete",
    )


def run_review_required_chain(
    *,
    database_url: str,
    platform_root: Path,
    v5_authority_root: Path,
    v5_executor_root: Path,
    compass_authority_root: Path,
) -> R1aSyntheticRepairResult:
    """Run the same chain with integrity-only evidence and honest review state."""
    return _run_chain(
        database_url=database_url,
        platform_root=platform_root,
        v5_authority_root=v5_authority_root,
        v5_executor_root=v5_executor_root,
        compass_authority_root=compass_authority_root,
        scope_evidence_mode="missing_scope",
    )


def _run_chain(
    *,
    database_url: str,
    platform_root: Path,
    v5_authority_root: Path,
    v5_executor_root: Path,
    compass_authority_root: Path,
    scope_evidence_mode: str,
) -> R1aSyntheticRepairResult:
    """Run one exact no-business-data chain and return redacted read-back facts."""
    _require_explicit_database(database_url)
    _require_clean_commit(v5_executor_root, _V5_EXECUTOR_COMMIT)
    platform_root = platform_root.resolve()
    source_readback = LocalR1aRuntimeSourceReadback(
        platform=platform_root,
        v5=v5_authority_root.resolve(),
        compass=compass_authority_root.resolve(),
    )
    admission_bytes = (platform_root / _RUNTIME_EVIDENCE_PATH).read_bytes()
    _require_empty_protocol_database(database_url)

    migrated = False
    engine = None
    signer_process: subprocess.Popen[bytes] | None = None
    try:
        upgrade_platform_database()
        migrated = True
        engine = create_engine(database_url)
        factory = sessionmaker(engine, expire_on_commit=False)

        started_at = datetime.now(UTC)
        challenge = create_platform_announce_challenge(
            session_nonce="nonce_" + secrets.token_hex(32),
            issued_at=started_at - timedelta(seconds=3),
            expires_at=started_at + timedelta(seconds=110),
            now=started_at,
        )
        signer_process = _start_signer(v5_executor_root)
        _send_protocol_line(signer_process, challenge.canonical_bytes)
        announcement_bytes = _read_protocol_line(signer_process)

        caller_key = Ed25519PrivateKey.generate()
        platform_key = Ed25519PrivateKey.generate()
        verifier_key = Ed25519PrivateKey.generate()
        _register_non_executor_identities(
            factory,
            caller_key=caller_key,
            platform_key=platform_key,
            verifier_key=verifier_key,
            registered_at=started_at - timedelta(seconds=3),
        )
        service = ProtocolService(
            session_factory=factory,
            r1a_admission_bytes=admission_bytes,
            r1a_source_readback=source_readback,
            r1a_executor_candidates=(_executor_candidate(),),
            r1a_ephemeral_challenge=challenge,
            r1a_ephemeral_announcement_bytes=announcement_bytes,
        )
        admission = service.register_r1a_ephemeral_executor_key(now=datetime.now(UTC))

        operation_now = datetime.now(UTC)
        operation_expires_at = _parse_utc(challenge.expires_at) - timedelta(seconds=10)
        request = OperationRequestV2(
            source_ref_hash=_sha256(FIXED_FIXTURE_BYTES),
            source_version="srcv_r1a_synthetic_01",
            operation_kind="bounded_execution",
            policy_version=R1A_POLICY_VERSION,
            idempotency_key="idem_r1a_synthetic_01",
            expires_at=operation_expires_at,
        )
        credential = _caller_credential(caller_key, request, operation_now)
        operation = service.issue_and_accept_r1a_operation(
            authenticated_caller=_CALLER_ID,
            operation_id=_OPERATION_ID,
            request=request,
            platform_identity=RegisteredIdentityV2(
                identity_id=_PLATFORM_ID,
                principal_id="prn_r1a_platform_01",
                release=_PLATFORM_RELEASE,
                key_id=_PLATFORM_KEY_ID,
                role="platform",
            ),
            signature_signer=lambda _key_id, payload: encode_ed25519_signature(
                platform_key.sign(payload)
            ),
            caller_credential=credential,
            now=operation_now,
        )

        attempt_secret = secrets.token_bytes(32)
        input_ref_hash = _derive_input_ref_hash(attempt_secret)
        attempt = ExecutionAttemptV2(
            operation_id=operation.operation_id,
            attempt_id=_ATTEMPT_ID,
            executor_id=R1A_EXECUTOR_ID,
            executor_release=R1A_EXECUTOR_RELEASE,
            lease_expires_at=operation_expires_at - timedelta(seconds=5),
            tool_policy_hash=R1A_TOOL_POLICY_HASH,
            input_ref_hash=input_ref_hash,
        )
        service.claim_r1a_attempt(attempt=attempt, now=datetime.now(UTC))

        execution_request = _execution_request(
            challenge=challenge,
            attempt_secret=attempt_secret,
            input_ref_hash=input_ref_hash,
            scope_evidence_mode=scope_evidence_mode,
        )
        _send_protocol_line(signer_process, execution_request)
        execution_result_bytes = _read_protocol_line(signer_process)
        signer_process.stdin.close()
        return_code = signer_process.wait(timeout=15)
        stderr = signer_process.stderr.read()
        if return_code != 0 or stderr:
            raise AssertionError("isolated V5 signer failed")
        signer_process = None
        artifact, evidence, _scope_evidence, result_state = _parse_execution_result(
            execution_result_bytes,
            challenge=challenge,
            attempt_secret=attempt_secret,
            expected_scope_evidence_mode=scope_evidence_mode,
        )

        store = TestOnlyProtectedArtifactStore()
        storage_ref = "vault://artifact/r1a_patch_01"
        store.put(storage_ref, artifact)
        manifest = ManifestV2(
            operation_id=operation.operation_id,
            attempt_id=attempt.attempt_id,
            executor_id=attempt.executor_id,
            executor_release=attempt.executor_release,
            artifacts=(
                ArtifactV2(
                    artifact_id="art_r1a_patch_01",
                    media_type="text/x-diff",
                    sha256=_sha256(artifact),
                    byte_size=len(artifact),
                    storage_ref=storage_ref,
                ),
            ),
        )
        service.record_execution_evidence_and_manifest(
            evidence=evidence,
            manifest=manifest,
            now=datetime.now(UTC),
        )

        verification_now = datetime.now(UTC)
        grant = create_manifest_read_grant(
            operation=operation,
            attempt=attempt,
            manifest=manifest,
            verifier_id=_VERIFIER_ID,
            verifier_release=_VERIFIER_RELEASE,
            nonce="nonce_" + secrets.token_hex(32),
            issued_at=verification_now,
            expires_at=verification_now + timedelta(seconds=20),
            platform_private_key=platform_key,
        )
        with factory() as verifier_session:
            verification = verify_and_sign_receipt(
                session=verifier_session,
                store=store,
                grant=grant,
                operation=operation,
                attempt=attempt,
                manifest=manifest,
                evidence=evidence,
                verifier_id=_VERIFIER_ID,
                verifier_release=_VERIFIER_RELEASE,
                verifier_key_id=_VERIFIER_KEY_ID,
                verifier_private_key=verifier_key,
                now=verification_now,
            )
        receipt = service.record_receipt(
            receipt=verification.receipt,
            now=datetime.now(UTC),
        )
        claim = service.claim_next_outbox(
            now=datetime.now(UTC), lease=timedelta(seconds=10)
        )
        if claim is None:
            raise AssertionError("expected one local outbox claim")
        acknowledgement = service.ack_outbox(
            outbox_id=claim.outbox_id,
            event_hash=claim.event_hash,
            claim_token=claim.claim_token,
            now=datetime.now(UTC),
        )
        if acknowledgement.state != "delivered":
            raise AssertionError("local outbox acknowledgement failed")

        return _read_back(
            database_url,
            source_admission_status="admitted_for_local_r1a_synthetic_repair",
            receipt=receipt,
            temporary_fixture_removed=verification.temporary_fixture_removed,
            admitted_executor_public_key=admission.public_key_material,
            expected_result_state=result_state,
        )
    finally:
        if signer_process is not None and signer_process.poll() is None:
            signer_process.kill()
            signer_process.wait(timeout=15)
        if engine is not None:
            engine.dispose()
        if migrated:
            _truncate_protocol_tables(database_url)
            downgrade_platform_database()


def _require_explicit_database(database_url: str) -> None:
    if os.environ.get("NAUTILUS_PLATFORM_DATABASE_URL") != database_url:
        raise AssertionError(
            "database URL must be explicitly provided by the test process"
        )


def _require_empty_protocol_database(database_url: str) -> None:
    engine = create_engine(database_url)
    try:
        tables = set(sa.inspect(engine).get_table_names(schema="public"))
    finally:
        engine.dispose()
    if not tables <= {PLATFORM_VERSION_TABLE}:
        raise AssertionError("R1a test database must contain no protocol tables")


def _truncate_protocol_tables(database_url: str) -> None:
    engine = create_engine(database_url)
    try:
        existing = set(sa.inspect(engine).get_table_names(schema="public"))
        protocol_tables = sorted(existing.intersection(PLATFORM_PROTOCOL_TABLES))
        if protocol_tables:
            with engine.begin() as connection:
                connection.execute(
                    sa.text(f"TRUNCATE TABLE {', '.join(protocol_tables)}")
                )
    finally:
        engine.dispose()


def _require_clean_commit(root: Path, expected_commit: str) -> None:
    root = root.resolve()
    head = _git(root, "rev-parse", "HEAD").strip()
    status = _git(root, "status", "--porcelain")
    if head != expected_commit or status:
        raise AssertionError("V5 executor root must be the exact clean owner commit")


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        check=False,
        timeout=15,
    )
    if completed.returncode != 0 or completed.stderr:
        raise AssertionError("Git source read-back failed")
    return completed.stdout.decode("utf-8")


def _start_signer(root: Path) -> subprocess.Popen[bytes]:
    environment = {
        key: os.environ[key]
        for key in ("COMSPEC", "PATH", "PATHEXT", "SYSTEMROOT", "TEMP", "TMP", "WINDIR")
        if key in os.environ
    }
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
    process = subprocess.Popen(
        [sys.executable, "-m", "nautilus_v5_ephemeral_signer"],
        cwd=root,
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.stdin is None or process.stdout is None or process.stderr is None:
        process.kill()
        raise AssertionError("isolated V5 signer pipes unavailable")
    return process


def _send_protocol_line(process: subprocess.Popen[bytes], data: bytes) -> None:
    if process.stdin is None:
        raise AssertionError("isolated V5 signer stdin unavailable")
    process.stdin.write(data + b"\n")
    process.stdin.flush()


def _read_protocol_line(process: subprocess.Popen[bytes]) -> bytes:
    if process.stdout is None:
        raise AssertionError("isolated V5 signer stdout unavailable")
    line = process.stdout.readline()
    if not line or not line.endswith(b"\n") or line.endswith(b"\r\n"):
        raise AssertionError("isolated V5 signer returned a noncanonical line")
    return line.removesuffix(b"\n")


def _register_non_executor_identities(
    factory: sessionmaker[Session],
    *,
    caller_key: Ed25519PrivateKey,
    platform_key: Ed25519PrivateKey,
    verifier_key: Ed25519PrivateKey,
    registered_at: datetime,
) -> None:
    registrations = (
        (
            _CALLER_ID,
            "prn_r1a_caller_01",
            "caller",
            _CALLER_RELEASE,
            _CALLER_KEY_ID,
            caller_key,
        ),
        (
            _PLATFORM_ID,
            "prn_r1a_platform_01",
            "platform",
            _PLATFORM_RELEASE,
            _PLATFORM_KEY_ID,
            platform_key,
        ),
        (
            _VERIFIER_ID,
            "prn_r1a_verifier_01",
            "verifier",
            _VERIFIER_RELEASE,
            _VERIFIER_KEY_ID,
            verifier_key,
        ),
    )
    with factory.begin() as session:
        for (
            identity_id,
            principal_id,
            role,
            release,
            key_id,
            private_key,
        ) in registrations:
            session.add(
                ProtocolIdentity(
                    identity_id=identity_id,
                    principal_id=principal_id,
                    role=role,
                    release=release,
                    registered_at=registered_at,
                )
            )
            session.add(
                ProtocolIdentityKey(
                    key_id=key_id,
                    identity_id=identity_id,
                    algorithm="ed25519-v1",
                    public_key_material=encode_ed25519_public_key(
                        private_key.public_key()
                    ),
                    status="active",
                    registered_at=registered_at,
                    revoked_at=None,
                )
            )


def _executor_candidate() -> R1aExecutorCandidateV1:
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


def _caller_credential(
    private_key: Ed25519PrivateKey,
    request: OperationRequestV2,
    now: datetime,
) -> CallerCredentialV2:
    unsigned = CallerCredentialV2(
        credential_version=CALLER_CREDENTIAL_VERSION_V2,
        audience=CALLER_CREDENTIAL_AUDIENCE_V2,
        caller_id=_CALLER_ID,
        caller_release=_CALLER_RELEASE,
        key_id=_CALLER_KEY_ID,
        request_hash=request.canonical_request_hash,
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(seconds=60),
        signature="sig_" + "A" * 86,
    )
    return replace(
        unsigned,
        signature=encode_ed25519_signature(
            private_key.sign(unsigned.canonical_signing_bytes)
        ),
    )


def _derive_input_ref_hash(attempt_secret: bytes) -> str:
    payload = _canonical_bytes(
        {
            "attempt_id": _ATTEMPT_ID,
            "bound_capsule_hash": _BOUND_CAPSULE_HASH,
            "derivation_version": _DERIVATION_VERSION,
            "opaque_input_id": _OPAQUE_INPUT_ID,
        }
    )
    return hmac.new(attempt_secret, payload, hashlib.sha256).hexdigest()


def _execution_request(
    *,
    challenge: PlatformAnnounceChallengeV1,
    attempt_secret: bytes,
    input_ref_hash: str,
    scope_evidence_mode: str,
) -> bytes:
    return _canonical_bytes(
        {
            "artifact_hash": _sha256(FIXED_PATCH_BYTES),
            "attempt_id": _ATTEMPT_ID,
            "attempt_secret_hex": attempt_secret.hex(),
            "bound_capsule_hash": _BOUND_CAPSULE_HASH,
            "capability": R1A_CAPABILITY,
            "executor_id": R1A_EXECUTOR_ID,
            "executor_key_id": R1A_EXECUTOR_KEY_ID,
            "executor_release": R1A_EXECUTOR_RELEASE,
            "fixture_hash": _sha256(FIXED_FIXTURE_BYTES),
            "input_ref_hash": input_ref_hash,
            "opaque_input_id": _OPAQUE_INPUT_ID,
            "operation_id": _OPERATION_ID,
            "platform_challenge_hash": challenge.challenge_hash,
            "schema_version": _EXECUTION_REQUEST_VERSION,
            "scope_evidence_mode": scope_evidence_mode,
            "session_nonce": challenge.session_nonce,
            "signature_algorithm": "ed25519-v1",
            "tool_policy_hash": R1A_TOOL_POLICY_HASH,
        }
    )


def _parse_execution_result(
    data: bytes,
    *,
    challenge: PlatformAnnounceChallengeV1,
    attempt_secret: bytes,
    expected_scope_evidence_mode: str,
) -> tuple[bytes, ExecutorExecutionEvidenceV1, tuple[str, ...], str]:
    document = _parse_json_object(data)
    if frozenset(document) != _RESULT_FIELDS:
        raise AssertionError("unexpected V5 execution result fields")
    if (
        document["schema_version"] != _EXECUTION_RESULT_VERSION
        or document["session_nonce"] != challenge.session_nonce
        or document["platform_challenge_hash"] != challenge.challenge_hash
    ):
        raise AssertionError("V5 execution result challenge mismatch")
    artifact = _decode_b64(document["artifact_b64"])
    evidence_bytes = _decode_b64(document["execution_evidence_b64"])
    if (
        artifact != FIXED_PATCH_BYTES
        or document["artifact_hash"] != _sha256(artifact)
        or document["execution_evidence_hash"] != _sha256(evidence_bytes)
        or attempt_secret.hex().encode("ascii") in data
    ):
        raise AssertionError("V5 execution result integrity mismatch")
    expected_outcomes = {
        "complete": (REQUIRED_SCOPE_EVIDENCE, "completed"),
        "missing_scope": (("integrity:fixed-patch-sha256",), "review_required"),
    }
    try:
        expected_scope_evidence, expected_result_state = expected_outcomes[
            expected_scope_evidence_mode
        ]
    except KeyError as error:
        raise AssertionError("invalid requested scope evidence mode") from error
    scope_evidence = tuple(document["scope_evidence_ids"])
    evidence = parse_executor_execution_evidence_bytes(evidence_bytes)
    if (
        document["scope_evidence_mode"] != expected_scope_evidence_mode
        or document["result_state"] != expected_result_state
        or scope_evidence != expected_scope_evidence
        or evidence.result_state != expected_result_state
    ):
        raise AssertionError("V5 execution result scope outcome mismatch")
    return (
        artifact,
        evidence,
        scope_evidence,
        expected_result_state,
    )


def _parse_json_object(data: bytes) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise AssertionError("duplicate V5 execution result field")
            result[key] = value
        return result

    try:
        document = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AssertionError("invalid V5 execution result JSON") from error
    if not isinstance(document, dict) or _canonical_bytes(document) != data:
        raise AssertionError("noncanonical V5 execution result")
    return document


def _decode_b64(value: object) -> bytes:
    if not isinstance(value, str):
        raise TypeError("invalid V5 execution result encoding")
    try:
        decoded = base64.b64decode(value, validate=True)
    except ValueError as error:
        raise AssertionError("invalid V5 execution result encoding") from error
    if base64.b64encode(decoded).decode("ascii") != value:
        raise AssertionError("noncanonical V5 execution result encoding")
    return decoded


def _canonical_bytes(value: dict[str, object]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
    except ValueError as error:
        raise AssertionError("invalid challenge timestamp") from error
    if parsed.strftime("%Y-%m-%dT%H:%M:%S.%fZ") != value:
        raise AssertionError("noncanonical challenge timestamp")
    return parsed


def _read_back(
    database_url: str,
    *,
    source_admission_status: str,
    receipt: Any,
    temporary_fixture_removed: bool,
    admitted_executor_public_key: str,
    expected_result_state: str,
) -> R1aSyntheticRepairResult:
    readback_engine = create_engine(database_url)
    try:
        with Session(readback_engine) as session:
            models = {
                "operations": ProtocolOperation,
                "attempts": ProtocolAttempt,
                "executor_evidence": ProtocolExecutorEvidence,
                "manifests": ProtocolManifest,
                "receipts": ProtocolReceipt,
                "audit_events": ProtocolAuditEvent,
                "outbox_events": ProtocolOutbox,
            }
            counts = {
                name: session.scalar(select(sa.func.count()).select_from(model)) or 0
                for name, model in models.items()
            }
            audit_types = tuple(
                session.scalars(
                    select(ProtocolAuditEvent.event_type).order_by(
                        ProtocolAuditEvent.occurred_at,
                        ProtocolAuditEvent.audit_event_id,
                    )
                )
            )
            outbox_types = tuple(
                session.scalars(
                    select(ProtocolOutbox.event_type).order_by(
                        ProtocolOutbox.created_at,
                        ProtocolOutbox.outbox_id,
                    )
                )
            )
            outbox_states = {
                state: count
                for state, count in session.execute(
                    select(ProtocolOutbox.state, sa.func.count()).group_by(
                        ProtocolOutbox.state
                    )
                )
            }
            operation = session.get(ProtocolOperation, _OPERATION_ID)
            executor = session.get(ProtocolIdentity, R1A_EXECUTOR_ID)
            verifier = session.get(ProtocolIdentity, _VERIFIER_ID)
            verifier_key = session.get(ProtocolIdentityKey, _VERIFIER_KEY_ID)
            persisted_evidence = session.scalar(
                select(ProtocolExecutorEvidence).where(
                    ProtocolExecutorEvidence.operation_id == _OPERATION_ID,
                    ProtocolExecutorEvidence.attempt_id == _ATTEMPT_ID,
                )
            )
            if (
                operation is None
                or executor is None
                or verifier is None
                or verifier_key is None
                or persisted_evidence is None
                or persisted_evidence.result_state != expected_result_state
            ):
                raise AssertionError("separate database read-back is incomplete")
            return R1aSyntheticRepairResult(
                source_admission_status=source_admission_status,
                protocol_row_counts=counts,
                attempt_claim_count=counts["attempts"],
                audit_event_types=audit_types,
                outbox_event_types=outbox_types,
                outbox_state_counts=outbox_states,
                receipt_decision=receipt.decision,
                receipt_reason_codes=receipt.reason_codes,
                operation_state=operation.state,
                executor_principal=executor.principal_id,
                verifier_principal=verifier.principal_id,
                executor_release=executor.release,
                verifier_release=verifier.release,
                executor_public_key=admitted_executor_public_key,
                verifier_public_key=verifier_key.public_key_material,
                network_delivery_count=0,
                separate_database_readback=True,
                temporary_fixture_removed=temporary_fixture_removed,
                executor_result_state=persisted_evidence.result_state,
                repair_completed=persisted_evidence.result_state == "completed",
            )
    finally:
        readback_engine.dispose()

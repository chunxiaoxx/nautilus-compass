from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from platform_protocol.contracts import (
    ExecutionAttemptV2,
    IndependentReceiptV2,
    ManifestV2,
    OperationEnvelopeV2,
    OperationRequestV2,
    ProtocolViolation,
    RegisteredIdentityV2,
    SignatureSigner,
    assert_idempotency_replay_matches,
    create_operation_envelope,
    validate_manifest_binding,
)
from platform_protocol.m1_r1a_admission import AdmissionViolation
from platform_protocol.m1_r1a_ephemeral_key_admission import (
    PlatformAnnounceChallengeV1,
    R1aEphemeralExecutorAdmissionV1,
    admit_ephemeral_executor_announcement,
)
from platform_protocol.m1_r1a_execution_evidence import ExecutorExecutionEvidenceV1
from platform_protocol.m1_r1a_routing import (
    R1A_CAPABILITY,
    R1A_EXECUTOR_ID,
    R1A_EXECUTOR_KEY_ID,
    R1A_EXECUTOR_RELEASE,
    R1A_POLICY_VERSION,
    R1A_TOOL_POLICY_HASH,
    R1aExecutorCandidateV1,
    R1aExecutorSelectionV1,
    select_unique_executor,
)
from platform_protocol.m1_r1a_runtime_admission import (
    R1aRuntimeAdmissionDecision,
    R1aRuntimeSourceReadback,
    evaluate_r1a_runtime_admission_bytes,
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
from platform_protocol.registry import CallerCredentialV2, DatabaseIdentityRegistryV2
from platform_protocol.repository import (
    ProtocolRepository,
    execution_attempt,
    executor_execution_evidence,
    operation_envelope,
)

_R1A_BOUND_CAPSULE_HASH = (
    "1387d4d12edddbe2a8b83e54160ac864760d33d8b9372010976df1279a5f53d0"
)
_R1A_FIXTURE_HASH = "340c7baf9e908ec8349bee450e87671b963f38d52440e743d88e717948724318"
_R1A_ARTIFACT_HASH = "ca32fce8c78684df61d5fdf4e8a101615181ab39978d3c29683b37492c2ef21e"
_R1A_EXECUTOR_PRINCIPAL_ID = "prn_r1a_synthetic_01"


@dataclass(frozen=True, slots=True)
class OutboxClaimV2:
    outbox_id: str
    operation_id: str
    event_type: str
    event_hash: str
    claim_token: str
    claim_expires_at: datetime


@dataclass(frozen=True, slots=True)
class OutboxAcknowledgementV2:
    outbox_id: str
    event_hash: str
    state: str


class ProtocolService:
    """Atomic Protocol V2 commands using only DB-registered public verification keys."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        r1a_admission_bytes: bytes | None = None,
        r1a_source_readback: R1aRuntimeSourceReadback | None = None,
        r1a_executor_candidates: tuple[R1aExecutorCandidateV1, ...] = (),
        r1a_ephemeral_challenge: PlatformAnnounceChallengeV1 | None = None,
        r1a_ephemeral_announcement_bytes: bytes | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._r1a_admission_bytes = r1a_admission_bytes
        self._r1a_source_readback = r1a_source_readback
        self._r1a_executor_candidates = tuple(r1a_executor_candidates)
        self._r1a_ephemeral_challenge = r1a_ephemeral_challenge
        self._r1a_ephemeral_announcement_bytes = r1a_ephemeral_announcement_bytes

    def register_r1a_ephemeral_executor_key(
        self,
        *,
        now: datetime,
    ) -> R1aEphemeralExecutorAdmissionV1:
        """Register only the source-admitted, Platform-challenged public key."""
        admission = self._derive_r1a_ephemeral_admission(now)
        with self._session_factory.begin() as session:
            identity = session.get(ProtocolIdentity, admission.executor_id)
            if identity is None:
                session.add(
                    ProtocolIdentity(
                        identity_id=admission.executor_id,
                        principal_id=_R1A_EXECUTOR_PRINCIPAL_ID,
                        role="executor",
                        release=admission.executor_release,
                        registered_at=admission.issued_at,
                    )
                )
            elif (
                identity.principal_id != _R1A_EXECUTOR_PRINCIPAL_ID
                or identity.role != "executor"
                or identity.release != admission.executor_release
                or _utc(identity.registered_at) != admission.issued_at
            ):
                raise ProtocolViolation("r1a_ephemeral_key_registration_conflict")
            key = session.get(ProtocolIdentityKey, admission.executor_key_id)
            if key is None:
                session.add(
                    ProtocolIdentityKey(
                        key_id=admission.executor_key_id,
                        identity_id=admission.executor_id,
                        algorithm="ed25519-v1",
                        public_key_material=admission.public_key_material,
                        status="active",
                        registered_at=admission.issued_at,
                        revoked_at=None,
                    )
                )
            elif (
                key.identity_id != admission.executor_id
                or key.algorithm != "ed25519-v1"
                or key.public_key_material != admission.public_key_material
                or key.status != "active"
                or _utc(key.registered_at) != admission.issued_at
                or key.revoked_at is not None
            ):
                raise ProtocolViolation("r1a_ephemeral_key_registration_conflict")
            try:
                session.flush()
            except IntegrityError:
                raise ProtocolViolation(
                    "r1a_ephemeral_key_registration_conflict"
                ) from None
        return admission

    def accept_operation(
        self,
        *,
        caller_credential: CallerCredentialV2,
        envelope: OperationEnvelopeV2,
        now: datetime,
    ) -> OperationEnvelopeV2:
        if envelope.policy_version == R1A_POLICY_VERSION:
            raise ProtocolViolation("r1a_admission_required")
        with self._session_factory.begin() as session:
            repository = ProtocolRepository(session)
            registry = DatabaseIdentityRegistryV2(session)
            self._validate_caller_acceptance(
                registry=registry,
                caller_credential=caller_credential,
                envelope=envelope,
                now=now,
            )
            return self._store_operation(repository, envelope, caller_credential, now)

    def issue_and_accept_r1a_operation(
        self,
        *,
        authenticated_caller: str,
        operation_id: str,
        request: OperationRequestV2,
        platform_identity: RegisteredIdentityV2,
        signature_signer: SignatureSigner,
        caller_credential: CallerCredentialV2,
        now: datetime,
    ) -> OperationEnvelopeV2:
        if request.policy_version != R1A_POLICY_VERSION:
            raise ProtocolViolation("r1a_policy_required")
        selection = self._derive_r1a_selection()
        ephemeral_admission = self._derive_r1a_ephemeral_admission(now)
        if request.expires_at > ephemeral_admission.expires_at:
            raise ProtocolViolation("operation_expiry_exceeds_ephemeral_key")
        with self._session_factory.begin() as session:
            repository = ProtocolRepository(session)
            registry = DatabaseIdentityRegistryV2(session)
            self._validate_r1a_executor_registration(
                registry, selection, ephemeral_admission, now
            )
            envelope = create_operation_envelope(
                authenticated_caller=authenticated_caller,
                operation_id=operation_id,
                request=request,
                platform_identity=platform_identity,
                signature_signer=signature_signer,
            )
            self._validate_caller_acceptance(
                registry=registry,
                caller_credential=caller_credential,
                envelope=envelope,
                now=now,
            )
            return self._store_operation(repository, envelope, caller_credential, now)

    def claim_r1a_attempt(
        self,
        *,
        attempt: ExecutionAttemptV2,
        now: datetime,
    ) -> ExecutionAttemptV2:
        selection = self._derive_r1a_selection()
        ephemeral_admission = self._derive_r1a_ephemeral_admission(now)
        return self._record_attempt(
            attempt=attempt,
            now=now,
            selection=selection,
            ephemeral_admission=ephemeral_admission,
            r1a_claim_authorized=True,
        )

    def record_attempt(
        self,
        *,
        attempt: ExecutionAttemptV2,
        now: datetime,
        selection: R1aExecutorSelectionV1 | None = None,
    ) -> ExecutionAttemptV2:
        return self._record_attempt(
            attempt=attempt,
            now=now,
            selection=selection,
            ephemeral_admission=None,
            r1a_claim_authorized=False,
        )

    def _record_attempt(
        self,
        *,
        attempt: ExecutionAttemptV2,
        now: datetime,
        selection: R1aExecutorSelectionV1 | None,
        ephemeral_admission: R1aEphemeralExecutorAdmissionV1 | None,
        r1a_claim_authorized: bool,
    ) -> ExecutionAttemptV2:
        with self._session_factory.begin() as session:
            repository = ProtocolRepository(session)
            registry = DatabaseIdentityRegistryV2(session)
            operation = self._required_operation(repository, attempt.operation_id)
            envelope = operation_envelope(operation)
            if envelope.policy_version == R1A_POLICY_VERSION:
                if not r1a_claim_authorized:
                    raise ProtocolViolation("r1a_claim_required")
                self._validate_r1a_selection(
                    registry,
                    attempt,
                    selection,
                    ephemeral_admission,
                    now,
                )
            existing = repository.attempt(attempt.attempt_id)
            if existing is not None:
                return self._existing_attempt(existing, attempt)
            self._validate_attempt_binding(registry, envelope, attempt, now)
            self._require_before(now, attempt.lease_expires_at, "attempt_expired")
            self._require_state(operation, "accepted")
            row = _attempt_row(attempt)
            if not self._insert_or_replay(repository, row, attempt):
                return execution_attempt(repository.attempt(attempt.attempt_id))
            try:
                repository.transition(operation.operation_id, "accepted", "dispatched")
            except RuntimeError as error:
                if (
                    envelope.policy_version == R1A_POLICY_VERSION
                    and str(error) == "protocol_operation_transition_conflict"
                ):
                    raise ProtocolViolation("attempt_claim_conflict") from None
                raise
            self._emit(
                repository,
                operation.operation_id,
                "dispatched",
                now,
                attempt.attempt_id,
                outbox_required=envelope.policy_version == R1A_POLICY_VERSION,
            )
            return attempt

    def record_manifest(self, *, manifest: ManifestV2, now: datetime) -> ManifestV2:
        with self._session_factory.begin() as session:
            repository = ProtocolRepository(session)
            operation = self._required_operation(repository, manifest.operation_id)
            if operation.policy_version == R1A_POLICY_VERSION:
                raise ProtocolViolation("executor_evidence_required")
            existing = repository.manifest(manifest.operation_id, manifest.attempt_id)
            if existing is not None:
                return self._existing_manifest(existing, manifest)
            attempt = self._required_attempt(repository, manifest.attempt_id)
            validate_manifest_binding(
                attempt=execution_attempt(attempt), manifest=manifest
            )
            self._require_before(now, attempt.lease_expires_at, "attempt_expired")
            self._require_state(operation, "dispatched")
            row = _manifest_row(manifest, now)
            if not self._insert_or_replay(repository, row, manifest):
                return self._existing_manifest(
                    repository.manifest(manifest.operation_id, manifest.attempt_id),
                    manifest,
                )
            repository.transition(
                operation.operation_id, "dispatched", "manifest_received"
            )
            self._emit(
                repository,
                operation.operation_id,
                "manifest_received",
                now,
                manifest.attempt_id,
                manifest.manifest_hash,
            )
            return manifest

    def record_execution_evidence_and_manifest(
        self,
        *,
        evidence: ExecutorExecutionEvidenceV1,
        manifest: ManifestV2,
        now: datetime,
    ) -> tuple[ExecutorExecutionEvidenceV1, ManifestV2]:
        """Persist the one R1a executor proof and manifest as one transaction."""
        ephemeral_admission = self._derive_r1a_ephemeral_admission(now)
        with self._session_factory.begin() as session:
            repository = ProtocolRepository(session)
            registry = DatabaseIdentityRegistryV2(session)
            operation = self._required_operation(repository, evidence.operation_id)
            if operation.policy_version != R1A_POLICY_VERSION:
                raise ProtocolViolation("r1a_execution_evidence_not_allowed")
            existing_evidence = repository.executor_evidence(
                evidence.operation_id, evidence.attempt_id
            )
            existing_manifest = repository.manifest(
                manifest.operation_id, manifest.attempt_id
            )
            if existing_evidence is not None or existing_manifest is not None:
                return self._existing_execution_evidence_and_manifest(
                    existing_evidence,
                    existing_manifest,
                    evidence,
                    manifest,
                )
            attempt = self._required_attempt(repository, evidence.attempt_id)
            self._validate_r1a_execution_evidence(
                registry,
                operation,
                attempt,
                evidence,
                manifest,
                ephemeral_admission,
                now,
            )
            self._require_state(operation, "dispatched")
            try:
                with repository.session.begin_nested():
                    repository.insert_executor_evidence(
                        _executor_evidence_row(evidence)
                    )
                    repository.insert_manifest(_manifest_row(manifest, now))
            except IntegrityError:
                return self._existing_execution_evidence_and_manifest(
                    repository.executor_evidence(
                        evidence.operation_id, evidence.attempt_id
                    ),
                    repository.manifest(manifest.operation_id, manifest.attempt_id),
                    evidence,
                    manifest,
                )
            try:
                repository.transition(
                    operation.operation_id, "dispatched", "manifest_received"
                )
            except RuntimeError as error:
                if str(error) == "protocol_operation_transition_conflict":
                    raise ProtocolViolation(
                        "executor_evidence_binding_conflict"
                    ) from None
                raise
            self._emit(
                repository,
                operation.operation_id,
                "manifest_received",
                now,
                evidence.attempt_id,
                _sha256(evidence.canonical_bytes),
                manifest.manifest_hash,
            )
            return evidence, manifest

    def record_receipt(
        self, *, receipt: IndependentReceiptV2, now: datetime
    ) -> IndependentReceiptV2:
        with self._session_factory.begin() as session:
            repository = ProtocolRepository(session)
            registry = DatabaseIdentityRegistryV2(session)
            operation = self._required_operation(repository, receipt.operation_id)
            attempt = self._required_attempt(repository, receipt.attempt_id)
            manifest = self._required_manifest(
                repository, receipt.operation_id, receipt.attempt_id
            )
            self._validate_receipt(registry, operation, attempt, manifest, receipt, now)
            existing = repository.receipt(receipt.operation_id, receipt.attempt_id)
            if existing is not None:
                return self._existing_receipt(existing, receipt)
            self._require_state(operation, "manifest_received")
            row = _receipt_row(receipt)
            if not self._insert_or_replay(repository, row, receipt):
                return self._existing_receipt(
                    repository.receipt(receipt.operation_id, receipt.attempt_id),
                    receipt,
                )
            repository.transition(
                operation.operation_id, "manifest_received", "receipt_verified"
            )
            self._emit(
                repository,
                operation.operation_id,
                "receipt_verified",
                now,
                receipt.attempt_id,
                receipt.manifest_hash,
                receipt.verifier_id,
                receipt.decision,
            )
            return receipt

    def claim_next_outbox(
        self, *, now: datetime, lease: timedelta
    ) -> OutboxClaimV2 | None:
        if lease.total_seconds() <= 0:
            raise ProtocolViolation("invalid_outbox_lease")
        with self._session_factory.begin() as session:
            row = ProtocolRepository(session).next_claimable_outbox(now)
            if row is None:
                return None
            claim_token = f"clm_{secrets.token_urlsafe(32)}"
            row.claim_token_hash = _sha256(claim_token.encode("ascii"))
            row.claim_expires_at = now + lease
            row.state = "claimed"
            session.flush()
            return OutboxClaimV2(
                outbox_id=row.outbox_id,
                operation_id=row.operation_id,
                event_type=row.event_type,
                event_hash=row.event_hash,
                claim_token=claim_token,
                claim_expires_at=row.claim_expires_at,
            )

    def ack_outbox(
        self, *, outbox_id: str, event_hash: str, claim_token: str, now: datetime
    ) -> OutboxAcknowledgementV2:
        with self._session_factory.begin() as session:
            row = ProtocolRepository(session).locked_outbox(outbox_id)
            if row is None:
                raise ProtocolViolation("outbox_not_found")
            if not hmac.compare_digest(row.event_hash, event_hash):
                raise ProtocolViolation("outbox_event_hash_mismatch")
            if not _claim_matches(row.claim_token_hash, claim_token):
                raise ProtocolViolation("outbox_claim_mismatch")
            if row.state == "delivered":
                return _acknowledgement(row)
            if row.state != "claimed":
                raise ProtocolViolation("outbox_not_claimed")
            if row.claim_expires_at is None or now > row.claim_expires_at:
                raise ProtocolViolation("outbox_claim_expired")
            row.state = "delivered"
            row.delivered_at = now
            session.flush()
            return _acknowledgement(row)

    def _store_operation(
        self,
        repository: ProtocolRepository,
        envelope: OperationEnvelopeV2,
        caller_credential: CallerCredentialV2,
        now: datetime,
    ) -> OperationEnvelopeV2:
        row = _operation_row(envelope, caller_credential, now)
        try:
            with repository.session.begin_nested():
                repository.insert_operation(row)
        except IntegrityError:
            existing = repository.operation_by_idempotency(
                envelope.caller_id, envelope.idempotency_key
            )
            if existing is None:
                raise ProtocolViolation("operation_binding_conflict") from None
            return assert_idempotency_replay_matches(
                existing=operation_envelope(existing), incoming=envelope
            )
        self._emit(
            repository,
            envelope.operation_id,
            "accepted",
            now,
            envelope.idempotency_payload_hash,
        )
        return envelope

    def _insert_or_replay(
        self, repository: ProtocolRepository, row: object, incoming: object
    ) -> bool:
        try:
            with repository.session.begin_nested():
                if isinstance(row, ProtocolAttempt):
                    repository.insert_attempt(row)
                elif isinstance(row, ProtocolManifest):
                    repository.insert_manifest(row)
                elif isinstance(row, ProtocolReceipt):
                    repository.insert_receipt(row)
                else:
                    raise TypeError("unsupported_protocol_row")
            return True
        except IntegrityError:
            if isinstance(incoming, ExecutionAttemptV2):
                self._existing_attempt(
                    repository.attempt(incoming.attempt_id), incoming
                )
            elif isinstance(incoming, ManifestV2):
                self._existing_manifest(
                    repository.manifest(incoming.operation_id, incoming.attempt_id),
                    incoming,
                )
            elif isinstance(incoming, IndependentReceiptV2):
                self._existing_receipt(
                    repository.receipt(incoming.operation_id, incoming.attempt_id),
                    incoming,
                )
            else:
                raise TypeError("unsupported_protocol_input") from None
            return False

    def _validate_receipt(
        self,
        registry: DatabaseIdentityRegistryV2,
        operation: ProtocolOperation,
        attempt: ProtocolAttempt,
        manifest: ProtocolManifest,
        receipt: IndependentReceiptV2,
        now: datetime,
    ) -> None:
        envelope = operation_envelope(operation)
        persisted_attempt = execution_attempt(attempt)
        self._validate_attempt_binding(registry, envelope, persisted_attempt, now)
        self._require_receipt_binding(
            registry, envelope, persisted_attempt, manifest, receipt, now
        )
        self._require_before(now, operation.expires_at, "operation_expired")
        self._require_before(receipt.issued_at, operation.expires_at, "receipt_expired")
        self._require_before(
            receipt.issued_at,
            now + timedelta(microseconds=1),
            "receipt_issued_in_future",
        )

    def _require_receipt_binding(
        self,
        registry: DatabaseIdentityRegistryV2,
        envelope: OperationEnvelopeV2,
        attempt: ExecutionAttemptV2,
        manifest: ProtocolManifest,
        receipt: IndependentReceiptV2,
        now: datetime,
    ) -> None:
        if receipt.operation_id != envelope.operation_id:
            raise ProtocolViolation("receipt_operation_mismatch")
        if receipt.attempt_id != attempt.attempt_id:
            raise ProtocolViolation("receipt_attempt_mismatch")
        if receipt.manifest_hash != manifest.manifest_hash:
            raise ProtocolViolation("receipt_manifest_mismatch")
        if receipt.policy_version != envelope.policy_version:
            raise ProtocolViolation("receipt_policy_mismatch")
        executor = registry.resolve_active_identity(
            identity_id=attempt.executor_id,
            release=attempt.executor_release,
            role="executor",
            now=now,
        )
        verifier = registry.verify_signature(
            identity_id=receipt.verifier_id,
            release=receipt.verifier_release,
            role="verifier",
            key_id=receipt.key_id,
            payload=receipt.canonical_signing_bytes,
            signature=receipt.signature,
            now=now,
            failure_code="invalid_receipt_signature",
        )
        if (
            verifier.principal_id == executor.principal_id
            or verifier.public_key_material == executor.public_key_material
        ):
            raise ProtocolViolation("executor_verifier_conflict")

    def _existing_attempt(
        self, existing: ProtocolAttempt | None, incoming: ExecutionAttemptV2
    ) -> ExecutionAttemptV2:
        if existing is None or execution_attempt(existing) != incoming:
            raise ProtocolViolation("attempt_binding_conflict")
        return incoming

    def _existing_manifest(
        self, existing: ProtocolManifest | None, incoming: ManifestV2
    ) -> ManifestV2:
        if existing is None or existing.manifest_hash != incoming.manifest_hash:
            raise ProtocolViolation("manifest_binding_conflict")
        return incoming

    def _existing_receipt(
        self, existing: ProtocolReceipt | None, incoming: IndependentReceiptV2
    ) -> IndependentReceiptV2:
        if existing is None or not _receipt_matches(existing, incoming):
            raise ProtocolViolation("receipt_binding_conflict")
        return incoming

    def _existing_execution_evidence_and_manifest(
        self,
        existing_evidence: ProtocolExecutorEvidence | None,
        existing_manifest: ProtocolManifest | None,
        incoming_evidence: ExecutorExecutionEvidenceV1,
        incoming_manifest: ManifestV2,
    ) -> tuple[ExecutorExecutionEvidenceV1, ManifestV2]:
        if (
            existing_evidence is None
            or existing_manifest is None
            or existing_evidence.evidence_hash
            != _sha256(incoming_evidence.canonical_bytes)
            or executor_execution_evidence(existing_evidence) != incoming_evidence
            or existing_manifest.manifest_hash != incoming_manifest.manifest_hash
        ):
            raise ProtocolViolation("executor_evidence_binding_conflict")
        return incoming_evidence, incoming_manifest

    def _validate_r1a_execution_evidence(
        self,
        registry: DatabaseIdentityRegistryV2,
        operation: ProtocolOperation,
        attempt: ProtocolAttempt,
        evidence: ExecutorExecutionEvidenceV1,
        manifest: ManifestV2,
        ephemeral_admission: R1aEphemeralExecutorAdmissionV1,
        now: datetime,
    ) -> None:
        persisted_attempt = execution_attempt(attempt)
        if (
            evidence.operation_id != operation.operation_id
            or evidence.attempt_id != persisted_attempt.attempt_id
            or evidence.input_ref_hash != persisted_attempt.input_ref_hash
            or evidence.executor_id != persisted_attempt.executor_id
            or evidence.executor_release != persisted_attempt.executor_release
            or evidence.executor_id != R1A_EXECUTOR_ID
            or evidence.executor_release != R1A_EXECUTOR_RELEASE
            or evidence.executor_key_id != R1A_EXECUTOR_KEY_ID
            or evidence.bound_capsule_hash != _R1A_BOUND_CAPSULE_HASH
            or evidence.fixture_hash != _R1A_FIXTURE_HASH
            or evidence.tool_policy_hash != persisted_attempt.tool_policy_hash
            or evidence.tool_policy_hash != R1A_TOOL_POLICY_HASH
            or evidence.artifact_hash != _R1A_ARTIFACT_HASH
            or evidence.executor_id != ephemeral_admission.executor_id
            or evidence.executor_release != ephemeral_admission.executor_release
            or evidence.executor_key_id != ephemeral_admission.executor_key_id
        ):
            raise ProtocolViolation("executor_evidence_binding_mismatch")
        validate_manifest_binding(attempt=persisted_attempt, manifest=manifest)
        if (
            len(manifest.artifacts) != 1
            or manifest.artifacts[0].sha256 != evidence.artifact_hash
        ):
            raise ProtocolViolation("executor_evidence_artifact_mismatch")
        ProtocolService._require_before(
            now, attempt.lease_expires_at, "attempt_expired"
        )
        if (
            evidence.produced_at < _utc(operation.accepted_at)
            or evidence.produced_at > now
        ):
            raise ProtocolViolation("executor_evidence_produced_at_mismatch")
        ProtocolService._require_before(
            evidence.produced_at,
            attempt.lease_expires_at,
            "executor_evidence_produced_after_lease",
        )
        ProtocolService._require_before(
            now,
            ephemeral_admission.expires_at,
            "r1a_ephemeral_key_expired",
        )
        if evidence.produced_at > ephemeral_admission.expires_at:
            raise ProtocolViolation("executor_evidence_produced_after_key_expiry")
        snapshot = registry.verify_signature(
            identity_id=evidence.executor_id,
            release=evidence.executor_release,
            role="executor",
            key_id=evidence.executor_key_id,
            payload=evidence.canonical_signing_bytes,
            signature=evidence.executor_signature,
            now=now,
            failure_code="invalid_executor_evidence_signature",
        )
        if snapshot.public_key_material != ephemeral_admission.public_key_material:
            raise ProtocolViolation("invalid_executor_evidence_signature")

    def _emit(
        self,
        repository: ProtocolRepository,
        operation_id: str,
        event_type: str,
        now: datetime,
        *bindings: str,
        outbox_required: bool = False,
    ) -> None:
        event_hash = _event_hash(event_type, operation_id, *bindings)
        repository.append_audit_event(
            ProtocolAuditEvent(
                audit_event_id=_opaque_id("aud_", event_hash),
                operation_id=operation_id,
                event_type=event_type,
                event_hash=event_hash,
                occurred_at=now,
            )
        )
        if outbox_required or event_type in {"manifest_received", "receipt_verified"}:
            repository.enqueue_outbox(
                ProtocolOutbox(
                    outbox_id=_opaque_id("out_", event_hash),
                    operation_id=operation_id,
                    event_type=event_type,
                    event_hash=event_hash,
                    state="pending",
                    created_at=now,
                    delivered_at=None,
                    claim_token_hash=None,
                    claim_expires_at=None,
                )
            )

    def _required_operation(
        self, repository: ProtocolRepository, operation_id: str
    ) -> ProtocolOperation:
        operation = repository.operation(operation_id)
        if operation is None:
            raise ProtocolViolation("operation_not_found")
        return operation

    def _required_attempt(
        self, repository: ProtocolRepository, attempt_id: str
    ) -> ProtocolAttempt:
        attempt = repository.attempt(attempt_id)
        if attempt is None:
            raise ProtocolViolation("attempt_not_found")
        return attempt

    def _required_manifest(
        self, repository: ProtocolRepository, operation_id: str, attempt_id: str
    ) -> ProtocolManifest:
        manifest = repository.manifest(operation_id, attempt_id)
        if manifest is None:
            raise ProtocolViolation("manifest_not_found")
        return manifest

    @staticmethod
    def _validate_caller_acceptance(
        *,
        registry: DatabaseIdentityRegistryV2,
        caller_credential: CallerCredentialV2,
        envelope: OperationEnvelopeV2,
        now: datetime,
    ) -> None:
        caller = registry.verify_caller_credential(
            credential=caller_credential,
            request_hash=envelope.canonical_request_hash,
            now=now,
        )
        if caller.identity_id != envelope.caller_id:
            raise ProtocolViolation("caller_envelope_mismatch")
        registry.verify_signature(
            identity_id=envelope.platform_identity_id,
            release=envelope.platform_release,
            role="platform",
            key_id=envelope.platform_key_id,
            payload=envelope.canonical_issuance_bytes,
            signature=envelope.platform_signature,
            now=now,
            failure_code="invalid_platform_signature",
        )
        if now >= envelope.expires_at:
            raise ProtocolViolation("operation_expired")

    def _derive_r1a_selection(self) -> R1aExecutorSelectionV1:
        decision = self._derive_r1a_runtime_admission()
        return select_unique_executor(
            self._r1a_executor_candidates,
            capability=R1A_CAPABILITY,
            executor_release=R1A_EXECUTOR_RELEASE,
            policy_version=R1A_POLICY_VERSION,
            tool_policy_hash=R1A_TOOL_POLICY_HASH,
            owner_admission=decision,
        )

    def _derive_r1a_runtime_admission(self) -> R1aRuntimeAdmissionDecision:
        if self._r1a_admission_bytes is None or self._r1a_source_readback is None:
            raise ProtocolViolation("r1a_admission_required")
        try:
            return evaluate_r1a_runtime_admission_bytes(
                self._r1a_admission_bytes,
                source_readback=self._r1a_source_readback,
            )
        except AdmissionViolation:
            raise ProtocolViolation("r1a_admission_required") from None

    def _derive_r1a_ephemeral_admission(
        self,
        now: datetime,
    ) -> R1aEphemeralExecutorAdmissionV1:
        if (
            self._r1a_ephemeral_challenge is None
            or self._r1a_ephemeral_announcement_bytes is None
        ):
            raise ProtocolViolation("r1a_ephemeral_key_admission_required")
        return admit_ephemeral_executor_announcement(
            self._r1a_ephemeral_announcement_bytes,
            expected_challenge=self._r1a_ephemeral_challenge,
            runtime_admission=self._derive_r1a_runtime_admission(),
            now=now,
        )

    @staticmethod
    def _validate_r1a_selection(
        registry: DatabaseIdentityRegistryV2,
        attempt: ExecutionAttemptV2,
        selection: R1aExecutorSelectionV1 | None,
        ephemeral_admission: R1aEphemeralExecutorAdmissionV1 | None,
        now: datetime,
    ) -> None:
        if (
            selection is None
            or attempt.executor_id != selection.executor_id
            or attempt.executor_release != selection.executor_release
            or attempt.tool_policy_hash != selection.tool_policy_hash
            or ephemeral_admission is None
            or attempt.lease_expires_at > ephemeral_admission.expires_at
        ):
            raise ProtocolViolation("executor_selection_required")
        ProtocolService._validate_r1a_executor_registration(
            registry, selection, ephemeral_admission, now
        )

    @staticmethod
    def _validate_r1a_executor_registration(
        registry: DatabaseIdentityRegistryV2,
        selection: R1aExecutorSelectionV1,
        ephemeral_admission: R1aEphemeralExecutorAdmissionV1,
        now: datetime,
    ) -> None:
        expected = R1aExecutorSelectionV1(
            executor_id=R1A_EXECUTOR_ID,
            executor_release=R1A_EXECUTOR_RELEASE,
            executor_key_id=R1A_EXECUTOR_KEY_ID,
            capability=R1A_CAPABILITY,
            policy_version=R1A_POLICY_VERSION,
            tool_policy_hash=R1A_TOOL_POLICY_HASH,
        )
        if (
            selection != expected
            or ephemeral_admission.executor_id != selection.executor_id
            or ephemeral_admission.executor_release != selection.executor_release
            or ephemeral_admission.executor_key_id != selection.executor_key_id
            or now >= ephemeral_admission.expires_at
        ):
            raise ProtocolViolation("executor_selection_required")
        try:
            snapshot = registry.resolve_key(
                identity_id=selection.executor_id,
                release=selection.executor_release,
                role="executor",
                key_id=selection.executor_key_id,
                now=now,
            )
        except ProtocolViolation:
            raise ProtocolViolation("executor_selection_required") from None
        if snapshot.public_key_material != ephemeral_admission.public_key_material:
            raise ProtocolViolation("executor_selection_required")

    @staticmethod
    def _validate_attempt_binding(
        registry: DatabaseIdentityRegistryV2,
        envelope: OperationEnvelopeV2,
        attempt: ExecutionAttemptV2,
        now: datetime,
    ) -> None:
        if attempt.operation_id != envelope.operation_id:
            raise ProtocolViolation("attempt_operation_mismatch")
        if attempt.lease_expires_at > envelope.expires_at:
            raise ProtocolViolation("attempt_expiry_exceeds_operation")
        registry.resolve_active_identity(
            identity_id=attempt.executor_id,
            release=attempt.executor_release,
            role="executor",
            now=now,
        )

    @staticmethod
    def _require_state(operation: ProtocolOperation, expected: str) -> None:
        if operation.state != expected:
            raise ProtocolViolation("invalid_operation_transition")

    @staticmethod
    def _require_before(value: datetime, limit: datetime, code: str) -> None:
        if value >= limit:
            raise ProtocolViolation(code)


def _operation_row(
    envelope: OperationEnvelopeV2,
    caller_credential: CallerCredentialV2,
    now: datetime,
) -> ProtocolOperation:
    return ProtocolOperation(
        operation_id=envelope.operation_id,
        caller_id=envelope.caller_id,
        caller_release=caller_credential.caller_release,
        caller_key_id=caller_credential.key_id,
        caller_credential_version=caller_credential.credential_version,
        caller_credential_hash=caller_credential.credential_hash,
        source_ref_hash=envelope.source_ref_hash,
        source_version=envelope.source_version,
        operation_kind=envelope.operation_kind,
        policy_version=envelope.policy_version,
        idempotency_key=envelope.idempotency_key,
        expires_at=envelope.expires_at,
        platform_identity_id=envelope.platform_identity_id,
        platform_release=envelope.platform_release,
        platform_key_id=envelope.platform_key_id,
        platform_signature=envelope.platform_signature,
        state="accepted",
        accepted_at=now,
    )


def _attempt_row(attempt: ExecutionAttemptV2) -> ProtocolAttempt:
    return ProtocolAttempt(
        attempt_id=attempt.attempt_id,
        operation_id=attempt.operation_id,
        executor_id=attempt.executor_id,
        executor_release=attempt.executor_release,
        lease_expires_at=attempt.lease_expires_at,
        tool_policy_hash=attempt.tool_policy_hash,
        input_ref_hash=attempt.input_ref_hash,
        execution_grant_hash=attempt.execution_grant_hash,
    )


def _manifest_row(manifest: ManifestV2, now: datetime) -> ProtocolManifest:
    return ProtocolManifest(
        manifest_hash=manifest.manifest_hash,
        operation_id=manifest.operation_id,
        attempt_id=manifest.attempt_id,
        executor_id=manifest.executor_id,
        executor_release=manifest.executor_release,
        received_at=now,
    )


def _executor_evidence_row(
    evidence: ExecutorExecutionEvidenceV1,
) -> ProtocolExecutorEvidence:
    return ProtocolExecutorEvidence(
        evidence_hash=_sha256(evidence.canonical_bytes),
        evidence_version=evidence.evidence_version,
        operation_id=evidence.operation_id,
        attempt_id=evidence.attempt_id,
        input_ref_hash=evidence.input_ref_hash,
        executor_id=evidence.executor_id,
        executor_release=evidence.executor_release,
        executor_key_id=evidence.executor_key_id,
        bound_capsule_hash=evidence.bound_capsule_hash,
        fixture_hash=evidence.fixture_hash,
        tool_policy_hash=evidence.tool_policy_hash,
        artifact_hash=evidence.artifact_hash,
        result_state=evidence.result_state,
        produced_at=evidence.produced_at,
        signature_algorithm=evidence.signature_algorithm,
        executor_signature=evidence.executor_signature,
    )


def _receipt_row(receipt: IndependentReceiptV2) -> ProtocolReceipt:
    return ProtocolReceipt(
        operation_id=receipt.operation_id,
        attempt_id=receipt.attempt_id,
        manifest_hash=receipt.manifest_hash,
        verifier_id=receipt.verifier_id,
        verifier_release=receipt.verifier_release,
        policy_version=receipt.policy_version,
        decision=receipt.decision,
        decision_vocabulary_version=receipt.decision_vocabulary_version,
        reason_codes=list(receipt.reason_codes),
        reason_code_vocabulary_version=receipt.reason_code_vocabulary_version,
        issued_at=receipt.issued_at,
        key_id=receipt.key_id,
        signature=receipt.signature,
    )


def _receipt_matches(existing: ProtocolReceipt, incoming: IndependentReceiptV2) -> bool:
    return (
        existing.manifest_hash == incoming.manifest_hash
        and existing.verifier_id == incoming.verifier_id
        and existing.verifier_release == incoming.verifier_release
        and existing.policy_version == incoming.policy_version
        and existing.decision == incoming.decision
        and existing.decision_vocabulary_version == incoming.decision_vocabulary_version
        and tuple(existing.reason_codes) == incoming.reason_codes
        and existing.reason_code_vocabulary_version
        == incoming.reason_code_vocabulary_version
        and _utc(existing.issued_at) == incoming.issued_at
        and existing.key_id == incoming.key_id
        and existing.signature == incoming.signature
    )


def _event_hash(event_type: str, operation_id: str, *bindings: str) -> str:
    payload = json.dumps(
        {
            "bindings": list(bindings),
            "event_type": event_type,
            "operation_id": operation_id,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256(payload)


def _opaque_id(prefix: str, digest: str) -> str:
    return f"{prefix}{digest[:60]}"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _claim_matches(stored_hash: str | None, claim_token: str) -> bool:
    if stored_hash is None or not isinstance(claim_token, str):
        return False
    return hmac.compare_digest(stored_hash, _sha256(claim_token.encode("ascii")))


def _acknowledgement(row: ProtocolOutbox) -> OutboxAcknowledgementV2:
    return OutboxAcknowledgementV2(
        outbox_id=row.outbox_id,
        event_hash=row.event_hash,
        state=row.state,
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

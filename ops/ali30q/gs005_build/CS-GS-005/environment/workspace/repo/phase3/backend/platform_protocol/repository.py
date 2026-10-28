from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Select, select, update
from sqlalchemy.orm import Session

from platform_protocol.contracts import ExecutionAttemptV2, OperationEnvelopeV2
from platform_protocol.m1_r1a_execution_evidence import ExecutorExecutionEvidenceV1
from platform_protocol.models import (
    ProtocolAttempt,
    ProtocolAuditEvent,
    ProtocolExecutorEvidence,
    ProtocolManifest,
    ProtocolOperation,
    ProtocolOutbox,
    ProtocolReceipt,
)


class ProtocolRepository:
    """Database-only access to the isolated Protocol V2 tables."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def operation(self, operation_id: str) -> ProtocolOperation | None:
        return self.session.get(ProtocolOperation, operation_id)

    def operation_by_idempotency(
        self, caller_id: str, idempotency_key: str
    ) -> ProtocolOperation | None:
        return self.session.scalar(
            select(ProtocolOperation).where(
                ProtocolOperation.caller_id == caller_id,
                ProtocolOperation.idempotency_key == idempotency_key,
            )
        )

    def attempt(self, attempt_id: str) -> ProtocolAttempt | None:
        return self.session.get(ProtocolAttempt, attempt_id)

    def manifest(self, operation_id: str, attempt_id: str) -> ProtocolManifest | None:
        return self.session.scalar(
            select(ProtocolManifest).where(
                ProtocolManifest.operation_id == operation_id,
                ProtocolManifest.attempt_id == attempt_id,
            )
        )

    def executor_evidence(
        self, operation_id: str, attempt_id: str
    ) -> ProtocolExecutorEvidence | None:
        return self.session.scalar(
            select(ProtocolExecutorEvidence).where(
                ProtocolExecutorEvidence.operation_id == operation_id,
                ProtocolExecutorEvidence.attempt_id == attempt_id,
            )
        )

    def receipt(self, operation_id: str, attempt_id: str) -> ProtocolReceipt | None:
        return self.session.scalar(
            select(ProtocolReceipt).where(
                ProtocolReceipt.operation_id == operation_id,
                ProtocolReceipt.attempt_id == attempt_id,
            )
        )

    def locked_outbox(self, outbox_id: str) -> ProtocolOutbox | None:
        return self.session.scalar(
            select(ProtocolOutbox)
            .where(ProtocolOutbox.outbox_id == outbox_id)
            .with_for_update()
        )

    def next_claimable_outbox(self, now: datetime) -> ProtocolOutbox | None:
        statement: Select[tuple[ProtocolOutbox]] = (
            select(ProtocolOutbox)
            .where(
                (ProtocolOutbox.state == "pending")
                | (
                    (ProtocolOutbox.state == "claimed")
                    & (ProtocolOutbox.claim_expires_at <= now)
                )
            )
            .order_by(ProtocolOutbox.created_at, ProtocolOutbox.outbox_id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        return self.session.scalar(statement)

    def insert_operation(self, row: ProtocolOperation) -> None:
        self.session.add(row)
        self.session.flush()

    def insert_attempt(self, row: ProtocolAttempt) -> None:
        self.session.add(row)
        self.session.flush()

    def insert_manifest(self, row: ProtocolManifest) -> None:
        self.session.add(row)
        self.session.flush()

    def insert_executor_evidence(self, row: ProtocolExecutorEvidence) -> None:
        self.session.add(row)
        self.session.flush()

    def insert_receipt(self, row: ProtocolReceipt) -> None:
        self.session.add(row)
        self.session.flush()

    def transition(self, operation_id: str, current: str, next_state: str) -> None:
        result = self.session.execute(
            update(ProtocolOperation)
            .where(
                ProtocolOperation.operation_id == operation_id,
                ProtocolOperation.state == current,
            )
            .values(state=next_state)
        )
        if result.rowcount != 1:
            raise RuntimeError("protocol_operation_transition_conflict")

    def append_audit_event(self, row: ProtocolAuditEvent) -> None:
        self.session.add(row)
        self.session.flush()

    def enqueue_outbox(self, row: ProtocolOutbox) -> None:
        self.session.add(row)
        self.session.flush()


def operation_envelope(row: ProtocolOperation) -> OperationEnvelopeV2:
    return OperationEnvelopeV2(
        operation_id=row.operation_id,
        caller_id=row.caller_id,
        source_ref_hash=row.source_ref_hash,
        source_version=row.source_version,
        operation_kind=row.operation_kind,
        policy_version=row.policy_version,
        idempotency_key=row.idempotency_key,
        expires_at=_utc(row.expires_at),
        platform_identity_id=row.platform_identity_id,
        platform_release=row.platform_release,
        platform_key_id=row.platform_key_id,
        platform_signature=row.platform_signature,
    )


def execution_attempt(row: ProtocolAttempt) -> ExecutionAttemptV2:
    return ExecutionAttemptV2(
        operation_id=row.operation_id,
        attempt_id=row.attempt_id,
        executor_id=row.executor_id,
        executor_release=row.executor_release,
        lease_expires_at=_utc(row.lease_expires_at),
        tool_policy_hash=row.tool_policy_hash,
        input_ref_hash=row.input_ref_hash,
        execution_grant_hash=row.execution_grant_hash,
    )


def executor_execution_evidence(
    row: ProtocolExecutorEvidence,
) -> ExecutorExecutionEvidenceV1:
    return ExecutorExecutionEvidenceV1(
        evidence_version=row.evidence_version,
        operation_id=row.operation_id,
        attempt_id=row.attempt_id,
        input_ref_hash=row.input_ref_hash,
        executor_id=row.executor_id,
        executor_release=row.executor_release,
        executor_key_id=row.executor_key_id,
        bound_capsule_hash=row.bound_capsule_hash,
        fixture_hash=row.fixture_hash,
        tool_policy_hash=row.tool_policy_hash,
        artifact_hash=row.artifact_hash,
        result_state=row.result_state,
        produced_at=_utc(row.produced_at),
        signature_algorithm=row.signature_algorithm,
        executor_signature=row.executor_signature,
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

PLATFORM_PROTOCOL_TABLES = frozenset(
    {
        "protocol_identities",
        "protocol_identity_keys",
        "protocol_operations",
        "protocol_attempts",
        "protocol_executor_evidence",
        "protocol_manifests",
        "protocol_receipts",
        "protocol_outbox",
        "protocol_audit_events",
    }
)


class PlatformBase(DeclarativeBase):
    """Metadata owned only by the isolated Platform Protocol V2 database."""


class ProtocolIdentity(PlatformBase):
    __tablename__ = "protocol_identities"
    __table_args__ = (
        sa.CheckConstraint(
            "role IN ('caller', 'platform', 'executor', 'verifier')",
            name="ck_protocol_identities_role",
        ),
        sa.UniqueConstraint(
            "identity_id",
            "release",
            name="uq_protocol_identities_identity_release",
        ),
    )

    identity_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    principal_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    role: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    release: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )


class ProtocolIdentityKey(PlatformBase):
    __tablename__ = "protocol_identity_keys"
    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('active', 'revoked')",
            name="ck_protocol_identity_keys_status",
        ),
        sa.CheckConstraint(
            "algorithm = 'ed25519-v1'",
            name="ck_protocol_identity_keys_algorithm",
        ),
        sa.CheckConstraint(
            "public_key_material ~ '^ed25519-v1:[A-Za-z0-9_-]{43}$'",
            name="ck_protocol_identity_keys_public_key_material",
        ),
        sa.CheckConstraint(
            "(status = 'active' AND revoked_at IS NULL) OR "
            "(status = 'revoked' AND revoked_at IS NOT NULL)",
            name="ck_protocol_identity_keys_revocation_binding",
        ),
        sa.UniqueConstraint(
            "identity_id",
            "key_id",
            name="uq_protocol_identity_keys_identity_key",
        ),
        sa.UniqueConstraint(
            "public_key_material",
            name="uq_protocol_identity_keys_public_key_material",
        ),
    )

    key_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    identity_id: Mapped[str] = mapped_column(
        sa.ForeignKey("protocol_identities.identity_id", ondelete="RESTRICT"),
        nullable=False,
    )
    algorithm: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    public_key_material: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class ProtocolOperation(PlatformBase):
    __tablename__ = "protocol_operations"
    __table_args__ = (
        sa.CheckConstraint(
            "state IN ('accepted', 'dispatched', 'manifest_received', "
            "'receipt_verified', 'failed', 'expired')",
            name="ck_protocol_operations_state",
        ),
        sa.CheckConstraint(
            "caller_credential_version = 'caller-credential-v2'",
            name="ck_protocol_operations_caller_credential_version",
        ),
        sa.CheckConstraint(
            "caller_credential_hash ~ '^[0-9a-f]{64}$'",
            name="ck_protocol_operations_caller_credential_hash",
        ),
        sa.ForeignKeyConstraint(
            ["caller_id", "caller_release"],
            ["protocol_identities.identity_id", "protocol_identities.release"],
            name="fk_protocol_operations_caller_identity_release",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["caller_id", "caller_key_id"],
            ["protocol_identity_keys.identity_id", "protocol_identity_keys.key_id"],
            name="fk_protocol_operations_caller_identity_key",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "caller_id",
            "idempotency_key",
            name="uq_protocol_operations_caller_idempotency_key",
        ),
        sa.ForeignKeyConstraint(
            ["platform_identity_id", "platform_release"],
            ["protocol_identities.identity_id", "protocol_identities.release"],
            name="fk_protocol_operations_platform_identity_release",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["platform_identity_id", "platform_key_id"],
            ["protocol_identity_keys.identity_id", "protocol_identity_keys.key_id"],
            name="fk_protocol_operations_platform_identity_key",
            ondelete="RESTRICT",
        ),
    )

    operation_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    caller_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    caller_release: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    caller_key_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    caller_credential_version: Mapped[str] = mapped_column(
        sa.String(64), nullable=False
    )
    caller_credential_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    source_ref_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    source_version: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    operation_kind: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    policy_version: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(sa.String(66), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    platform_identity_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    platform_release: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    platform_key_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    platform_signature: Mapped[str] = mapped_column(sa.String(516), nullable=False)
    state: Mapped[str] = mapped_column(sa.String(24), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )


class ProtocolAttempt(PlatformBase):
    __tablename__ = "protocol_attempts"
    __table_args__ = (
        sa.CheckConstraint(
            "(input_ref_hash IS NOT NULL AND execution_grant_hash IS NULL) OR "
            "(input_ref_hash IS NULL AND execution_grant_hash IS NOT NULL)",
            name="ck_protocol_attempts_one_input_binding",
        ),
        sa.ForeignKeyConstraint(
            ["executor_id", "executor_release"],
            ["protocol_identities.identity_id", "protocol_identities.release"],
            name="fk_protocol_attempts_executor_identity_release",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "operation_id",
            "attempt_id",
            "executor_id",
            "executor_release",
            name="uq_protocol_attempts_contract_binding",
        ),
    )

    attempt_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    operation_id: Mapped[str] = mapped_column(
        sa.ForeignKey("protocol_operations.operation_id", ondelete="RESTRICT"),
        nullable=False,
    )
    executor_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    executor_release: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    lease_expires_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    tool_policy_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    input_ref_hash: Mapped[str | None] = mapped_column(sa.String(64))
    execution_grant_hash: Mapped[str | None] = mapped_column(sa.String(64))


class ProtocolExecutorEvidence(PlatformBase):
    __tablename__ = "protocol_executor_evidence"
    __table_args__ = (
        sa.CheckConstraint(
            "evidence_version = 'm1-r1a-executor-execution-evidence-v1'",
            name="ck_protocol_executor_evidence_version",
        ),
        sa.CheckConstraint(
            "evidence_hash ~ '^[0-9a-f]{64}$' "
            "AND input_ref_hash ~ '^[0-9a-f]{64}$' "
            "AND bound_capsule_hash ~ '^[0-9a-f]{64}$' "
            "AND fixture_hash ~ '^[0-9a-f]{64}$' "
            "AND tool_policy_hash ~ '^[0-9a-f]{64}$' "
            "AND artifact_hash ~ '^[0-9a-f]{64}$'",
            name="ck_protocol_executor_evidence_hashes",
        ),
        sa.CheckConstraint(
            "result_state IN ('completed', 'review_required')",
            name="ck_protocol_executor_evidence_result_state",
        ),
        sa.CheckConstraint(
            "signature_algorithm = 'ed25519-v1'",
            name="ck_protocol_executor_evidence_signature_algorithm",
        ),
        sa.CheckConstraint(
            "executor_signature ~ '^sig_[A-Za-z0-9_-]{86}$'",
            name="ck_protocol_executor_evidence_signature",
        ),
        sa.ForeignKeyConstraint(
            ["operation_id", "attempt_id", "executor_id", "executor_release"],
            [
                "protocol_attempts.operation_id",
                "protocol_attempts.attempt_id",
                "protocol_attempts.executor_id",
                "protocol_attempts.executor_release",
            ],
            name="fk_protocol_executor_evidence_attempt_binding",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["executor_id", "executor_key_id"],
            ["protocol_identity_keys.identity_id", "protocol_identity_keys.key_id"],
            name="fk_protocol_executor_evidence_executor_identity_key",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "operation_id",
            "attempt_id",
            name="uq_protocol_executor_evidence_operation_attempt",
        ),
    )

    evidence_hash: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    evidence_version: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    operation_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    attempt_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    input_ref_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    executor_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    executor_release: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    executor_key_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    bound_capsule_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    fixture_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    tool_policy_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    artifact_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    result_state: Mapped[str] = mapped_column(sa.String(24), nullable=False)
    produced_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    signature_algorithm: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    executor_signature: Mapped[str] = mapped_column(sa.String(516), nullable=False)


class ProtocolManifest(PlatformBase):
    __tablename__ = "protocol_manifests"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["operation_id", "attempt_id", "executor_id", "executor_release"],
            [
                "protocol_attempts.operation_id",
                "protocol_attempts.attempt_id",
                "protocol_attempts.executor_id",
                "protocol_attempts.executor_release",
            ],
            name="fk_protocol_manifests_attempt_binding",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "operation_id",
            "attempt_id",
            "manifest_hash",
            name="uq_protocol_manifests_contract_binding",
        ),
        sa.UniqueConstraint(
            "operation_id",
            "attempt_id",
            name="uq_protocol_manifests_operation_attempt",
        ),
    )

    manifest_hash: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    operation_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    attempt_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    executor_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    executor_release: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )


class ProtocolReceipt(PlatformBase):
    __tablename__ = "protocol_receipts"
    __table_args__ = (
        sa.CheckConstraint(
            "decision IN ('accepted', 'rejected', 'blocked')",
            name="ck_protocol_receipts_decision",
        ),
        sa.ForeignKeyConstraint(
            ["operation_id", "attempt_id", "manifest_hash"],
            [
                "protocol_manifests.operation_id",
                "protocol_manifests.attempt_id",
                "protocol_manifests.manifest_hash",
            ],
            name="fk_protocol_receipts_manifest_binding",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["verifier_id", "verifier_release"],
            ["protocol_identities.identity_id", "protocol_identities.release"],
            name="fk_protocol_receipts_verifier_identity_release",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["verifier_id", "key_id"],
            ["protocol_identity_keys.identity_id", "protocol_identity_keys.key_id"],
            name="fk_protocol_receipts_verifier_identity_key",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "operation_id",
            "attempt_id",
            name="uq_protocol_receipts_operation_attempt",
        ),
    )

    operation_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    manifest_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    verifier_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    verifier_release: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    policy_version: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    decision: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    decision_vocabulary_version: Mapped[str] = mapped_column(
        sa.String(64), nullable=False
    )
    reason_codes: Mapped[list[str]] = mapped_column(
        ARRAY(sa.String(32)), nullable=False
    )
    reason_code_vocabulary_version: Mapped[str] = mapped_column(
        sa.String(64), nullable=False
    )
    issued_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    key_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    signature: Mapped[str] = mapped_column(sa.String(516), nullable=False)


class ProtocolOutbox(PlatformBase):
    __tablename__ = "protocol_outbox"
    __table_args__ = (
        sa.CheckConstraint(
            "event_type IN ('dispatched', 'manifest_received', 'receipt_verified')",
            name="ck_protocol_outbox_event_type",
        ),
        sa.CheckConstraint(
            "state IN ('pending', 'claimed', 'delivered', 'failed')",
            name="ck_protocol_outbox_state",
        ),
        sa.CheckConstraint(
            "(state = 'pending' AND claim_token_hash IS NULL AND claim_expires_at IS NULL) "
            "OR (state IN ('claimed', 'delivered', 'failed') "
            "AND claim_token_hash IS NOT NULL AND claim_expires_at IS NOT NULL) "
            "OR (state IN ('delivered', 'failed'))",
            name="ck_protocol_outbox_claim_binding",
        ),
    )

    outbox_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    operation_id: Mapped[str] = mapped_column(
        sa.ForeignKey("protocol_operations.operation_id", ondelete="RESTRICT"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(sa.String(24), nullable=False)
    event_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    state: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    delivered_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    claim_token_hash: Mapped[str | None] = mapped_column(sa.String(64))
    claim_expires_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True)
    )


class ProtocolAuditEvent(PlatformBase):
    __tablename__ = "protocol_audit_events"
    __table_args__ = (
        sa.CheckConstraint(
            "event_type IN ('accepted', 'dispatched', 'manifest_received', "
            "'receipt_verified', 'failed', 'expired')",
            name="ck_protocol_audit_events_event_type",
        ),
    )

    audit_event_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    operation_id: Mapped[str] = mapped_column(
        sa.ForeignKey("protocol_operations.operation_id", ondelete="RESTRICT"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(sa.String(24), nullable=False)
    event_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )

"""Create the isolated Protocol V2 persistence schema.

Revision ID: 20260803_01_protocol_v2
Revises:
Create Date: 2026-08-03
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260803_01_protocol_v2"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "protocol_identities",
        sa.Column("identity_id", sa.String(length=64), nullable=False),
        sa.Column("principal_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("release", sa.String(length=64), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role IN ('platform', 'executor', 'verifier')",
            name="ck_protocol_identities_role",
        ),
        sa.PrimaryKeyConstraint("identity_id"),
        sa.UniqueConstraint(
            "identity_id",
            "release",
            name="uq_protocol_identities_identity_release",
        ),
    )
    op.create_table(
        "protocol_identity_keys",
        sa.Column("key_id", sa.String(length=64), nullable=False),
        sa.Column("identity_id", sa.String(length=64), nullable=False),
        sa.Column("algorithm", sa.String(length=32), nullable=False),
        sa.Column("public_key_material", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('active', 'revoked')",
            name="ck_protocol_identity_keys_status",
        ),
        sa.ForeignKeyConstraint(
            ["identity_id"],
            ["protocol_identities.identity_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("key_id"),
        sa.UniqueConstraint(
            "identity_id",
            "key_id",
            name="uq_protocol_identity_keys_identity_key",
        ),
    )
    op.create_table(
        "protocol_operations",
        sa.Column("operation_id", sa.String(length=64), nullable=False),
        sa.Column("caller_id", sa.String(length=64), nullable=False),
        sa.Column("source_ref_hash", sa.String(length=64), nullable=False),
        sa.Column("source_version", sa.String(length=64), nullable=False),
        sa.Column("operation_kind", sa.String(length=64), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=66), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("platform_identity_id", sa.String(length=64), nullable=False),
        sa.Column("platform_release", sa.String(length=64), nullable=False),
        sa.Column("platform_key_id", sa.String(length=64), nullable=False),
        sa.Column("platform_signature", sa.String(length=516), nullable=False),
        sa.Column("state", sa.String(length=24), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "state IN ('accepted', 'dispatched', 'manifest_received', "
            "'receipt_verified', 'failed', 'expired')",
            name="ck_protocol_operations_state",
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
        sa.PrimaryKeyConstraint("operation_id"),
        sa.UniqueConstraint(
            "caller_id",
            "idempotency_key",
            name="uq_protocol_operations_caller_idempotency_key",
        ),
    )
    op.create_table(
        "protocol_attempts",
        sa.Column("attempt_id", sa.String(length=64), nullable=False),
        sa.Column("operation_id", sa.String(length=64), nullable=False),
        sa.Column("executor_id", sa.String(length=64), nullable=False),
        sa.Column("executor_release", sa.String(length=64), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tool_policy_hash", sa.String(length=64), nullable=False),
        sa.Column("input_ref_hash", sa.String(length=64), nullable=True),
        sa.Column("execution_grant_hash", sa.String(length=64), nullable=True),
        sa.CheckConstraint(
            "(input_ref_hash IS NOT NULL AND execution_grant_hash IS NULL) OR "
            "(input_ref_hash IS NULL AND execution_grant_hash IS NOT NULL)",
            name="ck_protocol_attempts_one_input_binding",
        ),
        sa.ForeignKeyConstraint(
            ["operation_id"],
            ["protocol_operations.operation_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["executor_id", "executor_release"],
            ["protocol_identities.identity_id", "protocol_identities.release"],
            name="fk_protocol_attempts_executor_identity_release",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("attempt_id"),
        sa.UniqueConstraint(
            "operation_id",
            "attempt_id",
            "executor_id",
            "executor_release",
            name="uq_protocol_attempts_contract_binding",
        ),
    )
    op.create_table(
        "protocol_manifests",
        sa.Column("manifest_hash", sa.String(length=64), nullable=False),
        sa.Column("operation_id", sa.String(length=64), nullable=False),
        sa.Column("attempt_id", sa.String(length=64), nullable=False),
        sa.Column("executor_id", sa.String(length=64), nullable=False),
        sa.Column("executor_release", sa.String(length=64), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("manifest_hash"),
        sa.UniqueConstraint(
            "operation_id",
            "attempt_id",
            "manifest_hash",
            name="uq_protocol_manifests_contract_binding",
        ),
    )
    op.create_table(
        "protocol_receipts",
        sa.Column("operation_id", sa.String(length=64), nullable=False),
        sa.Column("attempt_id", sa.String(length=64), nullable=False),
        sa.Column("manifest_hash", sa.String(length=64), nullable=False),
        sa.Column("verifier_id", sa.String(length=64), nullable=False),
        sa.Column("verifier_release", sa.String(length=64), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("decision_vocabulary_version", sa.String(length=64), nullable=False),
        sa.Column(
            "reason_codes", postgresql.ARRAY(sa.String(length=32)), nullable=False
        ),
        sa.Column(
            "reason_code_vocabulary_version", sa.String(length=64), nullable=False
        ),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("key_id", sa.String(length=64), nullable=False),
        sa.Column("signature", sa.String(length=516), nullable=False),
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
        sa.PrimaryKeyConstraint("operation_id", "attempt_id", "verifier_id", "key_id"),
    )
    op.create_table(
        "protocol_outbox",
        sa.Column("outbox_id", sa.String(length=64), nullable=False),
        sa.Column("operation_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=24), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "event_type IN ('manifest_received', 'receipt_verified')",
            name="ck_protocol_outbox_event_type",
        ),
        sa.CheckConstraint(
            "state IN ('pending', 'delivered', 'failed')",
            name="ck_protocol_outbox_state",
        ),
        sa.ForeignKeyConstraint(
            ["operation_id"],
            ["protocol_operations.operation_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("outbox_id"),
    )
    op.create_table(
        "protocol_audit_events",
        sa.Column("audit_event_id", sa.String(length=64), nullable=False),
        sa.Column("operation_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=24), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('accepted', 'dispatched', 'manifest_received', "
            "'receipt_verified', 'failed', 'expired')",
            name="ck_protocol_audit_events_event_type",
        ),
        sa.ForeignKeyConstraint(
            ["operation_id"],
            ["protocol_operations.operation_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("audit_event_id"),
    )
    op.execute(
        """
        CREATE FUNCTION protocol_v2_enforce_identity_roles()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            executor_principal text;
            verifier_principal text;
        BEGIN
            IF TG_TABLE_NAME = 'protocol_identities' THEN
                IF NEW.principal_id IS DISTINCT FROM OLD.principal_id
                   OR NEW.role IS DISTINCT FROM OLD.role
                   OR NEW.release IS DISTINCT FROM OLD.release THEN
                    RAISE EXCEPTION 'protocol_identity_binding_immutable'
                    USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'protocol_operations' THEN
                PERFORM 1
                FROM protocol_identities
                WHERE identity_id = NEW.platform_identity_id
                  AND release = NEW.platform_release
                  AND role = 'platform';
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'protocol_platform_identity_role_mismatch'
                    USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'protocol_attempts' THEN
                PERFORM 1
                FROM protocol_identities
                WHERE identity_id = NEW.executor_id
                  AND release = NEW.executor_release
                  AND role = 'executor';
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'protocol_executor_identity_role_mismatch'
                    USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'protocol_receipts' THEN
                SELECT executor.principal_id, verifier.principal_id
                INTO executor_principal, verifier_principal
                FROM protocol_attempts AS attempt
                JOIN protocol_identities AS executor
                  ON executor.identity_id = attempt.executor_id
                 AND executor.release = attempt.executor_release
                JOIN protocol_identities AS verifier
                  ON verifier.identity_id = NEW.verifier_id
                 AND verifier.release = NEW.verifier_release
                 AND verifier.role = 'verifier'
                WHERE attempt.operation_id = NEW.operation_id
                  AND attempt.attempt_id = NEW.attempt_id;
                IF executor_principal IS NULL
                   OR verifier_principal IS NULL
                   OR executor_principal = verifier_principal THEN
                    RAISE EXCEPTION 'protocol_receipt_verifier_not_independent'
                    USING ERRCODE = '23514';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_protocol_identities_binding_immutable
        BEFORE UPDATE OF principal_id, role, release
        ON protocol_identities
        FOR EACH ROW EXECUTE FUNCTION protocol_v2_enforce_identity_roles();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_protocol_operations_platform_role
        BEFORE INSERT OR UPDATE OF platform_identity_id, platform_release, platform_key_id
        ON protocol_operations
        FOR EACH ROW EXECUTE FUNCTION protocol_v2_enforce_identity_roles();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_protocol_attempts_executor_role
        BEFORE INSERT OR UPDATE OF executor_id, executor_release
        ON protocol_attempts
        FOR EACH ROW EXECUTE FUNCTION protocol_v2_enforce_identity_roles();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_protocol_receipts_verifier_independence
        BEFORE INSERT OR UPDATE OF operation_id, attempt_id, verifier_id, verifier_release, key_id
        ON protocol_receipts
        FOR EACH ROW EXECUTE FUNCTION protocol_v2_enforce_identity_roles();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER trg_protocol_identities_binding_immutable ON protocol_identities"
    )
    op.execute(
        "DROP TRIGGER trg_protocol_receipts_verifier_independence ON protocol_receipts"
    )
    op.execute("DROP TRIGGER trg_protocol_attempts_executor_role ON protocol_attempts")
    op.execute(
        "DROP TRIGGER trg_protocol_operations_platform_role ON protocol_operations"
    )
    op.execute("DROP FUNCTION protocol_v2_enforce_identity_roles()")
    op.drop_table("protocol_audit_events")
    op.drop_table("protocol_outbox")
    op.drop_table("protocol_receipts")
    op.drop_table("protocol_manifests")
    op.drop_table("protocol_attempts")
    op.drop_table("protocol_operations")
    op.drop_table("protocol_identity_keys")
    op.drop_table("protocol_identities")

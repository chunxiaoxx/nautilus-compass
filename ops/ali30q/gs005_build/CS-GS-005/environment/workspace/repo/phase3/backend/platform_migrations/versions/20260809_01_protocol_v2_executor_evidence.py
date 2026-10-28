"""Add authenticated executor evidence persistence for the bounded R1a path.

Revision ID: 20260809_01_r1a_evidence
Revises: 20260804_02_protocol_v2_task4
Create Date: 2026-08-09
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260809_01_r1a_evidence"
down_revision: str | Sequence[str] | None = "20260804_02_protocol_v2_task4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_protocol_outbox_event_type", "protocol_outbox", type_="check"
    )
    op.create_check_constraint(
        "ck_protocol_outbox_event_type",
        "protocol_outbox",
        "event_type IN ('dispatched', 'manifest_received', 'receipt_verified')",
    )
    op.create_table(
        "protocol_executor_evidence",
        sa.Column("evidence_hash", sa.String(length=64), primary_key=True),
        sa.Column("evidence_version", sa.String(length=64), nullable=False),
        sa.Column("operation_id", sa.String(length=64), nullable=False),
        sa.Column("attempt_id", sa.String(length=64), nullable=False),
        sa.Column("input_ref_hash", sa.String(length=64), nullable=False),
        sa.Column("executor_id", sa.String(length=64), nullable=False),
        sa.Column("executor_release", sa.String(length=64), nullable=False),
        sa.Column("executor_key_id", sa.String(length=64), nullable=False),
        sa.Column("bound_capsule_hash", sa.String(length=64), nullable=False),
        sa.Column("fixture_hash", sa.String(length=64), nullable=False),
        sa.Column("tool_policy_hash", sa.String(length=64), nullable=False),
        sa.Column("artifact_hash", sa.String(length=64), nullable=False),
        sa.Column("result_state", sa.String(length=24), nullable=False),
        sa.Column("produced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signature_algorithm", sa.String(length=32), nullable=False),
        sa.Column("executor_signature", sa.String(length=516), nullable=False),
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
    op.execute(
        """
        CREATE TRIGGER trg_protocol_executor_evidence_immutable
        BEFORE UPDATE OR DELETE ON protocol_executor_evidence
        FOR EACH ROW EXECUTE FUNCTION protocol_v2_prevent_record_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER trg_protocol_executor_evidence_immutable "
        "ON protocol_executor_evidence"
    )
    op.drop_table("protocol_executor_evidence")
    op.drop_constraint(
        "ck_protocol_outbox_event_type", "protocol_outbox", type_="check"
    )
    op.execute("DELETE FROM protocol_outbox WHERE event_type = 'dispatched'")
    op.create_check_constraint(
        "ck_protocol_outbox_event_type",
        "protocol_outbox",
        "event_type IN ('manifest_received', 'receipt_verified')",
    )

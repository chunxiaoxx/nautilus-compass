"""Add atomic replay and outbox claim constraints for Protocol V2.

Revision ID: 20260804_01_protocol_v2_task3
Revises: 20260803_01_protocol_v2
Create Date: 2026-08-04
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260804_01_protocol_v2_task3"
down_revision: str | Sequence[str] | None = "20260803_01_protocol_v2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM protocol_manifests
                GROUP BY operation_id, attempt_id
                HAVING COUNT(*) > 1
            ) THEN
                RAISE EXCEPTION 'protocol_v2_noncanonical_manifest_history'
                USING ERRCODE = '23514';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM protocol_receipts
                GROUP BY operation_id, attempt_id
                HAVING COUNT(*) > 1
            ) THEN
                RAISE EXCEPTION 'protocol_v2_noncanonical_receipt_history'
                USING ERRCODE = '23514';
            END IF;
        END;
        $$;
        """
    )
    op.create_unique_constraint(
        "uq_protocol_manifests_operation_attempt",
        "protocol_manifests",
        ["operation_id", "attempt_id"],
    )
    op.create_unique_constraint(
        "uq_protocol_receipts_operation_attempt",
        "protocol_receipts",
        ["operation_id", "attempt_id"],
    )
    op.add_column(
        "protocol_outbox", sa.Column("claim_token_hash", sa.String(length=64))
    )
    op.add_column(
        "protocol_outbox", sa.Column("claim_expires_at", sa.DateTime(timezone=True))
    )
    op.drop_constraint("ck_protocol_outbox_state", "protocol_outbox", type_="check")
    op.create_check_constraint(
        "ck_protocol_outbox_state",
        "protocol_outbox",
        "state IN ('pending', 'claimed', 'delivered', 'failed')",
    )
    op.create_check_constraint(
        "ck_protocol_outbox_claim_binding",
        "protocol_outbox",
        "(state = 'pending' AND claim_token_hash IS NULL AND claim_expires_at IS NULL) "
        "OR (state IN ('claimed', 'delivered', 'failed') "
        "AND claim_token_hash IS NOT NULL AND claim_expires_at IS NOT NULL) "
        "OR (state IN ('delivered', 'failed'))",
    )
    op.execute(
        """
        CREATE FUNCTION protocol_v2_prevent_record_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'protocol_record_immutable'
            USING ERRCODE = '23514';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_protocol_attempts_immutable
        BEFORE UPDATE OR DELETE ON protocol_attempts
        FOR EACH ROW EXECUTE FUNCTION protocol_v2_prevent_record_mutation();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_protocol_manifests_immutable
        BEFORE UPDATE OR DELETE ON protocol_manifests
        FOR EACH ROW EXECUTE FUNCTION protocol_v2_prevent_record_mutation();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_protocol_receipts_immutable
        BEFORE UPDATE OR DELETE ON protocol_receipts
        FOR EACH ROW EXECUTE FUNCTION protocol_v2_prevent_record_mutation();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_protocol_audit_events_append_only
        BEFORE UPDATE OR DELETE ON protocol_audit_events
        FOR EACH ROW EXECUTE FUNCTION protocol_v2_prevent_record_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER trg_protocol_audit_events_append_only ON protocol_audit_events"
    )
    op.execute("DROP TRIGGER trg_protocol_receipts_immutable ON protocol_receipts")
    op.execute("DROP TRIGGER trg_protocol_manifests_immutable ON protocol_manifests")
    op.execute("DROP TRIGGER trg_protocol_attempts_immutable ON protocol_attempts")
    op.execute("DROP FUNCTION protocol_v2_prevent_record_mutation()")
    op.execute(
        "UPDATE protocol_outbox SET state = 'pending', claim_token_hash = NULL, "
        "claim_expires_at = NULL WHERE state = 'claimed'"
    )
    op.drop_constraint(
        "ck_protocol_outbox_claim_binding", "protocol_outbox", type_="check"
    )
    op.drop_constraint("ck_protocol_outbox_state", "protocol_outbox", type_="check")
    op.create_check_constraint(
        "ck_protocol_outbox_state",
        "protocol_outbox",
        "state IN ('pending', 'delivered', 'failed')",
    )
    op.drop_column("protocol_outbox", "claim_expires_at")
    op.drop_column("protocol_outbox", "claim_token_hash")
    op.drop_constraint(
        "uq_protocol_receipts_operation_attempt",
        "protocol_receipts",
        type_="unique",
    )
    op.drop_constraint(
        "uq_protocol_manifests_operation_attempt",
        "protocol_manifests",
        type_="unique",
    )

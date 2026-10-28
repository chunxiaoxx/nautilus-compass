"""Add registered caller and Ed25519 key constraints for Protocol V2.

Revision ID: 20260804_02_protocol_v2_task4
Revises: 20260804_01_protocol_v2_task3
Create Date: 2026-08-04
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260804_02_protocol_v2_task4"
down_revision: str | Sequence[str] | None = "20260804_01_protocol_v2_task3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM protocol_operations LIMIT 1) THEN
                RAISE EXCEPTION 'protocol_v2_task4_existing_operations_require_reauthorization'
                USING ERRCODE = '23514';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM protocol_identity_keys
                WHERE algorithm <> 'ed25519-v1'
                   OR public_key_material !~ '^ed25519-v1:[A-Za-z0-9_-]{43}$'
                   OR (status = 'active' AND revoked_at IS NOT NULL)
                   OR (status = 'revoked' AND revoked_at IS NULL)
            ) THEN
                RAISE EXCEPTION 'protocol_v2_task4_existing_key_registration_invalid'
                USING ERRCODE = '23514';
            END IF;
            IF EXISTS (
                SELECT public_key_material
                FROM protocol_identity_keys
                GROUP BY public_key_material
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'protocol_v2_task4_existing_key_material_ambiguous'
                USING ERRCODE = '23514';
            END IF;
        END;
        $$;
        """
    )
    op.drop_constraint(
        "ck_protocol_identities_role", "protocol_identities", type_="check"
    )
    op.create_check_constraint(
        "ck_protocol_identities_role",
        "protocol_identities",
        "role IN ('caller', 'platform', 'executor', 'verifier')",
    )
    op.create_check_constraint(
        "ck_protocol_identity_keys_algorithm",
        "protocol_identity_keys",
        "algorithm = 'ed25519-v1'",
    )
    op.create_check_constraint(
        "ck_protocol_identity_keys_public_key_material",
        "protocol_identity_keys",
        "public_key_material ~ '^ed25519-v1:[A-Za-z0-9_-]{43}$'",
    )
    op.create_check_constraint(
        "ck_protocol_identity_keys_revocation_binding",
        "protocol_identity_keys",
        "(status = 'active' AND revoked_at IS NULL) OR "
        "(status = 'revoked' AND revoked_at IS NOT NULL)",
    )
    op.create_unique_constraint(
        "uq_protocol_identity_keys_public_key_material",
        "protocol_identity_keys",
        ["public_key_material"],
    )
    op.add_column(
        "protocol_operations",
        sa.Column("caller_release", sa.String(length=64), nullable=False),
    )
    op.add_column(
        "protocol_operations",
        sa.Column("caller_key_id", sa.String(length=64), nullable=False),
    )
    op.add_column(
        "protocol_operations",
        sa.Column("caller_credential_version", sa.String(length=64), nullable=False),
    )
    op.add_column(
        "protocol_operations",
        sa.Column("caller_credential_hash", sa.String(length=64), nullable=False),
    )
    op.create_check_constraint(
        "ck_protocol_operations_caller_credential_version",
        "protocol_operations",
        "caller_credential_version = 'caller-credential-v2'",
    )
    op.create_check_constraint(
        "ck_protocol_operations_caller_credential_hash",
        "protocol_operations",
        "caller_credential_hash ~ '^[0-9a-f]{64}$'",
    )
    op.create_foreign_key(
        "fk_protocol_operations_caller_identity_release",
        "protocol_operations",
        "protocol_identities",
        ["caller_id", "caller_release"],
        ["identity_id", "release"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_protocol_operations_caller_identity_key",
        "protocol_operations",
        "protocol_identity_keys",
        ["caller_id", "caller_key_id"],
        ["identity_id", "key_id"],
        ondelete="RESTRICT",
    )
    op.execute(
        """
        CREATE FUNCTION protocol_v2_enforce_task4_identity_and_key_bindings()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF TG_TABLE_NAME = 'protocol_identities' THEN
                IF TG_OP = 'DELETE'
                   OR NEW.identity_id IS DISTINCT FROM OLD.identity_id
                   OR NEW.principal_id IS DISTINCT FROM OLD.principal_id
                   OR NEW.role IS DISTINCT FROM OLD.role
                   OR NEW.release IS DISTINCT FROM OLD.release
                   OR NEW.registered_at IS DISTINCT FROM OLD.registered_at THEN
                    RAISE EXCEPTION 'protocol_identity_registration_immutable'
                    USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'protocol_identity_keys' THEN
                IF TG_OP = 'INSERT' THEN
                    IF NEW.status <> 'active' OR NEW.revoked_at IS NOT NULL THEN
                        RAISE EXCEPTION 'protocol_identity_key_rotation_invalid'
                        USING ERRCODE = '23514';
                    END IF;
                ELSIF TG_OP = 'DELETE'
                   OR NEW.key_id IS DISTINCT FROM OLD.key_id
                   OR NEW.identity_id IS DISTINCT FROM OLD.identity_id
                   OR NEW.algorithm IS DISTINCT FROM OLD.algorithm
                   OR NEW.public_key_material IS DISTINCT FROM OLD.public_key_material
                   OR NEW.registered_at IS DISTINCT FROM OLD.registered_at
                   OR OLD.status <> 'active'
                   OR OLD.revoked_at IS NOT NULL
                   OR NEW.status <> 'revoked'
                   OR NEW.revoked_at IS NULL
                   OR NEW.revoked_at < OLD.registered_at THEN
                    RAISE EXCEPTION 'protocol_identity_key_rotation_invalid'
                    USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'protocol_operations' THEN
                PERFORM 1
                FROM protocol_identities AS identity
                JOIN protocol_identity_keys AS key
                  ON key.identity_id = identity.identity_id
                WHERE identity.identity_id = NEW.caller_id
                  AND identity.release = NEW.caller_release
                  AND identity.role = 'caller'
                  AND identity.registered_at <= NEW.accepted_at
                  AND key.key_id = NEW.caller_key_id
                  AND key.algorithm = 'ed25519-v1'
                  AND key.status = 'active'
                  AND key.revoked_at IS NULL
                  AND key.registered_at <= NEW.accepted_at;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'protocol_caller_registration_invalid'
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
        CREATE TRIGGER trg_protocol_identities_task4_immutable
        BEFORE UPDATE OR DELETE ON protocol_identities
        FOR EACH ROW EXECUTE FUNCTION protocol_v2_enforce_task4_identity_and_key_bindings();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_protocol_identity_keys_task4_rotation
        BEFORE INSERT OR UPDATE OR DELETE ON protocol_identity_keys
        FOR EACH ROW EXECUTE FUNCTION protocol_v2_enforce_task4_identity_and_key_bindings();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_protocol_operations_task4_caller_binding
        BEFORE INSERT OR UPDATE OF caller_id, caller_release, caller_key_id,
            caller_credential_version, caller_credential_hash ON protocol_operations
        FOR EACH ROW EXECUTE FUNCTION protocol_v2_enforce_task4_identity_and_key_bindings();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER trg_protocol_operations_task4_caller_binding ON protocol_operations"
    )
    op.execute(
        "DROP TRIGGER trg_protocol_identity_keys_task4_rotation ON protocol_identity_keys"
    )
    op.execute(
        "DROP TRIGGER trg_protocol_identities_task4_immutable ON protocol_identities"
    )
    op.execute("DROP FUNCTION protocol_v2_enforce_task4_identity_and_key_bindings()")
    op.drop_constraint(
        "fk_protocol_operations_caller_identity_key",
        "protocol_operations",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_protocol_operations_caller_identity_release",
        "protocol_operations",
        type_="foreignkey",
    )
    op.drop_constraint(
        "ck_protocol_operations_caller_credential_hash",
        "protocol_operations",
        type_="check",
    )
    op.drop_constraint(
        "ck_protocol_operations_caller_credential_version",
        "protocol_operations",
        type_="check",
    )
    op.drop_column("protocol_operations", "caller_credential_hash")
    op.drop_column("protocol_operations", "caller_credential_version")
    op.drop_column("protocol_operations", "caller_key_id")
    op.drop_column("protocol_operations", "caller_release")
    op.drop_constraint(
        "uq_protocol_identity_keys_public_key_material",
        "protocol_identity_keys",
        type_="unique",
    )
    op.drop_constraint(
        "ck_protocol_identity_keys_revocation_binding",
        "protocol_identity_keys",
        type_="check",
    )
    op.drop_constraint(
        "ck_protocol_identity_keys_public_key_material",
        "protocol_identity_keys",
        type_="check",
    )
    op.drop_constraint(
        "ck_protocol_identity_keys_algorithm",
        "protocol_identity_keys",
        type_="check",
    )
    op.drop_constraint(
        "ck_protocol_identities_role", "protocol_identities", type_="check"
    )
    op.create_check_constraint(
        "ck_protocol_identities_role",
        "protocol_identities",
        "role IN ('platform', 'executor', 'verifier')",
    )

from __future__ import annotations

import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from platform_protocol.database import (
    PLATFORM_DATABASE_ENV,
    PlatformDatabaseConfigurationError,
    create_platform_engine,
)
from platform_protocol.migrations import (
    PLATFORM_MIGRATION_HEAD,
    PLATFORM_MIGRATION_TABLES,
    downgrade_platform_database,
    migration_config,
    upgrade_platform_database,
)
from platform_protocol.models import PLATFORM_PROTOCOL_TABLES, PlatformBase

PLATFORM_VERSION_TABLE = "platform_schema_version"
EXPECTED_TABLES = frozenset({PLATFORM_VERSION_TABLE, *PLATFORM_PROTOCOL_TABLES})
TASK2_ROOT = Path(__file__).parents[2]
INITIAL_EXPECTED_COLUMNS = {
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
    },
    "protocol_audit_events": {
        "audit_event_id",
        "operation_id",
        "event_type",
        "event_hash",
        "occurred_at",
    },
}
EXPECTED_COLUMNS = {
    **INITIAL_EXPECTED_COLUMNS,
    "protocol_operations": {
        *INITIAL_EXPECTED_COLUMNS["protocol_operations"],
        "caller_release",
        "caller_key_id",
        "caller_credential_version",
        "caller_credential_hash",
    },
    "protocol_outbox": {
        *INITIAL_EXPECTED_COLUMNS["protocol_outbox"],
        "claim_token_hash",
        "claim_expires_at",
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
}
EXPECTED_FOREIGN_KEY_BINDINGS = {
    "protocol_identity_keys": {
        (("identity_id",), "protocol_identities", ("identity_id",)),
    },
    "protocol_operations": {
        (
            ("caller_id", "caller_release"),
            "protocol_identities",
            ("identity_id", "release"),
        ),
        (
            ("caller_id", "caller_key_id"),
            "protocol_identity_keys",
            ("identity_id", "key_id"),
        ),
        (
            ("platform_identity_id", "platform_release"),
            "protocol_identities",
            ("identity_id", "release"),
        ),
        (
            ("platform_identity_id", "platform_key_id"),
            "protocol_identity_keys",
            ("identity_id", "key_id"),
        ),
    },
    "protocol_attempts": {
        (("operation_id",), "protocol_operations", ("operation_id",)),
        (
            ("executor_id", "executor_release"),
            "protocol_identities",
            ("identity_id", "release"),
        ),
    },
    "protocol_manifests": {
        (
            ("operation_id", "attempt_id", "executor_id", "executor_release"),
            "protocol_attempts",
            ("operation_id", "attempt_id", "executor_id", "executor_release"),
        ),
    },
    "protocol_executor_evidence": {
        (
            ("operation_id", "attempt_id", "executor_id", "executor_release"),
            "protocol_attempts",
            ("operation_id", "attempt_id", "executor_id", "executor_release"),
        ),
        (
            ("executor_id", "executor_key_id"),
            "protocol_identity_keys",
            ("identity_id", "key_id"),
        ),
    },
    "protocol_receipts": {
        (
            ("operation_id", "attempt_id", "manifest_hash"),
            "protocol_manifests",
            ("operation_id", "attempt_id", "manifest_hash"),
        ),
        (
            ("verifier_id", "verifier_release"),
            "protocol_identities",
            ("identity_id", "release"),
        ),
        (
            ("verifier_id", "key_id"),
            "protocol_identity_keys",
            ("identity_id", "key_id"),
        ),
    },
    "protocol_outbox": {
        (("operation_id",), "protocol_operations", ("operation_id",)),
    },
    "protocol_audit_events": {
        (("operation_id",), "protocol_operations", ("operation_id",)),
    },
}
INITIAL_EXPECTED_FOREIGN_KEY_BINDINGS = {
    **EXPECTED_FOREIGN_KEY_BINDINGS,
    "protocol_operations": {
        (
            ("platform_identity_id", "platform_release"),
            "protocol_identities",
            ("identity_id", "release"),
        ),
        (
            ("platform_identity_id", "platform_key_id"),
            "protocol_identity_keys",
            ("identity_id", "key_id"),
        ),
    },
}
INITIAL_EXPECTED_UNIQUE_BINDINGS = {
    "protocol_identities": {
        ("identity_id", "release"),
    },
    "protocol_identity_keys": {
        ("identity_id", "key_id"),
    },
    "protocol_operations": {
        ("caller_id", "idempotency_key"),
    },
    "protocol_attempts": {
        ("operation_id", "attempt_id", "executor_id", "executor_release"),
    },
    "protocol_manifests": {
        ("operation_id", "attempt_id", "manifest_hash"),
    },
}
EXPECTED_UNIQUE_BINDINGS = {
    **INITIAL_EXPECTED_UNIQUE_BINDINGS,
    "protocol_identity_keys": {
        *INITIAL_EXPECTED_UNIQUE_BINDINGS["protocol_identity_keys"],
        ("public_key_material",),
    },
    "protocol_manifests": {
        *INITIAL_EXPECTED_UNIQUE_BINDINGS["protocol_manifests"],
        ("operation_id", "attempt_id"),
    },
    "protocol_receipts": {
        ("operation_id", "attempt_id"),
    },
    "protocol_executor_evidence": {
        ("operation_id", "attempt_id"),
    },
}
INITIAL_ENFORCEMENT_OBJECTS = {
    "protocol_v2_enforce_identity_roles",
    "trg_protocol_identities_binding_immutable",
    "trg_protocol_operations_platform_role",
    "trg_protocol_attempts_executor_role",
    "trg_protocol_receipts_verifier_independence",
}
TASK3_ENFORCEMENT_OBJECTS = {
    "protocol_v2_prevent_record_mutation",
    "trg_protocol_attempts_immutable",
    "trg_protocol_manifests_immutable",
    "trg_protocol_receipts_immutable",
    "trg_protocol_audit_events_append_only",
}
TASK4_ENFORCEMENT_OBJECTS = {
    "protocol_v2_enforce_task4_identity_and_key_bindings",
    "trg_protocol_identities_task4_immutable",
    "trg_protocol_identity_keys_task4_rotation",
    "trg_protocol_operations_task4_caller_binding",
}
R1A_TASK4_ENFORCEMENT_OBJECTS = {
    "trg_protocol_executor_evidence_immutable",
}
TASK4_OPERATION_COLUMNS = {
    "caller_release",
    "caller_key_id",
    "caller_credential_version",
    "caller_credential_hash",
}
EXPECTED_ENFORCEMENT_OBJECTS = (
    INITIAL_ENFORCEMENT_OBJECTS
    | TASK3_ENFORCEMENT_OBJECTS
    | TASK4_ENFORCEMENT_OBJECTS
    | R1A_TASK4_ENFORCEMENT_OBJECTS
)


def _foreign_key_bindings(
    table: sa.Table,
) -> set[tuple[tuple[str, ...], str, tuple[str, ...]]]:
    bindings = set()
    for constraint in table.foreign_key_constraints:
        target_fullnames = tuple(
            element.target_fullname for element in constraint.elements
        )
        target_tables = {
            target.rsplit(".", maxsplit=1)[0] for target in target_fullnames
        }
        assert len(target_tables) == 1
        bindings.add(
            (
                tuple(constraint.column_keys),
                target_tables.pop(),
                tuple(target.rsplit(".", maxsplit=1)[1] for target in target_fullnames),
            )
        )
    return bindings


def _unique_bindings(table: sa.Table) -> set[tuple[str, ...]]:
    return {
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if isinstance(constraint, sa.UniqueConstraint)
    }


def _migration_upgrade_tables(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, tuple[object, ...]], list[str]]:
    migration_path = (
        TASK2_ROOT / "platform_migrations" / "versions" / "20260803_01_protocol_v2.py"
    )
    spec = spec_from_file_location("protocol_v2_migration_for_test", migration_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    created_tables: dict[str, tuple[object, ...]] = {}
    executed_sql: list[str] = []

    class RecordingOperations:
        def create_table(self, table_name: str, *elements: object) -> None:
            created_tables[table_name] = elements

        def execute(self, sql: str) -> None:
            executed_sql.append(sql)

    monkeypatch.setattr(module, "op", RecordingOperations())
    module.upgrade()
    return created_tables, executed_sql


def _migration_foreign_key_bindings(
    elements: tuple[object, ...],
) -> set[tuple[tuple[str, ...], str, tuple[str, ...]]]:
    bindings = set()
    for element in elements:
        if not isinstance(element, sa.ForeignKeyConstraint):
            continue
        target_fullnames = tuple(
            foreign_key.target_fullname for foreign_key in element.elements
        )
        target_tables = {
            target.rsplit(".", maxsplit=1)[0] for target in target_fullnames
        }
        assert len(target_tables) == 1
        bindings.add(
            (
                tuple(element.column_keys),
                target_tables.pop(),
                tuple(target.rsplit(".", maxsplit=1)[1] for target in target_fullnames),
            )
        )
    return bindings


def _migration_unique_bindings(elements: tuple[object, ...]) -> set[tuple[str, ...]]:
    return {
        tuple(element.columns.keys() or element._pending_colargs)
        for element in elements
        if isinstance(element, sa.UniqueConstraint)
    }


def _configured_database_url() -> str:
    database_url = os.environ.get(PLATFORM_DATABASE_ENV)
    if database_url is None:
        pytest.skip(
            f"{PLATFORM_DATABASE_ENV} is required for migration integration tests"
        )
    return database_url


def _table_names(database_url: str) -> set[str]:
    engine = create_engine(database_url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def _version_rows(database_url: str) -> list[str]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            return list(
                connection.execute(
                    text("SELECT version_num FROM platform_schema_version")
                )
            )
    finally:
        engine.dispose()


def _table_columns(database_url: str, table_name: str) -> set[str]:
    engine = create_engine(database_url)
    try:
        return {column["name"] for column in inspect(engine).get_columns(table_name)}
    finally:
        engine.dispose()


def _database_foreign_key_bindings(
    database_url: str,
    table_name: str,
) -> set[tuple[tuple[str, ...], str, tuple[str, ...]]]:
    engine = create_engine(database_url)
    try:
        return {
            (
                tuple(foreign_key["constrained_columns"]),
                foreign_key["referred_table"],
                tuple(foreign_key["referred_columns"]),
            )
            for foreign_key in inspect(engine).get_foreign_keys(table_name)
        }
    finally:
        engine.dispose()


def _database_unique_bindings(
    database_url: str, table_name: str
) -> set[tuple[str, ...]]:
    engine = create_engine(database_url)
    try:
        return {
            tuple(constraint["column_names"])
            for constraint in inspect(engine).get_unique_constraints(table_name)
        }
    finally:
        engine.dispose()


def _database_role_enforcement_objects(database_url: str) -> set[str]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            return {
                row[0]
                for row in connection.execute(
                    text(
                        "SELECT proname FROM pg_proc "
                        "JOIN pg_namespace ON pg_namespace.oid = pg_proc.pronamespace "
                        "WHERE pg_namespace.nspname = current_schema() "
                        "AND proname LIKE 'protocol_v2_%' "
                        "UNION ALL "
                        "SELECT tgname FROM pg_trigger "
                        "JOIN pg_class ON pg_class.oid = pg_trigger.tgrelid "
                        "JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace "
                        "WHERE pg_namespace.nspname = current_schema() "
                        "AND NOT tgisinternal AND tgname LIKE 'trg_protocol_%'"
                    )
                )
            }
    finally:
        engine.dispose()


def _assert_database_rejects_invalid_identity_role_or_principal_binding(
    database_url: str,
) -> None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO protocol_identities "
                    "(identity_id, principal_id, role, release, registered_at) VALUES "
                    "(:caller_identity_id, :caller_principal_id, 'caller', "
                    ":caller_release, CURRENT_TIMESTAMP), "
                    "(:platform_identity_id, :platform_principal_id, 'platform', "
                    ":platform_release, CURRENT_TIMESTAMP), "
                    "(:executor_identity_id, :shared_principal_id, 'executor', "
                    ":executor_release, CURRENT_TIMESTAMP), "
                    "(:verifier_identity_id, :shared_principal_id, 'verifier', "
                    ":verifier_release, CURRENT_TIMESTAMP)"
                ),
                {
                    "caller_identity_id": "svc_caller_01",
                    "caller_principal_id": "prn_caller_01",
                    "caller_release": "rel_caller_01",
                    "platform_identity_id": "plt_identity_01",
                    "platform_principal_id": "prn_platform_01",
                    "platform_release": "rel_platform_01",
                    "executor_identity_id": "exec_identity_01",
                    "shared_principal_id": "prn_shared_01",
                    "executor_release": "rel_executor_01",
                    "verifier_identity_id": "ver_identity_01",
                    "verifier_release": "rel_verifier_01",
                },
            )
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(
                    text(
                        "UPDATE protocol_identities "
                        "SET principal_id = 'prn_rebound_01' "
                        "WHERE identity_id = 'ver_identity_01'"
                    )
                )
            connection.execute(
                text(
                    "INSERT INTO protocol_identity_keys "
                    "(key_id, identity_id, algorithm, public_key_material, status, registered_at) "
                    "VALUES "
                    "('key_caller_01', 'svc_caller_01', 'ed25519-v1', :caller_public_key_material, "
                    "'active', CURRENT_TIMESTAMP), "
                    "('key_platform_01', 'plt_identity_01', 'ed25519-v1', :platform_public_key_material, "
                    "'active', CURRENT_TIMESTAMP), "
                    "('key_executor_01', 'exec_identity_01', 'ed25519-v1', :executor_public_key_material, "
                    "'active', CURRENT_TIMESTAMP), "
                    "('key_verifier_01', 'ver_identity_01', 'ed25519-v1', :verifier_public_key_material, "
                    "'active', CURRENT_TIMESTAMP)"
                ),
                {
                    "caller_public_key_material": "ed25519-v1:" + "A" * 43,
                    "platform_public_key_material": "ed25519-v1:" + "B" * 43,
                    "executor_public_key_material": "ed25519-v1:" + "C" * 43,
                    "verifier_public_key_material": "ed25519-v1:" + "D" * 43,
                },
            )
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(
                    text(
                        "INSERT INTO protocol_identity_keys "
                        "(key_id, identity_id, algorithm, public_key_material, status, "
                        "registered_at, revoked_at) VALUES "
                        "('key_direct_revoked_01', 'ver_identity_01', 'ed25519-v1', "
                        ":public_key_material, 'revoked', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                    ),
                    {"public_key_material": "ed25519-v1:" + "E" * 43},
                )
            connection.execute(
                text(
                    "INSERT INTO protocol_operations "
                    "(operation_id, caller_id, caller_release, caller_key_id, "
                    "caller_credential_version, caller_credential_hash, source_ref_hash, "
                    "source_version, operation_kind, "
                    "policy_version, idempotency_key, expires_at, platform_identity_id, "
                    "platform_release, platform_key_id, platform_signature, state, accepted_at) "
                    "VALUES ('op_valid_01', 'svc_caller_01', 'rel_caller_01', 'key_caller_01', "
                    "'caller-credential-v2', :credential_hash, :source_ref_hash, 'srcv_source_01', "
                    "'bounded_execution', 'pol_policy_01', 'idem_key_01', CURRENT_TIMESTAMP, "
                    "'plt_identity_01', 'rel_platform_01', 'key_platform_01', :signature, "
                    "'accepted', CURRENT_TIMESTAMP)"
                ),
                {
                    "credential_hash": "0" * 64,
                    "source_ref_hash": "a" * 64,
                    "signature": "sig_" + "a" * 16,
                },
            )
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(
                    text(
                        "INSERT INTO protocol_operations "
                        "(operation_id, caller_id, caller_release, caller_key_id, "
                        "caller_credential_version, caller_credential_hash, source_ref_hash, "
                        "source_version, "
                        "operation_kind, policy_version, idempotency_key, expires_at, "
                        "platform_identity_id, platform_release, platform_key_id, "
                        "platform_signature, state, accepted_at) VALUES "
                        "('op_wrong_role_01', 'svc_caller_01', 'rel_caller_01', 'key_caller_01', "
                        "'caller-credential-v2', :credential_hash, :source_ref_hash, "
                        "'srcv_source_02', 'bounded_execution', 'pol_policy_01', "
                        "'idem_key_02', CURRENT_TIMESTAMP, 'exec_identity_01', "
                        "'rel_executor_01', 'key_executor_01', :signature, 'accepted', "
                        "CURRENT_TIMESTAMP)"
                    ),
                    {
                        "credential_hash": "1" * 64,
                        "source_ref_hash": "b" * 64,
                        "signature": "sig_" + "b" * 16,
                    },
                )
            connection.execute(
                text(
                    "INSERT INTO protocol_attempts "
                    "(attempt_id, operation_id, executor_id, executor_release, lease_expires_at, "
                    "tool_policy_hash, input_ref_hash) VALUES "
                    "('att_valid_01', 'op_valid_01', 'exec_identity_01', 'rel_executor_01', "
                    "CURRENT_TIMESTAMP, :tool_policy_hash, :input_ref_hash)"
                ),
                {"tool_policy_hash": "c" * 64, "input_ref_hash": "d" * 64},
            )
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(
                    text(
                        "UPDATE protocol_attempts SET tool_policy_hash = :tool_policy_hash "
                        "WHERE attempt_id = 'att_valid_01'"
                    ),
                    {"tool_policy_hash": "e" * 64},
                )
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(
                    text(
                        "INSERT INTO protocol_attempts "
                        "(attempt_id, operation_id, executor_id, executor_release, "
                        "lease_expires_at, tool_policy_hash, input_ref_hash) VALUES "
                        "('att_wrong_role_01', 'op_valid_01', 'plt_identity_01', "
                        "'rel_platform_01', CURRENT_TIMESTAMP, :tool_policy_hash, "
                        ":input_ref_hash)"
                    ),
                    {"tool_policy_hash": "e" * 64, "input_ref_hash": "f" * 64},
                )
            connection.execute(
                text(
                    "INSERT INTO protocol_manifests "
                    "(manifest_hash, operation_id, attempt_id, executor_id, executor_release, "
                    "received_at) VALUES (:manifest_hash, 'op_valid_01', 'att_valid_01', "
                    "'exec_identity_01', 'rel_executor_01', CURRENT_TIMESTAMP)"
                ),
                {"manifest_hash": "1" * 64},
            )
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(
                    text(
                        "UPDATE protocol_manifests SET received_at = CURRENT_TIMESTAMP "
                        "WHERE manifest_hash = :manifest_hash"
                    ),
                    {"manifest_hash": "1" * 64},
                )
            connection.execute(
                text(
                    "INSERT INTO protocol_audit_events "
                    "(audit_event_id, operation_id, event_type, event_hash, occurred_at) "
                    "VALUES ('aud_valid_01', 'op_valid_01', 'accepted', :event_hash, "
                    "CURRENT_TIMESTAMP)"
                ),
                {"event_hash": "2" * 64},
            )
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(
                    text(
                        "UPDATE protocol_audit_events SET event_hash = :event_hash "
                        "WHERE audit_event_id = 'aud_valid_01'"
                    ),
                    {"event_hash": "3" * 64},
                )
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(
                    text(
                        "INSERT INTO protocol_receipts "
                        "(operation_id, attempt_id, manifest_hash, verifier_id, "
                        "verifier_release, policy_version, decision, "
                        "decision_vocabulary_version, reason_codes, "
                        "reason_code_vocabulary_version, issued_at, key_id, signature) "
                        "VALUES ('op_valid_01', 'att_valid_01', :manifest_hash, "
                        "'ver_identity_01', 'rel_verifier_01', 'pol_policy_01', "
                        "'accepted', 'protocol-v2-decisions-v1', ARRAY['policy_satisfied'], "
                        "'protocol-v2-reason-codes-v1', CURRENT_TIMESTAMP, "
                        "'key_verifier_01', :signature)"
                    ),
                    {"manifest_hash": "1" * 64, "signature": "sig_" + "1" * 16},
                )
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(
                    text(
                        "UPDATE protocol_operations SET caller_id = 'exec_identity_01', "
                        "caller_release = 'rel_executor_01', caller_key_id = 'key_executor_01' "
                        "WHERE operation_id = 'op_valid_01'"
                    )
                )
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(
                    text(
                        "UPDATE protocol_identity_keys SET public_key_material = :public_key_material "
                        "WHERE key_id = 'key_verifier_01'"
                    ),
                    {"public_key_material": "ed25519-v1:" + "B" * 43},
                )
            connection.execute(
                text(
                    "UPDATE protocol_identity_keys SET status = 'revoked', "
                    "revoked_at = CURRENT_TIMESTAMP WHERE key_id = 'key_verifier_01'"
                )
            )
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(
                    text(
                        "UPDATE protocol_identity_keys SET status = 'active', revoked_at = NULL "
                        "WHERE key_id = 'key_verifier_01'"
                    )
                )
            connection.execute(
                text(
                    "TRUNCATE TABLE protocol_audit_events, protocol_outbox, protocol_receipts, "
                    "protocol_executor_evidence, protocol_manifests, protocol_attempts, "
                    "protocol_operations, "
                    "protocol_identity_keys, protocol_identities"
                )
            )
    finally:
        engine.dispose()


def test_missing_database_url_fails_before_engine_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from platform_protocol import database

    monkeypatch.delenv(PLATFORM_DATABASE_ENV, raising=False)
    engine_calls: list[object] = []

    def unexpected_engine(*args: object, **kwargs: object) -> object:
        engine_calls.append((args, kwargs))
        raise AssertionError("engine creation must not occur without an explicit URL")

    monkeypatch.setattr(database, "create_engine", unexpected_engine)

    with pytest.raises(PlatformDatabaseConfigurationError, match=PLATFORM_DATABASE_ENV):
        create_platform_engine()

    assert engine_calls == []


def test_platform_migration_has_exactly_one_head_and_no_legacy_metadata_imports() -> (
    None
):
    script = ScriptDirectory.from_config(migration_config())
    assert script.get_heads() == [PLATFORM_MIGRATION_HEAD]
    assert set(PlatformBase.metadata.tables) == set(PLATFORM_PROTOCOL_TABLES)
    assert set(PLATFORM_PROTOCOL_TABLES) == set(EXPECTED_COLUMNS)
    for table_name, expected_columns in EXPECTED_COLUMNS.items():
        assert (
            set(PlatformBase.metadata.tables[table_name].columns.keys())
            == expected_columns
        )

    migration_sources = (
        TASK2_ROOT / "platform_protocol" / "database.py",
        TASK2_ROOT / "platform_protocol" / "models.py",
        TASK2_ROOT / "platform_protocol" / "migrations.py",
        TASK2_ROOT / "platform_migrations" / "env.py",
        TASK2_ROOT / "platform_migrations" / "versions" / "20260803_01_protocol_v2.py",
        TASK2_ROOT
        / "platform_migrations"
        / "versions"
        / "20260804_01_protocol_v2_task3.py",
        TASK2_ROOT
        / "platform_migrations"
        / "versions"
        / "20260804_02_protocol_v2_task4.py",
        TASK2_ROOT
        / "platform_migrations"
        / "versions"
        / "20260809_01_protocol_v2_executor_evidence.py",
    )
    forbidden_fragments = (
        "utils.database",
        "models.database",
        "dotenv",
        "create_all",
        "from models import Base",
        "alembic_version",
    )

    for source_path in migration_sources:
        source = source_path.read_text(encoding="utf-8")
        assert not any(fragment in source for fragment in forbidden_fragments), (
            source_path
        )


def test_metadata_enforces_exact_contract_binding_foreign_keys() -> None:
    for table_name in PLATFORM_PROTOCOL_TABLES:
        assert _foreign_key_bindings(PlatformBase.metadata.tables[table_name]) == (
            EXPECTED_FOREIGN_KEY_BINDINGS.get(table_name, set())
        )
        assert _unique_bindings(PlatformBase.metadata.tables[table_name]) == (
            EXPECTED_UNIQUE_BINDINGS.get(table_name, set())
        )


def test_migration_upgrade_defines_exact_metadata_columns_and_binding_foreign_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_tables, executed_sql = _migration_upgrade_tables(monkeypatch)
    assert set(created_tables) == set(INITIAL_EXPECTED_COLUMNS)

    for table_name, expected_columns in INITIAL_EXPECTED_COLUMNS.items():
        elements = created_tables[table_name]
        assert {
            element.name for element in elements if isinstance(element, sa.Column)
        } == expected_columns
        assert _migration_foreign_key_bindings(
            elements
        ) == INITIAL_EXPECTED_FOREIGN_KEY_BINDINGS.get(
            table_name,
            set(),
        )
        assert _migration_unique_bindings(
            elements
        ) == INITIAL_EXPECTED_UNIQUE_BINDINGS.get(
            table_name,
            set(),
        )

    role_enforcement_sql = "\n".join(executed_sql)
    for object_name in INITIAL_ENFORCEMENT_OBJECTS:
        assert object_name in role_enforcement_sql


def test_task3_forward_migration_adds_replay_and_outbox_claim_constraints() -> None:
    script = ScriptDirectory.from_config(migration_config())
    revisions = {revision.revision: revision for revision in script.walk_revisions()}
    task3 = revisions["20260804_01_protocol_v2_task3"]

    assert task3.down_revision == "20260803_01_protocol_v2"
    assert script.get_heads() == [PLATFORM_MIGRATION_HEAD]
    assert {"claim_token_hash", "claim_expires_at"} <= set(
        PlatformBase.metadata.tables["protocol_outbox"].columns.keys()
    )
    assert ("operation_id", "attempt_id") in _unique_bindings(
        PlatformBase.metadata.tables["protocol_manifests"]
    )
    assert ("operation_id", "attempt_id") in _unique_bindings(
        PlatformBase.metadata.tables["protocol_receipts"]
    )
    source = (
        TASK2_ROOT
        / "platform_migrations"
        / "versions"
        / "20260804_01_protocol_v2_task3.py"
    ).read_text(encoding="utf-8")
    assert all(object_name in source for object_name in TASK3_ENFORCEMENT_OBJECTS)
    assert "protocol_v2_noncanonical_manifest_history" in source
    assert "protocol_v2_noncanonical_receipt_history" in source
    assert "state IN ('delivered', 'failed')" in source


def test_task4_forward_migration_adds_caller_binding_and_key_rotation_constraints() -> (
    None
):
    script = ScriptDirectory.from_config(migration_config())
    revisions = {revision.revision: revision for revision in script.walk_revisions()}
    task4 = revisions["20260804_02_protocol_v2_task4"]

    assert task4.down_revision == "20260804_01_protocol_v2_task3"
    assert script.get_heads() == [PLATFORM_MIGRATION_HEAD]
    assert TASK4_OPERATION_COLUMNS <= set(
        PlatformBase.metadata.tables["protocol_operations"].columns.keys()
    )
    assert "caller" in str(
        next(
            constraint.sqltext
            for constraint in PlatformBase.metadata.tables[
                "protocol_identities"
            ].constraints
            if isinstance(constraint, sa.CheckConstraint)
            and constraint.name == "ck_protocol_identities_role"
        )
    )
    assert {
        (
            ("caller_id", "caller_release"),
            "protocol_identities",
            ("identity_id", "release"),
        ),
        (
            ("caller_id", "caller_key_id"),
            "protocol_identity_keys",
            ("identity_id", "key_id"),
        ),
    } <= _foreign_key_bindings(PlatformBase.metadata.tables["protocol_operations"])
    source = (
        TASK2_ROOT
        / "platform_migrations"
        / "versions"
        / "20260804_02_protocol_v2_task4.py"
    ).read_text(encoding="utf-8")
    assert all(object_name in source for object_name in TASK4_ENFORCEMENT_OBJECTS)
    assert "protocol_v2_task4_existing_operations_require_reauthorization" in source
    assert "protocol_v2_task4_existing_key_material_ambiguous" in source


def test_r1a_task4_forward_migration_adds_executor_evidence_and_dispatched_outbox() -> (
    None
):
    script = ScriptDirectory.from_config(migration_config())
    revisions = {revision.revision: revision for revision in script.walk_revisions()}
    task4 = revisions["20260809_01_r1a_evidence"]

    assert task4.down_revision == "20260804_02_protocol_v2_task4"
    assert script.get_heads() == [PLATFORM_MIGRATION_HEAD]
    assert PLATFORM_MIGRATION_HEAD == "20260809_01_r1a_evidence"
    table = PlatformBase.metadata.tables["protocol_executor_evidence"]
    assert set(table.columns.keys()) == EXPECTED_COLUMNS["protocol_executor_evidence"]
    assert (
        _foreign_key_bindings(table)
        == EXPECTED_FOREIGN_KEY_BINDINGS["protocol_executor_evidence"]
    )
    assert (
        _unique_bindings(table)
        == EXPECTED_UNIQUE_BINDINGS["protocol_executor_evidence"]
    )
    outbox_constraint = next(
        constraint
        for constraint in PlatformBase.metadata.tables["protocol_outbox"].constraints
        if isinstance(constraint, sa.CheckConstraint)
        and constraint.name == "ck_protocol_outbox_event_type"
    )
    assert "dispatched" in str(outbox_constraint.sqltext)
    source = (
        TASK2_ROOT
        / "platform_migrations"
        / "versions"
        / "20260809_01_protocol_v2_executor_evidence.py"
    ).read_text(encoding="utf-8")
    assert "protocol_executor_evidence" in source
    assert "trg_protocol_executor_evidence_immutable" in source
    assert "'dispatched', 'manifest_received', 'receipt_verified'" in source


def test_task4_fails_closed_for_historical_duplicate_public_key_material() -> None:
    database_url = _configured_database_url()
    config = migration_config()
    assert _table_names(database_url) <= {PLATFORM_VERSION_TABLE}
    assert _version_rows(database_url) == []
    try:
        command.upgrade(config, "20260804_01_protocol_v2_task3")
        engine = create_engine(database_url)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO protocol_identities "
                        "(identity_id, principal_id, role, release, registered_at) VALUES "
                        "('exec_history_01', 'prn_history_executor_01', 'executor', "
                        "'rel_history_executor_01', CURRENT_TIMESTAMP), "
                        "('ver_history_01', 'prn_history_verifier_01', 'verifier', "
                        "'rel_history_verifier_01', CURRENT_TIMESTAMP)"
                    )
                )
                connection.execute(
                    text(
                        "INSERT INTO protocol_identity_keys "
                        "(key_id, identity_id, algorithm, public_key_material, status, registered_at) "
                        "VALUES ('key_history_executor_01', 'exec_history_01', 'ed25519-v1', "
                        ":public_key_material, 'active', CURRENT_TIMESTAMP), "
                        "('key_history_verifier_01', 'ver_history_01', 'ed25519-v1', "
                        ":public_key_material, 'active', CURRENT_TIMESTAMP)"
                    ),
                    {"public_key_material": "ed25519-v1:" + "A" * 43},
                )
        finally:
            engine.dispose()

        with pytest.raises(sa.exc.DBAPIError, match="existing_key_material_ambiguous"):
            command.upgrade(config, PLATFORM_MIGRATION_HEAD)
        assert _version_rows(database_url) == [("20260804_01_protocol_v2_task3",)]
    finally:
        command.downgrade(config, "base")
    assert _table_names(database_url) == {PLATFORM_VERSION_TABLE}


def test_r1a_downgrade_handles_existing_dispatched_outbox_rows() -> None:
    database_url = _configured_database_url()
    config = migration_config()
    assert _table_names(database_url) <= {PLATFORM_VERSION_TABLE}
    assert _version_rows(database_url) == []
    try:
        command.upgrade(config, PLATFORM_MIGRATION_HEAD)
        engine = create_engine(database_url)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO protocol_identities "
                        "(identity_id, principal_id, role, release, registered_at) VALUES "
                        "('svc_downgrade_01', 'prn_downgrade_caller_01', 'caller', "
                        "'rel_downgrade_caller_01', CURRENT_TIMESTAMP), "
                        "('plt_downgrade_01', 'prn_downgrade_platform_01', 'platform', "
                        "'rel_downgrade_platform_01', CURRENT_TIMESTAMP)"
                    )
                )
                connection.execute(
                    text(
                        "INSERT INTO protocol_identity_keys "
                        "(key_id, identity_id, algorithm, public_key_material, status, "
                        "registered_at) VALUES "
                        "('key_downgrade_caller_01', 'svc_downgrade_01', 'ed25519-v1', "
                        ":caller_key, 'active', CURRENT_TIMESTAMP), "
                        "('key_downgrade_platform_01', 'plt_downgrade_01', 'ed25519-v1', "
                        ":platform_key, 'active', CURRENT_TIMESTAMP)"
                    ),
                    {
                        "caller_key": "ed25519-v1:" + "A" * 43,
                        "platform_key": "ed25519-v1:" + "B" * 43,
                    },
                )
                connection.execute(
                    text(
                        "INSERT INTO protocol_operations "
                        "(operation_id, caller_id, caller_release, caller_key_id, "
                        "caller_credential_version, caller_credential_hash, source_ref_hash, "
                        "source_version, operation_kind, policy_version, idempotency_key, "
                        "expires_at, platform_identity_id, platform_release, platform_key_id, "
                        "platform_signature, state, accepted_at) VALUES "
                        "('op_downgrade_01', 'svc_downgrade_01', "
                        "'rel_downgrade_caller_01', 'key_downgrade_caller_01', "
                        "'caller-credential-v2', :credential_hash, :source_ref_hash, "
                        "'srcv_downgrade_01', 'bounded_execution', "
                        "'pol_r1a_synthetic_repair_v1', 'idem_downgrade_01', "
                        "CURRENT_TIMESTAMP, 'plt_downgrade_01', "
                        "'rel_downgrade_platform_01', 'key_downgrade_platform_01', "
                        ":signature, 'dispatched', CURRENT_TIMESTAMP)"
                    ),
                    {
                        "credential_hash": "0" * 64,
                        "source_ref_hash": "1" * 64,
                        "signature": "sig_" + "a" * 16,
                    },
                )
                connection.execute(
                    text(
                        "INSERT INTO protocol_outbox "
                        "(outbox_id, operation_id, event_type, event_hash, state, created_at) "
                        "VALUES ('out_downgrade_01', 'op_downgrade_01', 'dispatched', "
                        ":event_hash, 'pending', CURRENT_TIMESTAMP)"
                    ),
                    {"event_hash": "2" * 64},
                )
        finally:
            engine.dispose()

        command.downgrade(config, "20260804_02_protocol_v2_task4")
        assert _version_rows(database_url) == [("20260804_02_protocol_v2_task4",)]
        engine = create_engine(database_url)
        try:
            with engine.connect() as connection:
                assert (
                    connection.scalar(
                        text(
                            "SELECT count(*) FROM protocol_outbox "
                            "WHERE event_type = 'dispatched'"
                        )
                    )
                    == 0
                )
        finally:
            engine.dispose()
    finally:
        existing_tables = _table_names(database_url)
        protocol_tables = tuple(
            table_name
            for table_name in PLATFORM_PROTOCOL_TABLES
            if table_name in existing_tables
        )
        if protocol_tables:
            engine = create_engine(database_url)
            try:
                with engine.begin() as connection:
                    connection.execute(
                        text(f"TRUNCATE TABLE {', '.join(protocol_tables)}")
                    )
            finally:
                engine.dispose()
        command.downgrade(config, "base")
    assert _table_names(database_url) == {PLATFORM_VERSION_TABLE}


def test_upgrade_downgrade_upgrade_is_deterministic_for_the_explicit_database() -> None:
    database_url = _configured_database_url()
    assert _table_names(database_url) <= {PLATFORM_VERSION_TABLE}
    assert _version_rows(database_url) == []

    upgrade_platform_database()
    assert _table_names(database_url) == EXPECTED_TABLES
    assert _version_rows(database_url) == [(PLATFORM_MIGRATION_HEAD,)]
    assert (
        _database_role_enforcement_objects(database_url) == EXPECTED_ENFORCEMENT_OBJECTS
    )
    for table_name, expected_columns in EXPECTED_COLUMNS.items():
        assert _table_columns(database_url, table_name) == expected_columns
        assert _database_foreign_key_bindings(database_url, table_name) == (
            EXPECTED_FOREIGN_KEY_BINDINGS.get(table_name, set())
        )
        assert _database_unique_bindings(
            database_url, table_name
        ) == EXPECTED_UNIQUE_BINDINGS.get(
            table_name,
            set(),
        )

    upgrade_platform_database()
    assert _table_names(database_url) == EXPECTED_TABLES
    assert _version_rows(database_url) == [(PLATFORM_MIGRATION_HEAD,)]
    _assert_database_rejects_invalid_identity_role_or_principal_binding(database_url)

    downgrade_platform_database()
    assert _table_names(database_url) == {PLATFORM_VERSION_TABLE}
    assert _version_rows(database_url) == []
    assert _database_role_enforcement_objects(database_url) == set()

    upgrade_platform_database()
    assert _table_names(database_url) == EXPECTED_TABLES
    assert _version_rows(database_url) == [(PLATFORM_MIGRATION_HEAD,)]


def test_migration_allowlist_contains_only_platform_protocol_tables() -> None:
    assert PLATFORM_MIGRATION_TABLES == EXPECTED_TABLES
    assert set(PlatformBase.metadata.tables) == EXPECTED_TABLES - {
        PLATFORM_VERSION_TABLE
    }

    allowed_prefixes = ("protocol_",)
    assert all(table.startswith(allowed_prefixes) for table in PLATFORM_PROTOCOL_TABLES)
    forbidden_table_fragments = (
        "legacy",
        "fde",
        "domain",
        "task",
        "reward",
        "wallet",
        "survival",
    )
    assert not any(
        fragment in table
        for table in PLATFORM_PROTOCOL_TABLES
        for fragment in forbidden_table_fragments
    )

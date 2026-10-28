from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from contextlib import ExitStack
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Self
from unittest.mock import patch

import sqlalchemy as sa
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from platform_protocol.contracts import ProtocolViolation
from platform_protocol.migrations import (
    PLATFORM_MIGRATION_HEAD,
    downgrade_platform_database,
    upgrade_platform_database,
)
from platform_protocol.models import (
    PLATFORM_PROTOCOL_TABLES,
    ProtocolAttempt,
    ProtocolAuditEvent,
    ProtocolExecutorEvidence,
    ProtocolManifest,
    ProtocolOperation,
    ProtocolOutbox,
    ProtocolReceipt,
)
from platform_protocol.service import ProtocolService
from tests.platform_protocol import m1_r1a_synthetic_repair_harness as harness
from tests.platform_protocol import m1_r1a_synthetic_repair_verifier as verifier

_DATABASE_NAME = re.compile(r"^nautilus_platform_g1b_[0-9]{14}$")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
_AUDIT_TABLE = "protocol_audit_events"
_OUTBOX_TABLE = "protocol_outbox"
_REPLAY_METHODS = (
    "register_r1a_ephemeral_executor_key",
    "issue_and_accept_r1a_operation",
    "claim_r1a_attempt",
    "record_execution_evidence_and_manifest",
    "record_receipt",
    "ack_outbox",
)


@dataclass(frozen=True, slots=True)
class ReplayedChainResult:
    chain: harness.R1aSyntheticRepairResult
    exact_replay_count: int
    row_growth: int
    audit_growth: int
    outbox_growth: int
    manifest_hash: str


@dataclass(frozen=True, slots=True)
class FailureMatrixEntry:
    boundary: str
    stage: str
    fallback: str
    test_node: str


@dataclass(frozen=True, slots=True)
class VerticalFailureResult:
    operation_state: str | None
    row_counts: dict[str, int]
    executor_calls: int
    verifier_calls: int
    network_delivery_count: int
    fallback: str


_ADMISSION_NODE = (
    "tests.platform_protocol.test_m1_r1a_runtime_admission:"
    "test_invalid_or_widened_admission_inputs_fail_closed"
)
_ROUTING_BINDING_NODE = (
    "tests.platform_protocol.test_m1_r1a_routing:"
    "test_changed_candidate_binding_fails_closed"
)
_VERTICAL_TAMPER_NODE = (
    "tests.platform_protocol.test_m1_r1a_synthetic_repair_fail_closed:"
    "test_task6_vertical_boundary_tamper_stops_at_expected_stage"
)

TASK6_FAILURE_MATRIX = (
    *(
        FailureMatrixEntry(name, "pre_operation", "none", _ADMISSION_NODE)
        for name in ("owner_commit", "owner_path", "owner_hash", "runtime_admission")
    ),
    FailureMatrixEntry(
        "caller_credential",
        "pre_operation",
        "none",
        "tests.platform_protocol.test_service_authentication:"
        "test_service_rejects_invalid_caller_credentials_and_platform_keys_without_writes",
    ),
    *(
        FailureMatrixEntry(
            name,
            "pre_operation" if name == "executor_key" else "claim",
            "none",
            (
                "tests.platform_protocol.test_m1_r1a_routing:"
                "test_zero_or_multiple_candidates_fail_closed"
                if name in {"dmas_zero_match", "dmas_multiple_match"}
                else _ROUTING_BINDING_NODE
            ),
        )
        for name in (
            "dmas_zero_match",
            "dmas_multiple_match",
            "executor_identity",
            "executor_release",
            "executor_key",
            "tool_policy",
        )
    ),
    FailureMatrixEntry(
        "lease",
        "claim",
        "none",
        "tests.platform_protocol.test_service:"
        "test_r1a_attempt_lease_cannot_exceed_ephemeral_key",
    ),
    *(
        FailureMatrixEntry(name, "pre_manifest", "none", _VERTICAL_TAMPER_NODE)
        for name in ("attempt_hmac", "capsule", "fixture", "artifact")
    ),
    *(
        FailureMatrixEntry(
            name,
            "pre_manifest",
            "none",
            "tests.platform_protocol.test_service:"
            "test_r1a_invalid_execution_evidence_rolls_back_without_partial_rows",
        )
        for name in ("executor_evidence_forged", "evidence_binding_tamper", "manifest")
    ),
    FailureMatrixEntry(
        "evidence_replay_mismatch",
        "post_manifest",
        "none",
        "tests.platform_protocol.test_m1_r1a_synthetic_repair_fail_closed:"
        "test_verifier_rejects_a_different_valid_outcome_than_the_persisted_evidence",
    ),
    *(
        FailureMatrixEntry(name, "post_manifest", "none", _VERTICAL_TAMPER_NODE)
        for name in ("grant_nonce", "grant_expiry", "oracle_result")
    ),
    *(
        FailureMatrixEntry(
            name,
            "post_manifest",
            "none",
            "tests.platform_protocol.test_service_authentication:"
            "test_service_rejects_invalid_verifier_registry_states_without_receipt_write",
        )
        for name in (
            "verifier_identity",
            "verifier_release",
            "verifier_key",
            "verifier_signature",
        )
    ),
    FailureMatrixEntry(
        "transaction_injection",
        "transaction",
        "none",
        "tests.platform_protocol.test_service:"
        "test_r1a_injected_failure_rolls_back_executor_evidence_and_manifest",
    ),
    FailureMatrixEntry(
        "concurrent_attempt_claim",
        "claim",
        "none",
        "tests.platform_protocol.test_service:"
        "test_r1a_two_session_attempt_claim_has_exactly_one_winner",
    ),
    FailureMatrixEntry(
        "changed_request_replay",
        "pre_operation",
        "none",
        "tests.platform_protocol.test_service:"
        "test_accept_operation_is_atomic_idempotent_and_rejects_changed_replay",
    ),
    *(
        FailureMatrixEntry(
            name,
            "post_manifest",
            "none",
            "tests.platform_protocol.test_service:"
            "test_attempt_and_manifest_replays_preserve_one_immutable_binding",
        )
        for name in ("changed_attempt_replay", "changed_manifest_replay")
    ),
    FailureMatrixEntry(
        "changed_receipt_replay",
        "post_manifest",
        "none",
        "tests.platform_protocol.test_service:"
        "test_receipt_requires_an_independent_registered_signature_and_one_binding",
    ),
)

_EVIDENCE_FIELDS = {
    "source": {
        "platform_commit",
        "failure_matrix_sha256",
        "task6_cli_sha256",
        "runtime_admission_sha256",
        "v5_executor_commit",
        "v5_contract_sha256",
        "compass_authority_commit",
        "compass_proposal_commit",
        "compass_capsule_sha256",
    },
    "protocol": {
        "contract_version",
        "execution_evidence_contract_version",
        "policy_version",
        "migration_head",
        "operation_id",
        "attempt_id",
        "manifest_hash",
    },
    "outcomes": {
        "positive",
        "missing_scope",
        "receipt_decision",
        "receipt_reason_codes",
    },
    "counts": {
        "first_run_rows",
        "first_run_audit_events",
        "first_run_outbox_events",
    },
    "replay": {
        "exact_replay_count",
        "row_growth",
        "audit_growth",
        "outbox_growth",
    },
    "fail_closed": {"case_count", "fallback_count"},
    "cleanup": {"database_present", "protocol_tables"},
}
_TOP_LEVEL_EVIDENCE_FIELDS = {"schema_version", "evidence_level", *_EVIDENCE_FIELDS}
_MAIN_ROW_COUNTS = {
    "operations": 1,
    "attempts": 1,
    "executor_evidence": 1,
    "manifests": 1,
    "receipts": 1,
}
_RUNTIME_ADMISSION_PATH = (
    "phase3/backend/docs/evidence/m1-r1a-runtime-admission-v1.json"
)
_FAILURE_MATRIX_PATH = (
    "phase3/backend/tests/platform_protocol/test_m1_r1a_synthetic_repair_fail_closed.py"
)
_TASK6_CLI_PATH = (
    "phase3/backend/tests/platform_protocol/test_m1_r1a_synthetic_repair_cli.py"
)
_TASK6_EVIDENCE_PATH = (
    "phase3/backend/docs/evidence/m1-r1a-synthetic-repair-readback-v1.json"
)


def _validated_database_url(database_url: str) -> str:
    try:
        parsed = make_url(database_url)
    except Exception as error:
        raise ValueError("disposable_database_url_rejected") from error
    if (
        parsed.drivername != "postgresql+psycopg2"
        or parsed.username != "postgres"
        or parsed.host != "127.0.0.1"
        or parsed.port != 5432
        or parsed.database is None
        or _DATABASE_NAME.fullmatch(parsed.database) is None
        or parsed.query
        or "#" in database_url
    ):
        raise ValueError("disposable_database_url_rejected")
    return database_url


def _admin_engine(database_url: str) -> sa.Engine:
    target = make_url(_validated_database_url(database_url))
    return sa.create_engine(
        target.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )


def _database_exists(database_url: str) -> bool:
    database_name = make_url(_validated_database_url(database_url)).database
    engine = _admin_engine(database_url)
    try:
        with engine.connect() as connection:
            return bool(
                connection.scalar(
                    sa.text("SELECT 1 FROM pg_database WHERE datname = :name"),
                    {"name": database_name},
                )
            )
    finally:
        engine.dispose()


def _create_database(database_url: str) -> None:
    database_name = make_url(_validated_database_url(database_url)).database
    if database_name is None or _database_exists(database_url):
        raise ValueError("disposable_database_already_exists")
    engine = _admin_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')
    finally:
        engine.dispose()


def _drop_database(database_url: str) -> None:
    database_name = make_url(_validated_database_url(database_url)).database
    engine = _admin_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(
                sa.text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :name AND pid <> pg_backend_pid()"
                ),
                {"name": database_name},
            )
            connection.exec_driver_sql(f'DROP DATABASE IF EXISTS "{database_name}"')
    finally:
        engine.dispose()


def _protocol_table_count(database_url: str) -> int:
    engine = sa.create_engine(database_url)
    try:
        tables = set(sa.inspect(engine).get_table_names(schema="public"))
        return len(tables.intersection(PLATFORM_PROTOCOL_TABLES))
    finally:
        engine.dispose()


def _require_migration_head(database_url: str) -> None:
    engine = sa.create_engine(database_url)
    try:
        with engine.connect() as connection:
            head = connection.scalar(
                sa.text("SELECT version_num FROM platform_schema_version")
            )
    finally:
        engine.dispose()
    if head != PLATFORM_MIGRATION_HEAD:
        raise ValueError("unexpected_platform_migration_head")


def _require_empty_public_schema(database_url: str) -> None:
    engine = sa.create_engine(_validated_database_url(database_url))
    try:
        with engine.connect() as connection:
            object_count = connection.scalar(
                sa.text(
                    "SELECT count(*) FROM pg_class AS c "
                    "JOIN pg_namespace AS n ON n.oid = c.relnamespace "
                    "WHERE n.nspname = 'public'"
                )
            )
    finally:
        engine.dispose()
    if object_count != 0:
        raise ValueError("disposable_database_public_schema_not_empty")


def _exact_evidence_section(
    document: dict[str, object], name: str
) -> dict[str, object]:
    value = document.get(name)
    if not isinstance(value, dict) or set(value) != _EVIDENCE_FIELDS[name]:
        raise ValueError("invalid_task6_evidence_document")
    return value


def _validate_evidence_document(
    document: dict[str, object], *, expected_source: dict[str, object]
) -> dict[str, object]:
    try:
        if (
            set(document) != _TOP_LEVEL_EVIDENCE_FIELDS
            or document["schema_version"] != "m1-r1a-synthetic-repair-readback-v1"
            or document["evidence_level"] != "local_r1a"
        ):
            raise ValueError("invalid_task6_evidence_document")
        source = _exact_evidence_section(document, "source")
        protocol = _exact_evidence_section(document, "protocol")
        outcomes = _exact_evidence_section(document, "outcomes")
        counts = _exact_evidence_section(document, "counts")
        replay = _exact_evidence_section(document, "replay")
        fail_closed = _exact_evidence_section(document, "fail_closed")
        cleanup = _exact_evidence_section(document, "cleanup")
        commit_fields = {
            "platform_commit",
            "v5_executor_commit",
            "compass_authority_commit",
            "compass_proposal_commit",
        }
        if source != expected_source or any(
            not isinstance(source[name], str) or _HEX40.fullmatch(source[name]) is None
            for name in commit_fields
        ):
            raise ValueError("invalid_task6_evidence_document")
        if any(
            not isinstance(source[name], str) or _HEX64.fullmatch(source[name]) is None
            for name in set(source) - commit_fields
        ):
            raise ValueError("invalid_task6_evidence_document")
        if (
            protocol["contract_version"] != "protocol-v2-contracts-v1"
            or protocol["execution_evidence_contract_version"]
            != "m1-r1a-executor-execution-evidence-v1"
            or protocol["policy_version"] != "pol_r1a_synthetic_repair_v1"
            or protocol["migration_head"] != "20260809_01_r1a_evidence"
            or not isinstance(protocol["operation_id"], str)
            or _IDENTIFIER.fullmatch(protocol["operation_id"]) is None
            or not isinstance(protocol["attempt_id"], str)
            or _IDENTIFIER.fullmatch(protocol["attempt_id"]) is None
            or not isinstance(protocol["manifest_hash"], str)
            or _HEX64.fullmatch(protocol["manifest_hash"]) is None
        ):
            raise ValueError("invalid_task6_evidence_document")
        if outcomes != {
            "positive": "completed",
            "missing_scope": "review_required",
            "receipt_decision": "accepted",
            "receipt_reason_codes": ["policy_satisfied"],
        }:
            raise ValueError("invalid_task6_evidence_document")
        first_run_rows = counts.get("first_run_rows")
        numeric_values = (
            counts.get("first_run_audit_events"),
            counts.get("first_run_outbox_events"),
            *(first_run_rows.values() if isinstance(first_run_rows, dict) else ()),
            *replay.values(),
            *fail_closed.values(),
            *cleanup.values(),
        )
        if not isinstance(first_run_rows, dict) or any(
            type(value) is not int for value in numeric_values
        ):
            raise ValueError("invalid_task6_evidence_document")
        if counts != {
            "first_run_rows": _MAIN_ROW_COUNTS,
            "first_run_audit_events": 4,
            "first_run_outbox_events": 3,
        }:
            raise ValueError("invalid_task6_evidence_document")
        if replay != {
            "exact_replay_count": 6,
            "row_growth": 0,
            "audit_growth": 0,
            "outbox_growth": 0,
        }:
            raise ValueError("invalid_task6_evidence_document")
        if fail_closed != {"case_count": 33, "fallback_count": 0}:
            raise ValueError("invalid_task6_evidence_document")
        if cleanup != {"database_present": 0, "protocol_tables": 0}:
            raise ValueError("invalid_task6_evidence_document")
    except (KeyError, TypeError) as error:
        raise ValueError("invalid_task6_evidence_document") from error
    return document


def _protocol_snapshot(database_url: str) -> dict[str, int]:
    engine = sa.create_engine(database_url)
    try:
        with engine.connect() as connection:
            return {
                table: int(
                    connection.scalar(sa.text(f'SELECT count(*) FROM "{table}"'))
                )
                for table in PLATFORM_PROTOCOL_TABLES
            }
    finally:
        engine.dispose()


class _ExactReplayProbe:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._originals: dict[str, Any] = {}
        self.exact_replay_count = 0
        self.row_growth = 0
        self.audit_growth = 0
        self.outbox_growth = 0
        self.manifest_hash: str | None = None

    def __enter__(self) -> Self:
        for method_name in _REPLAY_METHODS:
            original = getattr(ProtocolService, method_name)
            self._originals[method_name] = original

            def replay_exactly(
                service: ProtocolService,
                *args: object,
                _original: Any = original,
                _method_name: str = method_name,
                **kwargs: object,
            ) -> object:
                first = _original(service, *args, **kwargs)
                before_replay = _protocol_snapshot(self._database_url)
                second = _original(service, *args, **kwargs)
                after_replay = _protocol_snapshot(self._database_url)
                if first != second:
                    raise AssertionError(f"{_method_name}_replay_result_changed")
                if _method_name == "record_execution_evidence_and_manifest":
                    self.manifest_hash = first[1].manifest_hash
                if before_replay != after_replay:
                    raise AssertionError(f"{_method_name}_replay_grew_protocol_state")
                self.exact_replay_count += 1
                self.row_growth += sum(
                    after_replay[name] - before_replay[name]
                    for name in PLATFORM_PROTOCOL_TABLES - {_AUDIT_TABLE, _OUTBOX_TABLE}
                )
                self.audit_growth += (
                    after_replay[_AUDIT_TABLE] - before_replay[_AUDIT_TABLE]
                )
                self.outbox_growth += (
                    after_replay[_OUTBOX_TABLE] - before_replay[_OUTBOX_TABLE]
                )
                return first

            setattr(ProtocolService, method_name, replay_exactly)
        return self

    def __exit__(self, *_exc: object) -> None:
        for method_name, original in self._originals.items():
            setattr(ProtocolService, method_name, original)


def run_replayed_chain(
    *,
    database_url: str,
    platform_root: Path,
    v5_authority_root: Path,
    v5_executor_root: Path,
    compass_authority_root: Path,
) -> ReplayedChainResult:
    _validated_database_url(database_url)
    harness._require_empty_protocol_database(database_url)
    with _ExactReplayProbe(database_url) as probe:
        chain = harness.run_positive_chain(
            database_url=database_url,
            platform_root=platform_root,
            v5_authority_root=v5_authority_root,
            v5_executor_root=v5_executor_root,
            compass_authority_root=compass_authority_root,
        )
    if probe.manifest_hash is None:
        raise AssertionError("replayed_chain_manifest_hash_missing")
    return ReplayedChainResult(
        chain=chain,
        exact_replay_count=probe.exact_replay_count,
        row_growth=probe.row_growth,
        audit_growth=probe.audit_growth,
        outbox_growth=probe.outbox_growth,
        manifest_hash=probe.manifest_hash,
    )


def _stage_snapshot(database_url: str) -> tuple[str | None, dict[str, int]]:
    engine = sa.create_engine(database_url)
    models = {
        "operations": ProtocolOperation,
        "attempts": ProtocolAttempt,
        "executor_evidence": ProtocolExecutorEvidence,
        "manifests": ProtocolManifest,
        "receipts": ProtocolReceipt,
        "audit_events": ProtocolAuditEvent,
        "outbox_events": ProtocolOutbox,
    }
    try:
        with Session(engine) as session:
            counts = {
                name: int(
                    session.scalar(sa.select(sa.func.count()).select_from(model)) or 0
                )
                for name, model in models.items()
            }
            operation = session.get(ProtocolOperation, "op_r1a_vertical_01")
        return (None if operation is None else operation.state, counts)
    finally:
        engine.dispose()


def _install_vertical_tamper(stack: ExitStack, boundary: str) -> None:
    if boundary == "attempt_hmac":
        original = harness._execution_request

        def changed_request(**kwargs: object) -> bytes:
            document = harness._parse_json_object(original(**kwargs))
            document["input_ref_hash"] = "f" * 64
            return harness._canonical_bytes(document)

        stack.enter_context(
            patch.object(harness, "_execution_request", changed_request)
        )
        return
    if boundary in {"capsule", "fixture", "artifact"}:
        original = harness._parse_execution_result

        def changed_result(*args: object, **kwargs: object):
            artifact, evidence, scope, result_state = original(*args, **kwargs)
            if boundary == "artifact":
                artifact += b"tampered"
            elif boundary == "capsule":
                evidence = replace(evidence, bound_capsule_hash="e" * 64)
            else:
                evidence = replace(evidence, fixture_hash="e" * 64)
            return artifact, evidence, scope, result_state

        stack.enter_context(
            patch.object(harness, "_parse_execution_result", changed_result)
        )
        return
    if boundary in {"grant_nonce", "grant_expiry"}:
        original = harness.create_manifest_read_grant

        def changed_grant(**kwargs: object):
            grant = original(**kwargs)
            if boundary == "grant_nonce":
                return replace(grant, nonce="nonce_" + "f" * 64)
            return replace(grant, expires_at=grant.issued_at)

        stack.enter_context(
            patch.object(harness, "create_manifest_read_grant", changed_grant)
        )
        return
    if boundary == "oracle_result":
        stack.enter_context(
            patch.object(
                verifier,
                "_run_fixed_oracle",
                lambda _source: (_ for _ in ()).throw(
                    ProtocolViolation("synthetic_oracle_failed")
                ),
            )
        )
        return
    raise ValueError("unknown_vertical_failure_boundary")


def run_vertical_boundary_failure(
    *,
    boundary: str,
    database_url: str,
    platform_root: Path,
    v5_authority_root: Path,
    v5_executor_root: Path,
    compass_authority_root: Path,
) -> VerticalFailureResult:
    _validated_database_url(database_url)
    harness._require_empty_protocol_database(database_url)
    captured: list[tuple[str | None, dict[str, int]]] = []
    executor_calls = 0
    verifier_calls = 0
    original_start_signer = harness._start_signer
    original_verify = harness.verify_and_sign_receipt
    original_truncate = harness._truncate_protocol_tables

    def counted_start_signer(root: Path):
        nonlocal executor_calls
        executor_calls += 1
        return original_start_signer(root)

    def counted_verify(**kwargs: object):
        nonlocal verifier_calls
        verifier_calls += 1
        return original_verify(**kwargs)

    def capture_then_truncate(target_url: str) -> None:
        captured.append(_stage_snapshot(target_url))
        original_truncate(target_url)

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(harness, "_start_signer", counted_start_signer)
        )
        stack.enter_context(
            patch.object(harness, "verify_and_sign_receipt", counted_verify)
        )
        stack.enter_context(
            patch.object(harness, "_truncate_protocol_tables", capture_then_truncate)
        )
        _install_vertical_tamper(stack, boundary)
        try:
            harness.run_positive_chain(
                database_url=database_url,
                platform_root=platform_root,
                v5_authority_root=v5_authority_root,
                v5_executor_root=v5_executor_root,
                compass_authority_root=compass_authority_root,
            )
        except (AssertionError, ProtocolViolation, RuntimeError, ValueError):
            pass
        else:
            raise AssertionError("vertical_boundary_tamper_unexpectedly_succeeded")
    if len(captured) != 1:
        raise AssertionError("vertical_failure_stage_snapshot_missing")
    operation_state, row_counts = captured[0]
    return VerticalFailureResult(
        operation_state=operation_state,
        row_counts=row_counts,
        executor_calls=executor_calls,
        verifier_calls=verifier_calls,
        network_delivery_count=0,
        fallback="none",
    )


def _run_authorized_database_cycle(
    *,
    database_url: str,
    platform_root: Path,
    v5_authority_root: Path,
    v5_executor_root: Path,
    compass_authority_root: Path,
    expected_source: dict[str, object],
) -> dict[str, object]:
    _validated_database_url(database_url)
    if _database_exists(database_url):
        raise ValueError("disposable_database_already_exists")
    previous_url = os.environ.get("NAUTILUS_PLATFORM_DATABASE_URL")
    created = False
    executed_failure_count = -1
    protocol_tables_after_downgrade = -1
    try:
        _create_database(database_url)
        created = True
        _require_empty_public_schema(database_url)
        os.environ["NAUTILUS_PLATFORM_DATABASE_URL"] = database_url
        replay = run_replayed_chain(
            database_url=database_url,
            platform_root=platform_root,
            v5_authority_root=v5_authority_root,
            v5_executor_root=v5_executor_root,
            compass_authority_root=compass_authority_root,
        )
        review_required = harness.run_review_required_chain(
            database_url=database_url,
            platform_root=platform_root,
            v5_authority_root=v5_authority_root,
            v5_executor_root=v5_executor_root,
            compass_authority_root=compass_authority_root,
        )
        executed_failure_count = _run_failure_matrix_tests(
            database_url=database_url,
            backend_root=platform_root / "phase3" / "backend",
        )
        upgrade_platform_database()
        _require_migration_head(database_url)
        downgrade_platform_database()
        protocol_tables_after_downgrade = _protocol_table_count(database_url)
        if protocol_tables_after_downgrade != 0:
            raise ValueError("protocol_tables_remain_after_downgrade")
        upgrade_platform_database()
        _require_migration_head(database_url)
        downgrade_platform_database()
        protocol_tables_after_downgrade = _protocol_table_count(database_url)
        if protocol_tables_after_downgrade != 0:
            raise ValueError("protocol_tables_remain_after_determinism_check")
        rows = replay.chain.protocol_row_counts
        document: dict[str, object] = {
            "schema_version": "m1-r1a-synthetic-repair-readback-v1",
            "evidence_level": "local_r1a",
            "source": expected_source,
            "protocol": {
                "contract_version": "protocol-v2-contracts-v1",
                "execution_evidence_contract_version": (
                    "m1-r1a-executor-execution-evidence-v1"
                ),
                "policy_version": "pol_r1a_synthetic_repair_v1",
                "migration_head": PLATFORM_MIGRATION_HEAD,
                "operation_id": "op_r1a_vertical_01",
                "attempt_id": "att_r1a_vertical_01",
                "manifest_hash": replay.manifest_hash,
            },
            "outcomes": {
                "positive": replay.chain.executor_result_state,
                "missing_scope": review_required.executor_result_state,
                "receipt_decision": replay.chain.receipt_decision,
                "receipt_reason_codes": list(replay.chain.receipt_reason_codes),
            },
            "counts": {
                "first_run_rows": {
                    "operations": rows["operations"],
                    "attempts": rows["attempts"],
                    "executor_evidence": rows["executor_evidence"],
                    "manifests": rows["manifests"],
                    "receipts": rows["receipts"],
                },
                "first_run_audit_events": rows["audit_events"],
                "first_run_outbox_events": rows["outbox_events"],
            },
            "replay": {
                "exact_replay_count": replay.exact_replay_count,
                "row_growth": replay.row_growth,
                "audit_growth": replay.audit_growth,
                "outbox_growth": replay.outbox_growth,
            },
            "fail_closed": {
                "case_count": executed_failure_count,
                "fallback_count": sum(
                    entry.fallback != "none" for entry in TASK6_FAILURE_MATRIX
                ),
            },
            "cleanup": {"database_present": 1, "protocol_tables": 1},
        }
    finally:
        if previous_url is None:
            os.environ.pop("NAUTILUS_PLATFORM_DATABASE_URL", None)
        else:
            os.environ["NAUTILUS_PLATFORM_DATABASE_URL"] = previous_url
        if created:
            _drop_database(database_url)
    if _database_exists(database_url):
        raise ValueError("disposable_database_cleanup_failed")
    document["cleanup"] = {
        "database_present": 0,
        "protocol_tables": protocol_tables_after_downgrade,
    }
    return _validate_evidence_document(document, expected_source=expected_source)


def _pytest_node(test_node: str) -> str:
    module_name, function_name = test_node.rsplit(":", 1)
    if not module_name.startswith("tests.platform_protocol.test_"):
        raise ValueError("invalid_task6_failure_test_node")
    return f"{module_name.replace('.', '/')}.py::{function_name}"


def _run_failure_matrix_tests(*, database_url: str, backend_root: Path) -> int:
    _validated_database_url(database_url)
    root = backend_root.resolve()
    expected_root = Path(__file__).resolve().parents[2]
    if root != expected_root:
        raise ValueError("invalid_task6_backend_root")
    vertical_node = _pytest_node(_VERTICAL_TAMPER_NODE)
    declared_nodes = tuple(
        dict.fromkeys(_pytest_node(entry.test_node) for entry in TASK6_FAILURE_MATRIX)
    )
    nodes = (vertical_node, *(node for node in declared_nodes if node != vertical_node))
    environment = {
        name: os.environ[name]
        for name in (
            "COMSPEC",
            "PATH",
            "PATHEXT",
            "PGPASSWORD",
            "SYSTEMROOT",
            "TEMP",
            "TMP",
            "WINDIR",
            "NAUTILUS_V5_AUTHORITY_ROOT",
            "NAUTILUS_V5_EXECUTOR_ROOT",
            "NAUTILUS_COMPASS_AUTHORITY_ROOT",
        )
        if name in os.environ
    }
    environment.update(
        {
            "NAUTILUS_PLATFORM_DATABASE_URL": database_url,
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *nodes,
            "-o",
            "addopts=",
            "-q",
            "--confcutdir=tests/platform_protocol",
            "-p",
            "no:cacheprovider",
        ],
        cwd=root,
        env=environment,
        check=False,
        capture_output=True,
        timeout=240,
    )
    if completed.returncode != 0:
        raise ValueError("task6_failure_matrix_failed")
    return len(TASK6_FAILURE_MATRIX)


def _git_bytes(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _parse_json_object(data: bytes) -> dict[str, object]:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_json_field")
            result[key] = value
        return result

    value = json.loads(data, object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict):
        raise TypeError("expected_json_object")
    return value


def _read_source_binding(
    platform_root: Path,
    *,
    platform_commit: str | None = None,
    require_clean: bool = True,
) -> dict[str, object]:
    root = platform_root.resolve()
    if require_clean and _git_bytes(root, "status", "--porcelain"):
        raise ValueError("task6_source_worktree_not_clean")
    if platform_commit is None:
        platform_commit = _git_bytes(root, "rev-parse", "HEAD").decode("ascii").strip()
    if _HEX40.fullmatch(platform_commit) is None:
        raise ValueError("invalid_task6_source_commit")
    admission_bytes = _git_bytes(
        root, "show", f"{platform_commit}:{_RUNTIME_ADMISSION_PATH}"
    )
    failure_matrix_bytes = _git_bytes(
        root, "show", f"{platform_commit}:{_FAILURE_MATRIX_PATH}"
    )
    cli_bytes = _git_bytes(root, "show", f"{platform_commit}:{_TASK6_CLI_PATH}")
    admission = _parse_json_object(admission_bytes)
    v5_input = admission.get("v5_executor_input")
    compass_input = admission.get("compass_input")
    if not isinstance(v5_input, dict) or not isinstance(compass_input, dict):
        raise TypeError("invalid_runtime_admission_source")
    return {
        "platform_commit": platform_commit,
        "failure_matrix_sha256": hashlib.sha256(failure_matrix_bytes).hexdigest(),
        "task6_cli_sha256": hashlib.sha256(cli_bytes).hexdigest(),
        "runtime_admission_sha256": hashlib.sha256(admission_bytes).hexdigest(),
        "v5_executor_commit": v5_input["proposal_commit"],
        "v5_contract_sha256": v5_input["contract_sha256"],
        "compass_authority_commit": compass_input["authority_commit"],
        "compass_proposal_commit": compass_input["proposal_commit"],
        "compass_capsule_sha256": compass_input["capsule_sha256"],
    }


def _require_committed_evidence_relation(
    platform_root: Path, *, source_commit: str
) -> None:
    root = platform_root.resolve()
    if _git_bytes(root, "status", "--porcelain"):
        raise ValueError("task6_evidence_worktree_not_clean")
    if _HEX40.fullmatch(source_commit) is None:
        raise ValueError("invalid_task6_evidence_commit_relation")
    try:
        head = _git_bytes(root, "rev-parse", "HEAD").decode("ascii").strip()
        _git_bytes(root, "merge-base", "--is-ancestor", source_commit, head)
        evidence_commits = tuple(
            line
            for line in _git_bytes(
                root,
                "rev-list",
                "--full-history",
                "--reverse",
                f"{source_commit}..{head}",
                "--",
                _TASK6_EVIDENCE_PATH,
            )
            .decode("ascii")
            .splitlines()
            if line
        )
        if len(evidence_commits) != 1:
            raise ValueError("invalid_task6_evidence_commit_relation")
        evidence_commit = evidence_commits[0]
        commit_and_parents = (
            _git_bytes(root, "rev-list", "--parents", "-n", "1", evidence_commit)
            .decode("ascii")
            .split()
        )
        changed_paths = {
            line
            for line in _git_bytes(
                root, "diff", "--name-only", source_commit, evidence_commit
            )
            .decode("utf-8")
            .splitlines()
            if line
        }
        evidence_blob = _git_bytes(
            root, "show", f"{evidence_commit}:{_TASK6_EVIDENCE_PATH}"
        )
        head_blob = _git_bytes(root, "show", f"{head}:{_TASK6_EVIDENCE_PATH}")
    except (subprocess.CalledProcessError, UnicodeDecodeError) as error:
        raise ValueError("invalid_task6_evidence_commit_relation") from error
    if (
        len(commit_and_parents) != 2
        or commit_and_parents[1] != source_commit
        or changed_paths != {_TASK6_EVIDENCE_PATH}
        or evidence_blob != head_blob
    ):
        raise ValueError("invalid_task6_evidence_commit_relation")


def _write_evidence_document(document: dict[str, object]) -> None:
    platform_root = Path(__file__).resolve().parents[4]
    validated = _validate_evidence_document(
        document,
        expected_source=_read_source_binding(platform_root),
    )
    evidence_path = platform_root / _TASK6_EVIDENCE_PATH
    temporary_path = evidence_path.with_suffix(".json.tmp")
    payload = (
        json.dumps(
            validated,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    temporary_path.write_text(payload, encoding="utf-8", newline="\n")
    temporary_path.replace(evidence_path)


def _required_root(environment_name: str) -> Path:
    value = os.environ.get(environment_name)
    if value is None:
        raise ValueError(f"{environment_name}_required")
    root = Path(value).resolve()
    if not root.is_dir():
        raise ValueError(f"{environment_name}_invalid")
    return root


def _main(arguments: list[str]) -> int:
    if len(arguments) != 1:
        raise ValueError("exactly_one_database_url_required")
    database_url = _validated_database_url(arguments[0])
    platform_root = Path(__file__).resolve().parents[4]
    source = _read_source_binding(platform_root)
    document = _run_authorized_database_cycle(
        database_url=database_url,
        platform_root=platform_root,
        v5_authority_root=_required_root("NAUTILUS_V5_AUTHORITY_ROOT"),
        v5_executor_root=_required_root("NAUTILUS_V5_EXECUTOR_ROOT"),
        compass_authority_root=_required_root("NAUTILUS_COMPASS_AUTHORITY_ROOT"),
        expected_source=source,
    )
    _write_evidence_document(document)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))

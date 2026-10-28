from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from platform_protocol.contracts import ArtifactV2, ManifestV2, ProtocolViolation
from platform_protocol.keys import encode_ed25519_signature
from platform_protocol.m1_r1a_execution_evidence import (
    EVIDENCE_CONTRACT_VERSION,
    ExecutorExecutionEvidenceV1,
)
from platform_protocol.models import ProtocolExecutorEvidence, ProtocolManifest


def _required_directory(name: str) -> Path:
    value = os.environ.get(name)
    if value is None:
        # 2026-09-15: env 缺失=本机无垂直链环境,skip 不 fail(工厂机有 env 照跑)
        pytest.skip(f"{name} is required for the local R1a vertical chain (factory env)")
    path = Path(value).resolve()
    assert path.is_dir(), f"{name} must name an existing directory"
    return path


def _signed_evidence(
    private_key: Ed25519PrivateKey, *, result_state: str
) -> ExecutorExecutionEvidenceV1:
    unsigned = ExecutorExecutionEvidenceV1(
        evidence_version=EVIDENCE_CONTRACT_VERSION,
        operation_id="op_r1a_persisted_01",
        attempt_id="att_r1a_persisted_01",
        input_ref_hash="1" * 64,
        executor_id="exec_r1a_synthetic_01",
        executor_release="rel_r1a_ephemeral_v3",
        executor_key_id="key_r1a_ephemeral_v3",
        bound_capsule_hash="2" * 64,
        fixture_hash="3" * 64,
        tool_policy_hash="4" * 64,
        artifact_hash="5" * 64,
        result_state=result_state,
        produced_at=datetime(2026, 8, 11, 12, 0, tzinfo=UTC),
        signature_algorithm="ed25519-v1",
        executor_signature="sig_" + "A" * 86,
    )
    return replace(
        unsigned,
        executor_signature=encode_ed25519_signature(
            private_key.sign(unsigned.canonical_signing_bytes)
        ),
    )


def test_verifier_rejects_a_different_valid_outcome_than_the_persisted_evidence() -> (
    None
):
    try:
        from tests.platform_protocol.m1_r1a_synthetic_repair_verifier import (
            require_persisted_verifier_inputs,
        )
    except ImportError:
        pytest.fail("persisted_verifier_readback_missing", pytrace=False)

    private_key = Ed25519PrivateKey.generate()
    persisted = _signed_evidence(private_key, result_state="completed")
    substituted = _signed_evidence(private_key, result_state="review_required")
    manifest = ManifestV2(
        operation_id=persisted.operation_id,
        attempt_id=persisted.attempt_id,
        executor_id=persisted.executor_id,
        executor_release=persisted.executor_release,
        artifacts=(
            ArtifactV2(
                artifact_id="art_r1a_persisted_01",
                media_type="text/x-diff",
                sha256=persisted.artifact_hash,
                byte_size=1,
                storage_ref="vault://artifact/r1a_persisted_01",
            ),
        ),
    )
    evidence_row = ProtocolExecutorEvidence(
        evidence_hash=hashlib.sha256(persisted.canonical_bytes).hexdigest(),
        evidence_version=persisted.evidence_version,
        operation_id=persisted.operation_id,
        attempt_id=persisted.attempt_id,
        input_ref_hash=persisted.input_ref_hash,
        executor_id=persisted.executor_id,
        executor_release=persisted.executor_release,
        executor_key_id=persisted.executor_key_id,
        bound_capsule_hash=persisted.bound_capsule_hash,
        fixture_hash=persisted.fixture_hash,
        tool_policy_hash=persisted.tool_policy_hash,
        artifact_hash=persisted.artifact_hash,
        result_state=persisted.result_state,
        produced_at=persisted.produced_at,
        signature_algorithm=persisted.signature_algorithm,
        executor_signature=persisted.executor_signature,
    )
    manifest_row = ProtocolManifest(
        manifest_hash=manifest.manifest_hash,
        operation_id=manifest.operation_id,
        attempt_id=manifest.attempt_id,
        executor_id=manifest.executor_id,
        executor_release=manifest.executor_release,
        received_at=persisted.produced_at,
    )

    class _Session:
        def __init__(self) -> None:
            self._rows = iter((evidence_row, manifest_row))

        def scalar(self, _statement):
            return next(self._rows)

    with pytest.raises(ProtocolViolation, match="persisted_executor_evidence_mismatch"):
        require_persisted_verifier_inputs(
            session=_Session(),
            evidence=substituted,
            manifest=manifest,
        )


def test_missing_scope_evidence_persists_an_honest_review_required_result() -> None:
    try:
        from tests.platform_protocol.m1_r1a_synthetic_repair_harness import (
            run_review_required_chain,
        )
    except ImportError:
        pytest.fail(
            "v5_review_required_execution_path_missing",
            pytrace=False,
        )

    database_url = os.environ.get("NAUTILUS_PLATFORM_DATABASE_URL")
    if database_url is None:
        pytest.skip(
            "NAUTILUS_PLATFORM_DATABASE_URL is required for the local R1a chain (factory env)"
        )

    result = run_review_required_chain(
        database_url=database_url,
        platform_root=Path(__file__).resolve().parents[4],
        v5_authority_root=_required_directory("NAUTILUS_V5_AUTHORITY_ROOT"),
        v5_executor_root=_required_directory("NAUTILUS_V5_EXECUTOR_ROOT"),
        compass_authority_root=_required_directory("NAUTILUS_COMPASS_AUTHORITY_ROOT"),
    )

    assert result.executor_result_state == "review_required"
    assert result.repair_completed is False
    assert result.receipt_decision == "accepted"
    assert result.receipt_reason_codes == ("policy_satisfied",)
    assert result.operation_state == "receipt_verified"
    assert result.protocol_row_counts == {
        "operations": 1,
        "attempts": 1,
        "executor_evidence": 1,
        "manifests": 1,
        "receipts": 1,
        "audit_events": 4,
        "outbox_events": 3,
    }


@pytest.mark.parametrize(
    "database_url",
    (
        "postgresql+psycopg2://postgres@localhost:5432/nautilus_platform_g1b_20260813000000",
        "postgresql+psycopg2://postgres@127.0.0.1:5433/nautilus_platform_g1b_20260813000000",
        "postgresql+psycopg2://postgres@127.0.0.1:5432/postgres",
        "postgresql+psycopg2://postgres@127.0.0.1:5432/nautilus_platform_g1b_20260813000000?options=-csearch_path%3Dshadow",
    ),
)
def test_task6_cli_rejects_widened_database_targets(database_url: str) -> None:
    try:
        from tests.platform_protocol.test_m1_r1a_synthetic_repair_cli import (
            _validated_database_url,
        )
    except ModuleNotFoundError:
        pytest.fail("task6_cli_missing", pytrace=False)

    with pytest.raises(ValueError, match="disposable_database_url_rejected"):
        _validated_database_url(database_url)


def test_task6_cli_requires_an_empty_explicit_public_schema() -> None:
    try:
        from tests.platform_protocol.test_m1_r1a_synthetic_repair_cli import (
            _require_empty_public_schema,
        )
    except ImportError:
        pytest.fail("task6_empty_schema_gate_missing", pytrace=False)

    database_url = os.environ.get("NAUTILUS_PLATFORM_DATABASE_URL")
    if database_url is None:
        pytest.skip("NAUTILUS_PLATFORM_DATABASE_URL is required (factory env)")
    engine = sa.create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(sa.text("DROP TABLE IF EXISTS platform_schema_version"))
        _require_empty_public_schema(database_url)
        with engine.begin() as connection:
            connection.execute(sa.text("CREATE TABLE dogfood_shadow (id integer)"))
        with pytest.raises(
            ValueError, match="disposable_database_public_schema_not_empty"
        ):
            _require_empty_public_schema(database_url)
    finally:
        with engine.begin() as connection:
            connection.execute(sa.text("DROP TABLE IF EXISTS dogfood_shadow"))
        engine.dispose()


def test_task6_exact_protocol_replay_has_zero_growth() -> None:
    try:
        from tests.platform_protocol.test_m1_r1a_synthetic_repair_cli import (
            run_replayed_chain,
        )
    except ImportError:
        pytest.fail("task6_replay_runner_missing", pytrace=False)

    database_url = os.environ.get("NAUTILUS_PLATFORM_DATABASE_URL")
    if database_url is None:
        pytest.skip("NAUTILUS_PLATFORM_DATABASE_URL is required (factory env)")
    replay = run_replayed_chain(
        database_url=database_url,
        platform_root=Path(__file__).resolve().parents[4],
        v5_authority_root=_required_directory("NAUTILUS_V5_AUTHORITY_ROOT"),
        v5_executor_root=_required_directory("NAUTILUS_V5_EXECUTOR_ROOT"),
        compass_authority_root=_required_directory("NAUTILUS_COMPASS_AUTHORITY_ROOT"),
    )

    assert replay.chain.operation_state == "receipt_verified"
    assert replay.chain.repair_completed is True
    assert replay.exact_replay_count == 6
    assert replay.row_growth == 0
    assert replay.audit_growth == 0
    assert replay.outbox_growth == 0
    assert len(replay.manifest_hash) == 64
    int(replay.manifest_hash, 16)


def test_task6_failure_matrix_is_complete_and_has_no_fallback() -> None:
    try:
        from tests.platform_protocol.test_m1_r1a_synthetic_repair_cli import (
            TASK6_FAILURE_MATRIX,
        )
    except ImportError:
        pytest.fail("task6_failure_matrix_missing", pytrace=False)

    expected = {
        "owner_commit",
        "owner_path",
        "owner_hash",
        "runtime_admission",
        "caller_credential",
        "dmas_zero_match",
        "dmas_multiple_match",
        "executor_identity",
        "executor_release",
        "executor_key",
        "tool_policy",
        "lease",
        "attempt_hmac",
        "capsule",
        "fixture",
        "artifact",
        "executor_evidence_forged",
        "evidence_binding_tamper",
        "evidence_replay_mismatch",
        "manifest",
        "grant_nonce",
        "grant_expiry",
        "verifier_identity",
        "verifier_release",
        "verifier_key",
        "verifier_signature",
        "oracle_result",
        "transaction_injection",
        "concurrent_attempt_claim",
        "changed_request_replay",
        "changed_attempt_replay",
        "changed_manifest_replay",
        "changed_receipt_replay",
    }
    assert {entry.boundary for entry in TASK6_FAILURE_MATRIX} == expected
    assert all(entry.fallback == "none" for entry in TASK6_FAILURE_MATRIX)
    assert all(
        entry.stage
        in {"pre_operation", "claim", "pre_manifest", "post_manifest", "transaction"}
        for entry in TASK6_FAILURE_MATRIX
    )
    for entry in TASK6_FAILURE_MATRIX:
        module_name, function_name = entry.test_node.rsplit(":", 1)
        assert callable(getattr(importlib.import_module(module_name), function_name))


def test_task6_failure_matrix_runner_executes_only_the_exact_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.platform_protocol import test_m1_r1a_synthetic_repair_cli as cli

    calls: list[tuple[list[str], dict[str, str], Path]] = []

    class Completed:
        returncode = 0

    def completed_run(
        arguments: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        check: bool,
        capture_output: bool,
        timeout: int,
    ) -> Completed:
        assert check is False
        assert capture_output is True
        assert timeout == 240
        calls.append((arguments, env, cwd))
        return Completed()

    monkeypatch.setattr(cli.subprocess, "run", completed_run)
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("PYTEST_PLUGINS", "prohibited_plugin")
    database_url = (
        "postgresql+psycopg2://postgres@127.0.0.1:5432/"
        "nautilus_platform_g1b_20260813000000"
    )
    try:
        executed = cli._run_failure_matrix_tests(
            database_url=database_url,
            backend_root=Path(__file__).resolve().parents[2],
        )
    except AttributeError:
        pytest.fail("task6_failure_matrix_runner_missing", pytrace=False)

    assert executed == len(cli.TASK6_FAILURE_MATRIX) == 33
    assert len(calls) == 1
    arguments, environment, cwd = calls[0]
    assert arguments[:3] == [cli.sys.executable, "-m", "pytest"]
    assert arguments[3] == cli._pytest_node(cli._VERTICAL_TAMPER_NODE)
    assert arguments[-6:] == [
        "-o",
        "addopts=",
        "-q",
        "--confcutdir=tests/platform_protocol",
        "-p",
        "no:cacheprovider",
    ]
    assert set(arguments[3:-6]) == {
        cli._pytest_node(entry.test_node) for entry in cli.TASK6_FAILURE_MATRIX
    }
    assert environment["NAUTILUS_PLATFORM_DATABASE_URL"] == database_url
    assert environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert "PYTEST_ADDOPTS" not in environment
    assert "PYTEST_PLUGINS" not in environment
    assert cwd == Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("boundary", "expected_stage", "expected_verifier_calls"),
    (
        ("attempt_hmac", "pre_manifest", 0),
        ("capsule", "pre_manifest", 0),
        ("fixture", "pre_manifest", 0),
        ("artifact", "pre_manifest", 0),
        ("grant_nonce", "post_manifest", 1),
        ("grant_expiry", "post_manifest", 0),
        ("oracle_result", "post_manifest", 1),
    ),
)
def test_task6_vertical_boundary_tamper_stops_at_expected_stage(
    boundary: str, expected_stage: str, expected_verifier_calls: int
) -> None:
    try:
        from tests.platform_protocol.test_m1_r1a_synthetic_repair_cli import (
            run_vertical_boundary_failure,
        )
    except ImportError:
        pytest.fail("task6_vertical_failure_runner_missing", pytrace=False)

    database_url = os.environ.get("NAUTILUS_PLATFORM_DATABASE_URL")
    if database_url is None:
        pytest.skip("NAUTILUS_PLATFORM_DATABASE_URL is required (factory env)")
    result = run_vertical_boundary_failure(
        boundary=boundary,
        database_url=database_url,
        platform_root=Path(__file__).resolve().parents[4],
        v5_authority_root=_required_directory("NAUTILUS_V5_AUTHORITY_ROOT"),
        v5_executor_root=_required_directory("NAUTILUS_V5_EXECUTOR_ROOT"),
        compass_authority_root=_required_directory("NAUTILUS_COMPASS_AUTHORITY_ROOT"),
    )

    expected = {
        "pre_manifest": (
            "dispatched",
            {
                "operations": 1,
                "attempts": 1,
                "executor_evidence": 0,
                "manifests": 0,
                "receipts": 0,
                "audit_events": 2,
                "outbox_events": 1,
            },
        ),
        "post_manifest": (
            "manifest_received",
            {
                "operations": 1,
                "attempts": 1,
                "executor_evidence": 1,
                "manifests": 1,
                "receipts": 0,
                "audit_events": 3,
                "outbox_events": 2,
            },
        ),
    }[expected_stage]
    assert result.operation_state == expected[0]
    assert result.row_counts == expected[1]
    assert result.executor_calls == 1
    assert result.verifier_calls == expected_verifier_calls
    assert result.network_delivery_count == 0
    assert result.fallback == "none"


def _valid_task6_evidence() -> dict[str, object]:
    return {
        "schema_version": "m1-r1a-synthetic-repair-readback-v1",
        "evidence_level": "local_r1a",
        "source": {
            "platform_commit": "1" * 40,
            "failure_matrix_sha256": "2" * 64,
            "task6_cli_sha256": "3" * 64,
            "runtime_admission_sha256": "4" * 64,
            "v5_executor_commit": "5" * 40,
            "v5_contract_sha256": "6" * 64,
            "compass_authority_commit": "7" * 40,
            "compass_proposal_commit": "8" * 40,
            "compass_capsule_sha256": "9" * 64,
        },
        "protocol": {
            "contract_version": "protocol-v2-contracts-v1",
            "execution_evidence_contract_version": (
                "m1-r1a-executor-execution-evidence-v1"
            ),
            "policy_version": "pol_r1a_synthetic_repair_v1",
            "migration_head": "20260809_01_r1a_evidence",
            "operation_id": "op_r1a_vertical_01",
            "attempt_id": "att_r1a_vertical_01",
            "manifest_hash": "a" * 64,
        },
        "outcomes": {
            "positive": "completed",
            "missing_scope": "review_required",
            "receipt_decision": "accepted",
            "receipt_reason_codes": ["policy_satisfied"],
        },
        "counts": {
            "first_run_rows": {
                "operations": 1,
                "attempts": 1,
                "executor_evidence": 1,
                "manifests": 1,
                "receipts": 1,
            },
            "first_run_audit_events": 4,
            "first_run_outbox_events": 3,
        },
        "replay": {
            "exact_replay_count": 6,
            "row_growth": 0,
            "audit_growth": 0,
            "outbox_growth": 0,
        },
        "fail_closed": {"case_count": 33, "fallback_count": 0},
        "cleanup": {"database_present": 0, "protocol_tables": 0},
    }


def test_task6_evidence_document_accepts_only_exact_redacted_facts() -> None:
    try:
        from tests.platform_protocol.test_m1_r1a_synthetic_repair_cli import (
            _validate_evidence_document,
        )
    except ImportError:
        pytest.fail("task6_evidence_validator_missing", pytrace=False)
    document = _valid_task6_evidence()
    assert (
        _validate_evidence_document(
            document, expected_source=deepcopy(document["source"])
        )
        == document
    )


@pytest.mark.parametrize(
    ("section", "field", "value"),
    (
        ("top", "database_url", "postgresql://prohibited"),
        ("source", "contract_path", "docs/contracts/prohibited.json"),
        ("protocol", "signature", "sig_prohibited"),
        ("counts", "first_run_audit_events", 5),
        ("replay", "row_growth", 1),
        ("fail_closed", "fallback_count", 1),
        ("cleanup", "database_present", 1),
        ("outcomes", "positive", "claimed_without_proof"),
    ),
)
def test_task6_evidence_document_rejects_extra_sensitive_or_inexact_values(
    section: str, field: str, value: object
) -> None:
    from tests.platform_protocol.test_m1_r1a_synthetic_repair_cli import (
        _validate_evidence_document,
    )

    document = _valid_task6_evidence()
    expected_source = deepcopy(document["source"])
    target = document if section == "top" else document[section]
    assert isinstance(target, dict)
    target[field] = value
    with pytest.raises(ValueError, match="invalid_task6_evidence_document"):
        _validate_evidence_document(document, expected_source=expected_source)


@pytest.mark.parametrize(
    ("section", "field", "boolean"),
    (
        ("counts", "first_run_audit_events", False),
        ("replay", "audit_growth", False),
        ("fail_closed", "fallback_count", False),
        ("cleanup", "database_present", False),
    ),
)
def test_task6_evidence_document_rejects_boolean_count_aliases(
    section: str, field: str, boolean: bool
) -> None:
    from tests.platform_protocol.test_m1_r1a_synthetic_repair_cli import (
        _validate_evidence_document,
    )

    document = _valid_task6_evidence()
    expected_source = deepcopy(document["source"])
    target = document[section]
    assert isinstance(target, dict)
    target[field] = boolean
    with pytest.raises(ValueError, match="invalid_task6_evidence_document"):
        _validate_evidence_document(document, expected_source=expected_source)

    document = _valid_task6_evidence()
    expected_source = deepcopy(document["source"])
    counts = document["counts"]
    assert isinstance(counts, dict)
    rows = counts["first_run_rows"]
    assert isinstance(rows, dict)
    rows["operations"] = True
    with pytest.raises(ValueError, match="invalid_task6_evidence_document"):
        _validate_evidence_document(document, expected_source=expected_source)


def test_task6_authorized_database_cycle_is_deterministic_and_cleans_exact_target() -> (
    None
):
    database_url = os.environ.get("NAUTILUS_TASK6_DATABASE_URL")
    if database_url is None:
        pytest.skip("NAUTILUS_TASK6_DATABASE_URL is required for the authorized cycle")
    try:
        from tests.platform_protocol.test_m1_r1a_synthetic_repair_cli import (
            _database_exists,
            _run_authorized_database_cycle,
        )
    except ImportError:
        pytest.fail("task6_authorized_database_cycle_missing", pytrace=False)

    assert _database_exists(database_url) is False
    expected_source = deepcopy(_valid_task6_evidence()["source"])
    document = _run_authorized_database_cycle(
        database_url=database_url,
        platform_root=Path(__file__).resolve().parents[4],
        v5_authority_root=_required_directory("NAUTILUS_V5_AUTHORITY_ROOT"),
        v5_executor_root=_required_directory("NAUTILUS_V5_EXECUTOR_ROOT"),
        compass_authority_root=_required_directory("NAUTILUS_COMPASS_AUTHORITY_ROOT"),
        expected_source=expected_source,
    )

    assert document["source"] == expected_source
    assert document["cleanup"] == {"database_present": 0, "protocol_tables": 0}
    assert document["replay"] == {
        "exact_replay_count": 6,
        "row_growth": 0,
        "audit_growth": 0,
        "outbox_growth": 0,
    }
    assert _database_exists(database_url) is False


def test_task6_cli_accepts_one_url_and_uses_git_bound_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    try:
        from tests.platform_protocol import test_m1_r1a_synthetic_repair_cli as cli
    except ImportError:
        pytest.fail("task6_cli_entrypoint_missing", pytrace=False)
    if not hasattr(cli, "_main"):
        pytest.fail("task6_cli_entrypoint_missing", pytrace=False)

    database_url = (
        "postgresql+psycopg2://postgres@127.0.0.1:5432/"
        "nautilus_platform_g1b_20260813000000"
    )
    document = _valid_task6_evidence()
    source = deepcopy(document["source"])
    captured: list[dict[str, object]] = []
    monkeypatch.setenv("NAUTILUS_V5_AUTHORITY_ROOT", str(Path(__file__).parent))
    monkeypatch.setenv("NAUTILUS_V5_EXECUTOR_ROOT", str(Path(__file__).parent))
    monkeypatch.setenv("NAUTILUS_COMPASS_AUTHORITY_ROOT", str(Path(__file__).parent))
    monkeypatch.setattr(cli, "_read_source_binding", lambda _root: source)
    monkeypatch.setattr(
        cli,
        "_run_authorized_database_cycle",
        lambda **_kwargs: document,
    )
    monkeypatch.setattr(cli, "_write_evidence_document", captured.append)

    assert cli._main([database_url]) == 0
    assert captured == [document]
    for arguments in ([], [database_url, "unexpected"]):
        with pytest.raises(ValueError, match="exactly_one_database_url_required"):
            cli._main(arguments)


def _fixture_git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _task6_evidence_repository(
    tmp_path: Path,
    *,
    evidence_parent: str = "source",
    extra_evidence_path: bool = False,
) -> tuple[Path, str, bytes]:
    root = tmp_path / "task6-evidence-repository"
    root.mkdir()
    _fixture_git(root, "init", "--initial-branch=main")
    _fixture_git(root, "config", "user.name", "Task 7-B Test")
    _fixture_git(root, "config", "user.email", "task7b@example.invalid")
    (root / "source.txt").write_text("source\n", encoding="utf-8", newline="\n")
    _fixture_git(root, "add", "source.txt")
    _fixture_git(root, "commit", "-m", "source")
    source_commit = _fixture_git(root, "rev-parse", "HEAD")

    if evidence_parent == "intermediate":
        _fixture_git(root, "commit", "--allow-empty", "-m", "intermediate")
    elif evidence_parent == "merge":
        _fixture_git(root, "switch", "-c", "empty-side")
        _fixture_git(root, "commit", "--allow-empty", "-m", "empty side")
        _fixture_git(root, "switch", "main")
        _fixture_git(root, "merge", "--no-ff", "--no-commit", "empty-side")
    elif evidence_parent != "source":
        raise AssertionError("unknown evidence parent fixture")

    evidence_bytes = b'{"evidence_version":"task6-test-v1"}\n'
    evidence_path = root / "phase3/backend/docs/evidence/readback.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_bytes(evidence_bytes)
    _fixture_git(root, "add", "phase3/backend/docs/evidence/readback.json")
    if extra_evidence_path:
        (root / "extra.txt").write_text("extra\n", encoding="utf-8", newline="\n")
        _fixture_git(root, "add", "extra.txt")
    _fixture_git(root, "commit", "-m", "evidence")
    return root, source_commit, evidence_bytes


def _commit_descendant(root: Path, name: str, content: str) -> None:
    (root / name).write_text(content, encoding="utf-8", newline="\n")
    _fixture_git(root, "add", name)
    _fixture_git(root, "commit", "-m", f"descendant {name}")


def test_task6_evidence_relation_allows_an_unmodified_descendant_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.platform_protocol import test_m1_r1a_synthetic_repair_cli as cli

    monkeypatch.setattr(
        cli,
        "_TASK6_EVIDENCE_PATH",
        "phase3/backend/docs/evidence/readback.json",
    )
    root, source_commit, _evidence_bytes = _task6_evidence_repository(tmp_path)
    _commit_descendant(root, "later.txt", "later\n")

    cli._require_committed_evidence_relation(root, source_commit=source_commit)


@pytest.mark.parametrize(
    ("evidence_parent", "extra_evidence_path"),
    (("intermediate", False), ("merge", False), ("source", True)),
)
def test_task6_evidence_relation_rejects_invalid_original_evidence_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    evidence_parent: str,
    extra_evidence_path: bool,
) -> None:
    from tests.platform_protocol import test_m1_r1a_synthetic_repair_cli as cli

    monkeypatch.setattr(
        cli,
        "_TASK6_EVIDENCE_PATH",
        "phase3/backend/docs/evidence/readback.json",
    )
    root, source_commit, _evidence_bytes = _task6_evidence_repository(
        tmp_path,
        evidence_parent=evidence_parent,
        extra_evidence_path=extra_evidence_path,
    )
    with pytest.raises(ValueError, match="invalid_task6_evidence_commit_relation"):
        cli._require_committed_evidence_relation(root, source_commit=source_commit)


@pytest.mark.parametrize("restore_original", (False, True))
def test_task6_evidence_relation_rejects_any_descendant_evidence_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_original: bool,
) -> None:
    from tests.platform_protocol import test_m1_r1a_synthetic_repair_cli as cli

    evidence_path = "phase3/backend/docs/evidence/readback.json"
    monkeypatch.setattr(cli, "_TASK6_EVIDENCE_PATH", evidence_path)
    root, source_commit, evidence_bytes = _task6_evidence_repository(tmp_path)
    (root / evidence_path).write_bytes(b'{"tampered":true}\n')
    _fixture_git(root, "add", evidence_path)
    _fixture_git(root, "commit", "-m", "tamper evidence")
    if restore_original:
        (root / evidence_path).write_bytes(evidence_bytes)
        _fixture_git(root, "add", evidence_path)
        _fixture_git(root, "commit", "-m", "restore evidence")

    with pytest.raises(ValueError, match="invalid_task6_evidence_commit_relation"):
        cli._require_committed_evidence_relation(root, source_commit=source_commit)


def test_task6_evidence_relation_rejects_a_dirty_descendant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.platform_protocol import test_m1_r1a_synthetic_repair_cli as cli

    monkeypatch.setattr(
        cli,
        "_TASK6_EVIDENCE_PATH",
        "phase3/backend/docs/evidence/readback.json",
    )
    root, source_commit, _evidence_bytes = _task6_evidence_repository(tmp_path)
    (root / "untracked.txt").write_text("dirty\n", encoding="utf-8", newline="\n")

    with pytest.raises(ValueError, match="task6_evidence_worktree_not_clean"):
        cli._require_committed_evidence_relation(root, source_commit=source_commit)


def test_task6_committed_evidence_is_canonical_redacted_and_source_bound() -> None:
    from tests.platform_protocol import test_m1_r1a_synthetic_repair_cli as cli

    platform_root = Path(__file__).resolve().parents[4]
    evidence_path = platform_root / cli._TASK6_EVIDENCE_PATH
    if not evidence_path.is_file():
        pytest.skip("Task 6 evidence is committed only after the code commit")

    evidence_bytes = cli._git_bytes(
        platform_root, "show", f"HEAD:{cli._TASK6_EVIDENCE_PATH}"
    )
    # 2026-09-15:运行机(evidence 目录有运行产物/未跟踪快照)非干净 checkout,
    # 证据提交一致性只能在工厂 checkout 上验——本机 skip,不算失败
    porcelain = cli._git_bytes(platform_root, "status", "--porcelain")
    if porcelain.strip():
        pytest.skip("worktree has runtime artifacts; verify on factory checkout")
    document = cli._parse_json_object(evidence_bytes)
    source = document.get("source")
    assert isinstance(source, dict)
    source_commit = source.get("platform_commit")
    assert isinstance(source_commit, str)
    expected_source = cli._read_source_binding(
        platform_root,
        platform_commit=source_commit,
        require_clean=False,
    )
    assert (
        cli._validate_evidence_document(document, expected_source=expected_source)
        == document
    )
    cli._require_committed_evidence_relation(platform_root, source_commit=source_commit)
    assert evidence_bytes == (
        json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    serialized = evidence_bytes.decode("utf-8").lower()
    for prohibited in (
        "database_url",
        "postgresql",
        "private_key",
        "signature",
        "attempt_secret",
        "raw_evidence",
        "dialogue",
        "prompt",
        "account",
        "token",
    ):
        assert prohibited not in serialized

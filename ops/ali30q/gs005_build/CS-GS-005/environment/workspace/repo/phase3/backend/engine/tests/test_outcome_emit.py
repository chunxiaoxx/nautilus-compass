"""Tests for engine.outcome_emit · invariant: never raises."""
from pathlib import Path
from unittest.mock import MagicMock, patch

from engine import outcome_emit
from engine.outcome_emit import emit_outcome


# Reset module-level bootstrap flag between tests so DDL paths are re-exercised
def _reset_bootstrap():
    outcome_emit._SCHEMA_BOOTSTRAPPED = False


def _sample_row() -> dict:
    return {
        "cycle_id": "test_2026-05-25_x",
        "spec": "do thing\n\nSpec-Meta:\n  expected_added: 2\n",
        "spec_expected_added": 2,
        "spec_expected_removed": 0,
        "ship_status": "success",
        "semantic_pass": True,
        "tests_pass": True,
        "actual_lines_added": 2,
        "actual_lines_removed": 0,
        "drift_ratio": 1.0,
        "composite_score": 1.0,
        "git_sha": "abc1234",
        "cert_id": None,
    }


def test_emit_no_dsn_falls_back_to_jsonl(tmp_path, monkeypatch):
    _reset_bootstrap()
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)
    emit_outcome(_sample_row())
    fallback = tmp_path / ".engine-outcomes.jsonl"
    assert fallback.exists()
    assert "test_2026-05-25_x" in fallback.read_text()


def test_emit_db_success_no_jsonl(tmp_path, monkeypatch):
    _reset_bootstrap()
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")
    monkeypatch.chdir(tmp_path)

    fake_conn = MagicMock()
    fake_conn.__enter__ = MagicMock(return_value=fake_conn)
    fake_conn.__exit__ = MagicMock(return_value=False)
    fake_cursor = MagicMock()
    fake_conn.cursor.return_value.__enter__ = MagicMock(return_value=fake_cursor)
    fake_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("psycopg.connect", return_value=fake_conn):
        emit_outcome(_sample_row())

    fake_cursor.execute.assert_called()
    fake_conn.commit.assert_called()
    # No jsonl on happy path
    assert not (tmp_path / ".engine-outcomes.jsonl").exists()


def test_emit_db_fail_jsonl_fallback(tmp_path, monkeypatch):
    _reset_bootstrap()
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")
    monkeypatch.chdir(tmp_path)

    with patch("psycopg.connect", side_effect=Exception("simulated DB down")):
        emit_outcome(_sample_row())

    fallback = tmp_path / ".engine-outcomes.jsonl"
    assert fallback.exists()
    assert "test_2026-05-25_x" in fallback.read_text()


def test_emit_deadletter_routing(tmp_path, monkeypatch):
    _reset_bootstrap()
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")
    monkeypatch.chdir(tmp_path)

    fake_conn = MagicMock()
    fake_conn.__enter__ = MagicMock(return_value=fake_conn)
    fake_conn.__exit__ = MagicMock(return_value=False)
    fake_cursor = MagicMock()
    fake_conn.cursor.return_value.__enter__ = MagicMock(return_value=fake_cursor)
    fake_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    dl_row = {
        "cycle_id": "test_dl",
        "reason": "parse_error",
        "raw_error": "no parseable file blocks",
    }
    with patch("psycopg.connect", return_value=fake_conn):
        emit_outcome(dl_row)

    # Verify deadletter SQL was the one executed (look at last execute call)
    calls = [str(c) for c in fake_cursor.execute.call_args_list]
    assert any("engine_cycle_deadletter" in c for c in calls), \
        f"expected deadletter insert · got {calls}"


def test_emit_never_raises_on_total_failure(tmp_path, monkeypatch):
    _reset_bootstrap()
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")
    monkeypatch.chdir(tmp_path)

    # Both DB and jsonl unavailable: jsonl write fail by simulating IOError
    with patch("psycopg.connect", side_effect=Exception("DB down")):
        with patch.object(outcome_emit, "_jsonl_append", side_effect=OSError("disk full")):
            # Must not raise
            emit_outcome(_sample_row())


def test_bootstrap_runs_only_once_per_process(tmp_path, monkeypatch):
    _reset_bootstrap()
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")
    monkeypatch.chdir(tmp_path)

    fake_conn = MagicMock()
    fake_conn.__enter__ = MagicMock(return_value=fake_conn)
    fake_conn.__exit__ = MagicMock(return_value=False)
    fake_cursor = MagicMock()
    fake_conn.cursor.return_value.__enter__ = MagicMock(return_value=fake_cursor)
    fake_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("psycopg.connect", return_value=fake_conn):
        emit_outcome(_sample_row())
        first_call_count = len(fake_cursor.execute.call_args_list)
        emit_outcome(_sample_row())
        second_call_count = len(fake_cursor.execute.call_args_list)

    # First call: 5 DDL + 1 INSERT = 6. Second call: only 1 INSERT (bootstrap skipped).
    assert second_call_count - first_call_count == 1, \
        f"bootstrap should run once · second emit ran {second_call_count - first_call_count} statements"

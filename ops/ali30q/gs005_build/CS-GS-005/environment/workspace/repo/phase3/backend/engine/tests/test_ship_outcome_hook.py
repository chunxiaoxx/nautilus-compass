"""Integration test · ship.py auto-emits outcome row at each return site."""
from pathlib import Path
from unittest.mock import MagicMock, patch

from engine.nautilus_engine import NautilusEngine
from engine.ship import ship, _auto_cycle_id


def _mock_llm_returning(text: str) -> MagicMock:
    fake = MagicMock()
    fake.chat = MagicMock(return_value=text)
    return fake


def test_ship_emits_outcome_on_deadletter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # LLM returns no parseable blocks → deadletter path
    eng = NautilusEngine(
        llm_client=_mock_llm_returning("just prose · no fenced code blocks"),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    captured: list[dict] = []
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: captured.append(row)):
        result = ship(
            eng, task="test task",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
        )

    assert len(captured) == 1
    row = captured[0]
    assert row["cycle_id"].startswith("2026"), f"cycle_id auto-gen format · got {row['cycle_id']}"
    assert row.get("reason") == "parse_error", f"deadletter row · got {row}"
    assert "no parseable file blocks" in row.get("raw_error", "")


def test_ship_skips_emit_on_dryrun_with_passing_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # LLM returns parseable blocks but apply=False → after Gap 2 fix, no emit
    code_output = (
        "```python:hello.py\n"
        "def greet(): return 'hi'\n"
        "```\n"
    )
    eng = NautilusEngine(
        llm_client=_mock_llm_returning(code_output),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    captured: list[dict] = []
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: captured.append(row)):
        result = ship(
            eng, task="add greet function",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
        )

    # After Gap 2 fix (emit-skip dry-run): apply=False + passing checks + no errors
    # → row is skipped to avoid biasing v_engine_progress.avg_composite.
    assert captured == [], f"dry-run with passing blocks should be skipped · got {len(captured)} row(s)"
    assert result is not None
    assert not result.applied


def test_ship_custom_cycle_id_honored(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    eng = NautilusEngine(
        llm_client=_mock_llm_returning("no blocks here"),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    captured: list[dict] = []
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: captured.append(row)):
        ship(
            eng, task="x",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
            cycle_id="manual_cycle_42",
        )
    assert captured[0]["cycle_id"] == "manual_cycle_42"


def test_ship_emit_disabled(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    eng = NautilusEngine(
        llm_client=_mock_llm_returning("no blocks"),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    captured: list[dict] = []
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: captured.append(row)):
        ship(
            eng, task="x",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
            emit_outcome_telemetry=False,  # opt-out
        )
    assert captured == [], "telemetry opt-out should suppress emit"


def test_ship_emit_failure_does_not_break_pipeline(tmp_path, monkeypatch):
    """If emit_outcome itself raises (which it shouldn't · invariant), ship still returns."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    eng = NautilusEngine(
        llm_client=_mock_llm_returning("no blocks"),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    # Force the unthinkable: emit_outcome raises
    with patch("engine.ship.emit_outcome", side_effect=RuntimeError("simulated bug")):
        result = ship(
            eng, task="x",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
        )
    # Pipeline must still return a result · not propagate the exception
    assert result is not None
    assert result.errors  # at least the no-blocks error


def test_auto_cycle_id_stable_for_same_task():
    a = _auto_cycle_id("hello world")
    b = _auto_cycle_id("hello world")
    assert a == b, "same task on same UTC day → same cycle_id"


def test_auto_cycle_id_differs_for_different_tasks():
    a = _auto_cycle_id("task A")
    b = _auto_cycle_id("task B")
    assert a != b

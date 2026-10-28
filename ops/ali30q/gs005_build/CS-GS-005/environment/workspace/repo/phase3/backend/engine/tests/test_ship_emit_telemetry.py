"""Test emit-skip behavior for dry-run cycles · closes Gap 2 (handoff 2026-05-25).

The skip rule: if ship completes with apply=False AND no errors AND
parseable blocks → it is a dry-run preview, not a failure. Such rows
would bias v_engine_progress.avg_composite downward.
"""
from unittest.mock import MagicMock, patch

from engine.nautilus_engine import NautilusEngine
from engine.ship import ship


def _mock_llm(text: str) -> MagicMock:
    fake = MagicMock()
    fake.chat = MagicMock(return_value=text)
    return fake


_VALID_BLOCK = (
    "```python:hello.py\n"
    "def greet():\n"
    "    return 'hi'\n"
    "```\n"
)


def test_emit_skipped_when_dry_run_success(tmp_path, monkeypatch):
    """apply=False · checks pass · no errors · has blocks → NO emit."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    eng = NautilusEngine(
        llm_client=_mock_llm(_VALID_BLOCK),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    captured = []
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: captured.append(row)):
        result = ship(
            eng, task="add greet to hello.py",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
        )
    assert result is not None
    assert not result.applied
    assert not result.errors, f"dry-run with passing checks should have no errors · got {result.errors}"
    assert captured == [], f"dry-run with passing checks must NOT emit · captured {len(captured)} row(s)"


def test_emit_called_when_apply_success(tmp_path, monkeypatch):
    """apply=True · checks pass → emit called once with ship_status row."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    eng = NautilusEngine(
        llm_client=_mock_llm(_VALID_BLOCK),
        base_dir=str(tmp_path),
        dry_run=True,  # engine-level dry_run · ship() apply=True writes anyway
    )
    captured = []
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: captured.append(row)):
        ship(
            eng, task="add greet",
            base_dir=str(tmp_path),
            apply=True, dispatch_audit=False,
        )
    assert len(captured) == 1, f"apply=True success must emit exactly 1 row · captured {len(captured)}"
    assert captured[0].get("reason") is None
    assert "ship_status" in captured[0]


def test_emit_called_when_parse_error_deadletter(tmp_path, monkeypatch):
    """LLM returns no parseable blocks → deadletter row emitted (NOT skipped)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    eng = NautilusEngine(
        llm_client=_mock_llm("just prose no fenced code"),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    captured = []
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: captured.append(row)):
        ship(
            eng, task="x",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
        )
    assert len(captured) == 1
    assert captured[0].get("reason") == "parse_error", f"deadletter row · got {captured[0]}"


def test_emit_called_when_dry_run_has_errors(tmp_path, monkeypatch):
    """apply=False BUT checks fail (errors set) → emit called (intentional fail visible)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # LLM returns syntax-broken Python · check pipeline fails · errors set
    broken = (
        "```python:broken.py\n"
        "def f(:\n"  # syntax error
        "    pass\n"
        "```\n"
    )
    eng = NautilusEngine(
        llm_client=_mock_llm(broken),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    captured = []
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: captured.append(row)):
        ship(
            eng, task="x",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
        )
    # apply=False + errors set → not dry-run-success · MUST emit
    assert len(captured) == 1, f"dry-run with check failures must emit · captured {len(captured)}"
    assert captured[0].get("reason") is None  # not deadletter · normal row
    assert captured[0]["ship_status"] in ("fail", "partial")

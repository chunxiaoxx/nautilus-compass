"""TDD tests for ship() self-healing retry loop · cycle 8.

Automates the cycle 5 -> 5b feedback pattern: when static checks fail on the
first generation attempt, re-prompt the LLM with explicit error context and
the previous attempt's file paths, then try again.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from engine.ship import ship, ShipResult


def _make_engine_seq(responses: list[str], base_dir: Path) -> MagicMock:
    """Mock engine that returns successive responses across generate() calls."""
    mock = MagicMock()
    iterator = iter(responses)
    mock.generate.side_effect = lambda *_a, **_kw: next(iterator)
    from engine.nautilus_engine import NautilusEngine
    real = NautilusEngine(llm_client=MagicMock(), base_dir=str(base_dir))
    mock.parse_file_blocks.side_effect = real.parse_file_blocks
    return mock


# ---------- baseline · no retry ----------

def test_default_max_retries_is_zero(tmp_path: Path):
    """No retry by default · single attempt only."""
    engine = _make_engine_seq(
        ['```python:bad.py\ndef (\n```'],
        tmp_path,
    )
    result = ship(engine, "task", base_dir=str(tmp_path), apply=False, dispatch_audit=False)
    # Only one generate call should have been made
    assert engine.generate.call_count == 1
    assert hasattr(result, "attempts")
    assert len(result.attempts) == 1
    assert result.attempts[0]["check_result"]["passed"] is False


def test_no_retry_when_first_attempt_passes(tmp_path: Path):
    engine = _make_engine_seq(
        ['```python:ok.py\nx = 1\n```'],
        tmp_path,
    )
    result = ship(
        engine, "task", base_dir=str(tmp_path), apply=False,
        dispatch_audit=False, max_retries=2,
    )
    # Passes on attempt 1 · no retries used
    assert engine.generate.call_count == 1
    assert len(result.attempts) == 1
    assert result.attempts[0]["check_result"]["passed"] is True


# ---------- retry triggers ----------

def test_retry_triggered_on_check_fail(tmp_path: Path):
    """Broken first attempt + fixed second = success after 1 retry."""
    engine = _make_engine_seq(
        [
            '```python:f.py\ndef (\n```',      # syntax error
            '```python:f.py\nx = 1\n```',      # fixed
        ],
        tmp_path,
    )
    result = ship(
        engine, "task", base_dir=str(tmp_path), apply=False,
        dispatch_audit=False, max_retries=1,
    )
    assert engine.generate.call_count == 2
    assert len(result.attempts) == 2
    assert result.attempts[0]["check_result"]["passed"] is False
    assert result.attempts[1]["check_result"]["passed"] is True
    # Final check_result mirrors the last (successful) attempt
    assert result.check_result["passed"] is True
    assert result.errors == []


def test_retry_gives_up_after_max(tmp_path: Path):
    """Both attempts broken with max_retries=1 = total fail."""
    engine = _make_engine_seq(
        [
            '```python:f.py\ndef (\n```',     # broken 1
            '```python:f.py\ndef (\n```',     # broken 2 (same)
        ],
        tmp_path,
    )
    result = ship(
        engine, "task", base_dir=str(tmp_path), apply=False,
        dispatch_audit=False, max_retries=1,
    )
    assert engine.generate.call_count == 2
    assert len(result.attempts) == 2
    assert result.check_result["passed"] is False
    assert any("after 2 attempts" in e for e in result.errors)


def test_retry_prompt_includes_failed_check_messages(tmp_path: Path):
    """Retry prompt must reference the failed check + previous file path."""
    engine = _make_engine_seq(
        [
            '```python:auth.py\ndef (\n```',    # syntax error
            '```python:auth.py\nx = 1\n```',    # fixed
        ],
        tmp_path,
    )
    ship(
        engine, "build auth", base_dir=str(tmp_path), apply=False,
        dispatch_audit=False, max_retries=1,
    )
    # Second generate() call should have augmented prompt
    second_call_args = engine.generate.call_args_list[1]
    retry_prompt = second_call_args[0][0]
    assert "auth.py" in retry_prompt
    assert "FAILED" in retry_prompt or "failed" in retry_prompt
    assert "build auth" in retry_prompt  # original task preserved


# ---------- attempts trace ----------

def test_attempts_field_records_each_try(tmp_path: Path):
    engine = _make_engine_seq(
        [
            '```python:f.py\ndef (\n```',
            '```python:f.py\nstill_broken( = 1\n```',
            '```python:f.py\nx = 1\n```',
        ],
        tmp_path,
    )
    result = ship(
        engine, "task", base_dir=str(tmp_path), apply=False,
        dispatch_audit=False, max_retries=2,
    )
    assert len(result.attempts) == 3
    # Each attempt has attempt_number, raw_response_chars, files_planned, check_result
    for i, att in enumerate(result.attempts, start=1):
        assert att["attempt_number"] == i
        assert "raw_response_chars" in att
        assert "files_planned" in att
        assert "check_result" in att
        # Blocks (full content) should not leak into attempts for size
        assert "blocks" not in att


# ---------- apply gating after retry ----------

def test_apply_uses_final_successful_attempt(tmp_path: Path):
    import subprocess
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    (tmp_path / "seed.txt").write_text("seed\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "seed.txt"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "seed"], check=True)

    engine = _make_engine_seq(
        [
            '```python:retry_target.py\ndef (\n```',           # broken
            '```python:retry_target.py\nfinal = "ok"\n```',    # fixed
        ],
        tmp_path,
    )
    result = ship(
        engine, "task", base_dir=str(tmp_path), apply=True,
        dispatch_audit=False, max_retries=1,
        git_commit_msg="feat: retry then apply",
    )
    assert result.applied is True
    target = tmp_path / "retry_target.py"
    assert target.exists()
    assert target.read_text(encoding="utf-8") == 'final = "ok"'


def test_retry_does_not_apply_if_both_fail(tmp_path: Path):
    engine = _make_engine_seq(
        [
            '```python:f.py\ndef (\n```',
            '```python:f.py\nalso bad (\n```',
        ],
        tmp_path,
    )
    result = ship(
        engine, "task", base_dir=str(tmp_path), apply=True,
        dispatch_audit=False, max_retries=1,
    )
    assert result.applied is False
    assert not (tmp_path / "f.py").exists()

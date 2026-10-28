"""TDD tests for engine.ship · cycle 4 orchestrator (check → audit → commit)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from engine.ship import ship, ShipResult


def _make_engine(generated_text: str, base_dir: Path) -> MagicMock:
    """Build a mock engine whose generate() returns the given LLM-style output."""
    mock = MagicMock()
    mock.generate.return_value = generated_text
    # parse_file_blocks delegated to real implementation
    from engine.nautilus_engine import NautilusEngine
    real = NautilusEngine(llm_client=MagicMock(), base_dir=str(base_dir))
    mock.parse_file_blocks.side_effect = real.parse_file_blocks
    return mock


def _init_git(repo_dir: Path) -> None:
    subprocess.run(["git", "init", "-q", str(repo_dir)], check=True)
    subprocess.run(["git", "-C", str(repo_dir), "config", "user.email", "test@nautilus"], check=True)
    subprocess.run(["git", "-C", str(repo_dir), "config", "user.name", "Nautilus Test"], check=True)
    # Initial commit so we have a HEAD
    seed = repo_dir / "seed.txt"
    seed.write_text("seed\n")
    subprocess.run(["git", "-C", str(repo_dir), "add", "seed.txt"], check=True)
    subprocess.run(["git", "-C", str(repo_dir), "commit", "-q", "-m", "seed"], check=True)


# ---------- happy / dry-run paths ----------

def test_ship_dry_run_returns_files_planned(tmp_path: Path):
    engine = _make_engine('```python:hello.py\nx = 1\n```', tmp_path)
    result = ship(engine, "make hello", base_dir=str(tmp_path), apply=False, dispatch_audit=False)
    assert isinstance(result, ShipResult)
    assert len(result.files_planned) == 1
    assert result.files_planned[0]["path"] == "hello.py"
    assert result.applied is False
    # Dry-run must NOT touch base_dir
    assert not (tmp_path / "hello.py").exists()


def test_ship_returns_empty_when_no_blocks(tmp_path: Path):
    engine = _make_engine("no code blocks here just prose", tmp_path)
    result = ship(engine, "task", base_dir=str(tmp_path), apply=False, dispatch_audit=False)
    assert result.files_planned == []
    assert result.applied is False
    assert any("no parseable" in e.lower() or "no files" in e.lower() or "empty" in e.lower() for e in result.errors)


# ---------- check pipeline integration ----------

def test_ship_runs_check_pipeline_on_staged_files(tmp_path: Path):
    engine = _make_engine('```python:hello.py\nx = 1\n```', tmp_path)
    result = ship(engine, "make hello", base_dir=str(tmp_path), apply=False, dispatch_audit=False)
    assert result.check_result["passed"] is True
    assert len(result.check_result["checks"]) >= 2  # py_compile + import at least


def test_ship_apply_blocked_when_checks_fail(tmp_path: Path):
    # Syntax error in generated code
    engine = _make_engine('```python:bad.py\ndef (\n```', tmp_path)
    result = ship(engine, "task", base_dir=str(tmp_path), apply=True, dispatch_audit=False)
    assert result.check_result["passed"] is False
    assert result.applied is False
    assert not (tmp_path / "bad.py").exists()


# ---------- apply / write ----------

def test_ship_apply_writes_files_to_base_dir(tmp_path: Path):
    _init_git(tmp_path)
    engine = _make_engine('```python:apply.py\nx = 42\n```', tmp_path)
    result = ship(
        engine, "task",
        base_dir=str(tmp_path),
        apply=True,
        dispatch_audit=False,
        git_commit_msg=None,  # write but don't commit
    )
    assert result.applied is True
    target = tmp_path / "apply.py"
    assert target.exists()
    # parse_file_blocks consumes the trailing newline as block delimiter ·
    # see test_parse_file_blocks_single in test_engine_basic.py for the convention
    assert target.read_text(encoding="utf-8") == "x = 42"


def test_ship_apply_commits_when_msg_provided(tmp_path: Path):
    _init_git(tmp_path)
    engine = _make_engine('```python:committed.py\ny = 7\n```', tmp_path)
    result = ship(
        engine, "task",
        base_dir=str(tmp_path),
        apply=True,
        dispatch_audit=False,
        git_commit_msg="feat(engine): test commit via ship",
    )
    assert result.applied is True
    assert result.git_commit is not None
    assert len(result.git_commit) >= 7  # at least a short SHA
    # Verify commit is in the log
    log = subprocess.run(
        ["git", "-C", str(tmp_path), "log", "-1", "--pretty=%s"],
        capture_output=True, text=True, check=True,
    )
    assert "feat(engine): test commit via ship" in log.stdout


def test_ship_apply_rejects_path_escape(tmp_path: Path):
    _init_git(tmp_path)
    engine = _make_engine('```python:../escape.py\nbad = 1\n```', tmp_path)
    result = ship(
        engine, "task",
        base_dir=str(tmp_path),
        apply=True,
        dispatch_audit=False,
    )
    # Should not write outside base_dir
    assert not (tmp_path.parent / "escape.py").exists()


# ---------- audit dispatch ----------

def test_ship_audit_skipped_without_api_key(tmp_path: Path):
    engine = _make_engine('```python:a.py\nx = 1\n```', tmp_path)
    result = ship(
        engine, "task",
        base_dir=str(tmp_path),
        apply=False,
        dispatch_audit=True,
        api_key=None,
    )
    assert result.audit is not None
    assert result.audit.get("skipped") is True


def test_ship_audit_posts_to_endpoint_with_bearer(tmp_path: Path):
    engine = _make_engine('```python:a.py\nx = 1\n```', tmp_path)

    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.headers)
        captured["body"] = req.data.decode("utf-8") if req.data else ""
        # Return a mock response object with .read()
        class FakeResp:
            status = 201
            def read(self):
                return json.dumps({"data": {"audit_id": "audit_test_xyz", "fidelity_score": 0.85}}).encode()
            def __enter__(self): return self
            def __exit__(self, *a): pass
        return FakeResp()

    with patch("engine.ship.urllib.request.urlopen", side_effect=fake_urlopen):
        result = ship(
            engine, "create a.py",
            base_dir=str(tmp_path),
            apply=False,
            dispatch_audit=True,
            api_key="nau_test_key_123",
        )

    assert captured["url"].endswith("/api/v1/audit/dispatch")
    # Header keys may be capitalized by urllib · normalize for assert
    auth_header = next((v for k, v in captured["headers"].items() if k.lower() == "authorization"), None)
    assert auth_header == "Bearer nau_test_key_123"
    body = json.loads(captured["body"])
    assert "task_spec" in body
    assert "create a.py" in body["task_spec"]
    # ship returns the data dict
    assert result.audit["audit_id"] == "audit_test_xyz"
    assert result.audit["fidelity_score"] == 0.85


def test_ship_fidelity_below_threshold_blocks_apply(tmp_path: Path):
    _init_git(tmp_path)
    engine = _make_engine('```python:low_fid.py\nx = 1\n```', tmp_path)

    def fake_urlopen(req, timeout=None):
        class FakeResp:
            status = 201
            def read(self):
                return json.dumps({"data": {"audit_id": "low", "fidelity_score": 0.4}}).encode()
            def __enter__(self): return self
            def __exit__(self, *a): pass
        return FakeResp()

    with patch("engine.ship.urllib.request.urlopen", side_effect=fake_urlopen):
        result = ship(
            engine, "task",
            base_dir=str(tmp_path),
            apply=True,
            dispatch_audit=True,
            api_key="nau_test_key",
            fidelity_threshold=0.7,
        )
    assert result.applied is False
    assert any("fidelity" in e.lower() for e in result.errors)
    assert not (tmp_path / "low_fid.py").exists()


# ---------- cycle 12 P1 · semantic-check wiring in ship.py ----------

def _semantic_check_results(result: ShipResult) -> list[dict]:
    return [c for c in result.check_result.get("checks", []) if c.get("name") == "semantic"]


def test_semantic_check_fires_when_task_has_trigger_phrase(tmp_path: Path):
    """Task wording with 'keep ALL other code identical' → semantic check runs."""
    target = tmp_path / "foo.py"
    target.write_text("import os\n\ndef foo(x):\n    return x + 1\n")
    # LLM "preserves" the file: only adds docstring
    new_content = '"""Module doc."""\nimport os\n\ndef foo(x):\n    return x + 1\n'
    engine = _make_engine(f"```python:foo.py\n{new_content}```", tmp_path)
    result = ship(
        engine,
        "add module docstring to foo.py · keep ALL other code identical",
        base_dir=str(tmp_path),
        apply=False,
        dispatch_audit=False,
    )
    sem = _semantic_check_results(result)
    assert len(sem) == 1
    assert sem[0]["passed"] is True


def test_semantic_check_blocks_apply_when_over_rewrite(tmp_path: Path):
    """Layer 5 BUDDHA-A.1 simulation: trigger phrase + LLM rewrites imports + funcs."""
    _init_git(tmp_path)
    target = tmp_path / "translate.py"
    target.write_text(
        "import googletrans\n\ndef translate(text):\n    return googletrans.Translator().translate(text).text\n"
    )
    subprocess.run(["git", "-C", str(tmp_path), "add", "translate.py"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "seed translate"], check=True)
    # LLM over-rewrites: different imports, different function name
    rewritten = (
        "import re\n\n"
        "def detect_hangul(text):\n    return bool(re.search(r'[\\uac00-\\ud7af]', text))\n"
    )
    engine = _make_engine(f"```python:translate.py\n{rewritten}```", tmp_path)
    result = ship(
        engine,
        "add a docstring to translate.py · keep ALL other code identical",
        base_dir=str(tmp_path),
        apply=True,
        dispatch_audit=False,
    )
    sem = _semantic_check_results(result)
    assert len(sem) == 1
    assert sem[0]["passed"] is False
    assert "imports" in sem[0]["message"] or "functions" in sem[0]["message"]
    assert result.applied is False
    # Original file on disk must remain untouched after blocked apply
    assert "googletrans" in target.read_text(encoding="utf-8")


def test_semantic_check_skipped_when_task_wording_neutral(tmp_path: Path):
    """Open-ended task (no trigger phrase) → semantic check does NOT run."""
    target = tmp_path / "bar.py"
    target.write_text("def bar():\n    return 1\n")
    engine = _make_engine(
        "```python:bar.py\ndef bar():\n    return 2\n```",
        tmp_path,
    )
    result = ship(
        engine,
        "rewrite bar.py to return 2",
        base_dir=str(tmp_path),
        apply=False,
        dispatch_audit=False,
    )
    assert _semantic_check_results(result) == []


def test_semantic_check_skipped_for_new_file(tmp_path: Path):
    """Trigger phrase + new file (no original on disk) → semantic check vacuously skipped."""
    # Note: 'baz.py' does NOT exist under tmp_path
    engine = _make_engine(
        "```python:baz.py\ndef baz():\n    return 0\n```",
        tmp_path,
    )
    result = ship(
        engine,
        "only add a new baz.py with a single function · do not refactor",
        base_dir=str(tmp_path),
        apply=False,
        dispatch_audit=False,
    )
    # is_file() guard means no semantic check is appended when original is missing
    assert _semantic_check_results(result) == []


# ---------- cycle 15 · Karpathy Fix 1 · _inject_file_context ----------

from engine.ship import _inject_file_context  # noqa: E402


def test_inject_file_context_unchanged_when_no_paths(tmp_path: Path):
    """Task with no file paths in it · returns the task verbatim."""
    task = "rewrite the auth module to use JWT"
    out = _inject_file_context(task, tmp_path)
    assert out == task


def test_inject_file_context_prepends_content_when_file_exists(tmp_path: Path):
    """File mentioned in task AND exists under base_dir · content prepended as CONTEXT block."""
    (tmp_path / "foo.py").write_text("def foo():\n    return 1\n")
    task = "modify foo.py · only add a docstring · keep ALL other code identical"
    out = _inject_file_context(task, tmp_path)
    assert "CONTEXT for foo.py" in out
    assert "def foo():" in out
    assert task in out


def test_inject_file_context_skips_missing_files(tmp_path: Path):
    """Path mentioned but not on disk · no context block added."""
    task = "fix nonexistent.py"
    out = _inject_file_context(task, tmp_path)
    assert "CONTEXT" not in out
    assert out == task


def test_inject_file_context_skips_oversized_files(tmp_path: Path):
    """Files larger than max_chars_per_file are skipped to protect prompt budget."""
    big = tmp_path / "big.py"
    big.write_text("x = 1\n" * 5000)  # > default 8000 char cap
    task = "tweak big.py"
    out = _inject_file_context(task, tmp_path, max_chars_per_file=100)
    assert "CONTEXT" not in out


def test_inject_file_context_skips_path_escapes(tmp_path: Path):
    """Paths that escape base_dir (../etc/passwd-style) are not injected."""
    # The regex would match the literal string but relative_to() catches the escape.
    task = "include ../../../etc/secret.py in your reasoning"
    out = _inject_file_context(task, tmp_path)
    assert "CONTEXT" not in out


# ---------- cycle 16 · allow_additions wiring end-to-end via ship() ----------

def test_ship_semantic_check_allows_intentional_function_add(tmp_path: Path):
    """Cycle 16 · 'add helper' task + LLM correctly adds helper · check PASSES.

    Closes the cycle 15 false-positive: previously semantic check (strict mode)
    treated any addition as failure even when spec said 'add X'. Cycle 16
    auto-detects the additive verb + trigger phrase combo and runs the check
    with allow_additions=True.
    """
    target = tmp_path / "lib.py"
    target.write_text("def existing():\n    return 1\n")
    new_content = "def existing():\n    return 1\n\n\ndef helper():\n    return 2\n"
    engine = _make_engine(f"```python:lib.py\n{new_content}```", tmp_path)
    result = ship(
        engine,
        "add a new helper function to lib.py · keep ALL other code identical · do not refactor",
        base_dir=str(tmp_path),
        apply=False,
        dispatch_audit=False,
    )
    sem = _semantic_check_results(result)
    assert len(sem) == 1
    assert sem[0]["passed"] is True
    # The diff is still surfaced in message so callers see what changed
    assert "functions added" in sem[0]["message"]


def test_ship_semantic_check_with_allow_additions_still_blocks_removal(tmp_path: Path):
    """Cycle 16 negative · additive task but LLM drops an existing function · BLOCK."""
    target = tmp_path / "lib.py"
    target.write_text("def keep():\n    return 1\n\ndef drop():\n    return 2\n")
    # LLM adds helper but drops `drop` function (regression class)
    new_content = "def keep():\n    return 1\n\n\ndef helper():\n    return 3\n"
    engine = _make_engine(f"```python:lib.py\n{new_content}```", tmp_path)
    result = ship(
        engine,
        "add a new helper function to lib.py · keep ALL other code identical",
        base_dir=str(tmp_path),
        apply=False,
        dispatch_audit=False,
    )
    sem = _semantic_check_results(result)
    assert len(sem) == 1
    assert sem[0]["passed"] is False
    assert "functions removed" in sem[0]["message"]


# ---------- Gap 1 · integration: size trigger fires line_count + docstring_preserve ----------


def test_ship_runs_line_count_check_when_existing_file_over_50loc(tmp_path):
    """Size trigger fires line_count check · LLM truncate rejected.

    Closes the actual Day 6-7 dogfood scenario: task says "add aggregate_recent
    to outcomes.py" (no MINIMAL CHANGE phrase), outcomes.py already has 200
    LOC on disk, LLM emits a truncated 90-line version. Without Gap 1, this
    would ship silently. With Gap 1, line_count rejects.
    """
    # Seed existing file · 200 LOC, no MINIMAL CHANGE phrase in task
    target = tmp_path / "outcomes.py"
    target.write_text("\n".join(f"x = {i}" for i in range(200)) + "\n", encoding="utf-8")
    # LLM emits a 90-line replacement (ratio 0.45 · below 0.85 floor)
    truncated_body = "\n".join(f"x = {i}" for i in range(90))
    code_output = f"```python:outcomes.py\n{truncated_body}\n```\n"
    engine = _make_engine(code_output, tmp_path)
    result = ship(
        engine,
        task="add aggregate_recent to outcomes.py",
        base_dir=str(tmp_path),
        apply=False,
        dispatch_audit=False,
        emit_outcome_telemetry=False,
    )
    names = [c["name"] for c in result.check_result.get("checks", [])]
    assert "line_count" in names, f"line_count check must run · got {names}"
    line_count_check = next(c for c in result.check_result["checks"] if c["name"] == "line_count")
    assert not line_count_check["passed"], f"line_count must reject 0.45 ratio · {line_count_check}"


def test_ship_runs_docstring_preserve_check_when_existing_file(tmp_path):
    """Size trigger fires docstring_preserve · LLM docstring rewrite rejected."""
    # Existing 100-LOC file with module docstring · size > 50 fires trigger
    target = tmp_path / "module.py"
    body = "\n".join(f"x = {i}" for i in range(99))
    target.write_text(f'"""Original module docstring."""\n{body}\n', encoding="utf-8")
    # LLM rewrites docstring (preserves line count) · task has no escape keyword
    new_body = "\n".join(f"x = {i}" for i in range(99))
    code_output = (
        f'```python:module.py\n"""Rewritten module docstring."""\n{new_body}\n```\n'
    )
    engine = _make_engine(code_output, tmp_path)
    result = ship(
        engine,
        task="fix off-by-one in module.py",
        base_dir=str(tmp_path),
        apply=False,
        dispatch_audit=False,
        emit_outcome_telemetry=False,
    )
    names = [c["name"] for c in result.check_result.get("checks", [])]
    assert "docstring_preserve" in names, f"docstring_preserve must run · got {names}"
    doc_check = next(c for c in result.check_result["checks"] if c["name"] == "docstring_preserve")
    assert not doc_check["passed"], f"docstring rewrite without keyword must reject · {doc_check}"

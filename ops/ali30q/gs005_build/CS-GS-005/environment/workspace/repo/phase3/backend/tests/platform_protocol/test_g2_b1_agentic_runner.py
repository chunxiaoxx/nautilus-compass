"""Offline tests for the G2-B1 agentic repair loop (no LLM, no real pytest).

The completion function and the test runner are both injected fakes; the loop
logic (apply/feedback/budget/RED precondition) is what is under test.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import g2_b1_agentic_runner as agentic  # noqa: E402


def _make_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Tiny git repo: root + backend with one buggy python file."""
    backend = tmp_path / "phase3" / "backend"
    backend.mkdir(parents=True)
    (backend / "mod.py").write_text(
        "def add(a, b):\n    return a - b  # the bug\n", encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, timeout=30)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, timeout=30)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "buggy"],
        cwd=tmp_path, check=True, timeout=30,
    )
    return tmp_path, backend


GOOD_DIFF = (
    "--- a/mod.py\n+++ b/mod.py\n"
    "@@ -1,2 +1,2 @@\n def add(a, b):\n-    return a - b  # the bug\n"
    "+    return a + b\n"
)


def _fake_test_runner(test_id, cwd):
    """Fake pytest: passes only while the buggy line is patched."""
    text = (cwd / "mod.py").read_text(encoding="utf-8")
    ok = "a + b" in text
    return subprocess.CompletedProcess(
        ["fake"], 0 if ok else 1,
        stdout=(b"1 passed" if ok else b"FAILED mod.py - assert add(1,1)==2"),
        stderr=b"",
    )


def test_red_precondition_blocks_spend(tmp_path):
    repo, backend = _make_repo(tmp_path)
    called = []

    def completer(prompt):
        called.append(prompt)
        return {"content": "{}", "usage": {"total_tokens": 1}}

    def green_runner(test_id, cwd):
        return subprocess.CompletedProcess(["fake"], 0, stdout=b"1 passed", stderr=b"")

    result = agentic.run_agentic_loop(
        completer, backend, repo, "t", Path("mod.py"), run_test_fn=green_runner
    )
    assert result.test_passed is False
    assert called == []  # zero completions on a green task


def test_second_turn_feedback_fixes_bug(tmp_path):
    repo, backend = _make_repo(tmp_path)
    prompts_seen = []

    def completer(prompt):
        prompts_seen.append(prompt)
        if len(prompts_seen) == 1:
            bad = '{"unified_diff": "--- a/mod.py\\n+++ b/mod.py\\n@@ -1,2 +1,2 @@\\n def add(a, b):\\n-    return a - b  # the bug\\n+    return a * b\\n"}'
            return {"content": bad, "usage": {"total_tokens": 100}}
        return {"content": '{"unified_diff": ' + repr(GOOD_DIFF).replace("'", '"') + '}',
                "usage": {"total_tokens": 100}}

    result = agentic.run_agentic_loop(
        completer, backend, repo, "t", Path("mod.py"), run_test_fn=_fake_test_runner
    )
    assert result.test_passed is True
    assert len(result.turns) == 2
    assert result.turns[0].feedback_kind == "applied_fail"
    assert result.turns[1].feedback_kind == "applied_pass"
    assert "STILL FAILS" in prompts_seen[1]  # feedback was fed back
    # buggy state restored after success
    assert "a - b" in (backend / "mod.py").read_text(encoding="utf-8")


def test_apply_error_feedback_then_no_json(tmp_path):
    repo, backend = _make_repo(tmp_path)
    turns_out = []

    def completer(prompt):
        turns_out.append(prompt)
        if len(turns_out) == 1:
            return {"content": '{"unified_diff": "garbage"}',
                    "usage": {"total_tokens": 10}}
        return {"content": "not json at all", "usage": {"total_tokens": 10}}

    result = agentic.run_agentic_loop(
        completer, backend, repo, "t", Path("mod.py"),
        run_test_fn=_fake_test_runner, max_turns=2,
    )
    assert result.test_passed is False
    assert [t.feedback_kind for t in result.turns] == ["apply_error", "no_json"]
    assert "attempt1" in turns_out[1]  # aggregated per-attempt errors are fed back


def test_repo_root_relative_diff_applies(tmp_path):
    """Regression (8/22 first run): root-relative paths must not be double-prefixed."""
    repo, backend = _make_repo(tmp_path)

    def completer(prompt):
        root_diff = (
            "--- a/phase3/backend/mod.py\n+++ b/phase3/backend/mod.py\n"
            "@@ -1,2 +1,2 @@\n def add(a, b):\n-    return a - b  # the bug\n"
            "+    return a + b\n"
        )
        return {"content": '{"unified_diff": ' + repr(root_diff).replace("'", '"') + '}',
                "usage": {"total_tokens": 100}}

    result = agentic.run_agentic_loop(
        completer, backend, repo, "t", Path("mod.py"), run_test_fn=_fake_test_runner
    )
    assert result.test_passed is True


def test_budget_cap_fail_closed(tmp_path):
    repo, backend = _make_repo(tmp_path)

    def completer(prompt):
        return {"content": "no json", "usage": {"total_tokens": 150_000}}

    with pytest.raises(agentic.BudgetExceeded):
        agentic.run_agentic_loop(
            completer, backend, repo, "t", Path("mod.py"),
            run_test_fn=_fake_test_runner,
            max_turns=3, max_total_tokens=200_000,
        )


# --- fixture-broken RED pre-filter (8/24 · loofold_select burned 147k tokens) ---

def _fixture_broken_runner(kind: str):
    """Fake pytest whose RED failure is a broken fixture, not a real bug."""
    outputs = {
        "missing_file": (
            b"E       FileNotFoundError: [Errno 2] No such file or directory: "
            b"'fde_capsule/genopt/tasks/ContainerOps/loofold_select_0001/data/instances.json'\n"
            b"=========================== short test summary info ===========================\n"
            b"FAILED tests/test_loofold_select.py::test_baseline_runs_and_produces_valid_zero\n"
        ),
        "import_error": (
            b"E   ImportError: cannot import name '_core_helper' from 'src.helpers'\n"
            b"=========================== short test summary info ===========================\n"
            b"FAILED tests/test_loofold_select.py::test_baseline_runs_and_produces_valid_zero\n"
        ),
    }
    out = outputs[kind]
    def runner(test_id, cwd):
        return subprocess.CompletedProcess(["fake"], 1, stdout=out, stderr=b"")
    return runner


@pytest.mark.parametrize("kind", ["missing_file", "import_error"])
def test_fixture_broken_red_blocks_spend(tmp_path, kind):
    repo, backend = _make_repo(tmp_path)
    called = []

    def completer(prompt):
        called.append(prompt)
        return {"content": "{}", "usage": {"total_tokens": 1}}

    result = agentic.run_agentic_loop(
        completer, backend, repo, "t", Path("mod.py"),
        run_test_fn=_fixture_broken_runner(kind),
    )
    assert result.test_passed is False
    assert called == []  # zero completions — fixture is broken, not a repair task
    assert result.fixture_broken is True
    assert result.total_tokens == 0


def test_source_file_missing_error_is_not_fixture_broken(tmp_path):
    """A FileNotFoundError naming the PRIMARY source is a real bug, not a fixture issue."""
    repo, backend = _make_repo(tmp_path)
    called = []

    def completer(prompt):
        called.append(prompt)
        return {"content": '{"unified_diff": ' + repr(GOOD_DIFF).replace("'", '"') + '}',
                "usage": {"total_tokens": 100}}

    def runner(test_id, cwd):
        out = (b"E       FileNotFoundError: 'mod.py'\n"
               b"FAILED tests/test_mod.py::test_add\n")
        return subprocess.CompletedProcess(["fake"], 1, stdout=out, stderr=b"")

    result = agentic.run_agentic_loop(
        completer, backend, repo, "t", Path("mod.py"), run_test_fn=runner,
    )
    assert result.fixture_broken is False
    assert len(called) == 3  # real RED — the loop proceeds and spends all turns

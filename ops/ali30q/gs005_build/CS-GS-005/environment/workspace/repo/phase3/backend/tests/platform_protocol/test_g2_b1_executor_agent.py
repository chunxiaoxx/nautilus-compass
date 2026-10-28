"""Offline tests for the G2-B1 resident executor (no LLM, no network, no DB).

Covers: test-anchor derivation from the reference fix diff, and per-task
evidence idempotency (one terminal state per task).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import g2_b1_executor_agent as executor  # noqa: E402


def _commit_repo(tmp_path: Path, fix_diff: str) -> str:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, timeout=30)
    (tmp_path / "mod.py").write_text("x = 1\n", encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "t.py").write_text("def test_a():\n    pass\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, timeout=30)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "base"], cwd=tmp_path, check=True,
                   timeout=30)
    patch = tmp_path / "fix.patch"
    patch.write_text(fix_diff, encoding="utf-8")
    subprocess.run(["git", "apply", str(patch)], cwd=tmp_path, check=True,
                   timeout=30)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, timeout=30)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "fix"], cwd=tmp_path, check=True,
                   timeout=30)
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                         capture_output=True, check=True, timeout=30)
    return out.stdout.decode().strip()


FIX_DIFF = (
    "diff --git a/tests/t.py b/tests/t.py\n"
    "--- a/tests/t.py\n+++ b/tests/t.py\n"
    "@@ -1,2 +1,5 @@\n"
    "+import pytest\n"
    "+def test_broken_thing():\n"
    "+    assert False\n"
    " def test_a():\n"
    "     pass\n"
)


def test_derive_test_anchor_prefers_added_test(tmp_path):
    fix = _commit_repo(tmp_path, FIX_DIFF)
    anchor = executor._derive_test_anchor(tmp_path, fix, ["tests/t.py"])
    assert anchor == "tests/t.py::test_broken_thing"


def test_derive_test_anchor_falls_back_to_file(tmp_path):
    fix = _commit_repo(tmp_path, "diff --git a/mod.py b/mod.py\n"
                                 "--- a/mod.py\n+++ b/mod.py\n"
                                 "@@ -1 +1 @@\n-x = 1\n+x = 2\n")
    anchor = executor._derive_test_anchor(tmp_path, fix, ["tests/t.py"])
    assert anchor == "tests/t.py"


def test_run_task_idempotent_on_existing_evidence(tmp_path):
    evidence_dir = tmp_path / "ev"
    evidence_dir.mkdir()
    task = {"buggy_commit": "x" * 40, "reference_fix_commit": "abc1234567",
            "test_files": [], "source_files": []}
    existing = {"schema_version": "g2b1-exec-run-v1", "test_passed": True}
    (evidence_dir / "g2b1-exec-abc1234567-deepseek.json").write_text(
        json.dumps(existing), encoding="utf-8")

    def boom(*a, **k):  # must never be called
        raise AssertionError("re-ran a finished task")

    result = executor.run_task(tmp_path, task, boom, "deepseek", evidence_dir)
    assert result["test_passed"] is True


# --- 自愈三件套①:LLM 臂 fallback 链(2026-08-28 V5) ---

def test_fallback_completer_switches_on_failure():
    """主臂失败应自动切备胎,切换事件可观测,evidence 不丢。"""
    import tools.g2_b1_executor_agent as ex
    calls = []

    def bad(prompt):
        calls.append("bad")
        raise RuntimeError("http_403")

    def good(prompt):
        calls.append("good")
        return {"content": "fixed code", "usage": {}, "model": "m2",
                "finish_reason": "end_turn"}

    orig = ex.make_completer
    ex.make_completer = lambda p, m=16384: bad if p == "arm_a" else good
    try:
        c = ex.make_fallback_completer(["arm_a", "arm_b"])
        out = c("prompt")
    finally:
        ex.make_completer = orig
    assert out["content"] == "fixed code"
    assert calls == ["bad", "good"]


# --- provider_used 归因(V5 驾驶舱条件 · fallback 链实际产出臂) ---

def test_fallback_completer_records_provider_used():
    """备胎成功时记录实际产出臂;主臂直接成功时记录主臂。"""
    import tools.g2_b1_executor_agent as ex

    def bad(prompt):
        raise RuntimeError("http_403")

    def good(prompt):
        return {"content": "ok", "usage": {}, "model": "m2",
                "finish_reason": "end"}

    orig = ex.make_completer
    ex.make_completer = lambda p, m=16384: bad if p == "arm_a" else good
    try:
        c = ex.make_fallback_completer(["arm_a", "arm_b"])
        c("prompt")
        assert c.used["provider"] == "arm_b"
        assert c.used["all"] == ["arm_b"]
        # 主臂即成功 → 归因主臂
        c2 = ex.make_fallback_completer(["arm_b", "arm_a"])
        c2("prompt")
        assert c2.used["provider"] == "arm_b" and c2.used["all"] == ["arm_b"]
    finally:
        ex.make_completer = orig


def test_provider_used_of_falls_back_to_arm_name():
    """单臂 completer(无 used 属性)归因到臂名本身,不炸。"""
    import tools.g2_b1_executor_agent as ex

    def plain(prompt):  # pragma: no cover — 不会被调用
        return {"content": "", "usage": {}}

    assert ex._provider_used_of(plain, "deepseek") == "deepseek"

    class _Chain:
        used = {"provider": "glm_plan", "all": ["glm_plan"]}

    assert ex._provider_used_of(_Chain(), "deepseek") == "glm_plan"


def test_fallback_completer_all_arms_fail_raises_last():
    import tools.g2_b1_executor_agent as ex

    def bad1(prompt):
        raise RuntimeError("http_403")

    def bad2(prompt):
        raise RuntimeError("http_429")

    orig = ex.make_completer
    ex.make_completer = lambda p, m=16384: bad1 if p == "a" else bad2
    try:
        c = ex.make_fallback_completer(["a", "b"])
        import pytest
        with pytest.raises(RuntimeError, match="http_429"):
            c("prompt")
    finally:
        ex.make_completer = orig

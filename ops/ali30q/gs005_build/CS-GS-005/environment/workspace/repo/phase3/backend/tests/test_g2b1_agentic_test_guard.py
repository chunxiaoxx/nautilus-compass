# -*- coding: utf-8 -*-
"""agentic loop 防作弊守卫单测(9/7:diff 触碰 test 文件即拒)。

背景:组织 OS 分析自检实证——`_apply_patch` 不校验 diff 触碰路径,agent 把
测试断言删掉也能拿 applied_pass(reward hacking 面敞开)。守卫=测试是评分
契约不是修复面:diff 触碰 tests/ 目录、test_*/\*_test.py、conftest.py 一律
拒绝,turn 记 test_tamper,反馈明示重新生成只改源码的 diff。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.g2_b1_agentic_runner import (  # noqa: E402
    _diff_touches_tests,
    run_agentic_loop,
)

TAMPER_DIFF = (
    "--- a/tests/test_x.py\n"
    "+++ b/tests/test_x.py\n"
    "@@ -1,2 +1 @@\n"
    "-    assert False\n"
    "+    pass\n"
)

GOOD_DIFF = (
    "--- a/src.py\n"
    "+++ b/src.py\n"
    "@@ -1,2 +1,3 @@\n"
    " x = 1\n"
    "+patched = True\n"
    " y = 2\n"
)


@pytest.fixture()
def git_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    (repo / "src.py").write_text("x = 1\ny = 2\n", encoding="utf-8")
    (repo / "tests" / "test_x.py").write_text(
        "def test_a():\n    assert True\n", encoding="utf-8")

    def _git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, check=True,
                       capture_output=True)

    _git("init", "-q")
    _git("config", "user.email", "t@t")
    _git("config", "user.name", "t")
    _git("add", ".")
    _git("commit", "-qm", "init")
    return repo


def _red_then_green():
    """第 1 次 RED,第 2 次 GREEN——模拟两轮修复成功。"""
    state = {"n": 0}

    def _run(test_id: str, cwd: Path) -> subprocess.CompletedProcess:
        state["n"] += 1
        code = 1 if state["n"] == 1 else 0
        return subprocess.CompletedProcess([], code, stdout=b"ok", stderr=b"")

    return _run


def test_diff_touches_tests_unit():
    hits = _diff_touches_tests(TAMPER_DIFF, Path("tests/test_x.py"))
    assert hits == ["tests/test_x.py"]
    assert _diff_touches_tests(
        "--- a/phase3/backend/tests/test_y.py\n"
        "+++ b/phase3/backend/tests/test_y.py\n"
        "@@ -1 +1 @@\n", Path("tests/test_y.py")) == [
        "phase3/backend/tests/test_y.py"]
    assert _diff_touches_tests(
        "--- a/tests/conftest.py\n+++ b/tests/conftest.py\n@@\n",
        Path("tests/test_x.py")) == ["tests/conftest.py"]
    assert _diff_touches_tests(GOOD_DIFF, Path("tests/test_x.py")) == []


def test_tamper_rejected_without_apply(git_repo):
    outputs = ['{"unified_diff": %s}' % json.dumps(TAMPER_DIFF)]
    prompts = []

    def _complete(prompt: str) -> dict:
        prompts.append(prompt)
        return {"content": outputs[0], "usage": {"total_tokens": 10},
                "model": "t"}

    def _always_red(test_id: str, cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess([], 1, stdout=b"1 failed",
                                           stderr=b"")

    result = run_agentic_loop(_complete, git_repo, git_repo,
                              "tests/test_x.py::test_a", Path("src.py"),
                              run_test_fn=_always_red, max_turns=1)
    turn = result.turns[0]
    assert turn.feedback_kind == "test_tamper"
    assert turn.patch_applied is False
    assert turn.test_passed is False
    # 关键:diff 从未被 apply——测试文件原样(修复前此处会失败:diff 会落地)
    assert (git_repo / "tests" / "test_x.py").read_text(
        encoding="utf-8") == "def test_a():\n    assert True\n"
    assert "FORBIDDEN" in turn.feedback_excerpt


def test_tamper_then_clean_still_passes(git_repo):
    outputs = ['{"unified_diff": %s}' % json.dumps(TAMPER_DIFF),
               '{"unified_diff": %s}' % json.dumps(GOOD_DIFF)]
    prompts = []
    state = {"n": 0}

    def _complete(prompt: str) -> dict:
        prompts.append(prompt)
        out = outputs[state["n"]]
        state["n"] += 1
        return {"content": out, "usage": {"total_tokens": 10}, "model": "t"}

    result = run_agentic_loop(_complete, git_repo, git_repo,
                              "tests/test_x.py::test_a", Path("src.py"),
                              run_test_fn=_red_then_green(), max_turns=2)
    assert result.turns[0].feedback_kind == "test_tamper"
    assert result.test_passed is True
    assert result.turns[1].feedback_kind == "applied_pass"
    assert result.winning_diff == GOOD_DIFF
    # 反馈链没断:第 2 轮 prompt 必须讲清为什么被拒
    assert "test" in prompts[1].lower()

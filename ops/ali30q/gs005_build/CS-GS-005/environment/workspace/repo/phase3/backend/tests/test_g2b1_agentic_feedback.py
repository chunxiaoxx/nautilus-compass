# -*- coding: utf-8 -*-
"""agentic loop 反馈协议单测(9/5:k3 三轮死法修复)。

背景:evidence g2b1-exec-724533e03b —— turn1 patch 打上但语义错,文件被
checkout 还原后模型无感知(turn3 diff 基于旧状态打不上);turn2 返回空 diff
只收到笼统的 "No valid patches";apply_error 的 raw dump 落在 worktree 内,
finally 随 worktree 销毁,离线诊断断粮。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.g2_b1_agentic_runner import run_agentic_loop  # noqa: E402

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
    """最小 git 仓:tracked src.py + tests/test_x.py,供真 git apply/checkout。"""
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


def _fake_run_test():
    """恒 RED(简化输出,避开 collected-0 与 fixture-broken 特征)。"""
    def _run(test_id: str, cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess([], 1, stdout=b"1 failed in 0.01s",
                                           stderr=b"")
    return _run


def _completer_capturing(outputs):
    """按轮返回预置 content,并捕获每轮 prompt 供断言 feedback 文案。"""
    prompts: list[str] = []
    state = {"n": 0}

    def _complete(prompt: str) -> dict:
        prompts.append(prompt)
        out = outputs[min(state["n"], len(outputs) - 1)]
        state["n"] += 1
        return {"content": out, "usage": {"total_tokens": 10}, "model": "t"}

    return _complete, prompts


def test_applied_fail_feedback_mentions_rollback(git_repo):
    outputs = ['{"unified_diff": %s}' % json.dumps(GOOD_DIFF),
               '{"unified_diff": ""}']
    complete, prompts = _completer_capturing(outputs)
    run_agentic_loop(complete, git_repo, git_repo,
                     "tests/test_x.py::test_a", Path("src.py"),
                     run_test_fn=_fake_run_test(), max_turns=2)
    assert len(prompts) == 2
    # turn1 patch 已被 checkout 还原,feedback 必须让模型知道从原始态重出
    assert "ORIGINAL buggy state" in prompts[1]
    assert "regenerate your diff" in prompts[1]


def test_empty_diff_gets_explicit_feedback(git_repo):
    outputs = ['{"unified_diff": ""}']
    complete, _ = _completer_capturing(outputs)
    result = run_agentic_loop(complete, git_repo, git_repo,
                              "tests/test_x.py::test_a", Path("src.py"),
                              run_test_fn=_fake_run_test(), max_turns=1)
    turn = result.turns[0]
    assert turn.patch_applied is False
    assert turn.feedback_kind == "empty_diff"
    assert "EMPTY" in turn.feedback_excerpt


def test_apply_error_dumps_to_dump_dir(git_repo, tmp_path):
    dump_dir = tmp_path / "evidence-external"
    outputs = ['{"unified_diff": "this is not a diff"}']
    complete, _ = _completer_capturing(outputs)
    run_agentic_loop(complete, git_repo, git_repo,
                     "tests/test_x.py::test_a", Path("src.py"),
                     run_test_fn=_fake_run_test(), max_turns=1,
                     dump_dir=dump_dir)
    dumps = list(dump_dir.glob(".g2b1-failed-turn1.patch"))
    assert len(dumps) == 1
    assert dumps[0].read_text(encoding="utf-8") == "this is not a diff"

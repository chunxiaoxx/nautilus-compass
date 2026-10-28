"""soul 交付质量闸修复测试(2026-09-14 · 治 PR #143/#144 两洞)。

洞A:PR base 写死 master(8/26 已归档)→ 30 万行历史包袱;
洞B:checks 不验证目标文件存在 → 空活 PR 混过(#144 无 phase3/ 文件)。
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from soul.config import MAIN_BRANCH
from soul import pr_gate


def test_main_branch_is_current_trunk():
    """主干名= soul-distill-deploy(8/26 换轨后),非 master。"""
    assert MAIN_BRANCH == "soul-distill-deploy"


def test_create_draft_pr_targets_current_trunk():
    """gh pr create 的 --base 必须是当前主干(治洞A:base=master 带 30 万行包袱)。"""
    calls = {}

    def fake_run(cmd, **kw):
        if "pr" in cmd and "create" in cmd:
            calls["base"] = cmd[cmd.index("--base") + 1]
        return subprocess.CompletedProcess(cmd, 0, stdout="https://github.com/x/pull/1", stderr="")

    with patch.object(pr_gate.subprocess, "run", side_effect=fake_run):
        url = pr_gate.create_draft_pr("soul/cycle-x", "t", "b")
    assert url
    assert calls["base"] == "soul-distill-deploy"


def test_check_expect_files(tmp_path: Path):
    """洞B:目标文件不在 cycle HEAD → 失败+报缺失清单;都在 → 过。"""
    repo = tmp_path / "r"
    repo.mkdir()
    for cmd in (["git", "init", "-q"], ["git", "config", "user.email", "t@t"],
                ["git", "config", "user.name", "t"]):
        subprocess.run(cmd + [str(repo)] if cmd[0] == "git" and cmd[1] == "init" else cmd,
                       cwd=repo, capture_output=True)
    (repo / "sub").mkdir()
    (repo / "sub" / "have.py").write_text("x = 1", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, capture_output=True)

    ok, missing = pr_gate.check_expect_files(str(repo), ["sub/have.py"])
    assert ok and missing == []

    ok2, missing2 = pr_gate.check_expect_files(
        str(repo), ["sub/have.py", "phase3/backend/tools/report_templates_l1l2l3.py"])
    assert not ok2 and missing2 == ["phase3/backend/tools/report_templates_l1l2l3.py"]

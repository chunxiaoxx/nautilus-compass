"""Offline integration: executor variant flow on a fixture repo (batch 1).

变体题:buggy_commit == reference_fix_commit(起点=模板 fix),
合成 bug 由 variant_patch 表达 —— worktree@fix + apply patch = starter。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import g2_b1_executor_agent as ex  # noqa: E402

PATCH = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-x = 2\n+x = 1\n"


def _fixture_repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()

    def sh(*a):
        subprocess.run(a, cwd=r, check=True, capture_output=True)

    sh("git", "init", "-q")
    sh("git", "config", "user.email", "t@t")
    sh("git", "config", "user.name", "t")
    (r / "app.py").write_text("x = 1\n", encoding="utf-8")
    sh("git", "add", "-A")
    sh("git", "commit", "-qm", "buggy")
    (r / "app.py").write_text("x = 2\n", encoding="utf-8")
    tdir = r / "tests"
    tdir.mkdir()
    (tdir / "test_app.py").write_text(
        "from app import x\n\ndef test_two():\n    assert x == 2\n",
        encoding="utf-8")
    sh("git", "add", "-A")
    sh("git", "commit", "-qm", "fix")
    rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=r,
                         capture_output=True, text=True).stdout.strip()
    return r, rev


def _variant_row(fix, uid, patch=PATCH):
    return {"schema_version": "g2-b1-task-v1", "buggy_commit": fix,
            "reference_fix_commit": fix, "subject": "fix: two [variant:1a]",
            "test_files": ["tests/test_app.py"], "source_files": ["app.py"],
            "repo_path": "FIXTURE", "task_uid": uid,
            "variant_of": f"g2b1:{fix[:12]}",
            "variant_op": "1a", "variant_patch": patch}


def test_run_task_variant_flow(tmp_path):
    repo, fix = _fixture_repo(tmp_path)
    uid = "g2b1:abc123def456"
    ev_dir = tmp_path / "ev"
    ev_dir.mkdir()

    def boom(*a, **k):
        raise ex.BudgetExceeded()

    ev = ex.run_task(repo, _variant_row(fix, uid), boom, "ark_glm", ev_dir)
    # evidence 用行 uid 命名 —— 不落模板 ref10 对账前缀域
    p = ev_dir / f"g2b1-exec-{uid.split(':')[1][:10]}-ark_glm.json"
    assert p.exists(), f"evidence not at uid path: {sorted(x.name for x in ev_dir.iterdir())}"
    on_disk = json.loads(p.read_text(encoding="utf-8"))
    assert on_disk["task"]["task_uid"] == uid
    # patch 应用成功且 RED 检测真实跑过(进入 loop 后预算终态,非 skip)
    assert on_disk.get("skipped_reason") is None
    assert on_disk["budget_exceeded"] is True


def test_run_task_variant_patch_apply_fail(tmp_path):
    repo, fix = _fixture_repo(tmp_path)
    bad = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-x = 999\n+z = 0\n"
    row = _variant_row(fix, "g2b1:fff123def456", patch=bad)
    ev_dir = tmp_path / "ev"
    ev_dir.mkdir()
    ev = ex.run_task(repo, row, lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("loop must not run when patch fails to apply")),
        "ark_glm", ev_dir)
    assert ev.get("skipped_reason") == "variant_patch_apply_failed"

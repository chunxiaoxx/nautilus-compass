"""g2b1 双门验证器 · plan 层 TDD(spine 断裂修复 · 2026-08-25)。"""
from __future__ import annotations

import json
import os

import pytest

from services.g2b1_double_gate import (
    G2B1_SOURCE, evidence_candidates, load_evidence, plan_g2b1_jobs)


@pytest.fixture
def evidence_dir(tmp_path):
    (tmp_path / "g2b1-exec-e49e8ade78-ark_glm.json").write_text(json.dumps({
        "task": {"buggy_commit": "b" * 40, "reference_fix_commit": "f" * 40,
                 "subject": "s"},
        "test_id": "tests/test_x.py::test_y", "test_passed": True}), encoding="utf-8")
    (tmp_path / "g2b1-exec-e49e8ade78-minimax.json").write_text("not json",
                                                                encoding="utf-8")
    (tmp_path / "g2b1-exec-ffffffff00-ark_glm.json").write_text(json.dumps({
        "task": {"buggy_commit": "x"}}), encoding="utf-8")  # 缺 reference_fix → 不可解析
    return str(tmp_path)


def test_evidence_candidates_matches_suffix(evidence_dir):
    assert evidence_candidates("g2b1:e49e8ade7849", evidence_dir) == [
        "g2b1-exec-e49e8ade78-ark_glm.json", "g2b1-exec-e49e8ade78-minimax.json"]
    assert evidence_candidates("g2b1:deadbeef12", evidence_dir) == []
    assert evidence_candidates("other:e49e8ade78", evidence_dir) == []


def test_load_evidence_requires_both_commits(evidence_dir):
    good = load_evidence(os.path.join(evidence_dir, "g2b1-exec-e49e8ade78-ark_glm.json"))
    assert good["buggy_commit"] == "b" * 40
    assert good["test_id"] == "tests/test_x.py::test_y"
    bad = load_evidence(os.path.join(evidence_dir, "g2b1-exec-ffffffff00-ark_glm.json"))
    assert bad is None


def test_plan_g2b1_jobs_only_matching_source_and_schema(evidence_dir):
    rows = [
        {"verdict_id": "v1", "task_uid": "g2b1:e49e8ade7849", "source": G2B1_SOURCE,
         "artifacts": {"evidence_schema": "g2b1-exec-run-v1"}},
        {"verdict_id": "v2", "task_uid": "g2b1:deadbeef12", "source": G2B1_SOURCE,
         "artifacts": {"evidence_schema": "g2b1-exec-run-v1"}},      # 无 evidence → 跳过
        {"verdict_id": "v3", "task_uid": "g2b1:e49e8ade7849", "source": "gmint",
         "artifacts": {"evidence_schema": "g2b1-exec-run-v1"}},      # 源不对 → 跳过
        {"verdict_id": "v4", "task_uid": "g2b1:e49e8ade7849", "source": G2B1_SOURCE,
         "artifacts": {}},                                          # schema 不对 → 跳过
    ]
    jobs = plan_g2b1_jobs(rows, evidence_dir)
    assert len(jobs) == 1
    j = jobs[0]
    assert j["verdict_id"] == "v1"
    assert j["kind"] == "g2b1_double_gate"
    assert j["evidence"] == "g2b1-exec-e49e8ade78-ark_glm.json"  # 跳过损坏的 minimax 文件
    assert j["buggy_commit"] == "b" * 40


def _mk_repo(tmp_path):
    """夹具仓: buggy commit(无 timeout 参数) → fix commit(加参数+加测试)。"""
    import subprocess
    repo = tmp_path / "repo"
    repo.mkdir()
    def git(*a):
        subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True)
    def cfg():
        git("config", "user.email", "t@t"); git("config", "user.name", "t")
    git("init", "-q"); cfg()
    (repo / "calc.py").write_text(
        "def f(timeout=None):\n    return timeout\n", encoding="utf-8")
    (repo / "tests").mkdir(); (repo / "tests" / "__init__.py").write_text("", encoding="utf-8")
    git("add", "-A"); git("commit", "-qm", "base")
    (repo / "calc.py").write_text(                       # buggy: 签名丢 timeout
        "def f(*, a=1):\n    return a\n", encoding="utf-8")
    git("add", "-A"); git("commit", "-qm", "buggy")
    buggy = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                           capture_output=True, text=True).stdout.strip()
    (repo / "calc.py").write_text(                       # fix: 恢复 timeout
        "def f(*, a=1, timeout=None):\n    return a if timeout is None else a + timeout\n",
        encoding="utf-8")
    (repo / "tests" / "test_calc.py").write_text(
        "from calc import f\n\ndef test_timeout():\n    assert f(timeout=5) == 6\n",
        encoding="utf-8")
    git("add", "-A"); git("commit", "-qm", "fix")
    ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                         capture_output=True, text=True).stdout.strip()
    return str(repo), buggy, ref


def test_run_double_gate_red_then_green(tmp_path):
    from services.g2b1_double_gate import run_double_gate
    repo, buggy, ref = _mk_repo(tmp_path)
    out = run_double_gate(repo, buggy, ref, "tests/test_calc.py::test_timeout")
    assert out["gate_a_starter_fails"] is True, out
    assert out["gate_b_fix_passes"] is True, out
    assert out["passed"] is True


def test_run_double_gate_detects_fake_gate_a(tmp_path):
    """防自骗: 若 buggy 本来就过测试(门A 不红),整体验证必须 fail。"""
    from services.g2b1_double_gate import run_double_gate
    repo, buggy, ref = _mk_repo(tmp_path)
    # 用 ref 的 buggy(即已修好的代码)冒充 buggy → 门A 应不红
    out = run_double_gate(repo, ref, ref, "tests/test_calc.py::test_timeout")
    assert out["gate_a_starter_fails"] is False
    assert out["passed"] is False


def test_plan_resolves_repo_via_queue(tmp_path, evidence_dir):
    """四仓题源: queue buggy_commit→repo_path→云端仓目录; 无溯源→repo_dir=None。"""
    from services.g2b1_double_gate import plan_g2b1_jobs
    q = tmp_path / "queue.jsonl"
    q.write_text(json.dumps({"buggy_commit": "b" * 40, "repo_path": r"C:\Users\chunx\Projects\nautilus-compass"}) + "\n", encoding="utf-8")
    rows = [{"verdict_id": "v1", "task_uid": "g2b1:e49e8ade7849", "source": G2B1_SOURCE,
             "artifacts": {"evidence_schema": "g2b1-exec-run-v1"}},
            {"verdict_id": "v9", "task_uid": "g2b1:ffffffff001", "source": G2B1_SOURCE,
             "artifacts": {"evidence_schema": "g2b1-exec-run-v1"}}]
    ev2 = evidence_dir + "/g2b1-exec-ffffffff00-ark_glm.json"
    open(ev2, "w", encoding="utf-8").write(json.dumps(
        {"task": {"buggy_commit": "z" * 40, "reference_fix_commit": "f" * 40},
         "test_id": "t"}))
    jobs = plan_g2b1_jobs(rows, evidence_dir, str(q))
    by_id = {j["verdict_id"]: j for j in jobs}
    assert by_id["v1"]["repo_dir"].endswith("nautilus-compass")
    assert by_id["v9"]["repo_dir"] is None  # buggy 不在 queue → 无仓,runner 跳过

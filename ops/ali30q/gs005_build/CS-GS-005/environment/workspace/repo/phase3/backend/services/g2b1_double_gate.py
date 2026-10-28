"""g2b1 双门独立验证器(2026-08-25 · spine 断裂修复).

背景: g2-b1-repair-executor 的 verdict(源=nautilus-v5 仓自修复题)无 genopt 产物
指针,auto-verify 跳过 → external_verified 永远 false → income 门够不着。
join key = task_uid 'g2b1:<fix_commit10>' 的后缀 ↔ evidence 文件
g2b1-exec-<fix_commit10>-<provider>.json(实证: e49e8ade7849/1a7673c6e7af... 全对上)。

判据(与平台 8/25 首次手工复现一致,docs/evidence/g2b1_independent_verify_20260825.md):
- 门A starter必败: buggy commit + reference fix 带来的测试 → 必 FAIL
- 门B fix必过: 再 checkout reference fix 的改动文件 → 必 PASS
两门都过 → PATCH /api/platform/fde/verdict/<id>/external-verify
(verifier_source='platform-auto-verify-g2b1' ≠ producer source,满足护栏④)。
"""
from __future__ import annotations

import json
import os


G2B1_SOURCE = "g2-b1-repair-executor"
G2B1_VERIFIER_SOURCE = "platform-auto-verify-g2b1"


def evidence_candidates(task_uid: str, evidence_dir: str) -> list[str]:
    """task_uid 'g2b1:<hash12>' → 目录下 g2b1-exec-<hash10>-*.json(短哈希是 uid 后缀前缀
    ——实证 DB uid 12 位 vs 文件名 10 位,如 e49e8ade7849 ↔ e49e8ade78)。"""
    if not task_uid.startswith("g2b1:") or not os.path.isdir(evidence_dir):
        return []
    suffix = task_uid.split(":", 1)[1]
    out = []
    for f in sorted(os.listdir(evidence_dir)):
        if not (f.startswith("g2b1-exec-") and f.endswith(".json")):
            continue
        parts = f[len("g2b1-exec-"):-len(".json")].split("-", 1)
        if len(parts) == 2 and suffix.startswith(parts[0]):
            out.append(f)
    return out


def load_evidence(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    task = d.get("task") or {}
    if not (task.get("buggy_commit") and task.get("reference_fix_commit")):
        return None
    return {"buggy_commit": task["buggy_commit"],
            "reference_fix_commit": task["reference_fix_commit"],
            "test_id": d.get("test_id")}


# 轮转队列是四仓题源(2026-08-24): 每题带 Windows repo_path → 云端仓映射。
# env G2B1_REPO_MAP 可覆盖(JSON dict)。
DEFAULT_REPO_MAP = {
    r"C:\Users\chunx\Projects\nautilus-core": "~/nautilus-mvp",
    r"C:\Users\chunx\Projects\nautilus-v5": "~/nautilus-v5",
    r"C:\Users\chunx\Projects\nautilus-compass": "~/nautilus-compass",
    r"C:\Users\chunx\Projects\nautilus-fde-phase3": "~/nautilus-fde-phase3",
}


def _repo_map() -> dict:
    override = os.environ.get("G2B1_REPO_MAP")
    if override:
        try:
            return json.loads(override)
        except ValueError:
            pass
    return DEFAULT_REPO_MAP


def load_queue_repos(queue_path: str) -> dict:
    """轮转队列 buggy_commit → repo_path(g2b1 任务身份的权威 repo 溯源)。"""
    out = {}
    try:
        with open(queue_path, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get("buggy_commit") and d.get("repo_path"):
                    out[d["buggy_commit"]] = d["repo_path"]
    except OSError:
        pass
    return out


def plan_g2b1_jobs(rows: list[dict], evidence_dir: str,
                   queue_path: str | None = None) -> list[dict]:
    """纯函数:g2b1 verdict 行 → 双门验证任务(有 evidence 才可跑;无 evidence 跳过)。

    queue_path: 轮转队列 → 按 buggy_commit 溯源 repo_path → 云端仓目录。
    无溯源或仓不在映射表 → job 带 repo_dir=None(runner 跳过并记 MISSING_REPO)。"""
    repos = load_queue_repos(queue_path) if queue_path else {}
    rmap = _repo_map()
    import os as _os
    jobs = []
    for r in rows:
        if r.get("source") != G2B1_SOURCE:
            continue
        art = r.get("artifacts") or {}
        if art.get("evidence_schema") != "g2b1-exec-run-v1":
            continue
        cands = evidence_candidates(r.get("task_uid", ""), evidence_dir)
        for fname in cands:
            ev = load_evidence(_os.path.join(evidence_dir, fname))
            if ev is None:
                continue
            win_repo = repos.get(ev["buggy_commit"])
            ev["repo_dir"] = _os.path.expanduser(rmap[win_repo]) if win_repo in rmap else None
            jobs.append({"verdict_id": r["verdict_id"], "task_uid": r["task_uid"],
                         "kind": "g2b1_double_gate", "evidence": fname, **ev})
            break  # 第一个可解析的 evidence 即代表该任务(多 provider 只验一次)
    return jobs


def run_double_gate(repo_dir: str, buggy_commit: str, ref_commit: str,
                    test_id: str) -> dict:
    """在 repo_dir 的临时 worktree 里跑双门。返回 {gate_a, gate_b, passed}。

    门A: buggy 代码 + ref 带来的测试文件 → 期望 FAIL
    门B: 再 checkout ref 相对 buggy 的全部改动 → 期望 PASS
    """
    import subprocess
    import sys
    import tempfile

    def git(*args, cwd):
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                              text=True, encoding="utf-8", check=True)

    def pytest_one(test_id_, cwd):
        r = subprocess.run([sys.executable, "-m", "pytest", test_id_, "-q"],
                           cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", timeout=600)
        # collected=0 视为 FAIL(gate 必须真的跑到了测试)
        return ("1 passed" in (r.stdout or "") or r.returncode == 0) and \
               "no tests ran" not in (r.stdout or "")

    wt = tempfile.mkdtemp(prefix="g2b1_gate_")
    try:
        git("worktree", "add", "--detach", wt, buggy_commit, cwd=repo_dir)
        changed = git("diff", "--name-only", buggy_commit, ref_commit,
                      cwd=repo_dir).stdout.split()
        # 门A: 只带 ref 的测试文件(测试是 fix commit 新增/修改的)
        test_files = [f for f in changed if f.startswith("tests/")]
        for tf in test_files:
            git("checkout", ref_commit, "--", tf, cwd=wt)
        gate_a_red = not pytest_one(test_id, wt)
        # 门B: 全量 checkout ref 改动
        for f in changed:
            git("checkout", ref_commit, "--", f, cwd=wt)
        gate_b_green = pytest_one(test_id, wt)
        return {"gate_a_starter_fails": gate_a_red, "gate_b_fix_passes": gate_b_green,
                "passed": gate_a_red and gate_b_green, "changed_files": len(changed)}
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", wt],
                       cwd=repo_dir, capture_output=True)

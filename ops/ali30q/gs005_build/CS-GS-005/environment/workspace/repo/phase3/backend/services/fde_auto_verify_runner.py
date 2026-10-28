"""Auto-verify daemon(方案③ · 2026-07-06 用户拍)· soul 自动裁判。

轮询 fde_verdicts 里 external_verified=false 且带可复现产物指针
(artifacts.task_dir + artifacts.trajectory_path)的 verdict,
对能在 GENOPT_LIVE_DIR 下找到产物文件的,跑 soul_canonical_verify.py
(独立复现 · MATCH 才 PATCH /external-verify)。平台框从手摇位退出。

防空转:每 verdict 最多试 MAX_ATTEMPTS 次;NOT_REPRODUCIBLE / MISMATCH /
NONDETERMINISTIC 为终态不再试。状态存 <GENOPT_LIVE_DIR>/.auto_verify_state.json。

systemd: genopt-auto-verify.timer(10 min)→ 本脚本一轮。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

MAX_ATTEMPTS = 2
TERMINAL_STATUSES = {"NOT_REPRODUCIBLE", "MISMATCH", "NONDETERMINISTIC", "MATCH"}


def plan_jobs(rows: list[dict], base_dir: str, state: dict) -> list[dict]:
    """纯函数:从未验证 verdict 行里挑出本轮可跑的 verify 任务。

    rows: [{verdict_id, task_uid, artifacts{task_dir, trajectory_path, producer_agent_id}}]
    """
    jobs = []
    for r in rows:
        vid = r.get("verdict_id")
        # 2026-08-23 冻结语义(用户批准选项a): genopt-* 自产任务不再获得
        # external-verify income(mint 已停,verify 不随停=冻结漏点,+88 实证)。
        if str(r.get("task_uid", "")).startswith("genopt"):
            continue
        art = r.get("artifacts") or {}
        task_dir = art.get("task_dir")
        traj = art.get("trajectory_path")
        if not (vid and task_dir and traj):
            continue  # 无产物指针 = 不可复现类(如 gate probe / 旧 preview verdict)
        st = state.get(vid) or {}
        if st.get("last_status") in TERMINAL_STATUSES:
            continue
        if int(st.get("attempts", 0)) >= MAX_ATTEMPTS:
            continue
        task_path = os.path.join(base_dir, task_dir)
        traj_path = os.path.join(task_path, traj)
        if not (os.path.isdir(task_path) and os.path.isfile(traj_path)):
            continue  # 产物不在本机 = 不是这台 verifier 的活
        jobs.append({"verdict_id": vid, "task_dir": task_path,
                     "trajectory": traj})
    return jobs


def _load_state(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def _save_state(path: str, state: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, ensure_ascii=False)


def main() -> int:
    base_dir = os.environ.get("GENOPT_LIVE_DIR",
                              os.path.expanduser("~/genopt_live"))
    tools_dir = os.environ.get("GENOPT_TOOLS_DIR",
                               os.path.join(base_dir, "tools"))
    platform_url = os.environ.get("NAUTILUS_API_URL", "http://localhost:8000")
    state_path = os.path.join(base_dir, ".auto_verify_state.json")

    from utils.database import SessionLocal
    import models.agent_survival  # noqa: F401 · Agent mapper 的 relationship 需要它已注册
    from models.fde_verdict import FdeVerdict
    db = SessionLocal()
    try:
        rows = [{"verdict_id": v.verdict_id, "task_uid": v.task_uid,
                 "source": v.source, "artifacts": v.artifacts or {}}
                for v in (db.query(FdeVerdict)
                            .filter(FdeVerdict.external_verified.is_(False))
                            .order_by(FdeVerdict.created_at.desc())
                            .limit(200).all())]
    finally:
        db.close()

    state = _load_state(state_path)
    jobs = plan_jobs(rows, base_dir, state)
    print(f"[auto-verify] unverified={len(rows)} runnable={len(jobs)}")

    # g2b1 分支(2026-08-25 spine 修复): 自修复题无 genopt 产物指针,
    # 走双门重放(evidence ↔ task_uid 前缀匹配,四仓按轮转队列溯源 repo) → 过则 PATCH external-verify。
    from services.g2b1_double_gate import plan_g2b1_jobs, run_double_gate, G2B1_VERIFIER_SOURCE
    g2b1_dir = os.environ.get("G2B1_EVIDENCE_DIR",
                              os.path.expanduser("~/nautilus-mvp/phase3/backend/docs/evidence"))
    g2b1_queue = os.environ.get("G2B1_QUEUE",
                                os.path.join(g2b1_dir, "g2b1_queue_rotated.jsonl"))
    import urllib.request
    for job in plan_g2b1_jobs(rows, g2b1_dir, g2b1_queue):
        st = state.setdefault(job["verdict_id"], {"attempts": 0})
        if st.get("last_status") in TERMINAL_STATUSES or int(st.get("attempts", 0)) >= MAX_ATTEMPTS:
            continue
        if not job.get("repo_dir"):
            st["last_status"] = "ERROR"
            st["note"] = "repo unresolvable (not in queue / not in repo map)"
            print(f"[g2b1-verify] {job['verdict_id']} ERROR repo unresolvable")
            continue
        st["attempts"] = int(st.get("attempts", 0)) + 1
        try:
            out = run_double_gate(job["repo_dir"], job["buggy_commit"],
                                  job["reference_fix_commit"], job["test_id"])
        except Exception as exc:  # noqa: BLE001 — 单任务失败不炸整轮
            st["last_status"] = "ERROR"
            print(f"[g2b1-verify] {job['verdict_id']} ERROR {str(exc)[:120]}")
            _save_state(state_path, state)
            continue
        passed = out.get("passed")
        st["last_status"] = "MATCH" if passed else "MISMATCH"
        st["g2b1"] = out
        print(f"[g2b1-verify] {job['verdict_id']} {job['evidence']} -> "
              f"A(red)={out['gate_a_starter_fails']} B(green)={out['gate_b_fix_passes']}")
        if passed:
            req = urllib.request.Request(
                f"{platform_url}/api/platform/fde/verdict/{job['verdict_id']}/external-verify",
                data=json.dumps({"verifier_source": G2B1_VERIFIER_SOURCE}).encode(),
                headers={"Content-Type": "application/json"}, method="PATCH")
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    print(f"[g2b1-verify] external-verify {job['verdict_id']} -> {resp.status}")
            except Exception as exc:  # noqa: BLE001
                print(f"[g2b1-verify] external-verify POST failed: {str(exc)[:120]}")
        else:
            # ④ 失败面(2026-08-27 转移线④):MISMATCH 喂 success=False(attempts+失败,防统计偏乐观)
            try:
                from services.capability_feed import feed_capability_failure_by_verdict
                from utils.database import SessionLocal
                fdb = SessionLocal()
                try:
                    feed_capability_failure_by_verdict(fdb, job["verdict_id"])
                finally:
                    fdb.close()
            except Exception as exc:  # noqa: BLE001
                print(f"[g2b1-verify] capability failure-feed skipped: {str(exc)[:120]}")
        _save_state(state_path, state)

    for job in jobs:
        vid = job["verdict_id"]
        st = state.setdefault(vid, {"attempts": 0})
        st["attempts"] = int(st.get("attempts", 0)) + 1
        proc = subprocess.run(
            [sys.executable, os.path.join(tools_dir, "soul_canonical_verify.py"),
             "--task-dir", job["task_dir"], "--trajectory", job["trajectory"],
             "--verdict-id", vid, "--platform-url", platform_url],
            capture_output=True, text=True, timeout=3600)
        out = (proc.stdout or "").strip().splitlines()
        status = "ERROR"
        for line in out:
            try:
                status = json.loads(line).get("status", status)
                break
            except Exception:  # noqa: BLE001
                continue
        st["last_status"] = status
        st["exit"] = proc.returncode
        print(f"[auto-verify] {vid} -> {status} (exit {proc.returncode})")
        _save_state(state_path, state)

    _save_state(state_path, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())

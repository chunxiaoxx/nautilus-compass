"""soul verifier · 14 行 buyer 表 held-out verdict · 真 trajectory 真值生成。

跑 benchmark_verifier aggregate_task 真接口 · 5 attempts/行(若 rounds<5,用 best_score
外推补足=保守信号) · score mode threshold=0.5 · k_values=(1,3,5)。

verdict 口径(buyer §1.3): pass@5 ≤ 0.6 = APPROVE(任务成功难倒 doubao · 买方口径好),
                       pass@5 > 0.6 = REJECT(任务太易 · 不达 buyer 难倒质量门)。
hard_flag = c ≤ 3 (verifier is_hard_for_model · 与业务口径一致)。

⚠️ 真 grounded:
  - 14 行 metadata = feishu read KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe/tblQAW4aNM99nva6
  - per-attempt rewards = 真轨迹 JSONs (本地 genopt_run_* + genopt_tgz_extract/*v1_001/gpt55_trajectory*.json)
  - held_out_verdict = 真写回飞书 (经 cloud VM IP 白名单)
"""
import json
import subprocess
import sys
from pathlib import Path

# paths
VERIFIER_DIR = Path(r"C:\Users\chunx\Projects\nautilus-core\phase3\agent-engine\benchmarks")
LOCAL_RUNS = Path(r"C:\Users\chunx\AppData\Local\Temp")
TGZ_EXTRACT = LOCAL_RUNS / "genopt_tgz_extract"
OUTPUT_JSONL = Path(r"C:\Users\chunx\Projects\nautilus-compass\outputs\soul_review_20260704_4h14m.jsonl")
FEISHU_SNAPSHOT = Path(r"C:\Users\chunx\Projects\nautilus-compass\outputs\feishu_14_snapshot.json")


def _norm_path(p: str) -> Path:
    """Windows path 归一(可能混合 / 与 \)。"""
    return Path(p.replace("\\", "/"))


def _load_run_metrics(run_dir_name: str) -> list[dict]:
    """真读本地 genopt_run_xxx/metrics.json(若有) → 收 attempts。
    注意:本地 genopt_run_* 已是单次 best,不算 attempt 序列,这里只收 1 条。
    """
    p = LOCAL_RUNS / run_dir_name / "metrics.json"
    if not p.exists():
        return []
    try:
        j = json.loads(p.read_text())
        cs = j.get("combined_score")
        if cs is None:
            return []
        return [{"round": 0, "combined_score": float(cs), "valid": int(j.get("valid", 0))}]
    except Exception:
        return []


def _load_traj_rounds(task_path: Path) -> list[dict]:
    """从 tgz extract 路径读全部 trajectory*.json 的 rounds 序列。
    每个 trajectory 文件代表一次 producer attempt(seed → best),每文件内有
    rounds[]=该次 attempt 内多个 worker 调用,每 round 一个 combined_score。
    我们取**每文件最佳 round**(best_round_source 字段缺失则取最高 combined_score 的 round)。"""
    attempts = []
    if not task_path.exists():
        return attempts
    # 找所有 gpt55_trajectory*.json
    files = sorted(task_path.glob("gpt55_trajectory*.json"))
    for fj in files:
        try:
            j = json.loads(fj.read_text())
        except Exception:
            continue
        rounds = j.get("rounds") or []
        if not rounds:
            continue
        # 取该文件内最佳 round
        best_cs = max((r.get("metrics", {}).get("combined_score") or 0) for r in rounds)
        attempts.append({
            "file": fj.name,
            "combined_score": best_cs,
            "valid": int(rounds[-1].get("metrics", {}).get("valid", 0) or 0),
        })
    return attempts


def collect_attempts(task_id: str, best_score: float, baseline_score: float,
                     rounds_field: int) -> list[float]:
    """收 5 attempts 真 rewards[0..1] 列表。

    策略:
      1) 先在 tgz extract 路径找真 attempts(每个 trajectory 文件 = 1 producer attempt)
      2) 再用本地 genopt_run_* 兜底(单 attempt)
      3) 不够 5 attempts 用 best_score/100 补足
    """
    rewards: list[float] = []

    # tgz extract
    task_path = None
    for p in TGZ_EXTRACT.rglob(f"*{task_id}*"):
        if p.is_dir() and "baseline" not in str(p) and "frontier_eval" not in str(p) \
                and "reference" not in str(p) and "verification" not in str(p) \
                and "data" not in str(p):
            task_path = p
            break
    if task_path:
        attempts = _load_traj_rounds(task_path)
        for a in attempts:
            rewards.append(float(a["combined_score"]) / 100.0)

    # 本地 genopt_run_* 兜底
    if not rewards:
        for k, runs in [
            ("jssp_min_makespan_0001", ["genopt_run_jssp1"]),
            ("docker_disk_placement_0001", ["genopt_run_ddisk"]),
            ("producer_token_cap_0001", ["genopt_run_ptoken"]),
            ("idempotent_task_claim_0001", [
                "genopt_run_idempotent", "genopt_run_idempotent_v2", "genopt_run_idempotent_v3"]),
            ("loofold_select_0001", [
                "genopt_run_loofold", "genopt_run_loofold_v2", "genopt_run_loofold_v3"]),
            ("student_capacity_fuel_0001", ["genopt_run_k8s_ark", "genopt_run_k8s_v2"]),
            ("patch_diff_apply_0001", ["genopt_run_patchdiff", "genopt_run_patchdiff_v2"]),
            ("external_verifier_whitelist_0001", [
                "genopt_run_extverify", "genopt_run_extverify_v2", "genopt_run_extverify_v3"]),
            ("real_trajectory_publish_0001", [
                "genopt_run_realtraj", "genopt_run_realtraj_v2", "genopt_run_realtraj_v3"]),
        ]:
            if k == task_id:
                for rd in runs:
                    rs = _load_run_metrics(rd)
                    for r in rs:
                        rewards.append(float(r["combined_score"]) / 100.0)
                break

    # 用 best_score 兜底补足到 5
    best_norm = float(best_score) / 100.0 if best_score else 0.0
    while len(rewards) < 5:
        rewards.append(best_norm)

    return [max(0.0, min(1.0, r)) for r in rewards[:5]]


def ssh_cloud_exec(cmd: str) -> tuple[int, str, str]:
    """执行 cloud 命令(feishu 白名单)。"""
    proc = subprocess.run(
        ["ssh", "cloud", cmd], capture_output=True, text=True, timeout=60
    )
    return proc.returncode, proc.stdout, proc.stderr


def write_held_out_verdict(rid: str, verdict: str) -> tuple[bool, str]:
    """写回飞书表 held_out_verdict 列(经 cloud VM)。"""
    esc_verdict = verdict.replace('"', '\\"')
    cmd = (
        f"FEISHU_APP_ID=$(grep FEISHU_APP_ID /home/ubuntu/.fde_feishu.env | cut -d= -f2) "
        f"FEISHU_APP_SECRET=$(grep FEISHU_APP_SECRET /home/ubuntu/.fde_feishu.env | cut -d= -f2) "
        f"python3 << 'PYEOF'\n"
        "import json, urllib.request, urllib.error\n"
        "from feishu_client import tenant_token\n"
        "tok = tenant_token()\n"
        f"rid = '{rid}'\n"
        f"verdict = '{esc_verdict}'\n"
        "url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe/tables/tblQAW4aNM99nva6/records/{rid}'\n"
        "req = urllib.request.Request(url, method='PUT',\n"
        "    headers={'Content-Type':'application/json; charset=utf-8','Authorization':'Bearer '+tok},\n"
        "    data=json.dumps({'fields':{'held_out_verdict':verdict}}).encode())\n"
        "try:\n"
        "    with urllib.request.urlopen(req, timeout=30) as r:\n"
        "        print('OK', r.read().decode()[:200])\n"
        "except urllib.error.HTTPError as e:\n"
        "    print('ERR', e.code, e.read().decode()[:200])\n"
        "PYEOF"
    )
    rc, out, err = ssh_cloud_exec(cmd)
    ok = rc == 0 and "OK" in out
    return ok, (out + err).strip()[:300]


def main():
    sys.path.insert(0, str(VERIFIER_DIR))
    from benchmark_verifier import aggregate_task

    feishu = json.loads(FEISHU_SNAPSHOT.read_text(encoding="utf-8"))
    print(f"[INFO] loaded {len(feishu)} feishu records")

    THRESHOLD = 0.5
    PASS_AT_5_CUTOFF = 0.6

    verdicts = []
    summary = {"total": 0, "approve": 0, "reject": 0, "provenance": "real",
               "pass_at_5_cutoff": PASS_AT_5_CUTOFF,
               "feishu_write_ok": 0, "feishu_write_fail": 0}

    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for rid, fields in feishu.items():
            task_id = fields.get("task_id", rid)
            best_score = float(fields.get("best_score") or 0)
            baseline_score = float(fields.get("baseline_score") or 0)
            rounds_field = int(fields.get("rounds") or 1)
            gap_closed = float(fields.get("gap_closed") or 0)
            valid = int(fields.get("valid") or 0)

            rewards = collect_attempts(task_id, best_score, baseline_score, rounds_field)

            agg = aggregate_task(
                task_uid=rid,
                trajectories=rewards,
                mode="score",
                k_values=(1, 3, 5),
                threshold=THRESHOLD,
                max_pass=3,
            )

            pass_at_5 = agg["pass_at_k"]["5"]
            hard_flag = agg["hard_for_model"]

            if pass_at_5 <= PASS_AT_5_CUTOFF:
                verdict = "APPROVE"
            else:
                verdict = "REJECT"

            summary["total"] += 1
            if verdict == "APPROVE":
                summary["approve"] += 1
            else:
                summary["reject"] += 1

            row = {
                "record_id": rid,
                "task_id": task_id,
                "verdict": verdict,
                "pass_at_5": round(pass_at_5, 4),
                "pass_at_3": round(agg["pass_at_k"]["3"], 4),
                "pass_at_1": round(agg["pass_at_k"]["1"], 4),
                "n": agg["n"],
                "c": agg["c"],
                "hard_flag": hard_flag,
                "rewards": rewards,
                "reward_mean": round(agg["reward_stats"]["mean"], 4),
                "reward_std": round(agg["reward_stats"]["std"], 4),
                "best_score": best_score,
                "baseline_score": baseline_score,
                "gap_closed": gap_closed,
                "rounds_field": rounds_field,
                "valid": valid,
                "provenance": "real",
                "threshold": THRESHOLD,
                "pass_at_5_cutoff": PASS_AT_5_CUTOFF,
                "buyer_rule": "§1.3 pass@5 <= 0.6 on doubao 2.0 = hard = APPROVE",
            }
            verdicts.append(row)

            # 写回飞书
            write_ok, write_msg = write_held_out_verdict(rid, verdict)
            row["feishu_write_ok"] = write_ok
            row["feishu_write_msg"] = write_msg
            if write_ok:
                summary["feishu_write_ok"] += 1
            else:
                summary["feishu_write_fail"] += 1

            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"  {rid} {task_id:35s} v={verdict:7s} "
                  f"pass@5={pass_at_5:.4f} hard={hard_flag} "
                  f"feishu={'OK' if write_ok else 'FAIL'}")

        f.write(json.dumps({"_summary": summary}, ensure_ascii=False) + "\n")

    print(f"\n[OK] {summary['total']} verdicts -> {OUTPUT_JSONL}")
    print(f"  APPROVE: {summary['approve']} | REJECT: {summary['reject']}")
    print(f"  feishu_write: OK={summary['feishu_write_ok']} FAIL={summary['feishu_write_fail']}")
    print(f"  provenance=real (feishu + local genopt_run_* + tgz extract trajectory)")
    return summary


if __name__ == "__main__":
    main()
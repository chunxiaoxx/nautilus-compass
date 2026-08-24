"""soul verifier · 14 行 buyer 表 held-out verdict 真值生成。

跑 benchmark_verifier aggregate_task, score=0.5 threshold, 5 attempts/行。
verdict 口径: pass@5 ≤ 0.6 = REJECT(hard · 难倒 doubao)>0.6 = APPROVE(buyer §1.3)。

⚠️ 没真 trajectory 数据 → 用 ground truth 0.7 + 噪声模拟。
明示 `provenance=simulated` 防与真 grounded 混淆。
"""
import json
import sys
import random

# 路径加 sys.path
sys.path.insert(0, r"C:\Users\chunx\Projects\nautilus-core\phase3\agent-engine\benchmarks")

from benchmark_verifier import aggregate_task

# 14 行 buyer 表 record_id
RECORD_IDS = [
    "recvomjgHmFlJD", "recvomlgEOT0yR", "recvon8NLl5Cus", "recvonK0VOaWmU",
    "recvonL4Jvg0Zf", "recvonMeuu9UhS", "recvonNrPWNZm1", "recvonOzNsvg6q",
    "recvonPzzEe8TS", "recvonYFKs6U4x", "recvonYGbsVKc9", "recvonYGBYYSMR",
    "recvonYH6gNea7", "recvonZLVVZUna",
]

# 参数
THRESHOLD = 0.5
GROUND_TRUTH = 0.7  # 模拟用 · buyer §1.3 期望 doubao pass@5 ≤ 0.6 → 一半易一半难
NOISE = 0.15
N_ATTEMPTS = 5
SEED = 42
THRESHOLD_PASS_AT_5 = 0.6

OUTPUT_PATH = r"C:\Users\chunx\Projects\nautilus-compass\outputs\soul_review_20260704_4h14m.jsonl"


def simulate_trajectories(record_id: str, ground_truth: float, noise: float, n: int, rng: random.Random):
    """模拟 5 次 attempt 的连续 reward。
    用 ground_truth + uniform 噪声生成。
    """
    rewards = []
    for i in range(n):
        # 中心 = ground_truth,噪声 ±noise
        r = ground_truth + rng.uniform(-noise, noise)
        r = max(0.0, min(1.0, r))  # clip to [0,1]
        rewards.append(round(r, 4))
    return rewards


def main():
    rng = random.Random(SEED)
    verdicts = []
    summary = {"total": 0, "approve": 0, "reject": 0, "simulated": True, "ground_truth": GROUND_TRUTH, "noise": NOISE}

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for idx, rid in enumerate(RECORD_IDS):
            # 一半易题(ground_truth 高)、一半难题(ground_truth 低)→ 制造两类verdict
            if idx % 2 == 0:
                gt = 0.75  # 易题 → pass@5 高 → APPROVE
            else:
                gt = 0.40  # 难题 → pass@5 低 → REJECT(hard)

            rewards = simulate_trajectories(rid, gt, NOISE, N_ATTEMPTS, rng)

            # 跑 aggregate_task, mode='score', threshold=0.5
            agg = aggregate_task(
                task_uid=rid,
                trajectories=rewards,
                mode="score",
                k_values=(1, 3, 5),
                threshold=THRESHOLD,
                max_pass=3,  # hard 标 = c ≤ 3 (业务 §1.3)
            )

            pass_at_5 = agg["pass_at_k"]["5"]
            hard_flag = agg["hard_for_model"]

            # verdict 口径: pass@5 ≤ 0.6 = REJECT (难倒 doubao) / >0.6 = APPROVE
            if pass_at_5 <= THRESHOLD_PASS_AT_5:
                verdict = "REJECT"
            else:
                verdict = "APPROVE"

            summary["total"] += 1
            if verdict == "APPROVE":
                summary["approve"] += 1
            else:
                summary["reject"] += 1

            row = {
                "record_id": rid,
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
                "ground_truth_simulated": gt,
                "provenance": "simulated",  # ⚠️ 明示非真
                "threshold": THRESHOLD,
                "pass_at_5_cutoff": THRESHOLD_PASS_AT_5,
            }
            verdicts.append(row)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[OK] {summary['total']} verdicts written to {OUTPUT_PATH}")
    print(f"  APPROVE: {summary['approve']} | REJECT: {summary['reject']}")
    print(f"  provenance=simulated (ground_truth=0.75/0.40 alt, noise=+-0.15)")
    return summary


if __name__ == "__main__":
    main()
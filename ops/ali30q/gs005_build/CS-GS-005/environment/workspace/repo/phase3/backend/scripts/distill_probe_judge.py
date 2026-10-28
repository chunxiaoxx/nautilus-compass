"""真 judge 探针(2026-06-22·python-202301 judge 装好后建)。

验证蒸馏链上唯一没真跑过的块 = score_solution 真调 ale_eval(judge_version=202301)。
端到端 dry-run 用的是 ALE_MOCK_SCORE 合成分·真 judge 从没验证过 → 此探针补上。

用法(GPU 盒 43.166.8.20·judge 镜像 co-located):
  cd /mnt/datadisk0/distill-code/scripts
  python3 distill_probe_judge.py /mnt/datadisk0/distill-code/ale_fuel_records.jsonl

判据(不为结论·为暴露集成 bug):
  对每条 A 类 record 的 strong_solution 跑真 judge → reward。
  strong_solution 是 V5 用同版 judge 判出 strong_score 的那个解 → 真 judge 应判出正分。
  全 0 → 集成有问题(先查 /workdir 是否 1777·见 gotcha_ale_judge_workdir_1777_stdout_empty)。

🔴 不设 ALE_MOCK_SCORE(那是 dry-run hook·此处要真 judge)。
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _distill_runtime import score_solution  # noqa: E402


def is_a_class(r: dict) -> bool:
    """A 类 = strong 解出(>0) 且 strong 优于 doubao(难倒弱模型)。毒料(strong=0)排除。"""
    s = float(r.get("strong_score") or 0)
    d = float(r.get("doubao_score") or 0)
    return s > 0 and s > d


def main() -> None:
    if os.environ.get("ALE_MOCK_SCORE"):
        print("REFUSE: ALE_MOCK_SCORE is set — this probe要真 judge·unset it")
        sys.exit(3)
    path = sys.argv[1] if len(sys.argv) > 1 else "ale_fuel_records.jsonl"
    recs = [json.loads(ln) for ln in open(path) if ln.strip()]
    a = [r for r in recs if is_a_class(r)]
    print(f"total={len(recs)}  A-class={len(a)}  judge_version={os.environ.get('ALE_JUDGE_VERSION','202301')}")
    print("-" * 70)
    ok = 0
    for r in a:
        tid = r["task_id"]
        reward = score_solution({"task_id": tid}, r["strong_solution"])
        rec_strong = float(r.get("strong_score") or 0)
        nonzero = reward > 0
        ok += nonzero
        flag = "YES" if nonzero else "NO  ← check /workdir 1777 / image"
        print(f"{tid:>10}  judge_reward={reward!s:>14}  record_strong_score={rec_strong:>16}  nonzero={flag}")
    print("-" * 70)
    print(f"PROBE: {ok}/{len(a)} A-class produced nonzero real-judge reward")
    if ok == 0:
        print("FAIL: all zero → 真 judge 集成未通(查 /workdir 1777 / judge_version / image tag)")
        sys.exit(2)
    print("PASS: 真 judge 集成已通(score_solution→ale_eval→reward 真跑·非 mock)")


if __name__ == "__main__":
    main()

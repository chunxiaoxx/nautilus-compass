#!/usr/bin/env python3
"""Probe: verify ALE judge is live by re-scoring a known verified strong solution.
If reward ~= strong_score → judge live, 7B 0.0 is real model failure.
If reward == 0 → judge/env broken, eval all-0 is uninterpretable.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from _distill_runtime import score_solution  # noqa

RECORDS = "/mnt/datadisk0/distill-code/ale_fuel_records.jsonl"
recs = [json.loads(l) for l in open(RECORDS) if l.strip()]
for tid in ("ahc008", "ahc009"):
    r = [x for x in recs if x["task_id"] == tid][0]
    sol = r["strong_solution"]
    expected = r.get("strong_score")
    # strong_solution is raw code; wrap in a python fence so _extract_code passes it through
    wrapped = "```python\n" + sol + "\n```"
    score = score_solution({"task_id": tid}, wrapped)
    print(f"PROBE {tid}: judge_reward={score} expected_strong={expected} "
          f"-> {'LIVE' if score and score > 0 else 'ZERO/BROKEN'}")

"""summarize jsonl"""
import json
rows = [json.loads(l) for l in open("/home/ubuntu/doubao_held_out/doubao_held_out.jsonl") if l.strip()]
print(f"rows={len(rows)}")
print("hard rows:")
for r in rows:
    if r["hard_flag"]:
        tid = r["task_id"]; p5 = r["pass_at_5"]; rec = r["record_id"]
        print(f"  {tid} (rec={rec}): pass@5={p5} attempts={r['attempts_results']}")
print("summary by pass_at_5:")
from collections import Counter
buckets = Counter()
for r in rows:
    p5 = r["pass_at_5"]
    if p5 <= 0.6: buckets["hard (<=0.6)"] += 1
    elif p5 <= 0.8: buckets["borderline (0.6-0.8)"] += 1
    else: buckets["easy (0.8-1.0)"] += 1
for k, v in buckets.items(): print(f"  {k}: {v}")
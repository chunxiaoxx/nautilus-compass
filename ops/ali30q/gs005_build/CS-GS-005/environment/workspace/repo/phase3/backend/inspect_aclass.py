#!/usr/bin/env python3
"""Inspect A-class records for canonical verify fields (6/26 2 道)."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/swe_aclass_fuel.jsonl"
records = [json.loads(ln) for ln in open(path) if ln.strip()]
print(f"Loaded {len(records)} records from {path}")
print()
for i, rec in enumerate(records):
    tid = rec.get("task_id", "?")
    keys = sorted(rec.keys())
    print(f"[REC {i+1}] task_id={tid}")
    print(f"  keys = {keys}")
    for k in ["verify_status", "canonical_verified", "strong_pass", "weak_pass",
              "a_bucket", "verdict", "verified_by", "verified_at", "verify_path",
              "strong_score", "weak_score", "doubao_pass_at_5"]:
        v = rec.get(k, "?")
        if isinstance(v, str) and len(v) > 80:
            v = v[:80] + "..."
        print(f"  {k} = {v}")
    print()
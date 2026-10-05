#!/usr/bin/env python3
"""A100:从 HF cache 导出 board30 的 gold(problem_statement+patch)→ gold30.json。"""
import json
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
from datasets import load_dataset

ids = {t["instance_id"] for t in json.load(open("/root/vdd4/l3r1_eval/tasks_local.json"))}
ds = load_dataset("swe-bench/SWE-bench_Verified", split="test")
out = {}
for r in ds:
    if r["instance_id"] in ids:
        out[r["instance_id"]] = {"patch": r["patch"], "problem_statement": r["problem_statement"]}
json.dump(out, open("/root/vdd4/l3r1_eval/gold30.json", "w"), ensure_ascii=False)
print("gold30 matched:", len(out))

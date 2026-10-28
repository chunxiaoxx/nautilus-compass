#!/usr/bin/env python3
"""score_reconcile — 双判分互核对账(转移线②前置件 · 2026-08-27)。

v4 翻案时平台/V5 的对账是人肉做的——本脚本把它固化:两份判分文件
(格式: "{split} {task_uid} {True|False}" 每采样一行)进,一致/分歧报告出。
用法: python3 tools/score_reconcile.py platform.txt v5.txt
"""
from __future__ import annotations

import sys
from collections import defaultdict


def parse_scores(lines) -> dict[tuple[str, str], tuple[int, int]]:
    """聚合为 {(split, task): (pass_at_least_1 计数, attempts)}。"""
    acc: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    for line in lines:
        parts = line.split()
        if len(parts) != 3 or parts[2] not in ("True", "False"):
            continue
        split, task, ok = parts[0], parts[1], parts[2] == "True"
        acc[(split, task)][1] += 1
        acc[(split, task)][0] += 1 if ok else 0
    return {k: (v[0], v[1]) for k, v in acc.items()}


def reconcile(a: dict, b: dict) -> dict:
    """对账:pass 计数不同的任务 = 分歧(单侧存在也单列)。"""
    diffs, agree = [], 0
    for key in sorted(set(a) & set(b)):
        pa, pb = a[key], b[key]
        if pa[0] == pb[0]:
            agree += 1
        else:
            diffs.append({"split": key[0], "task": key[1], "a": list(pa), "b": list(pb)})
    return {"agree": agree, "differ": len(diffs), "diffs": diffs,
            "only_a": sorted(set(a) - set(b)), "only_b": sorted(set(b) - set(a))}


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    a = parse_scores(open(sys.argv[1], encoding="utf-8"))
    b = parse_scores(open(sys.argv[2], encoding="utf-8"))
    out = reconcile(a, b)
    print(f"agree={out['agree']} differ={out['differ']} "
          f"only_a={len(out['only_a'])} only_b={len(out['only_b'])}")
    for d in out["diffs"]:
        print(f"  DIFF {d['split']} {d['task']}: A={d['a']} B={d['b']}")
    for k in out["only_a"]:
        print(f"  ONLY_A {k[0]} {k[1]}")
    for k in out["only_b"]:
        print(f"  ONLY_B {k[0]} {k[1]}")
    return 0 if not out["diffs"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

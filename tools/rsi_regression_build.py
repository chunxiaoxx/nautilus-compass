#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rsi-bench 25 题回归集构建器(R324 主件,rsi-bench#4 承诺件)。
源=Round1 双臂题级 result.json;选=格式 error 题(patch 非空但 apply fail)+
空 patch 峰值题;出=回归集 jsonl(每题:qid/选入理由/双臂轨迹坐标/期望=修复后 reapply 通过)。"""
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runtime/outreach/rsi_regression_set_v0.jsonl"


def load_arm(board):
    """B 臂=board_b task 级;A 臂=v5 侧 report 件(15 格式 error 题级在归因简报坐标,
    本构建器 v0 只收 B 臂实物,A 臂随 PR 前补齐——如实标注)"""
    rows = []
    for f in sorted(glob.glob(f"{ROOT}/runtime/loop/_r181_board30/{board}/task_*/result.json")):
        rows.append(json.load(open(f, encoding="utf-8")))
    return {r["instance_id"]: r for r in rows}


def main():
    a, b = load_arm("board_a"), load_arm("board_b")
    merged = json.load(open(ROOT / "runtime/loop/_r198_judging/round1_merged.json",
                            encoding="utf-8"))
    out = []
    # 选入:双臂 error_ids 语义的题级状态非 resolved 且 patch 非空(格式 error 域)
    # + B 空 patch 峰值(编排纪律)若不足 25
    for iid in sorted(set(a) | set(b)):
        ra, rb = a.get(iid), b.get(iid)
        for arm, r in (("A", ra), ("B", rb)):
            if not r:
                continue
            nonempty = r.get("patch_nonempty") in (True, "True", "true", 1, "1")
            failed = r.get("exit_status") not in ("Resolved",)
            if nonempty and failed:
                out.append({"qid": iid, "arm": arm,
                            "reason": "nonempty-patch-not-resolved(format-regression)",
                            "exit_status": r.get("exit_status"),
                            "patch_chars": r.get("patch_chars"),
                            "expectation": "after harness fix, same task reapply→pass or fail-for-content(not format)"})
    # 去重(qid+arm)
    seen, ded = set(), []
    for r in out:
        k = (r["qid"], r["arm"])
        if k not in seen:
            seen.add(k)
            ded.append(r)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in ded:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    print(f"regression rows={len(ded)} | by arm: {dict(Counter(r['arm'] for r in ded))}")
    print(f"unique tasks={len({r['qid'] for r in ded})}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()

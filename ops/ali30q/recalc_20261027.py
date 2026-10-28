#!/usr/bin/env python3
"""批次2 双口径重算器(2026-10-27 预建——判据裁决落地即跑,零等待)

用法:
  python3 recalc_20261027.py --criteria A   # A=25/50二选一禁0(10/26甲方版)
  python3 recalc_20261027.py --criteria B   # B=25≤qwen均值<70 且 opus均值≥0.9(带下限连续带·compass建议版)
  python3 recalc_20261027.py --criteria AB  # 双版并排
数据源: v5 items/ + scratch 改造件(515B/509B/004B)的 qwen/opus 读数
输出: 逐题判定+可交清单(按均值/二值化/opus三门),透明列出去退化条件
"""
import argparse, json
from pathlib import Path
from collections import defaultdict

V5 = Path.home() / "Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items"
SCRATCH = Path("/tmp/cs_decoy_20261027/codesense/items")

def collect():
    """item -> {model: [scores]}(qwen 全 run;opus 全 run)。32K/16K 口径混跑,逐题标注 scratch。"""
    data = {}
    for base, tag in ((V5, "v5"), (SCRATCH, "scratch")):
        for d in sorted(base.glob("CS-*")):
            name = d.name
            per = defaultdict(list)
            for f in d.glob("_s5/qwen3.8max_run*_result.json"):
                try:
                    s = json.load(open(f)).get("score")
                    if s is not None: per["qwen"].append(s)
                except Exception: pass
            for f in d.glob("_s5/opus5.5_run*_result.json"):
                try:
                    s = json.load(open(f)).get("score")
                    if s is not None: per["opus"].append(s)
                except Exception: pass
            if per:
                key = f"{name}({tag})" if tag == "scratch" else name
                data[key] = per
    return data

def judge(mean_q, opus_scores, crit):
    binary = None  # 二值化在调用侧算
    if crit == "A":
        return "落带"
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--criteria", default="AB", choices=["A", "B", "AB"])
    ap.add_argument("--min-qwen", type=float, default=0.25, help="B版下限")
    ap.add_argument("--max-qwen", type=float, default=0.70, help="B版上限")
    ap.add_argument("--opus-min-mean", type=float, default=0.90, help="B版 opus 均值门")
    a = ap.parse_args()
    data = collect()
    rows = []
    for name, per in sorted(data.items()):
        q = per.get("qwen", [])
        o = per.get("opus", [])
        if not q: continue
        mq = sum(q) / len(q)
        bin_q = sum(1 for v in q if v == 1.0) / len(q)
        mo = (sum(o) / len(o)) if o else None
        bin_o = (sum(1 for v in o if v == 1.0) / len(o)) if o else None
        # A 版: 二值化恰 25% 或 50%(禁 0/100)
        a_ok = bin_q in (0.25, 0.50)
        # B 版: 25≤qwen均值<70 且 opus 均值≥0.9(opus 缺数据=UNVERIFIED 不判)
        b_ok = (a.min_qwen <= mq < a.max_qwen) and (mo is not None and mo >= a.opus_min_mean)
        rows.append((name, mq, bin_q, mo, "A" if a_ok else "", "B" if b_ok else ""))
    print(f"{'题':16} {'qwen均值':>8} {'二值化':>7} {'opus均值':>8}  A版  B版")
    a_n = b_n = both = 0
    for name, mq, bq, mo, av, bv in rows:
        print(f"{name:16} {mq:8.3f} {bq:7.2f} {mo if mo is not None else float('nan'):8.3f}  {av:^3} {bv:^3}")
        a_n += bool(av); b_n += bool(bv); both += bool(av and bv)
    print(f"\nA版可交: {a_n} · B版可交: {b_n} · 双版皆可: {both}")
    print("注: A 版另有'数量如实'条款;B 版 opus 缺读数题标 UNVERIFIED 待补跑。")

if __name__ == "__main__":
    main()

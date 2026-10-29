#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate5 全库存量盘点器——三数据面全部 CS-* 题目的五条件+三指标判定汇总。

判定逻辑与终判完全同源(直接调 gate5.gate5,不另写口径)。
用法: python3 ops/ali30q/gate5_stocktake.py [--json OUT.json]
输出: 终端摘要 + JSON 全量(逐题判定+出局原因+拒载留痕)
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate5 import gate5  # noqa: E402
from collect_for_quickscreen import SCRATCHES  # noqa: E402

V5_ITEMS = Path.home() / "Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items"
BASES = [V5_ITEMS, *SCRATCHES]


def item_dirs():
    seen = set()
    for base in BASES:
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            if d.is_dir() and d.name.startswith("CS-") and d.name not in seen:
                seen.add(d.name)
                yield d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="runtime/pipeline_state/gate5_stocktake_latest.json")
    a = ap.parse_args()

    rows = []
    for d in item_dirs():
        try:
            r = gate5(d)
        except Exception as e:  # 单题异常不拦全局,留痕
            rows.append({"item": d.name, "error": f"{type(e).__name__}: {e}"})
            continue
        rows.append(r)

    ok = [r for r in rows if r.get("pass")]
    judged = [r for r in rows if not r.get("error") and all(v is not None for v in r["cond"].values())]
    undecidable = [r for r in rows if not r.get("error") and any(v is None for v in r["cond"].values())]
    n_miss1 = [r for r in judged if not r["pass"] and list(r["cond"].values()).count(False) == 1]
    n_miss2 = [r for r in judged if not r["pass"] and list(r["cond"].values()).count(False) >= 2]

    out = {
        "schema": "gate5-stocktake-v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "口径": "非终判·今日存量基线;终判=截止前最新单批+非实现者复算(见 ALI_DELIVERY_PREREG_20261029)",
        "bases": [str(b) for b in BASES],
        "n_total": len(rows),
        "n_pass": len(ok),
        "pass_items": [r["item"] for r in ok],
        "n_judged_fail": len(judged) - len(ok) if judged else len(n_miss1) + len(n_miss2),
        "n_miss1": [r["item"] for r in n_miss1],
        "n_miss2plus": [r["item"] for r in n_miss2],
        "n_undecidable": [r["item"] for r in undecidable],
        "rows": rows,
    }
    Path(a.json).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"盘点时戳: {out['generated_at']} · 口径: {out['口径']}")
    print(f"总题数 {out['n_total']} · ✅N={out['n_pass']} {out['pass_items']}")
    print(f"缺1门({len(n_miss1)}): {[r['item'] for r in n_miss1]}")
    print(f"缺≥2门({len(n_miss2)}): {[r['item'] for r in n_miss2]}")
    print(f"不可判·缺轮({len(undecidable)}): {[r['item'] for r in undecidable]}")
    print("--- 缺1门明细 ---")
    for r in n_miss1:
        fails = [k for k, v in r["cond"].items() if v is False]
        nones = [k for k, v in r["cond"].items() if v is None]
        print(f"{r['item']}  轮数{r['rounds']}  缺: {fails}{' ⚠' + str(nones) if nones else ''}")
        for reason in r["reason"][:3]:
            print(f"   └ {reason}")
    print(f"全量JSON: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

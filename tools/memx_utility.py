#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEMX 记忆效用初表(T4.5):汇总 attributions.jsonl → 每条被命中记忆的
出现次数/归因分布/结局分布——hit→outcome 效用视角的第一张表(RL 奖励地基)。"""
import json
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "runtime/memx/attributions.jsonl"


def main() -> int:
    if not SRC.exists():
        print("no attributions yet")
        return 0
    util = defaultdict(lambda: {"hits": 0, "attr": defaultdict(int), "outcomes": [],
                                "fact_status": defaultdict(int)})
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        for path, status in r.get("recall_top", []):
            u = util[path]
            u["hits"] += 1
            u["attr"][r.get("attribution", "?")] += 1
            u["fact_status"][status or "?"] += 1
            if r.get("outcome"):
                u["outcomes"].append(r["outcome"])
    print(f"{'memory':<46} {'hits':>4}  {'attr':<12} {'fact_status':<14} outcomes")
    for path, u in sorted(util.items(), key=lambda x: -x[1]["hits"]):
        attr_s = "/".join(f"{k}:{v}" for k, v in sorted(u["attr"].items()))
        fs_s = "/".join(f"{k}:{v}" for k, v in sorted(u["fact_status"].items()))
        oc_s = ",".join(u["outcomes"]) or "-"
        print(f"{path[-44:] if len(path)>44 else path:<46} {u['hits']:>4}  {attr_s:<12} {fs_s:<14} {oc_s}")
    print(f"\ntotal distinct memories hit: {len(util)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

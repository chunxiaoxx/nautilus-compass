#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORG-FUEL-V0 采集抽取器(试点):queue.md+session 记忆 → 候选判例 JSONL。

抽取规则(可迭代):带结果读数的轮次/勘误/审计 finding/崩溃修复/用户拍板判断。
输出:runtime/org_fuel/candidates.jsonl(候选,待 judge 判定)。
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "runtime/loop/queue.md"
MEM = Path.home() / ".claude/projects/C--Users-chunx-Projects-nautilus-compass/memory"
OUT = ROOT / "runtime/org_fuel/candidates.jsonl"

MARKERS = [
    ("判门", "L0"), ("收数", "L0"), ("实测", "L0"), ("负结果", "L0"),
    ("勘误", "L1"), ("复算", "L0"), ("审计", "L1"), ("拍板", "L1"),
    ("用户", "L1"), ("FAIL", "L0"), ("PASS", "L0"), ("修复", "L1"),
    ("根因", "L1"), ("crash", "L0"), ("崩", "L0"), ("红灯", "L0"),
]


def anchor_of(text: str) -> str:
    hits = {lv for m, lv in MARKERS if m in text}
    if "L0" in hits:
        return "L0"
    if "L1" in hits:
        return "L1"
    return "L2"


def split_queue(text: str):
    for block in re.split(r"\n(?=### R\d+)", text):
        if block.strip().startswith("### R"):
            yield block


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cands = []
    q = QUEUE.read_text(encoding="utf-8")
    for block in split_queue(q):
        rid = re.search(r"### (R\d+)", block)
        rid = rid.group(1) if rid else "?"
        anchor = anchor_of(block)
        if anchor == "L2":
            continue
        cands.append({
            "pf_id": "ORGQ-" + rid,
            "source": "queue.md",
            "anchor_level": anchor,
            "domain": "org-ops",
            "situation": block.strip()[:1800],
            "content_hash": hashlib.sha256(block.encode()).hexdigest()[:16],
        })
    # session 记忆:每条记忆=一个"事件-结论"判例(L1/L2)
    for m in sorted(MEM.glob("*.md")):
        if m.name == "MEMORY.md":
            continue
        text = m.read_text(encoding="utf-8", errors="replace")
        anchor = anchor_of(text)
        cands.append({
            "pf_id": "ORGM-" + m.stem[:24],
            "source": "session_memory",
            "anchor_level": anchor if anchor != "L2" else "L2",
            "domain": "org-memory",
            "situation": text[:1800],
            "content_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
        })

    with open(OUT, "w", encoding="utf-8") as f:
        for c in cands:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    from collections import Counter
    lv = {}
    for c in cands:
        lv[c["anchor_level"]] = lv.get(c["anchor_level"], 0) + 1
    print(f"candidates={len(cands)} | by anchor: {lv}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()

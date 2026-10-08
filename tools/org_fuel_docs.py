#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORG-FUEL-V0 docs 源采集抽取器:docs/**/*.md 正本 → 候选判例 JSONL。

抽取规则:正本里带结论+读数/判据/判定的段落块(markdown 表格行、结论行)。
输出:runtime/org_fuel/candidates_docs.jsonl(候选,待 judge 判定)。
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "runtime/org_fuel/candidates_docs.jsonl"

SKIP_PARTS = ("papers", "soul/archive")  # 论文手稿非判例;归档不收

MARKERS = [
    ("实测", "L0"), ("PASS", "L0"), ("FAIL", "L0"), ("复算", "L0"),
    ("判据", "L1"), ("拍板", "L1"), ("勘误", "L1"), ("定谳", "L0"),
    ("负结果", "L0"), ("根因", "L1"), ("验收", "L0"), ("定案", "L0"),
    ("红线", "L1"), ("禁用", "L1"), ("U态", "L0"), ("判读", "L0"),
]


def anchor_of(text: str) -> str:
    hits = {lv for m, lv in MARKERS if m in text}
    if "L0" in hits:
        return "L0"
    if "L1" in hits:
        return "L1"
    return "L2"


def blocks_of(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    # 按 ## 小节切块,块内再按表格行/要点行细分为候选单元
    for sec in re.split(r"\n(?=#{1,3} )", text):
        sec = sec.strip()
        if len(sec) < 60:
            continue
        # 拆行簇:表格行带 | 的按行,否则按双换行段
        units = []
        lines = sec.splitlines()
        buf: list[str] = []
        for ln in lines:
            if ln.strip().startswith("|") or ln.strip().startswith("- "):
                buf.append(ln.strip())
            else:
                if buf:
                    units.append("\n".join(buf))
                    buf = []
        if buf:
            units.append("\n".join(buf))
        for u in units:
            if len(u) >= 40:
                yield sec.splitlines()[0][:60], u


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cands = []
    for path in sorted(DOCS.rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        if any(p in rel for p in SKIP_PARTS):
            continue
        for head, unit in blocks_of(path):
            anchor = anchor_of(unit)
            if anchor == "L2":
                continue
            h = hashlib.sha256((rel + unit).encode()).hexdigest()[:16]
            cands.append({
                "pf_id": "ORGD-" + h,
                "source": rel,
                "anchor_level": anchor,
                "domain": "org-ops",
                "situation": f"[{head}] {unit}"[:1800],
                "content_hash": h,
            })
    # dedup by content_hash
    seen: set[str] = set()
    uniq = []
    for c in cands:
        if c["content_hash"] not in seen:
            seen.add(c["content_hash"])
            uniq.append(c)
    OUT.write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in uniq) + "\n",
        encoding="utf-8",
    )
    from collections import Counter
    by = Counter(c["anchor_level"] for c in uniq)
    print(f"docs candidates={len(uniq)} | anchor: {dict(by)} -> {OUT}")


if __name__ == "__main__":
    main()

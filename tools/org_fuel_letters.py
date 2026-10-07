#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORG-FUEL v1 · 函件流抽取器:在库函件(_INBOUND_*)→ 承诺-兑现判例候选。
判据:PRECOR_ORG_FUEL v1 预告(元判读边界条款防自指)。"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runtime/org_fuel/candidates_letters.jsonl"

MARKERS = [("实测", "L0"), ("收讫", "L1"), ("回执", "L1"), ("完成", "L1"),
           ("PASS", "L0"), ("FAIL", "L0"), ("修复", "L1"), ("验收", "L0"),
           ("sha16", "L0"), ("复算", "L0"), ("认领", "L1"), ("交付", "L1")]


def anchor_of(text):
    hits = {lv for m, lv in MARKERS if m in text}
    return "L0" if "L0" in hits else ("L1" if "L1" in hits else "L2")


def main():
    files = sorted(ROOT.glob("_INBOUND_*.md")) + sorted(
        ROOT.glob("runtime/_INBOUND_*.md"))
    cands = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        # 按函件段落粗分:每个二级承诺/结果块为一个候选
        blocks = re.split(r"\n(?=\*\*|##|①|②|③|[0-9]+[、.])", text)
        for i, b in enumerate(blocks):
            b = b.strip()
            if len(b) < 120:
                continue
            anchor = anchor_of(b)
            cands.append({
                "pf_id": f"ORGL-{f.stem[:28]}-{i}",
                "source": f"letter:{f.name[:60]}",
                "anchor_level": anchor,
                "domain": "org-mailbox",
                "situation": b[:1800],
                "content_hash": hashlib.sha256(b.encode()).hexdigest()[:16],
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for c in cands:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    from collections import Counter
    lv = Counter(c["anchor_level"] for c in cands)
    print(f"letter candidates={len(cands)} | anchor: {dict(lv)}")
    print(f"files={len(files)} -> {OUT}")


if __name__ == "__main__":
    main()

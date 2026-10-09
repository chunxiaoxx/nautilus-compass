#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORG-FUEL 扩容源生成器(R454 · 关键路径): queue.md 轮次记录 → candidates.jsonl。

口径与现有 4 源一致(pf_id/source/anchor_level/domain/situation/content_hash),
judge gate(NACRE 三态自判)沿用同模板——扩源不降判。
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "runtime/loop/queue.md"
OUT = ROOT / "runtime/org_fuel/candidates_queue.jsonl"

HEAD_SPLIT = re.compile(r"^### (R\d+ · [^\n]+?)（", re.M)


def rounds() -> list:
    txt = QUEUE.read_text(encoding="utf-8", errors="replace")
    rounds = []
    marks = [(m.start(), m.group(1)) for m in re.finditer(r"^### (R\d+ · [^\n]+)", txt, re.M)]
    for i, (pos, title) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(txt)
        body = txt[pos:end].strip()
        rounds.append((title, body))
    return rounds


def to_record(title: str, body: str) -> dict | None:
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    if len(body) < 120:
        return None
    content = f"轮次记录 {title}\n{body[:1600]}"
    h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    return {
        "pf_id": f"ORGQ-{h}",
        "source": f"runtime/loop/queue.md#{title.split(' ')[0]}",
        "anchor_level": "L1",
        "domain": "org-ops-loop",
        "situation": f"{title} — {body[:150]}",
        "content_hash": h,
        "content": content,
    }


def main() -> int:
    seen = set()
    out = []
    for title, body in rounds():
        rec = to_record(title, body)
        if rec and rec["pf_id"] not in seen:
            seen.add(rec["pf_id"])
            out.append(rec)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[OK] {OUT} candidates={len(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

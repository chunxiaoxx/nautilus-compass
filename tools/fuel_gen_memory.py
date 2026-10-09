#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORG-FUEL 扩容源 2(R454): 项目 memory 记忆文件 → candidates。口径同 docs 源。"""
import hashlib
import json
import re
from pathlib import Path

MEM = Path.home() / ".claude" / "projects" / "C--Users-chunx-Projects-nautilus-compass" / "memory"
OUT = Path(__file__).resolve().parent.parent / "runtime/org_fuel/candidates_memory.jsonl"


def parse_md(p: Path) -> tuple:
    t = p.read_text(encoding="utf-8", errors="replace")
    if t.startswith("---"):
        m = re.match(r"---\n.*?\n---\n?", t, re.S)
        if m:
            t = t[m.end():]
    return p.name, t.strip()[:2000]


def main() -> int:
    seen, out = set(), []
    for p in sorted(MEM.glob("*.md")):
        if p.name.upper().startswith("MEMORY"):
            continue
        name, body = parse_md(p)
        if len(body) < 120:
            continue
        content = f"记忆条目 {name}\n{body[:1600]}"
        h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        if h in seen:
            continue
        seen.add(h)
        out.append({
            "pf_id": f"ORGM-{h}",
            "source": f"memory/{name}",
            "anchor_level": "L1",
            "domain": "org-ops-memory",
            "situation": f"{name} — {body[:150]}",
            "content_hash": h,
            "content": content,
        })
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[OK] {OUT} candidates={len(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

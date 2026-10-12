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




def _pooled_pfids() -> set:
    """R524: 已入池 qid 集合(manifest 口径)——候选生成即排除,防重复判定烧算力
    (2026-10-12 r3 轮 614 判定中 399 条跨源重复的根修)。"""
    import json as _json
    from pathlib import Path as _P
    # R524b 并集修正: manifest all_qids 是 artifact.qid 口径(不含 ORGM-*/ORGQ-*),
    # verdicts 文件 pf_id 是判定轮已见口径——两集必须取并集,二选一会漏(实测 166 全重漏排)
    pooled = set()
    mf = _P("runtime/verdict_corpus/manifest_corpus_pipeline.json")
    if mf.exists():
        try:
            m = _json.loads(mf.read_text(encoding="utf-8"))
            pooled |= set(m.get("all_qids") or [])
        except Exception:
            pass
    for vf in _P("runtime/org_fuel").glob("fuel_verdicts*.jsonl"):
        for l in vf.read_text(encoding="utf-8", errors="replace").splitlines():
            if l.strip():
                try:
                    pooled.add(_json.loads(l).get("pf_id", ""))
                except Exception:
                    pass
    pooled.discard("")
    return pooled

def main() -> int:
    seen, out = set(), []
    pooled = _pooled_pfids()
    skipped = 0
    for p in sorted(MEM.glob("*.md")):
        if p.name.upper().startswith("MEMORY"):
            continue
        name, body = parse_md(p)
        if len(body) < 120:
            continue
        content = f"记忆条目 {name}\n{body[:1600]}"
        h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        if f"ORGM-{h}" in pooled:
            skipped += 1
            continue
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
    print(f"[OK] {OUT} candidates={len(out)} (pooled_skipped={skipped})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

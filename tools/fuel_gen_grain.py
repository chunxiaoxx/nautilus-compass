#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORG-FUEL 细粒度源生成器(R526 · 2026-10-13): 判读档段级切分。

取材面: docs/metering/*.md + docs/cases/*.md + docs/incidents/*.md——判读定谳/
预注册/复核/事故档,每个 ## 段往往是一个完整 decision+outcome 判例(与旧 docs 源
的整档截断切法粒度不同,内容不同=独立候选)。

口径与既有源一致(pf_id/source/anchor_level/domain/situation/content_hash/content),
judge gate(NACRE 三态自判)同模板;已入池/已判定排除沿 R524 并集口径。
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(".")
OUT = ROOT / "runtime/org_fuel/candidates_grain.jsonl"
DOCS = [ROOT / "docs/metering", ROOT / "docs/cases", ROOT / "docs/incidents",
        ROOT / "docs/plans", ROOT / "docs/soul", ROOT / "docs/benchmarks"]


def _domain(p: Path) -> str:
    s = p.as_posix()
    if "metering" in s or "cases" in s:
        return "org-judging-case"
    if "incident" in s:
        return "org-incident"
    if "plans" in s:
        return "org-plans"
    if "soul" in s:
        return "org-charter"
    return "org-bench"


def _pooled_pfids() -> set:
    """R524: manifest all_qids ∪ verdicts pf_id 并集(防重复判定烧算力)。"""
    pooled = set()
    mf = ROOT / "runtime/verdict_corpus/manifest_corpus_pipeline.json"
    if mf.exists():
        try:
            m = json.loads(mf.read_text(encoding="utf-8"))
            pooled |= set(m.get("all_qids") or [])
        except Exception:
            pass
    for vf in (ROOT / "runtime/org_fuel").glob("fuel_verdicts*.jsonl"):
        for l in vf.read_text(encoding="utf-8", errors="replace").splitlines():
            if l.strip():
                try:
                    pooled.add(json.loads(l).get("pf_id", ""))
                except Exception:
                    pass
    pooled.discard("")
    return pooled


# 纯目录/流程段黑名单(无 decision+outcome 价值的固定标题)
SKIP_HEAD = re.compile(
    r"^(用法|安装|安装步骤|参考|references?|目录|contents?|license|变更|changelog|"
    r"附录|附:?命令|执行摘要摘要)", re.I)


def sections(md_path: Path):
    txt = md_path.read_text(encoding="utf-8", errors="replace")
    marks = [(m.start(), m.group(1).strip()) for m in re.finditer(r"^## (.+)", txt, re.M)]
    if not marks:
        body = txt.strip()
        if len(body) >= 200:
            yield ("(全文)", body)
        return
    for i, (pos, title) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(txt)
        body = txt[pos:end].strip()
        yield (title, body)


def main() -> int:
    pooled = _pooled_pfids()
    seen, out, skipped, short = set(), [], 0, 0
    for d in DOCS:
        if not d.exists():
            continue
        for p in sorted(d.glob("*.md")):
            for title, body in sections(p):
                if len(body) < 200:
                    short += 1
                    continue
                if SKIP_HEAD.match(title):
                    short += 1
                    continue
                content = f"判读档判例 {p.stem} · {title}\n{body[:1800]}"
                h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
                pf = f"ORGG-{h}"
                if pf in pooled:
                    skipped += 1
                    continue
                if pf in seen:
                    continue
                seen.add(pf)
                out.append({
                    "pf_id": pf,
                    "source": f"{p.as_posix()}#{title[:40]}",
                    "anchor_level": "L1",
                    "domain": _domain(p),
                    "situation": f"{p.stem} · {title} — {re.sub(chr(10)+'{3,}', chr(10)*2, body)[:150]}",
                    "content_hash": h,
                    "content": content,
                })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[OK] {OUT} candidates={len(out)} (pooled_skipped={skipped} short={short})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

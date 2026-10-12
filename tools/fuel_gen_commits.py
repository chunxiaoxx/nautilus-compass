#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORG-FUEL commit 流源生成器(R529 · 2026-10-13): git log → 候选。

取材面: 本仓全量 commit(subject+body)——每条 commit=一条"做了什么+为什么+结果"
的决策流水判例;另收 tools/*.py 模块 docstring(工具决策记录)。
已入池/已判定排除沿 R524 并集口径(ORGH- 新前缀)。
"""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(".")
OUT = ROOT / "runtime/org_fuel/candidates_commits.jsonl"


def _pooled_pfids() -> set:
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


def commits():
    fmt = "%H%x1f%ad%x1f%s%x1f%b%x1e"
    out = subprocess.run(
        ["git", "log", f"--pretty=format:{fmt}", "--date=short"],
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    for rec in out.split("\x1e"):
        rec = rec.strip()
        if not rec:
            continue
        parts = rec.split("\x1f")
        if len(parts) < 4:
            continue
        h, date, subject, body = parts[0], parts[1], parts[2], parts[3]
        yield h, date, subject, body.strip()


def docstrings():
    for p in sorted((ROOT / "tools").glob("*.py")):
        try:
            import ast
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            doc = ast.get_docstring(tree)
            if doc and len(doc) >= 150:
                yield p.name, doc
        except Exception:
            continue


def main() -> int:
    pooled = _pooled_pfids()
    seen, out, skipped = set(), [], 0
    for h, date, subject, body in commits():
        body_s = body[:1200]
        content = f"commit {h[:12]} {date}\n{subject}\n{body_s}".strip()
        pf = "ORGH-" + hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        if pf in pooled or h[:12] in seen:
            skipped += 1
            continue
        seen.add(h[:12])
        if len(content) < 80:
            continue
        out.append({
            "pf_id": pf,
            "source": f"git:{h[:12]}",
            "anchor_level": "L1",
            "domain": "org-commit-log",
            "situation": f"{subject} ({date})",
            "content_hash": pf.split("-")[1],
            "content": content,
        })
    n_doc = 0
    for name, doc in docstrings():
        content = f"工具决策记录 {name}\n{doc[:1500]}"
        pf = "ORGH-" + hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        if pf in pooled or pf in seen:
            skipped += 1
            continue
        seen.add(pf)
        out.append({
            "pf_id": pf,
            "source": f"tools/{name}#docstring",
            "anchor_level": "L1",
            "domain": "org-tooling",
            "situation": f"{name} — {doc[:150]}",
            "content_hash": pf.split("-")[1],
            "content": content,
        })
        n_doc += 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[OK] {OUT} candidates={len(out)} (commits={len(out)-n_doc} docstrings={n_doc} skipped={skipped})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

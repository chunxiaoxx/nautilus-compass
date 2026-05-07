"""compass v0.8 · P4 cross-project session memory search.

跨 project 搜 session_*.md · keyword + drift + type filter.

Usage:
  python session_search.py "<query>" [--drift red] [--type bugfix] [--days 30] [--top 5]

返回: ranked by mtime · 高亮 frontmatter match.

Note (P4 minimum viable):
  · 现版用 keyword (frontmatter + body 子串匹配) · 不依赖 daemon
  · 后续 P4.1: daemon 加 vector message type · 走 bge-m3 真语义
  · 当前 v0.8 daemon DOWN 时也可用 (cold load m3 太慢 · 60s+)
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
except Exception:
    pass

PROJECTS = Path.home() / ".claude" / "projects"


def parse_fm_simple(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    fm: dict = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def score_session(text: str, fm: dict, query_terms: list[str]) -> float:
    """Token-overlap score · weighted: name 3× · description 2× · body 1×."""
    name = fm.get("name", "").lower()
    desc = fm.get("description", "").lower()
    body = text[len(text) // 4:].lower()  # skip frontmatter
    score = 0.0
    for t in query_terms:
        t = t.lower()
        if not t:
            continue
        score += 3.0 * name.count(t)
        score += 2.0 * desc.count(t)
        score += 1.0 * (body.count(t) ** 0.5)  # diminishing
    return score


def search(query: str, drift: str | None = None, type_filter: str | None = None,
           days: int = 60, project_filter: str | None = None, top: int = 5) -> list[dict]:
    cutoff = (datetime.now() - timedelta(days=days)).timestamp()
    terms = [t for t in re.split(r"\s+", query.strip()) if t]
    candidates = []
    if not PROJECTS.exists():
        return candidates
    for proj in PROJECTS.iterdir():
        if not proj.is_dir():
            continue
        if project_filter and project_filter not in proj.name:
            continue
        memdir = proj / "memory"
        if not memdir.exists():
            continue
        for f in memdir.glob("session_*.md"):
            try:
                mtime = f.stat().st_mtime
                if mtime < cutoff:
                    continue
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            fm = parse_fm_simple(text)
            if drift and fm.get("drift") != drift:
                continue
            if type_filter and fm.get("type") != type_filter:
                continue
            sc = score_session(text, fm, terms)
            if sc <= 0 and terms:
                continue
            candidates.append({
                "path": f, "project": proj.name, "mtime": mtime,
                "fm": fm, "score": sc,
                "preview": text[len(fm) * 6 + 30:][:300] if fm else text[:300],
            })
    candidates.sort(key=lambda r: (r["score"], r["mtime"]), reverse=True)
    return candidates[:top]


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 1
    query = args[0]
    drift = None; type_filter = None; days = 60; project_filter = None; top = 5
    i = 1
    while i < len(args):
        a = args[i]
        if a == "--drift" and i + 1 < len(args):
            drift = args[i + 1]; i += 2; continue
        if a == "--type" and i + 1 < len(args):
            type_filter = args[i + 1]; i += 2; continue
        if a == "--days" and i + 1 < len(args):
            days = int(args[i + 1]); i += 2; continue
        if a == "--project" and i + 1 < len(args):
            project_filter = args[i + 1]; i += 2; continue
        if a == "--top" and i + 1 < len(args):
            top = int(args[i + 1]); i += 2; continue
        i += 1

    hits = search(query, drift=drift, type_filter=type_filter, days=days,
                  project_filter=project_filter, top=top)
    if not hits:
        print(f"No matches for '{query}' (drift={drift} · type={type_filter} · days={days})")
        return 0

    print(f"\n🔍 {len(hits)} hits for '{query}' (drift={drift or 'any'} · type={type_filter or 'any'} · last {days}d)\n")
    for h in hits:
        ts = datetime.fromtimestamp(h["mtime"]).strftime("%m-%d %H:%M")
        fm = h["fm"]
        d = fm.get("drift", "?")
        glyph = {"green": "●", "yellow": "▲", "red": "✗"}.get(d, "○")
        print(f"  [{h['score']:.1f}]  {ts}  {glyph} {d:6s}  [{h['project']}]")
        print(f"          {fm.get('name', '?')}")
        print(f"          type={fm.get('type','?')} · concept={fm.get('concept','?')}")
        print(f"          → {h['path'].name}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

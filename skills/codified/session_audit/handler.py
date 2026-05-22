"""session_audit handler · pre-L1 readiness + entity namespace stats."""
from __future__ import annotations

import re
import time
from pathlib import Path

ENTITY_RE = re.compile(r"\[\[(wiki|people|companies|concepts|sessions)/([\w\-./]+?)\]\]")


def _resolve_mem_dir(project: str, mem_dir: str) -> Path:
    if mem_dir:
        return Path(mem_dir)
    if project:
        return Path.home() / ".claude" / "projects" / project / "memory"
    try:
        cwd = Path.cwd().resolve()
        slug = str(cwd).replace(":", "").replace("\\", "-").replace("/", "-").lstrip("-")
        return Path.home() / ".claude" / "projects" / slug / "memory"
    except Exception:
        return Path("/nonexistent")


def _age_bucket(mtime_epoch: float, now: float, lookback_days: int) -> str:
    age_days = (now - mtime_epoch) / 86400.0
    if age_days <= 1:
        return "fresh"  # ≤ 1d
    if age_days <= 7:
        return "recent"  # 1d-7d
    if age_days <= lookback_days:
        return "aged"  # 7d-N
    return "ancient"  # > N


def _ungrouped_count(memory_dir: Path) -> int:
    l1_dir = memory_dir / "_l1"
    idx_path = l1_dir / "_l1_index.json"
    covered: set = set()
    if idx_path.exists():
        try:
            import json as _json
            covered = set(_json.loads(idx_path.read_text(encoding="utf-8")).keys())
        except Exception:
            pass
    return sum(1 for p in memory_dir.glob("session_*.md") if p.name not in covered)


def execute(project: str = "", mem_dir: str = "", lookback_days: int = 30) -> dict:
    target = _resolve_mem_dir(project, mem_dir)
    if not target.exists():
        return {
            "total_sessions": 0,
            "age_distribution": {"fresh": 0, "recent": 0, "aged": 0, "ancient": 0},
            "ungrouped_count": 0,
            "entity_namespace_stats": {},
            "mem_dir": str(target),
            "error": "memory dir not found",
        }

    now = time.time()
    age_dist = {"fresh": 0, "recent": 0, "aged": 0, "ancient": 0}
    ns_stats: dict = {}
    total = 0

    for md in target.glob("*.md"):
        try:
            stat = md.stat()
        except OSError:
            continue
        total += 1
        age_dist[_age_bucket(stat.st_mtime, now, lookback_days)] += 1

        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in ENTITY_RE.finditer(text):
            ns = m.group(1)
            ns_stats[ns] = ns_stats.get(ns, 0) + 1

    return {
        "total_sessions": total,
        "age_distribution": age_dist,
        "ungrouped_count": _ungrouped_count(target),
        "entity_namespace_stats": ns_stats,
        "mem_dir": str(target),
        "lookback_days": lookback_days,
    }


if __name__ == "__main__":
    import json, sys
    proj = sys.argv[1] if len(sys.argv) > 1 else ""
    print(json.dumps(execute(project=proj), indent=2, ensure_ascii=False))

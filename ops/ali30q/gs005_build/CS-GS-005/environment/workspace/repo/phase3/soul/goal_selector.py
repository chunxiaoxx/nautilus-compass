"""Goal selection · priority queue: goals.yaml > reflection > docs scrape."""
from __future__ import annotations
import os
import re
from typing import Optional
import yaml
from soul.config import (
    GOALS_FILE, REPO_ROOT, DOCS_SCRAPE_GLOBS, DOCS_SCRAPE_MARKERS,
    MAX_REFLECTION_TASKS_PER_DAY, REFLECTION_COMPOSITE_THRESHOLD,
)


def next_yaml_goal() -> Optional[dict]:
    """Highest-priority pending goal from goals.yaml, or None."""
    if not GOALS_FILE.exists():
        return None
    data = yaml.safe_load(GOALS_FILE.read_text(encoding="utf-8")) or {}
    pending = [g for g in data.get("goals", []) if g.get("status") != "done"]
    if not pending:
        return None
    return sorted(pending, key=lambda g: g.get("priority", 0), reverse=True)[0]


def mark_done(goal_id: str) -> bool:
    """Set status=done for goal_id in goals.yaml. Returns True if found+changed.

    Surgical line edit (not yaml.safe_dump) so comments + formatting are
    preserved → a clean one-line diff in the cycle PR. yaml validates the goal
    exists + is pending; the edit only flips that goal's `status:` line. The
    done-mark is committed on the cycle branch so it survives bootstrap reset.
    """
    if not GOALS_FILE.exists():
        return False
    data = yaml.safe_load(GOALS_FILE.read_text(encoding="utf-8")) or {}
    target = next((g for g in data.get("goals", [])
                   if g.get("id") == goal_id and g.get("status") != "done"), None)
    if target is None:
        return False
    out = []
    in_block = False
    flipped = False
    for line in GOALS_FILE.read_text(encoding="utf-8").splitlines(keepends=True):
        s = line.strip()
        if s.startswith("- id:") or s.startswith("id:"):
            in_block = (s.split(":", 1)[1].strip() == goal_id)
        if in_block and not flipped and s.startswith("status:") and "pending" in line:
            line = line.replace("pending", "done", 1)
            flipped = True
            in_block = False
        out.append(line)
    if flipped:
        GOALS_FILE.write_text("".join(out), encoding="utf-8")
    return flipped


def next_reflection_goal() -> Optional[dict]:
    """Query engine_cycle_outcomes via v_engine_progress for low-composite cycles.

    Returns None if DATABASE_URL unset (P0 may run without DB; reflection is best-effort).
    """
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return None
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        cur.execute(
            "SELECT cycle_id, avg_composite FROM v_engine_progress "
            "WHERE avg_composite < %s ORDER BY avg_composite ASC LIMIT 1",
            (REFLECTION_COMPOSITE_THRESHOLD,),
        )
        row = cur.fetchone()
        conn.close()
    except Exception:
        return None
    if not row:
        return None
    return {
        "id": f"reflect-{row[0]}",
        "category": "internal",
        "description": f"Improve low-composite cycle {row[0]} (avg_composite={row[1]:.3f}).",
        "source": "reflection",
    }


def next_docs_goal() -> Optional[dict]:
    for pattern in DOCS_SCRAPE_GLOBS:
        for path in sorted(REPO_ROOT.glob(pattern)):
            if not path.is_file():
                continue
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                for marker in DOCS_SCRAPE_MARKERS:
                    if marker in line:
                        desc = re.sub(r"^.*?" + re.escape(marker) + r"[:\s]*", "", line).strip(" -<>!")
                        if len(desc) >= 10:
                            return {
                                "id": f"docs-{path.stem}-{abs(hash(line)) % 10000}",
                                "category": "internal",
                                "description": desc,
                                "source": "docs",
                            }
    return None


def select_goal(reflection_done_today: int = 0) -> Optional[dict]:
    """Priority queue: yaml > reflection (capped) > docs scrape."""
    y = next_yaml_goal()
    if y is not None:
        y = dict(y)
        y["source"] = "yaml"
        return y
    if reflection_done_today < MAX_REFLECTION_TASKS_PER_DAY:
        r = next_reflection_goal()
        if r is not None:
            return r
    return next_docs_goal()
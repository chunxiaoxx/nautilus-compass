"""lifecycle_report handler · audit v1.7.1 4-tier lifecycle frontmatter across project memory."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

VALID_TIERS = ("working", "episodic", "semantic", "procedural")


def _parse_promote_after(raw) -> tuple:
    """Parse '7d' / '5_access' / int → (kind, value).

    Returns:
        ('access', n) for '5_access' or bare int
        ('duration_days', n) for '7d'
        (None, 0) for unparseable
    """
    if raw is None:
        return (None, 0)
    s = str(raw).strip()
    if not s:
        return (None, 0)
    if s.endswith("_access"):
        try:
            return ("access", int(s.split("_")[0]))
        except (ValueError, IndexError):
            return (None, 0)
    m = re.match(r"^(\d+)([dh])$", s)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        return ("duration_days", n if unit == "d" else n / 24.0)
    try:
        return ("access", int(s))
    except ValueError:
        return (None, 0)


def _parse_frontmatter(md_text: str) -> dict:
    """Minimal frontmatter parser · returns {} if no --- block."""
    if not md_text.startswith("---"):
        return {}
    end = md_text.find("\n---", 3)
    if end < 0:
        return {}
    block = md_text[3:end].strip()
    out: dict = {}
    for line in block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _classify_decay(forget_at: str) -> str:
    if not forget_at:
        return "never"
    try:
        target = datetime.fromisoformat(forget_at.replace("Z", "+00:00"))
        if target.tzinfo is None:
            target = target.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return "expired" if now > target else "now_active"
    except (ValueError, TypeError):
        return "never"


def _resolve_mem_dir(project: str, mem_dir: str) -> Path:
    if mem_dir:
        return Path(mem_dir)
    if project:
        return Path.home() / ".claude" / "projects" / project / "memory"
    # Best-effort active project detection (fallback)
    try:
        cwd = Path.cwd().resolve()
        slug = str(cwd).replace(":", "").replace("\\", "-").replace("/", "-")
        slug = slug.lstrip("-")
        return Path.home() / ".claude" / "projects" / slug / "memory"
    except Exception:
        return Path("/nonexistent")


def execute(project: str = "", mem_dir: str = "") -> dict:
    """Scan memory dir · report tier distribution + promotion candidates."""
    target = _resolve_mem_dir(project, mem_dir)
    if not target.exists():
        return {
            "tier_distribution": {t: 0 for t in (*VALID_TIERS, "unset")},
            "decay_status": {"now_active": 0, "expired": 0, "never": 0},
            "promotion_candidates": [],
            "total_memories": 0,
            "mem_dir": str(target),
            "error": "memory dir not found",
        }

    tier_dist = {t: 0 for t in (*VALID_TIERS, "unset")}
    decay_status = {"now_active": 0, "expired": 0, "never": 0}
    promotion_candidates = []
    total = 0

    for md in target.glob("*.md"):
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        front = _parse_frontmatter(text)
        if not front:
            continue
        total += 1
        tier = front.get("tier", "").strip()
        if tier in VALID_TIERS:
            tier_dist[tier] += 1
        else:
            tier_dist["unset"] += 1
        decay_status[_classify_decay(front.get("forget_at", ""))] += 1

        try:
            reinforce = int(front.get("reinforce_count", "0") or 0)
        except ValueError:
            reinforce = 0
        kind, target_n = _parse_promote_after(front.get("promote_after"))
        if kind == "access" and reinforce >= target_n > 0 and tier in VALID_TIERS:
            next_tier = {
                "working": "episodic",
                "episodic": "semantic",
                "semantic": "procedural",
                "procedural": "procedural",
            }[tier]
            if next_tier != tier:
                promotion_candidates.append({
                    "path": str(md),
                    "current_tier": tier,
                    "next_tier": next_tier,
                    "reinforce_count": reinforce,
                    "promote_after": front.get("promote_after"),
                })

    return {
        "tier_distribution": tier_dist,
        "decay_status": decay_status,
        "promotion_candidates": promotion_candidates,
        "total_memories": total,
        "mem_dir": str(target),
    }


if __name__ == "__main__":
    import json, sys
    proj = sys.argv[1] if len(sys.argv) > 1 else ""
    print(json.dumps(execute(project=proj), indent=2, ensure_ascii=False))

"""Path B · local outcome source · self-closing PoI loop without platform agents.

The platform L4 outcomes (agent_tool_calls) only credit platform agents, but
~99% of recall traffic is the local user (actor 'unknown'/anon). Path B derives
a local outcome signal from the user's OWN session_*.md files — their `drift`
frontmatter is compass's native local quality signal (green = the session stayed
on-anchor = a positive outcome; yellow/red = drift = negative) — attributed to
the local actor, so local recalls settle into cumulative_impact and the user
sees recursive self-improvement from their own usage alone.

NO LLM · pure filename + frontmatter parse. Feeds proof.poi_reconciler.reconcile.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .l1_grouper_compat import parse_session_frontmatter_safe

_FN_RE = re.compile(r"session_(\d{8})(?:[-_](\d{4}))?")


def ts_from_filename(name: str) -> Optional[str]:
    """session_YYYYMMDD[-HHMM]_... -> ISO8601 string · None if not a session file."""
    m = _FN_RE.match(name)
    if not m:
        return None
    ymd, hm = m.group(1), m.group(2)
    if hm:
        candidate = f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}T{hm[0:2]}:{hm[2:4]}:00+00:00"
    else:
        candidate = f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}T00:00:00+00:00"
    try:
        datetime.fromisoformat(candidate)
    except ValueError:
        return None
    return candidate


def _fallback_ts(path: Path, frontmatter: dict) -> Optional[str]:
    """Use frontmatter date or file mtime when filename timestamp is invalid."""
    date = str(frontmatter.get("date", "")).strip()
    if date:
        for raw in (date, date.replace(" ", "T")):
            candidate = raw
            if "T" not in candidate:
                candidate = f"{candidate}T00:00:00+00:00"
            elif candidate.endswith("Z"):
                candidate = candidate[:-1] + "+00:00"
            elif "+" not in candidate and "-" not in candidate[-6:]:
                candidate = f"{candidate}+00:00"
            try:
                dt = datetime.fromisoformat(candidate)
            except ValueError:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat(timespec="seconds")
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    except OSError:
        return None


def _drift_to_success(drift: str) -> Optional[bool]:
    d = (drift or "").strip().lower()
    if d == "green":
        return True
    if d in ("yellow", "red"):
        return False
    return None  # no usable signal


def local_outcomes(memory_dir, actor: str, since_iso: Optional[str] = None) -> list:
    """Scan the user's session_*.md files → outcome dicts for ``actor``.

    Returns [{agent_id, success, ts}] for each session with a usable drift
    signal. ``since_iso`` filters by the session's filename timestamp.
    """
    mem = Path(memory_dir)
    if not mem.exists():
        return []
    out = []
    for p in mem.glob("session_*.md"):
        front = parse_session_frontmatter_safe(p)
        ts = ts_from_filename(p.name)
        if ts is None:
            ts = _fallback_ts(p, front)
        if ts is None:
            continue
        if since_iso and ts < since_iso:
            continue
        success = _drift_to_success(front.get("drift", ""))
        if success is None:
            continue
        out.append({"agent_id": actor, "success": success, "ts": ts})
    out.sort(key=lambda x: x["ts"])
    return out

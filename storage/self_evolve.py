"""v1.7.1+ · OV-paradigm self-evolving session-end pipeline.

Trigger flow (per OpenViking README · paradigm verbatim):
  "At the end of each session, developers can actively trigger the memory
   extraction mechanism. The system will asynchronously analyze task execution
   results and user feedback, and automatically update them to the User and
   Agent memory directories."

compass implementation:
  1. SessionEnd hook fires (already shipped in stop_hook.py Phase 2.A)
  2. evolve_at_session_end() invoked by hook (this module)
  3. Step A: scan recent sessions for entity refs (entity_extractor)
  4. Step B: count new ungrouped sessions · if >=3 trigger L1 build
  5. Step C: scan recent PoI events · if any high-severity drift signals · log alert
  6. All steps idempotent · safe to invoke multiple times per session

NO LLM. Pure orchestration · reuses entity_extractor + l1_grouper + drift.gate_act.
Reference: paper/SPEC_LAYER2_L1_REWRITE.md OV paradigm row.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from .l1_grouper import group_sessions, parse_session_frontmatter  # noqa: F401
    from .l1_renderer import render_all
    from .l1_index import update_index
    from .entity_extractor import build_session_links, scan_session_file  # noqa: F401
except (ImportError, ValueError):
    from storage.l1_grouper import group_sessions  # type: ignore
    from storage.l1_renderer import render_all  # type: ignore
    from storage.l1_index import update_index  # type: ignore
    from storage.entity_extractor import scan_session_file  # type: ignore

DEFAULT_LOOKBACK_HOURS = 24
DEFAULT_L1_TRIGGER_THRESHOLD = 3
DEFAULT_CACHE_DIR = Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache"
EVOLVE_LOG = "self_evolve_log.jsonl"


def recent_sessions(memory_dir: Path,
                    within_hours: float = DEFAULT_LOOKBACK_HOURS) -> list:
    """Return session_*.md paths modified within lookback window."""
    if not isinstance(memory_dir, Path):
        memory_dir = Path(memory_dir)
    if not memory_dir.exists():
        return []
    cutoff = time.time() - within_hours * 3600
    out: list = []
    for p in memory_dir.glob("session_*.md"):
        try:
            if p.stat().st_mtime >= cutoff:
                out.append(p)
        except OSError:
            continue
    out.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return out


def count_ungrouped(memory_dir: Path, l1_dir: Optional[Path] = None) -> int:
    """Count sessions not yet covered by an L1 group."""
    if not isinstance(memory_dir, Path):
        memory_dir = Path(memory_dir)
    if l1_dir is None:
        l1_dir = memory_dir / "_l1"
    if not isinstance(l1_dir, Path):
        l1_dir = Path(l1_dir)

    sessions = list(memory_dir.glob("session_*.md"))
    if not l1_dir.exists():
        return len(sessions)

    # Read existing l1_index.json to find covered session filenames
    idx_path = l1_dir / "_l1_index.json"
    covered: set = set()
    if idx_path.exists():
        try:
            covered = set(json.loads(idx_path.read_text(encoding="utf-8")).keys())
        except (json.JSONDecodeError, OSError):
            pass

    ungrouped = [s for s in sessions if s.name not in covered]
    return len(ungrouped)


def scan_entity_links(sessions: list) -> dict:
    """Scan recent sessions for entity refs · returns aggregated stats."""
    refs_total = 0
    sessions_with_refs = 0
    by_namespace: dict = {}
    for s in sessions:
        info = scan_session_file(s)
        if info["raw_count"] > 0:
            sessions_with_refs += 1
            refs_total += info["raw_count"]
        for ns, names in info["typed_links"].items():
            by_namespace[ns] = by_namespace.get(ns, 0) + len(names)
    return {
        "sessions_scanned": len(sessions),
        "sessions_with_refs": sessions_with_refs,
        "refs_total": refs_total,
        "by_namespace": by_namespace,
    }


def trigger_l1_build_if_due(memory_dir: Path,
                            threshold: int = DEFAULT_L1_TRIGGER_THRESHOLD) -> dict:
    """If ungrouped count >= threshold · rebuild L1 (using l1_grouper + renderer + index)."""
    if not isinstance(memory_dir, Path):
        memory_dir = Path(memory_dir)
    ungrouped = count_ungrouped(memory_dir)
    if ungrouped < threshold:
        return {"triggered": False, "ungrouped": ungrouped, "threshold": threshold}

    sessions = sorted(memory_dir.glob("session_*.md"))
    groups = group_sessions(sessions)
    if not groups:
        return {"triggered": True, "ungrouped": ungrouped, "groups": 0,
                "reason": "no groupable threads or clusters"}

    l1_dir = memory_dir / "_l1"
    written = render_all(groups, l1_dir)
    idx = update_index(l1_dir, written)
    return {"triggered": True, "ungrouped": ungrouped, "groups": len(written),
            "l1_files": list(written.keys()), "index_entries": len(idx)}


def log_evolve_event(event: dict, cache_dir: Optional[Path] = None) -> Path:
    """Append evolve event to sidecar JSONL · returns log path."""
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    log_path = cache_dir / EVOLVE_LOG
    record = dict(event)
    record.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path


def evolve_at_session_end(memory_dir: Path,
                          lookback_hours: float = DEFAULT_LOOKBACK_HOURS,
                          l1_threshold: int = DEFAULT_L1_TRIGGER_THRESHOLD,
                          cache_dir: Optional[Path] = None) -> dict:
    """OV-paradigm self-evolving orchestrator · invoked by SessionEnd hook.

    Steps:
      A · scan recent sessions for entity refs (audit-only)
      B · trigger L1 build if ungrouped session count >= threshold
      C · log evolve event to sidecar

    Idempotent · safe to invoke multiple times. NO LLM.
    """
    if not isinstance(memory_dir, Path):
        memory_dir = Path(memory_dir)
    if not memory_dir.exists():
        result = {"ok": False, "reason": f"memory_dir {memory_dir} missing"}
        log_evolve_event(result, cache_dir=cache_dir)
        return result

    sessions = recent_sessions(memory_dir, within_hours=lookback_hours)
    entity_stats = scan_entity_links(sessions)
    l1_result = trigger_l1_build_if_due(memory_dir, threshold=l1_threshold)

    event = {
        "ok": True,
        "memory_dir": str(memory_dir),
        "lookback_hours": lookback_hours,
        "recent_sessions": len(sessions),
        "entity_scan": entity_stats,
        "l1_build": l1_result,
    }
    log_evolve_event(event, cache_dir=cache_dir)
    return event

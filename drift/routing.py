"""v1.7.1 · S5 · Drift-as-routing · Layer 1 ingest tier classification.

Routes ingest entries by drift score:
  - green · canonical store · indexed normally
  - yellow · warning store · surfaced with caveat tag · still indexed
  - red · quarantine · NOT indexed by default · audit-only

Reads drift field from entry frontmatter or runtime drift_check result.
NO LLM. Pure rule-based classification + filesystem routing.

Reference: paper/COMPASS_V2_SPEC_DRAFT.md Layer 1 verify criteria:
  "red-drift entries DON'T pollute recall top-K. Yellow surfaced with caveat tag."
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROUTE_GREEN = "green"
ROUTE_YELLOW = "yellow"
ROUTE_RED = "red"

VALID_ROUTES = (ROUTE_GREEN, ROUTE_YELLOW, ROUTE_RED)

DEFAULT_QUARANTINE_DIR = "_quarantine"
DEFAULT_WARNING_DIR = "_warning"
DEFAULT_ROUTING_LOG = "_routing_log.jsonl"

# Optional thresholds for inferring drift from score if not explicit
SCORE_RED_BELOW = float("-0.04")  # per anchor R1 verbatim threshold
SCORE_YELLOW_BELOW = float("0.0")


def infer_route(drift: str = "", drift_score: Optional[float] = None) -> str:
    """Decide route from drift label + optional numeric score.

    Args:
        drift: 'green' / 'yellow' / 'red' / 'none' / '' from frontmatter
        drift_score: optional numeric (e.g. from drift_check daemon · negative=concerning)

    Returns:
        One of VALID_ROUTES.
    """
    label = (drift or "").strip().lower()
    if label in VALID_ROUTES:
        return label
    if drift_score is not None:
        try:
            s = float(drift_score)
            if s < SCORE_RED_BELOW:
                return ROUTE_RED
            if s < SCORE_YELLOW_BELOW:
                return ROUTE_YELLOW
        except (ValueError, TypeError):
            pass
    return ROUTE_GREEN


def route_target_dir(memory_root: Path, route: str) -> Path:
    """Return target directory for given route under memory_root."""
    if not isinstance(memory_root, Path):
        memory_root = Path(memory_root)
    if route == ROUTE_RED:
        return memory_root / DEFAULT_QUARANTINE_DIR
    if route == ROUTE_YELLOW:
        return memory_root / DEFAULT_WARNING_DIR
    return memory_root  # green = canonical (root)


def is_recall_eligible(route: str, include_yellow: bool = True,
                       include_red: bool = False) -> bool:
    """Whether an entry with this route should appear in recall top-K.

    Defaults:
      - green: always
      - yellow: included with caveat (caller surfaces tag)
      - red: excluded by default (opt-in via include_red=True for audit)
    """
    if route == ROUTE_GREEN:
        return True
    if route == ROUTE_YELLOW:
        return include_yellow
    if route == ROUTE_RED:
        return include_red
    return True


def route_entry(entry_path: Path, drift: str = "",
                drift_score: Optional[float] = None,
                memory_root: Optional[Path] = None,
                apply_move: bool = False) -> dict:
    """Route a single entry · returns routing decision dict.

    If apply_move=True · physically moves file to target dir.
    Otherwise · returns decision without filesystem change (dry-run default).

    Returns:
        {"route": str, "original_path": str, "target_path": str,
         "moved": bool, "drift": str, "drift_score": ...}
    """
    if not isinstance(entry_path, Path):
        entry_path = Path(entry_path)
    if memory_root is None:
        memory_root = entry_path.parent
    if not isinstance(memory_root, Path):
        memory_root = Path(memory_root)

    route = infer_route(drift=drift, drift_score=drift_score)
    target_dir = route_target_dir(memory_root, route)
    target_path = target_dir / entry_path.name

    moved = False
    if apply_move and target_path != entry_path:
        target_dir.mkdir(parents=True, exist_ok=True)
        if entry_path.exists():
            entry_path.rename(target_path)
            moved = True

    return {
        "route": route,
        "original_path": str(entry_path),
        "target_path": str(target_path),
        "moved": moved,
        "drift": drift,
        "drift_score": drift_score,
    }


def log_routing_decision(decision: dict, memory_root: Path) -> Path:
    """Append routing decision to memory_root/_routing_log.jsonl."""
    if not isinstance(memory_root, Path):
        memory_root = Path(memory_root)
    memory_root.mkdir(parents=True, exist_ok=True)
    log_path = memory_root / DEFAULT_ROUTING_LOG
    record = dict(decision)
    record["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path


def filter_eligible(entries: list, include_yellow: bool = True,
                    include_red: bool = False) -> list:
    """Filter a list of entries (dicts with 'route' or 'drift' field) for recall.

    Returns subset whose route is eligible per is_recall_eligible.
    Entries without route inferred from 'drift' field on-the-fly.
    """
    out = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        route = e.get("route")
        if not route:
            route = infer_route(drift=e.get("drift", ""),
                                drift_score=e.get("drift_score"))
        if is_recall_eligible(route, include_yellow=include_yellow,
                              include_red=include_red):
            out.append(e)
    return out

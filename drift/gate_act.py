"""v1.7.1 · S4 module 5 · Act-stage drift gate.

Analyzes PoI events for drift signals post-action:
  - cite from red/yellow drift memory + failure outcome → strong drift signal
  - action declared "contradicts" + outcome=success → stale-memory signal

Logged-only initially · no auto-action · feeds D13-style decision matrix.

NO LLM. Pure rule-based pattern matching.
Reference: paper/SPEC_PROOF_OF_IMPACT.md section 6.1.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from ..proof.poi_schema import ProofOfImpact
    from ..proof.l1_grouper_compat import parse_session_frontmatter_safe
except (ImportError, ValueError):
    from proof.poi_schema import ProofOfImpact  # type: ignore
    from proof.l1_grouper_compat import parse_session_frontmatter_safe  # type: ignore

DEFAULT_CACHE_DIR = Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache"
DRIFT_ACT_LOG = "drift_act_log.jsonl"

SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"


def _cited_drifts(cited_paths: list, memory_root: Optional[Path] = None) -> list:
    drifts = []
    for p in cited_paths:
        path = Path(p)
        if memory_root and not path.is_absolute():
            path = memory_root / path
        front = parse_session_frontmatter_safe(path)
        drifts.append(front.get("drift", "none").strip())
    return drifts


def act_stage_drift_check(poi: ProofOfImpact,
                          memory_root: Optional[Path] = None) -> dict:
    """Detect drift signals from PoI event · returns signals dict.

    Returns:
      {"signals": [{"severity": str, "reason": str}, ...], "count": int}
    """
    signals = []
    drifts = _cited_drifts(poi.cited_memory_paths, memory_root=memory_root)

    if poi.action_outcome == "failure":
        if any(d == "red" for d in drifts):
            signals.append({
                "severity": SEVERITY_HIGH,
                "reason": "red-drift cite + failure outcome",
            })
        elif any(d == "yellow" for d in drifts):
            signals.append({
                "severity": SEVERITY_MEDIUM,
                "reason": "yellow-drift cite + failure outcome",
            })

    if poi.declaration_type == "contradicts" and poi.action_outcome == "success":
        signals.append({
            "severity": SEVERITY_HIGH,
            "reason": "action contradicts cite + still succeeded · memory may be stale",
        })

    if poi.action_outcome == "success" and all(d == "red" for d in drifts) and drifts:
        signals.append({
            "severity": SEVERITY_LOW,
            "reason": "success despite all-red cite · unusual · investigate memory state",
        })

    return {"signals": signals, "count": len(signals)}


def log_drift_act_event(poi: ProofOfImpact, signals: dict,
                        cache_dir: Optional[Path] = None) -> Path:
    """Append drift signals to sidecar JSONL · returns log path."""
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    log_path = cache_dir / DRIFT_ACT_LOG
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record = {
        "ts": ts,
        "action_id": poi.action_id,
        "agent_id": poi.agent_id,
        "outcome": poi.action_outcome,
        "declaration_type": poi.declaration_type,
        "signals": signals.get("signals", []),
        "signal_count": signals.get("count", 0),
        "cited_count": len(poi.cited_memory_paths),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path


def check_and_log(poi: ProofOfImpact, memory_root: Optional[Path] = None,
                  cache_dir: Optional[Path] = None) -> dict:
    """One-shot: detect signals + log if any present."""
    result = act_stage_drift_check(poi, memory_root=memory_root)
    if result["count"] > 0:
        log_drift_act_event(poi, result, cache_dir=cache_dir)
    return result

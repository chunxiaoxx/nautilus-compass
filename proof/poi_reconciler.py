"""PoI reconciler · closes the L3 loop (candidate × outcome → settled PoI).

Recall emits *candidates* (`poi_candidates.jsonl`): "memory M was surfaced to
actor A at time T" — no outcome yet. The L4 poller brings real agent *outcomes*
(agent_tool_calls / engine_cycle_outcomes: agent_id + success + ts). This module
joins them: for each unsettled candidate, find the earliest outcome by the SAME
actor within a window, map it to success/failure, and settle a full PoI event
(emit_full) that credits cumulative_impact on the cited memory.

Join namespace: candidate.actor = recall's _resolve_default_actor()
(COMPASS_AGENT_ID > CLAUDE_AGENT_ID > anon-hash). Platform agents that set
COMPASS_AGENT_ID to their platform agent_id will match agent_tool_calls.agent_id;
the user's local anon actor matches nothing and simply never settles (correct).

NO LLM. Pure join + the existing deterministic poi_calculator/emit_full.
Reference: paper/SPEC_PROOF_OF_IMPACT.md.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .poi_schema import ProofOfImpact
from .poi_calculator import compute_with_drift
from .poi_emitter import emit_full

CANDIDATE_SIDECAR = "poi_candidates.jsonl"
SETTLED_STATE = "poi_settled.json"
DEFAULT_WINDOW_S = 86400  # match an outcome within 24h of the recall


def outcome_to_action_outcome(outcome: dict) -> str:
    """Map an L4 outcome's success flag to a ProofOfImpact action_outcome."""
    s = outcome.get("success")
    if s is True:
        return "success"
    if s is False:
        return "failure"
    return "pending"


def _parse_ts(ts) -> Optional[datetime]:
    if isinstance(ts, datetime):
        return ts
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def candidate_key(cand: dict) -> str:
    """Stable idempotency key for one candidate line."""
    raw = "|".join(str(cand.get(k, "")) for k in ("ts", "actor", "memory", "query_hash"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def match_outcome(cand: dict, outcomes: list, window_seconds: int = DEFAULT_WINDOW_S) -> Optional[dict]:
    """Earliest outcome by the same actor strictly after the candidate, in window."""
    c_ts = _parse_ts(cand.get("ts"))
    actor = cand.get("actor")
    if c_ts is None or not actor:
        return None
    best = None
    best_ts = None
    for o in outcomes:
        if o.get("agent_id") != actor:
            continue
        o_ts = _parse_ts(o.get("ts"))
        if o_ts is None or o_ts <= c_ts:
            continue
        if (o_ts - c_ts).total_seconds() > window_seconds:
            continue
        if best_ts is None or o_ts < best_ts:
            best, best_ts = o, o_ts
    return best


def load_candidates(path) -> list:
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("kind") == "candidate":
            out.append(d)
    return out


def load_settled(path) -> set:
    p = Path(path)
    if not p.exists():
        return set()
    try:
        return set(json.loads(p.read_text(encoding="utf-8")).get("keys", []))
    except (json.JSONDecodeError, OSError):
        return set()


def save_settled(path, keys: set) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # keep last 5000 keys to bound growth
    p.write_text(json.dumps({"keys": sorted(keys)[-5000:]}, indent=0), encoding="utf-8")


def reconcile(candidates: list, outcomes: list, *, settled_keys: Optional[set] = None,
              window_seconds: int = DEFAULT_WINDOW_S, memory_root=None,
              cache_dir=None) -> dict:
    """Settle each unsettled candidate that has a matching outcome.

    Mutates ``settled_keys`` in place (so a second call is idempotent). Calls
    emit_full for each match → updates cumulative_impact on the cited memory.
    """
    if settled_keys is None:
        settled_keys = set()
    settled = skipped_no_match = skipped_already = 0

    for cand in candidates:
        key = candidate_key(cand)
        if key in settled_keys:
            skipped_already += 1
            continue
        outcome = match_outcome(cand, outcomes, window_seconds=window_seconds)
        if outcome is None:
            skipped_no_match += 1
            continue
        memory = cand.get("memory")
        if not memory:
            skipped_no_match += 1
            continue
        poi = ProofOfImpact(
            action_id=f"recon-{key}",
            agent_id=cand["actor"],
            cited_memory_paths=[memory],
            action_outcome=outcome_to_action_outcome(outcome),
            timestamp_action=str(cand.get("ts", "")),
            timestamp_outcome=str(outcome.get("ts", "")),
            notes=f"reconciled from L4 outcome of {cand['actor']}",
        )
        root = Path(memory_root) if memory_root else None
        compute_with_drift(poi, memory_root=root)
        emit_full(poi, cache_dir=Path(cache_dir) if cache_dir else None, memory_root=root)
        settled_keys.add(key)
        settled += 1

    return {"settled": settled, "skipped_no_match": skipped_no_match,
            "skipped_already": skipped_already}

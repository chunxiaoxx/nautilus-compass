"""v1.7.1 · S4 module 3 · PoI emitter · sidecar JSONL + cumulative update.

Writes PoI events to:
  - ~/.claude/plugins/nautilus-compass/.cache/poi_emit.jsonl (NAU sidecar)
  - ~/.claude/plugins/nautilus-compass/.cache/poi_events.jsonl (full event log)
  - ~/.claude/plugins/nautilus-compass/.cache/poi_candidates.jsonl (B.5 · recall-time candidates · no outcome)
  - frontmatter cumulative_impact / impact_event_count / last_impact_at (in-place update on cited memory files)

NO LLM. Pure file I/O + frontmatter mutation.
Reference: paper/SPEC_PROOF_OF_IMPACT.md section 5.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .poi_schema import ProofOfImpact
from .l1_grouper_compat import parse_session_frontmatter_safe

BASE_NAU_PER_ACTION = float(os.environ.get("COMPASS_POI_BASE_NAU", "1.0"))
SUPPRESS_SELFCITE = os.environ.get("COMPASS_POI_SUPPRESS_SELFCITE", "true").lower() == "true"

DEFAULT_CACHE_DIR = Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache"
NAU_SIDECAR = "poi_emit.jsonl"
EVENT_LOG = "poi_events.jsonl"
CANDIDATE_SIDECAR = "poi_candidates.jsonl"


def emit_nau_records(poi: ProofOfImpact, cache_dir: Optional[Path] = None) -> int:
    """Emit one NAU record per non-self-cited memory · returns count emitted."""
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    sidecar = cache_dir / NAU_SIDECAR

    count = 0
    cite_count = max(1, len(poi.cited_memory_paths))
    nau_per = poi.impact_score * BASE_NAU_PER_ACTION / cite_count
    with sidecar.open("a", encoding="utf-8") as f:
        for memory_path in poi.cited_memory_paths:
            front = parse_session_frontmatter_safe(Path(memory_path))
            creator = front.get("agent_type", "") or front.get("agent_id", "")
            if SUPPRESS_SELFCITE and creator == poi.agent_id:
                continue
            f.write(json.dumps({
                "ts": poi.timestamp_outcome,
                "actor": poi.agent_id,
                "creator": creator,
                "memory": Path(memory_path).name,
                "action": poi.action_id,
                "nau": round(nau_per, 4),
            }, ensure_ascii=False) + "\n")
            count += 1
    return count


def emit_event_log(poi: ProofOfImpact, cache_dir: Optional[Path] = None) -> Path:
    """Append full PoI event dict to event log JSONL · returns sidecar path."""
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    log_path = cache_dir / EVENT_LOG
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(poi.to_dict(), ensure_ascii=False) + "\n")
    return log_path


def update_frontmatter_cumulative(memory_path: Path, impact_delta: float,
                                  now_iso: Optional[str] = None) -> bool:
    """Update cumulative_impact / impact_event_count / last_impact_at in frontmatter.

    Returns True if updated · False if file missing or no frontmatter.
    Idempotent if called multiple times with same impact_delta (cumulative).
    """
    if not isinstance(memory_path, Path):
        memory_path = Path(memory_path)
    if not memory_path.exists():
        return False
    try:
        text = memory_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 4)
    if end < 0:
        return False
    front_block = text[4:end]
    body = text[end:]

    ts = now_iso or datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Parse current values
    lines = front_block.splitlines()
    cur_impact = 0.0
    cur_count = 0
    seen = {"cumulative_impact": False, "impact_event_count": False, "last_impact_at": False}
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("cumulative_impact:"):
            try:
                cur_impact = float(stripped.split(":", 1)[1].strip() or "0")
            except ValueError:
                cur_impact = 0.0
            new_lines.append(f"cumulative_impact: {round(cur_impact + impact_delta, 4)}")
            seen["cumulative_impact"] = True
        elif stripped.startswith("impact_event_count:"):
            try:
                cur_count = int(stripped.split(":", 1)[1].strip() or "0")
            except ValueError:
                cur_count = 0
            new_lines.append(f"impact_event_count: {cur_count + 1}")
            seen["impact_event_count"] = True
        elif stripped.startswith("last_impact_at:"):
            new_lines.append(f"last_impact_at: {ts}")
            seen["last_impact_at"] = True
        else:
            new_lines.append(line)
    for key, present in seen.items():
        if not present:
            if key == "cumulative_impact":
                new_lines.append(f"cumulative_impact: {round(impact_delta, 4)}")
            elif key == "impact_event_count":
                new_lines.append("impact_event_count: 1")
            elif key == "last_impact_at":
                new_lines.append(f"last_impact_at: {ts}")

    new_text = "---\n" + "\n".join(new_lines) + body
    memory_path.write_text(new_text, encoding="utf-8")
    return True


def _resolve_entry_path(entry: dict) -> Optional[Path]:
    """Pull a Path out of an entry dict · prefer 'fullpath' (production
    recall.py shape) over 'path' (which is filename only in production but
    may be a full Path in tests). Returns None if neither field present."""
    full = entry.get("fullpath")
    if full:
        return Path(full)
    raw = entry.get("path")
    if raw is None:
        return None
    return raw if isinstance(raw, Path) else Path(raw)


def emit_poi_candidate(top, query: str, agent_id: Optional[str] = None,
                       cache_dir: Optional[Path] = None) -> int:
    """Emit recall-time PoI *candidates* (no outcome yet) · one JSONL line per
    non-self-cited memory in ``top`` to ``poi_candidates.jsonl``.

    Distinct from ``emit_nau_records``: a candidate captures "these memories
    were surfaced to the actor at recall time" · the downstream action
    outcome is not yet known. Reconciled later when a real PoI event lands.

    Args:
        top: list of ``(score, entry_dict)`` tuples as produced by
             ``render_v02_vector_mode`` · ``entry_dict`` must carry a path
             (preferred field: ``fullpath`` · fallback: ``path``).
        query: the user query that produced ``top`` · hashed (not stored raw).
        agent_id: actor who made the recall · ``None`` → ``"unknown"``.
        cache_dir: target dir · ``None`` → ``DEFAULT_CACHE_DIR``.

    Returns:
        int · number of candidate lines written (after self-cite suppression).
    """
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    sidecar = cache_dir / CANDIDATE_SIDECAR

    actor = agent_id or "unknown"
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    q_hash = hashlib.sha1((query or "").encode("utf-8")).hexdigest()[:16]

    count = 0
    with sidecar.open("a", encoding="utf-8") as f:
        for rank, (score, entry) in enumerate(top):
            path = _resolve_entry_path(entry)
            if path is None:
                continue
            # Self-cite suppression · mirrors emit_nau_records · skip when the
            # memory was created by the same agent making the recall.
            if SUPPRESS_SELFCITE and agent_id:
                front = parse_session_frontmatter_safe(path)
                creator = front.get("agent_type", "") or front.get("agent_id", "")
                if creator == agent_id:
                    continue
            f.write(json.dumps({
                "ts": ts,
                "kind": "candidate",
                "actor": actor,
                "memory": path.name,
                "query_hash": q_hash,
                "rank": rank,
                "score": round(float(score), 4),
            }, ensure_ascii=False) + "\n")
            count += 1
    return count


def emit_full(poi: ProofOfImpact, cache_dir: Optional[Path] = None,
              memory_root: Optional[Path] = None) -> dict:
    """One-shot: NAU sidecar + event log + frontmatter cumulative update."""
    nau_count = emit_nau_records(poi, cache_dir=cache_dir)
    log_path = emit_event_log(poi, cache_dir=cache_dir)
    fm_updated = 0
    for p in poi.cited_memory_paths:
        path = Path(p)
        if memory_root and not path.is_absolute():
            path = memory_root / path
        if update_frontmatter_cumulative(path, poi.impact_score):
            fm_updated += 1
    return {"nau_records": nau_count, "log_path": str(log_path), "frontmatter_updated": fm_updated}

"""build_recall_result · L2 integration glue (the missing wire).

Turns the production recall path's match dicts into a metamemory `RecallResult`
(per-match confidence + source trail + explicit gaps), so the subject LLM sees
"compass has / does NOT have evidence for X" and stops hallucinating absence.

Pluggable LLM backend (per handoff 2026-06-02):
  · default `llm_backend=None`  -> fully deterministic · no LLM · data never
    leaves the machine (black-box moat preserved). Always available, zero cost.
  · optional callable `(query, matches, deterministic_gaps) -> list[GapStatement]`
    -> local-qwen / cloud-gemini may refine gaps semantically. A backend that
    raises is swallowed and we fall back to deterministic gaps — recall must
    never break because an optional LLM is down.

Per design doc 2026-05-29-compass-comprehensive-uplift-design.md §2.4.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from metamemory.confidence import ConfidenceVector
from metamemory.gap_detector import detect_gaps
from metamemory.calibration import calibration_score
from metamemory.result import RecallResult

_RECENCY_HORIZON_S = 30 * 86400  # linear decay to 0 over 30 days


def _clamp01(x: float) -> float:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _recency_factor(age_seconds: Any) -> float:
    try:
        age = float(age_seconds)
    except (TypeError, ValueError):
        return 0.0
    if age <= 0:
        return 1.0
    return max(0.0, 1.0 - age / _RECENCY_HORIZON_S)


def _source_diversity(matches: List[Dict[str, Any]]) -> float:
    """Result-level diversity · distinct (type) over count · [0,1]."""
    if not matches:
        return 0.0
    types = {(m.get("type") or "?") for m in matches}
    return min(len(types) / len(matches), 1.0)


def _evidence_count(match: Dict[str, Any], matches: List[Dict[str, Any]]) -> int:
    """How many matches corroborate this one (share a non-empty concept)."""
    concept = match.get("concept")
    if not concept:
        return 1
    return sum(1 for m in matches if m.get("concept") == concept) or 1


def _source_str(match: Dict[str, Any]) -> str:
    path = match.get("path", "?")
    type_ = match.get("type", "?")
    age = match.get("age_str")
    return f"{path} ({type_}" + (f", {age} old)" if age else ")")


def build_recall_result(
    query: str,
    matches: List[Dict[str, Any]],
    *,
    history: Optional[List[Dict[str, Any]]] = None,
    gap_threshold: float = 0.4,
    llm_backend: Optional[Callable[[str, list, list], list]] = None,
) -> RecallResult:
    """Construct a metamemory RecallResult from real recall matches."""
    matches = list(matches or [])
    diversity = _source_diversity(matches)

    confidence: List[ConfidenceVector] = []
    source_trail: Dict[str, str] = {}
    for m in matches:
        mid = str(m.get("path") or m.get("id") or m.get("name") or "?")
        confidence.append(ConfidenceVector(
            match_id=mid,
            score=_clamp01(m.get("score", 0.0)),
            evidence_count=_evidence_count(m, matches),
            recency_factor=_recency_factor(m.get("age_seconds", 0)),
            source_diversity=diversity,
        ))
        source_trail[mid] = _source_str(m)

    gaps = detect_gaps(query, matches, confidence, threshold=gap_threshold)

    if llm_backend is not None:
        try:
            refined = llm_backend(query, matches, gaps)
            if refined is not None:
                gaps = list(refined)
        except Exception:
            # optional LLM must never break recall · keep deterministic gaps
            pass

    return RecallResult(
        matches=matches,
        confidence=confidence,
        gaps=gaps,
        source_trail=source_trail,
        calibration_score=calibration_score(history or []),
    )


def format_metamemory_notice(rr: RecallResult) -> str:
    """Render an LLM-facing notice for the subject agent · "" when evidence strong.

    The hallucinate-absence cure: when compass has no/weak evidence, say so
    explicitly so the agent does not fabricate a "prior finding". Empty string
    when there is solid evidence (no noise injected into the agent's context).
    """
    if not rr.gaps:
        return ""
    lines = ["⚠️ metamemory · 自知层:"]
    for g in rr.gaps:
        lines.append(f"  · compass 对「{g.topic}」**没有可靠 evidence**({g.reason})")
    lines.append("  → 不要凭空声称一条找不到出处的「既往结论」· "
                 "如确需该信息,明说 compass 没存,而不是 hallucinate 一个。")
    return "\n".join(lines)

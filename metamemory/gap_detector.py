"""Gap detection · L2 metamemory.

Returns GapStatement when no retrieved match exceeds confidence threshold ·
surfaces 'compass does not have evidence for X' to subject LLM.

Per design doc 2026-05-29-compass-comprehensive-uplift-design.md §2.4.
"""
from __future__ import annotations
from typing import Any, Dict, List

from metamemory.confidence import ConfidenceVector
from metamemory.gap import GapStatement


def detect_gaps(
    query: str,
    matches: List[Dict[str, Any]],
    confidence: List[ConfidenceVector],
    threshold: float = 0.4,
) -> List[GapStatement]:
    """Return GapStatement if no match exceeds composite-confidence threshold.

    Returns:
        - 1 GapStatement when matches/confidence empty (no recall happened)
        - 1 GapStatement when max composite below threshold (low quality recall)
        - empty list when at least one match meets threshold (compass has evidence)
    """
    if not matches or not confidence:
        return [GapStatement(topic=query, reason="recall returned 0 results")]
    composite_scores = [cv.composite() for cv in confidence]
    if max(composite_scores) < threshold:
        return [GapStatement(
            topic=query,
            reason=f"max confidence {max(composite_scores):.2f} below threshold {threshold}",
        )]
    return []

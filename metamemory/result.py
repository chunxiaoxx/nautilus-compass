"""RecallResult · upgraded recall API returning matches + confidence + gaps + source trail.

Per design doc 2026-05-29-compass-comprehensive-uplift-design.md §2.4.
H5 metamemory · subject LLM uses gaps to avoid hallucinate-absence.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List

from metamemory.confidence import ConfidenceVector
from metamemory.gap import GapStatement


@dataclass
class RecallResult:
    matches: List[Dict[str, Any]] = field(default_factory=list)
    confidence: List[ConfidenceVector] = field(default_factory=list)
    gaps: List[GapStatement] = field(default_factory=list)
    source_trail: Dict[str, str] = field(default_factory=dict)
    calibration_score: float = 0.0

    def is_empty(self) -> bool:
        return len(self.matches) == 0

    def has_evidence_for(self, key: str) -> bool:
        """True if `key` matches a retrieved match id · False if it appears in a gap · False otherwise."""
        if key in {m.get("id") for m in self.matches}:
            return True
        if any(g.topic == key for g in self.gaps):
            return False
        return False

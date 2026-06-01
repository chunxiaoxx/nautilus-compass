"""ConfidenceVector · L2 metamemory primitive (H5)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ConfidenceVector:
    """Per-match confidence with deterministic monotonic composite scoring.

    Per design doc 2026-05-29-compass-comprehensive-uplift-design.md §2.4.
    """

    match_id: str
    score: float           # BGE cosine normalised to [0, 1]
    evidence_count: int    # how many sessions support this
    recency_factor: float  # [0, 1] · 1.0 = today
    source_diversity: float  # [0, 1] · 1.0 = many distinct sources

    def composite(self) -> float:
        """Weighted composite · deterministic · monotonic in each input."""
        ev_norm = min(self.evidence_count / 5.0, 1.0)
        return min(
            0.4 * self.score
            + 0.2 * ev_norm
            + 0.2 * self.recency_factor
            + 0.2 * self.source_diversity,
            1.0,
        )

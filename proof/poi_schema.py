"""v1.7.1 · S4 module 1 · Proof-of-Impact schema + validators.

Defines ProofOfImpact dataclass for tracing agent actions to cited memory
and deterministically computing impact scores.

NO LLM. Pure dataclass + arithmetic.
Reference: paper/SPEC_PROOF_OF_IMPACT.md section 3.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional, List

VALID_OUTCOMES = ("success", "failure", "partial", "pending")
VALID_DECLARATIONS = ("supports", "contradicts", "neutral")


@dataclass
class ProofOfImpact:
    """Trace from agent action outcome to cited memory · deterministic score."""

    action_id: str
    agent_id: str
    cited_memory_paths: List[str]
    action_outcome: str
    timestamp_action: str  # ISO8601
    timestamp_outcome: str  # ISO8601
    impact_score: float = 0.0
    nau_emit: Optional[float] = None
    declaration_type: str = "supports"
    notes: str = ""

    def __post_init__(self):
        if self.action_outcome not in VALID_OUTCOMES:
            raise ValueError(
                f"invalid action_outcome: {self.action_outcome!r} "
                f"(must be one of {VALID_OUTCOMES})"
            )
        if self.declaration_type not in VALID_DECLARATIONS:
            raise ValueError(
                f"invalid declaration_type: {self.declaration_type!r} "
                f"(must be one of {VALID_DECLARATIONS})"
            )
        if not self.action_id:
            raise ValueError("action_id required")
        if not self.agent_id:
            raise ValueError("agent_id required")
        if not isinstance(self.cited_memory_paths, list):
            raise ValueError("cited_memory_paths must be a list")
        if len(self.notes) > 200:
            self.notes = self.notes[:200]

    def to_dict(self) -> dict:
        return asdict(self)


def validate_iso8601(ts: str) -> bool:
    """Minimal ISO8601 validation (just format prefix check)."""
    if not ts or not isinstance(ts, str):
        return False
    # YYYY-MM-DDTHH:MM
    if len(ts) < 16:
        return False
    return ts[4] == "-" and ts[7] == "-" and ts[10] == "T" and ts[13] == ":"

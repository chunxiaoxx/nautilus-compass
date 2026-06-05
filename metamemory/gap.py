"""GapStatement · L2 metamemory primitive (H5)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class GapStatement:
    """compass actively surfacing 'I don't have evidence for X'.

    Per design doc 2026-05-29-compass-comprehensive-uplift-design.md §2.4.
    """

    topic: str   # what the query asked about
    reason: str  # why compass thinks there is no evidence

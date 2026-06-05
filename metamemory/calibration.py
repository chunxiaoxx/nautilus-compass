"""Calibration scoring · L2 metamemory.

Measures how well reported confidence matches actual correctness.
Uses simple 2-bucket approach: [0, 0.5) low-confidence · [0.5, 1.0] high-confidence.

calibration_score = 1.0 - mean(|bucket_avg_confidence - bucket_actual_correct_rate|)

Score 1.0 = perfectly calibrated · 0.0 = maximally miscalibrated · empty history → 0.0.

Per design doc 2026-05-29-compass-comprehensive-uplift-design.md §2.4.
"""
from __future__ import annotations
from typing import Any, Dict, List


def calibration_score(history: List[Dict[str, Any]]) -> float:
    """Return calibration score in [0, 1]."""
    if not history:
        return 0.0

    low_bucket: List[Dict[str, Any]] = []
    high_bucket: List[Dict[str, Any]] = []
    for item in history:
        if item["confidence"] < 0.5:
            low_bucket.append(item)
        else:
            high_bucket.append(item)

    gaps: List[float] = []
    for bucket in (low_bucket, high_bucket):
        if not bucket:
            continue
        avg_conf = sum(b["confidence"] for b in bucket) / len(bucket)
        correct_rate = sum(1 for b in bucket if b["correct"]) / len(bucket)
        gaps.append(abs(avg_conf - correct_rate))

    if not gaps:
        return 0.0

    return 1.0 - (sum(gaps) / len(gaps))

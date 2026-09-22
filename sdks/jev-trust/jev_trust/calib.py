# -*- coding: utf-8 -*-
"""Runtime calibration tracking — the same math Assay uses (ECE top-label, Brier).

ECE = sum over equal-width confidence bins of (bin share) * |bin accuracy - bin confidence|.
For binary (noul) questions the top-label confidence is max(p, 1-p); for choice
questions it is the probability of the chosen option. Identical formulas to
nautilus-compass verifypack calibration checks (cross-validated against
sklearn-style references in Assay research #1/#2).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

DEFAULT_BINS = 10
MIN_BIN_SAMPLES = 5  # below this a bin's observed accuracy is not trustworthy


@dataclass(frozen=True)
class Prediction:
    """One recorded decision/outcome pair."""
    qid: str
    stated_confidence: float  # top-label confidence the model claimed
    correct: int  # 1 / 0 — was the top-label decision right
    p_true: float  # probability the model assigned to the TRUE outcome


def _top_label_binary(p: float) -> float:
    """Jev noul answers state P(yes); top-label confidence = max(p, 1-p)."""
    return max(p, 1.0 - p)


def brier(preds: List[Prediction]) -> float:
    """mean((1 - p_true)^2) — probability mass the model denied the truth.
    For binary questions identical to the standard (p - y)^2 form."""
    if not preds:
        raise ValueError("no predictions")
    return round(sum((1.0 - pr.p_true) ** 2 for pr in preds) / len(preds), 8)


def _bin_of(conf: float, nbins: int) -> int:
    return min(int(conf * nbins), nbins - 1)


def ece_toplabel(preds: List[Prediction], nbins: int = DEFAULT_BINS) -> float:
    """Equal-width binned top-label ECE."""
    if not preds:
        raise ValueError("no predictions")
    bins: dict = {}
    for pr in preds:
        b = _bin_of(pr.stated_confidence, nbins)
        acc_sum, conf_sum, cnt = bins.get(b, (0.0, 0.0, 0))
        bins[b] = (acc_sum + pr.correct, conf_sum + pr.stated_confidence, cnt + 1)
    total = len(preds)
    ece = 0.0
    for acc_sum, conf_sum, cnt in bins.values():
        ece += (cnt / total) * abs(acc_sum / cnt - conf_sum / cnt)
    return round(ece, 8)


@dataclass
class CalibrationState:
    """Accumulated calibration evidence for one domain."""
    preds: List[Prediction] = field(default_factory=list)

    def add(self, pred: Prediction) -> "CalibrationState":
        self.preds.append(pred)
        return self

    @property
    def n(self) -> int:
        return len(self.preds)

    @property
    def accuracy(self) -> Optional[float]:
        if not self.preds:
            return None
        return round(sum(p.correct for p in self.preds) / len(self.preds), 4)

    @property
    def ece(self) -> Optional[float]:
        if not self.preds:
            return None
        return ece_toplabel(self.preds)

    @property
    def brier(self) -> Optional[float]:
        if not self.preds:
            return None
        return brier(self.preds)

    @property
    def C(self) -> Optional[float]:
        """Calibration currency: C = 1 - ECE (Assay definition)."""
        if not self.preds:
            return None
        return round(1.0 - self.ece, 4)

    def bin_accuracy(self, conf: float, nbins: int = DEFAULT_BINS,
                     min_samples: int = MIN_BIN_SAMPLES) -> Optional[float]:
        """Observed accuracy among past decisions that stated confidence in the
        same bin — 'what is this confidence worth in my domain'. None if the bin
        has too few samples to say anything."""
        b = _bin_of(conf, nbins)
        same = [p.correct for p in self.preds if _bin_of(p.stated_confidence, nbins) == b]
        if len(same) < min_samples:
            return None
        return round(sum(same) / len(same), 4)


# ── trust verdicts (Assay calibration-currency reading levels) ────────────

FACE_VALUE_C = 0.80
DISCOUNT_C = 0.50

FACE_VALUE = "FACE_VALUE"      # C >= 0.80: stated confidence may be used at face value
DISCOUNT = "DISCOUNT"          # 0.50 <= C < 0.80: trust stated confidence times C
DOWNGRADE = "DOWNGRADE"        # C < 0.50: route to human review
UNVERIFIED = "UNVERIFIED"      # not enough measured evidence in this domain yet


def verdict_for(C: Optional[float], n: int, min_n: int = 20) -> str:
    """Verdict from measured calibration currency. Needs min_n outcomes before
    any 'verified' verdict is issued — below that everything is UNVERIFIED
    (the same discipline Assay applies to its own numbers)."""
    if C is None or n < min_n:
        return UNVERIFIED
    if C >= FACE_VALUE_C:
        return FACE_VALUE
    if C >= DISCOUNT_C:
        return DISCOUNT
    return DOWNGRADE


def effective_confidence(state: CalibrationState, stated: float) -> Tuple[Optional[float], str]:
    """How much a stated confidence is worth in this domain, given evidence.

    Priority: (1) observed accuracy of the matching confidence bin (>=5 samples);
    (2) binless fallback: stated confidence adjusted by measured C; (3) None —
    insufficient evidence, caller must fall back to its own policy."""
    if state.n == 0:
        return None, UNVERIFIED
    bin_acc = state.bin_accuracy(stated)
    if bin_acc is not None:
        return bin_acc, "bin_observed"
    if state.n >= 20:
        return round(0.5 + state.C * (stated - 0.5), 4), "C_adjusted"
    return None, "insufficient_n"

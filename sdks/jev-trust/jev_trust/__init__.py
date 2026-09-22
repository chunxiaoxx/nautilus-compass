# -*- coding: utf-8 -*-
"""jev-trust · trust middleware for Jev decision APIs.

Three lines::

    from jev_trust import TrustedJev

    jev = TrustedJev(api_key=..., domain="email-triage")
    r = jev.decide(state, {"q": q})["q"]
    r.stated_confidence, r.effective_confidence, r.domain_verdict

Every call is logged; record outcomes and the session measures how much
Jev's stated confidence is actually worth in YOUR domain (accuracy, Brier,
ECE, calibration currency C = 1 - ECE). Logs sign with ed25519 for
independent recomputation (Assay-compatible).
"""
from .calib import (CalibrationState, Prediction, ece_toplabel, brier,
                    verdict_for, effective_confidence,
                    FACE_VALUE, DISCOUNT, DOWNGRADE, UNVERIFIED)
from .client import JevClient, JevAPIError, top_label, correctness
from .receipt import KeyPair, ReceiptResult, verify_log
from .trust import TrustedJev, TrustResult, ASSAY_REFERENCE_RATES

__version__ = "0.1.0"
__all__ = [
    "TrustedJev", "TrustResult", "ASSAY_REFERENCE_RATES",
    "CalibrationState", "Prediction", "ece_toplabel", "brier",
    "verdict_for", "effective_confidence",
    "FACE_VALUE", "DISCOUNT", "DOWNGRADE", "UNVERIFIED",
    "JevClient", "JevAPIError", "top_label", "correctness",
    "KeyPair", "ReceiptResult", "verify_log",
]

# -*- coding: utf-8 -*-
"""TrustedJev — Jev API with trust middleware.

What it adds over a raw client:

1. Every call lands in an append-only JSONL log (question, answer, stated
   confidence, effective confidence, usage, timestamp).
2. You record outcomes as ground truth arrives; the session tracks running
   accuracy / Brier / ECE in YOUR domain — not the vendor's benchmark.
3. Every answer carries an `effective_confidence`: what the stated confidence
   is worth so far in this domain (bin-observed accuracy preferred, else
   C-adjusted, else None = insufficient evidence).
4. An overconfidence alert fires when a decision is confident enough to act
   on but the domain has not earned that confidence yet.
5. The whole log signs with ed25519 — hand it to Assay (or anyone) for
   independent recomputation of your numbers.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

from . import calib
from .calib import (CalibrationState, Prediction, effective_confidence,
                    verdict_for)
from .client import DEFAULT_MODEL, DEFAULT_ENDPOINT, JevClient, correctness, top_label
from .receipt import KeyPair

Alert = Callable[["TrustResult"], None]


@dataclass(frozen=True)
class TrustResult:
    qid: str
    decision: object
    stated_confidence: float
    effective_confidence: Optional[float]   # what it is worth in this domain
    basis: str                              # bin_observed / C_adjusted / insufficient_n
    domain_verdict: str                     # FACE_VALUE / DISCOUNT / DOWNGRADE / UNVERIFIED
    answer: dict                            # raw answer from Jev
    rid: int                                # call sequence number in this session
    ts: str
    usage: dict = field(default_factory=dict)

    @property
    def overconfident(self) -> bool:
        return self.effective_confidence is not None \
            and (self.stated_confidence - self.effective_confidence) >= 0.10


# Reference rates measured by Assay on hosted Jev 1.13 (public research #1/#2,
# 2026-09). Informational only — your domain is measured by your own outcomes.
ASSAY_REFERENCE_RATES = {
    "closed-deterministic": {"C": 0.959, "ece": 0.041, "source": "Assay research #1, n=240"},
    "adversarial-stress": {"C": 0.988, "ece": 0.012, "source": "Assay research #2, n=200"},
    "synthetic-email-choice": {"C": 0.086, "ece": None,
                               "source": "Assay mini-DCR: acc 50% at stated conf 91%"},
}


class TrustedJev:
    """One session, one domain. Create one per task domain you care about."""

    def __init__(self, api_key: str = "", domain: str = "default",
                 log_path: Optional[str] = None,
                 endpoint: str = DEFAULT_ENDPOINT, model: str = DEFAULT_MODEL,
                 transport=None,
                 min_verdict_n: int = 20,
                 alert_confidence: float = 0.90,
                 on_overconfidence: Optional[Alert] = None,
                 keys: Optional[KeyPair] = None):
        self.domain = domain
        self.client = JevClient(api_key, endpoint=endpoint, model=model,
                                transport=transport)
        self.state = CalibrationState()
        self.min_verdict_n = min_verdict_n
        self.alert_confidence = alert_confidence
        self.on_overconfidence = on_overconfidence
        self.keys = keys
        self._rid = 0
        self._pending: Dict[str, dict] = {}
        self.log_path = Path(log_path) if log_path else Path(f"jev-trust-{domain}-{_stamp()}.jsonl")
        if self.log_path.exists():
            self._replay(self.log_path)

    # ── core: call + log + annotate ──────────────────────────────────────

    def decide(self, state: dict, questions: dict) -> Dict[str, TrustResult]:
        """Ask Jev one batch of questions. Returns {qid: TrustResult}.
        Every answer is annotated with its effective confidence before you
        see it — no unexamined confidence leaves this method."""
        raw = self.client.decide(state, questions)
        out: Dict[str, TrustResult] = {}
        for qid, answer in raw.get("answers", {}).items():
            top = top_label(answer)
            eff, basis = effective_confidence(self.state, top["stated_confidence"])
            verdict = verdict_for(self.state.C, self.state.n, self.min_verdict_n)
            self._rid += 1
            r = TrustResult(qid=qid, decision=top["decision"],
                            stated_confidence=round(top["stated_confidence"], 4),
                            effective_confidence=eff, basis=basis,
                            domain_verdict=verdict, answer=answer, rid=self._rid,
                            ts=_now(), usage=raw.get("usage", {}))
            self._pending[qid] = {"answer": top, "ts": r.ts, "rid": r.rid}
            self._log({"kind": "call", "rid": r.rid, "qid": qid, "ts": r.ts,
                       "domain": self.domain, "decision": top["decision"],
                       "stated_confidence": r.stated_confidence,
                       "effective_confidence": eff, "basis": basis,
                       "domain_verdict": verdict,
                       "usage": raw.get("usage", {})})
            out[qid] = r
            if self.on_overconfidence and r.stated_confidence >= self.alert_confidence \
                    and verdict != calib.FACE_VALUE:
                self.on_overconfidence(r)
        return out

    # ── outcomes: feed ground truth back ─────────────────────────────────

    def record_outcome(self, qid: str, truth) -> calib.Prediction:
        """Record ground truth for a previously-asked question. Feeds the
        running calibration. Brier uses the probability the model gave the
        *correct* answer (0 for choice misses; p/max(1-p) for noul)."""
        if qid not in self._pending:
            raise KeyError(f"no pending call for qid {qid!r} (already recorded?)")
        top = self._pending.pop(qid)["answer"]
        correct = correctness(top, truth)
        p_true = _p_true(top, truth)
        pred = Prediction(qid=qid, stated_confidence=top["stated_confidence"],
                          correct=correct, p_true=p_true)
        self.state.add(pred)
        self._log({"kind": "outcome", "qid": qid, "ts": _now(),
                   "domain": self.domain, "truth": truth, "correct": correct,
                   "p_true": p_true})
        return pred

    # ── readings ──────────────────────────────────────────────────────────

    def stats(self) -> dict:
        return {"domain": self.domain,
                "n_calls": self._rid, "n_outcomes": self.state.n,
                "accuracy": self.state.accuracy, "brier": self.state.brier,
                "ece": self.state.ece, "C": self.state.C,
                "verdict": verdict_for(self.state.C, self.state.n, self.min_verdict_n),
                "assay_reference": ASSAY_REFERENCE_RATES.get(self.domain)}

    def reference_rate(self, domain: str) -> Optional[dict]:
        return ASSAY_REFERENCE_RATES.get(domain)

    # ── receipts ──────────────────────────────────────────────────────────

    def sign_log(self) -> Path:
        """Sign the decision log; returns the .sig path. Publish log+sig+pubkey
        — anyone (including Assay) can recompute your calibration from it."""
        if self.keys is None:
            self.keys = KeyPair()
        return self.keys.sign_log(self.log_path)

    def verify_log(self) -> "ReceiptResult":
        if self.keys is None:
            raise RuntimeError("no keys: sign_log first or pass keys=")
        return self.keys.verify_log(self.log_path, Path(str(self.log_path) + ".sig"))

    # ── internals ─────────────────────────────────────────────────────────

    def _log(self, rec: dict) -> None:
        with self.log_path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")

    def _replay(self, path: Path) -> None:
        """Resume a session from an existing log: rebuild calibration state."""
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("kind") == "call":
                self._rid = max(self._rid, int(rec.get("rid", 0)))
                self._pending[rec["qid"]] = {
                    "answer": {"decision": rec["decision"],
                               "stated_confidence": rec["stated_confidence"],
                               "probabilities": None},
                    "ts": rec.get("ts"), "rid": rec["rid"]}
            elif rec.get("kind") == "outcome":
                top = self._pending.pop(rec["qid"], {}).get("answer")
                if top is None:
                    continue
                p_true = rec.get("p_true")
                if p_true is None:
                    p_true = _p_true(top, rec["truth"])
                self.state.add(Prediction(qid=rec["qid"],
                                          stated_confidence=top["stated_confidence"],
                                          correct=int(rec["correct"]), p_true=p_true))


def _p_true(top: dict, truth) -> float:
    """Probability the model assigned to the true outcome (Brier input)."""
    probs = top.get("probabilities")
    if probs:
        if top["decision"] in ("yes", "no"):
            key = "yes" if truth in (1, True) else "no"
            return float(probs.get(key, 0.0))
        return float(probs.get(str(truth), 0.0))
    # noul without a probabilities dict: top-label conf or its complement
    correct = correctness(top, truth)
    return top["stated_confidence"] if correct else 1.0 - top["stated_confidence"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")

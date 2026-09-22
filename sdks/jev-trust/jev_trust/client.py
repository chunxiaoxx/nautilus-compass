# -*- coding: utf-8 -*-
"""Minimal Jev API client (TypeSafe System One endpoint), pure stdlib.

The transport is injectable so tests run offline and callers can plug in
their own HTTP stack / mocks.
"""
from __future__ import annotations

import json
import time
import urllib.request
from typing import Callable, Dict, Optional

DEFAULT_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
DEFAULT_TIMEOUT = 60

Transport = Callable[[str, bytes, Dict[str, str]], dict]
"""transport(url, body_bytes, headers) -> parsed json response dict"""


def _urllib_transport(url: str, body: bytes, headers: Dict[str, str]) -> dict:
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as r:
        return json.loads(r.read())


class JevClient:
    def __init__(self, api_key: str, endpoint: str = DEFAULT_ENDPOINT,
                 model: str = DEFAULT_MODEL, transport: Optional[Transport] = None):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self._transport = transport or _urllib_transport
        self.calls = 0
        self.errors = 0

    def decide(self, state: dict, questions: dict, retries: int = 2,
               retry_delay: float = 1.0) -> dict:
        """Call Jev once. questions = {qid: {type: noul|choice|score, ...}}.
        Returns the raw response dict {answers: {...}, usage: {...}}.
        Transient errors are retried; content is never retried (no fishing
        for better answers — Assay discipline)."""
        body = json.dumps({"model": self.model, "state": state,
                           "questions": questions}).encode()
        headers = {"Authorization": "Bearer " + self.api_key,
                   "Content-Type": "application/json"}
        last_err = None
        for attempt in range(retries + 1):
            self.calls += 1
            try:
                return self._transport(self.endpoint, body, headers)
            except Exception as e:  # network/5xx class only reaches here
                self.errors += 1
                last_err = e
                if attempt < retries:
                    time.sleep(retry_delay * (attempt + 1))
        raise JevAPIError(f"jev api failed after {retries + 1} attempts: {last_err}")


class JevAPIError(RuntimeError):
    pass


# ── answer normalization ──────────────────────────────────────────────────

def top_label(answer: dict) -> dict:
    """Normalize a Jev answer into {decision, stated_confidence, probabilities}.

    - noul:   {noul: 0.93, type: noul}                -> decision yes/no
    - choice: {choice: 'alpha', probabilities: {...}} -> decision 'alpha'
    - score:  {score: 0.8, type: score}               -> value 0.8, confidence 1.0
    """
    t = answer.get("type")
    if t == "noul":
        p = float(answer["noul"])
        decision = "yes" if p >= 0.5 else "no"
        return {"decision": decision, "stated_confidence": max(p, 1.0 - p),
                "probabilities": {"yes": p, "no": 1.0 - p}}
    if t == "choice":
        probs = dict(answer.get("probabilities") or {})
        decision = answer.get("choice")
        stated = answer.get("confidence")
        if stated is None:
            stated = max(probs.values()) if probs else 1.0
        return {"decision": decision, "stated_confidence": float(stated),
                "probabilities": probs}
    if t == "score":
        return {"decision": float(answer["score"]), "stated_confidence": 1.0,
                "probabilities": None}
    raise ValueError(f"unknown answer type: {t!r}")


def correctness(top: dict, truth) -> int:
    """Was the top-label decision correct, given ground truth?
    noul: truth in {0,1} vs decision yes/no; choice: string equality.
    score answers carry no notion of correctness — raise rather than guess."""
    decision = top["decision"]
    if isinstance(decision, float):
        raise ValueError("score answers have no top-label correctness")
    if decision in ("yes", "no"):
        yes = {1: "yes", 0: "no", True: "yes", False: "no"}.get(truth)
        if yes is None:
            raise ValueError(f"bad truth for noul answer: {truth!r}")
        return 1 if decision == yes else 0
    return 1 if str(decision) == str(truth) else 0

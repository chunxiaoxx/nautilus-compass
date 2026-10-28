"""Per-instance token-budget accountant — the matched-budget confound control.

Wraps any duck-typed model (``query(messages, **kw) -> dict``) and sums
prompt+completion tokens across calls. Before each call it checks whether the cap
is already reached; if so it raises ``BudgetExceeded`` instead of querying. Token
cost is only known *after* a call (from the response ``usage``), so the only sound
gate is "already at/over budget -> stop before spending more". This equalizes the
total-token ceiling across mono and decomp arms so a decomp gain cannot be merely
bought compute (the Paradigm-B analog of "best-of-N is not a persona moat").
"""
from typing import Dict, List


class BudgetExceeded(Exception):
    """Raised when the per-instance token budget is already exhausted."""


def _estimate_tokens(messages: List[Dict], output_text: str) -> int:
    """Crude char/4 fallback when a model returns no usage block.

    Documented as an estimate: real arms should return ``usage``; this only keeps a
    usage-less model from spending unbounded.
    """
    in_chars = sum(len(str(m.get("content", ""))) for m in messages)
    return (in_chars + len(output_text)) // 4


def _cost_from_result(result, messages: List[Dict]) -> int:
    """Token cost of one model call, robust across shapes:

    1. mini-swe-agent ``LitellmModel``: ``result["extra"]["response"]["usage"]`` with
       ``prompt_tokens`` / ``completion_tokens``.
    2. generic adapter: top-level ``result["usage"]`` with ``input_tokens`` /
       ``output_tokens``.
    3. neither -> char/4 estimate (documented fallback).
    """
    if isinstance(result, dict):
        resp = (result.get("extra") or {}).get("response") or {}
        u = resp.get("usage") or {}
        if u:
            return int(u.get("prompt_tokens", 0)) + int(u.get("completion_tokens", 0))
        u = result.get("usage") or {}
        if u:
            return int(u.get("input_tokens", 0)) + int(u.get("output_tokens", 0))
        return _estimate_tokens(messages, str(result.get("content", "")))
    return _estimate_tokens(messages, "")


class BudgetedModel:
    """Token-counting proxy over a Model with a hard per-instance cap.

    Delegates the rest of the mini-swe-agent ``Model`` protocol (``config``,
    ``format_message``, ``format_observation_messages``, ``get_template_vars``,
    ``serialize``) to the wrapped model, so it is a drop-in for ``DefaultAgent``.
    """

    def __init__(self, model, max_total_tokens: int):
        self.model = model
        self.max_total_tokens = max_total_tokens
        self.spent = 0

    @property
    def config(self):
        return self.model.config

    @property
    def remaining(self) -> int:
        return max(0, self.max_total_tokens - self.spent)

    def query(self, messages: List[Dict], **kw) -> Dict:
        if self.spent >= self.max_total_tokens:
            raise BudgetExceeded(
                f"budget exhausted: spent {self.spent} >= cap {self.max_total_tokens}"
            )
        result = self.model.query(messages, **kw)
        self.spent += _cost_from_result(result, messages)
        return result

    # --- Model-protocol passthrough (so a DefaultAgent can use this directly) ---
    def format_message(self, **kw):
        return self.model.format_message(**kw)

    def format_observation_messages(self, message, outputs, template_vars=None):
        return self.model.format_observation_messages(message, outputs, template_vars)

    def get_template_vars(self, **kw):
        return self.model.get_template_vars(**kw)

    def serialize(self) -> Dict:
        return self.model.serialize()

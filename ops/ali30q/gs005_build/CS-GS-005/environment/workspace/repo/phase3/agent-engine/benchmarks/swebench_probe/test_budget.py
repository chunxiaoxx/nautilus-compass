"""Tests for the per-instance token-budget accountant (Phase 4 Task 6).

Matched total budget is the headline confound control: mono and decomp arms are
compared at an equal per-instance token ceiling, so a decomp gain cannot be "just
bought more compute". The accountant stops the loop once the budget is reached —
token cost is only known after a call, so the gate is "already at/over cap -> stop
before the next call".
"""
import pytest

from budget import BudgetedModel, BudgetExceeded


class FakeModel:
    def query(self, messages, **kw):
        return {"content": "ok",
                "usage": {"input_tokens": 100, "output_tokens": 50}}


class NoUsageModel:
    def query(self, messages, **kw):
        return {"content": "x" * 400}  # ~100 tokens by the /4 char estimate


def test_counts_tokens_and_raises_at_cap():
    m = BudgetedModel(FakeModel(), max_total_tokens=300)
    m.query([{"role": "user", "content": "a"}])   # spent 150
    m.query([{"role": "user", "content": "b"}])    # spent 300 == cap
    assert m.spent == 300
    with pytest.raises(BudgetExceeded):
        m.query([{"role": "user", "content": "c"}])  # already at cap -> stop


def test_passes_through_return_value():
    m = BudgetedModel(FakeModel(), max_total_tokens=1000)
    out = m.query([{"role": "user", "content": "a"}])
    assert out["content"] == "ok"


def test_estimates_tokens_when_usage_absent():
    m = BudgetedModel(NoUsageModel(), max_total_tokens=10_000)
    m.query([{"role": "user", "content": "hello"}])
    # input ~ len("hello")/4 rounded + output 400/4 = 100 -> spent > 0, no usage key
    assert m.spent > 0


def test_remaining_reported():
    m = BudgetedModel(FakeModel(), max_total_tokens=500)
    m.query([{"role": "user", "content": "a"}])  # 150
    assert m.remaining == 350


# --- Task 11: full Model-protocol proxy + litellm usage shape ---

class FakeLitellmModel:
    """Mimics minisweagent LitellmModel: query returns a message dict whose
    extra.response.usage carries prompt_tokens/completion_tokens; also exposes the
    other Model-protocol methods + a config object."""
    def __init__(self):
        self.config = type("C", (), {"model_name": "anthropic/MiniMax-M3"})()
        self.calls = []

    def query(self, messages, **kw):
        return {"role": "assistant", "content": "hi", "extra": {
            "response": {"usage": {"prompt_tokens": 300, "completion_tokens": 120}}}}

    def format_message(self, **kw):
        self.calls.append(("format_message", kw)); return {"role": kw.get("role"), "content": kw.get("content"), "extra": kw.get("extra", {})}

    def format_observation_messages(self, message, outputs, template_vars=None):
        self.calls.append(("format_observation_messages", None)); return [{"role": "user", "content": "obs"}]

    def get_template_vars(self, **kw):
        self.calls.append(("get_template_vars", None)); return {"k": "v"}

    def serialize(self):
        return {"info": {"wrapped": True}}


def test_reads_litellm_usage_shape():
    m = BudgetedModel(FakeLitellmModel(), max_total_tokens=10_000)
    m.query([{"role": "user", "content": "x"}])
    assert m.spent == 420  # 300 prompt + 120 completion


def test_delegates_config_and_protocol_methods():
    fake = FakeLitellmModel()
    m = BudgetedModel(fake, max_total_tokens=10_000)
    assert m.config.model_name == "anthropic/MiniMax-M3"          # config passthrough
    msg = m.format_message(role="system", content="s")
    assert msg["role"] == "system"
    assert m.format_observation_messages({}, [], {}) == [{"role": "user", "content": "obs"}]
    assert m.get_template_vars() == {"k": "v"}
    assert m.serialize()["info"]["wrapped"] is True
    assert ("format_message", {"role": "system", "content": "s"}) in fake.calls

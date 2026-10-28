"""W4.3 止血 · the production multi-provider LLMClient must pass a per-request
timeout into messages.create so a hung provider raises (and the fallback loop
moves to the next provider) instead of hanging the whole daemon cycle.

NOTE: a 6/3 fix added timeout to agent-engine/llm/client.py — but the daemon
runs the multi-provider phase3/backend/agent_engine/llm/client.py copy, which
was NOT covered (split-brain). This guards the production copy.
"""
from __future__ import annotations
import pytest
from agent_engine.llm.client import LLMClient


class _FakeMessages:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs

        class _Block:
            type = "text"
            text = "ok"

        class _Resp:
            content = [_Block()]

        return _Resp()


class _FakeAnthropic:
    def __init__(self):
        self.messages = _FakeMessages()


def _client_with_fake():
    """Construct an LLMClient without env keys · inject one fake anthropic provider."""
    c = object.__new__(LLMClient)
    fake = _FakeAnthropic()
    c._providers = [{"name": "fake", "type": "anthropic", "client": fake, "model": "m"}]
    c.client = fake
    c.model = "m"
    return c, fake


def test_chat_passes_default_timeout():
    c, fake = _client_with_fake()
    c.chat("hi")
    assert "timeout" in fake.messages.kwargs, "chat must pass timeout to messages.create"
    assert fake.messages.kwargs["timeout"] == LLMClient.DEFAULT_TIMEOUT


def test_chat_with_messages_passes_default_timeout():
    c, fake = _client_with_fake()
    c.chat_with_messages([{"role": "user", "content": "hi"}])
    assert "timeout" in fake.messages.kwargs
    assert fake.messages.kwargs["timeout"] == LLMClient.DEFAULT_TIMEOUT


def test_explicit_timeout_override_is_honored():
    c, fake = _client_with_fake()
    c.chat("hi", timeout=30)
    assert fake.messages.kwargs["timeout"] == 30


def test_default_timeout_is_bounded():
    """A sane default · long enough for slow models, short enough to not hang forever."""
    assert 30 <= LLMClient.DEFAULT_TIMEOUT <= 600

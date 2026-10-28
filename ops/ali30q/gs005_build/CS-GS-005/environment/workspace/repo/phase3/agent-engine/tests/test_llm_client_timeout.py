"""LLMClient per-request timeout (Phase-3 seed3 hang root cause).

A hung M3 request must raise (so _chat_safe retries/degrades) instead of
deadlocking a ThreadPoolExecutor. These tests inject a fake Anthropic client and
assert the `timeout` kwarg is forwarded to `messages.create`, defaulting to
LLMClient.DEFAULT_TIMEOUT.
"""
import types

from llm.client import LLMClient


class _FakeMessages:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return types.SimpleNamespace(
            content=[types.SimpleNamespace(type="text", text="ok")]
        )


class _FakeAnthropic:
    def __init__(self):
        self.messages = _FakeMessages()


def _client_with_fake() -> LLMClient:
    c = LLMClient(api_key="x")
    c.client = _FakeAnthropic()
    return c


def test_chat_forwards_default_timeout():
    c = _client_with_fake()
    assert c.chat("hi") == "ok"
    assert c.client.messages.kwargs["timeout"] == LLMClient.DEFAULT_TIMEOUT


def test_chat_forwards_explicit_timeout():
    c = _client_with_fake()
    c.chat("hi", timeout=30)
    assert c.client.messages.kwargs["timeout"] == 30


def test_chat_with_messages_forwards_default_timeout():
    c = _client_with_fake()
    assert c.chat_with_messages([{"role": "user", "content": "hi"}]) == "ok"
    assert c.client.messages.kwargs["timeout"] == LLMClient.DEFAULT_TIMEOUT


def test_chat_with_messages_forwards_explicit_timeout():
    c = _client_with_fake()
    c.chat_with_messages([{"role": "user", "content": "hi"}], timeout=45)
    assert c.client.messages.kwargs["timeout"] == 45

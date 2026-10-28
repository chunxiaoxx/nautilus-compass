"""LLM client thinking-only 自适应重试测试(2026-09-15)。

背景:soul fw-tpl 轮在 max_tokens=32768 下 thinking-only(MiniMax-M3 经中转,
结构性生成任务推理无界)。修=chat() 捕获 _extract_text 的 ValueError 后以
2x 预算重试一次。真实战场验证=02:07 soul 轮(部署后自动)。
注意:仿 SDK 块形状——ThinkingBlock 有 .thinking/.signature 无 .text;
TextBlock 有 .text。
"""
from __future__ import annotations

import pytest

import agent_engine.llm.client as llm_mod
from agent_engine.llm.client import LLMClient


class _Blk:
    def __init__(self, type_, text=None, signature=None, thinking=None):
        self.type = type_
        if text is not None:
            self.text = text
        if signature is not None:
            self.signature = signature
        if thinking is not None:
            self.thinking = thinking


class _Resp:
    def __init__(self, blocks):
        self.content = blocks


class _ScriptedCreate:
    """按脚本依次返回响应。"""

    calls: list = []
    script: list = []

    @staticmethod
    def create(**kwargs):
        _ScriptedCreate.calls.append(kwargs)
        return _ScriptedCreate.script[len(_ScriptedCreate.calls) - 1]


class _FakeAnthropic:
    def __init__(self, **kw):
        self.messages = _ScriptedCreate


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "k-test")
    monkeypatch.setattr(llm_mod, "Anthropic", _FakeAnthropic)
    _ScriptedCreate.calls.clear()
    _ScriptedCreate.script.clear()
    return LLMClient(model="fake-m")


def test_thinking_only_retries_at_double_budget(client):
    _ScriptedCreate.script = [
        _Resp([_Blk("thinking", thinking="r" * 100, signature="s")]),  # thinking-only
        _Resp([_Blk("thinking", thinking="r", signature="s"), _Blk("text", text="ANSWER")]),
    ]
    out = client.chat("write a template", max_tokens=32768)
    assert out == "ANSWER"
    assert len(_ScriptedCreate.calls) == 2
    assert _ScriptedCreate.calls[0]["max_tokens"] == 32768
    assert _ScriptedCreate.calls[1]["max_tokens"] == 65536


def test_normal_response_no_retry(client):
    _ScriptedCreate.script = [
        _Resp([_Blk("text", text="PLAIN")]),
    ]
    out = client.chat("hi", max_tokens=1000)
    assert out == "PLAIN"
    assert len(_ScriptedCreate.calls) == 1


def test_second_failure_raises(client):
    _ScriptedCreate.script = [
        _Resp([_Blk("thinking", thinking="x", signature="s")]),
        _Resp([_Blk("thinking", thinking="y", signature="s")]),
    ]
    with pytest.raises(ValueError):
        client.chat("boom", max_tokens=100)
    assert len(_ScriptedCreate.calls) == 2  # 恰好一次重试,不死循环

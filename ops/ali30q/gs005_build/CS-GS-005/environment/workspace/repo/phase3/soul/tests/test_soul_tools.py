# -*- coding: utf-8 -*-
"""U19 工具箱单测:MCP 解析/搜索解析/verdict 行/fail-open。"""
from soul import tools
from soul.config import SELF_IMPROVE_EXCLUDE


def test_mcp_parse_json_body():
    body = ('{"jsonrpc":"2.0","id":1,"result":{"content":'
            '[{"type":"text","text":"hello"}],"isError":false}}')
    r = tools._parse_mcp_result(200, "application/json", body)
    assert r == {"text": "hello"}


def test_mcp_parse_sse_body():
    body = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"via-sse"}]}}\n\n'
    r = tools._parse_mcp_result(200, "text/event-stream", body)
    assert r == {"text": "via-sse"}


def test_mcp_parse_error_returns_none():
    body = '{"jsonrpc":"2.0","id":1,"error":{"code":-32000,"message":"boom"}}'
    assert tools._parse_mcp_result(200, "application/json", body) is None
    assert tools._parse_mcp_result(500, "text/plain", "garbage") is None


def test_mcp_no_token_fail_open(monkeypatch):
    monkeypatch.setattr(tools, "COMPASS_TOKEN", "")
    assert tools._mcp_call("recall", {}) is None  # 无钥匙=静默空,不抛


def test_parse_ddg_extracts_triples():
    html = ('<a class="result-link" href="//duck.com/l/?uddg=https%3A%2F%2Fx.io%2Fa&amp;rut=abc">T<b>1</b></a>'
            '<td class="result-snippet">S<b>nip</b></td>')
    items = tools._parse_ddg(html)
    assert items and items[0][0] == "T1"
    assert items[0][1] == "https://x.io/a"
    assert items[0][2] == "Snip"


def test_verdict_line():
    assert tools._verdict_line("REJECT: 回归风险\n细节") == "REJECT: 回归风险"
    assert tools._verdict_line("\n\nAPPROVE") == "APPROVE"
    assert tools._verdict_line("我觉得不行") == ""
    assert tools._verdict_line("") == ""


def test_tools_module_locked_from_self_improve():
    """感官器官禁自改:soul/tools 在 EXCLUDE。"""
    assert "soul/tools" in SELF_IMPROVE_EXCLUDE

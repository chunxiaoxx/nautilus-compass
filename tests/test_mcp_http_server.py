"""Tests for the standard-remote (streamable-http) compass MCP server.

Covers tool listing + dispatch (direct async calls) and the bearer-auth
middleware (via Starlette TestClient). Does not exercise the full
streamable-http protocol handshake — that is the Task-2 live smoke.
"""
import asyncio
import json

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

import mcp_http_server as srv
import mcp_server as cmp


def test_lists_all_17_tools_with_schemas():
    tools = asyncio.run(srv._list_tools())
    assert len(tools) == 17
    names = {t.name for t in tools}
    assert "recall" in names and "ingest_obs" in names
    for t in tools:
        assert t.inputSchema.get("type") == "object"


def test_call_tool_dispatches_to_registry():
    orig = cmp.TOOLS["recall"]
    cmp.TOOLS["recall"] = {"fn": lambda a: {"echo": a}, "schema": orig["schema"]}
    try:
        out = asyncio.run(srv._call_tool("recall", {"query": "hi"}))
    finally:
        cmp.TOOLS["recall"] = orig
    assert out[0].type == "text"
    assert json.loads(out[0].text)["echo"] == {"query": "hi"}


def test_call_tool_unknown_raises():
    try:
        asyncio.run(srv._call_tool("does_not_exist", {}))
        assert False, "expected ValueError"
    except ValueError as e:
        assert "unknown tool" in str(e)


def _init_body():
    return json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "t", "version": "0"}},
    })


_HDR = {"Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"}


def _auth_only_app():
    """Throwaway app exercising ONLY the bearer-auth middleware (isolated from
    the shared StreamableHTTPSessionManager, which may run() only once)."""
    async def ok(_request):
        return PlainTextResponse("ok")
    return Starlette(routes=[Route("/mcp", ok, methods=["POST"])],
                     middleware=[Middleware(srv._BearerAuth)])


def test_missing_token_401(monkeypatch):
    monkeypatch.setattr(srv, "VALID_TOKENS", {"good"})
    r = TestClient(_auth_only_app()).post("/mcp", content=_init_body(), headers=_HDR)
    assert r.status_code == 401


def test_valid_token_passes(monkeypatch):
    monkeypatch.setattr(srv, "VALID_TOKENS", {"good"})
    r = TestClient(_auth_only_app()).post(
        "/mcp", content=_init_body(),
        headers={**_HDR, "Authorization": "Bearer good"})
    assert r.status_code == 200
    assert r.text == "ok"

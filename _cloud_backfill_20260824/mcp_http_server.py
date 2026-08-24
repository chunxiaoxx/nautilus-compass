#!/usr/bin/env python3
"""Compass standard-remote MCP server (spec Streamable-HTTP).

Reuses the 17-tool registry in ``mcp_server.TOOLS`` (name -> {"fn", "schema"}).
Mirrors the platform HR-agent pattern (FastMCP over public HTTPS, behind nginx
+ certbot). Lets Claude Code connect natively with ``type: http`` + ``url`` —
no stdio bridge, no SSH tunnel.

Run:   uvicorn mcp_http_server:app --host 127.0.0.1 --port 8097
"""
from __future__ import annotations

import contextlib
import json
import os

import anyio
import anyio.to_thread
import mcp.types as types
import mcp_server as cmp
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

server: Server = Server("nautilus-compass", version="2.3.0")


@server.list_tools()
async def _list_tools() -> list[types.Tool]:
    out: list[types.Tool] = []
    for meta in cmp.TOOLS.values():
        s = meta["schema"]
        out.append(types.Tool(
            name=s["name"],
            description=s.get("description", ""),
            inputSchema=s.get("inputSchema", {"type": "object"}),
        ))
    return out


@server.call_tool()
async def _call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    meta = cmp.TOOLS.get(name)
    if not meta:
        raise ValueError(f"unknown tool: {name}")
    # compass fns are SYNC and do blocking socket I/O to the BGE daemon —
    # never run them directly on the event loop.
    result = await anyio.to_thread.run_sync(meta["fn"], arguments or {})
    return [types.TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2),
    )]


# ─── auth ───────────────────────────────────────────────────────────

def _load_tokens() -> set[str]:
    """Reuse the same tokens the TCP service already trusts."""
    path = os.environ.get("COMPASS_TOKENS_FILE", "/etc/compass/tokens.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "tokens" not in data:
            return set(data.keys())
        if isinstance(data, dict):
            return set(data.get("tokens", []))
        if isinstance(data, list):
            return set(data)
    except Exception:
        pass
    return set(filter(None, os.environ.get("COMPASS_MCP_TOKENS", "").split(",")))


VALID_TOKENS: set[str] = _load_tokens()


class _BearerAuth(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/mcp"):
            auth = request.headers.get("authorization", "")
            tok = auth[7:] if auth.lower().startswith("bearer ") \
                else request.headers.get("x-agent-key", "")
            if not VALID_TOKENS or tok not in VALID_TOKENS:
                return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


# ─── streamable-http app ────────────────────────────────────────────

_session_manager = StreamableHTTPSessionManager(
    app=server, json_response=True, stateless=True,
)


async def _handle(scope: Scope, receive: Receive, send: Send) -> None:
    await _session_manager.handle_request(scope, receive, send)


@contextlib.asynccontextmanager
async def _lifespan(_app):
    async with _session_manager.run():
        yield


# Mounted at /mcp → canonical endpoint is /mcp/ (Starlette adds the slash;
# bare /mcp 307-redirects to it, which real MCP/httpx clients follow). nginx
# should proxy_pass to the backend's /mcp/ so no redirect crosses the wire.
app = Starlette(
    routes=[Mount("/mcp", app=_handle)],
    middleware=[Middleware(_BearerAuth)],
    lifespan=_lifespan,
)

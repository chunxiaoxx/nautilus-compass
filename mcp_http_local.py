#!/usr/bin/env python3
"""Compass standard-remote MCP server (spec Streamable-HTTP).

Reuses the 17-tool registry in ``mcp_server.TOOLS`` (name -> {"fn", "schema"}).
Mirrors the platform HR-agent pattern (FastMCP over public HTTPS, behind nginx
+ certbot). Lets Claude Code connect natively with ``type: http`` + ``url`` —
no stdio bridge, no SSH tunnel.

Mac ingress only: no signup/login or self-service account routes.
Run:   uvicorn mcp_http_local:app --host 127.0.0.1 --port 8097
"""
from __future__ import annotations

import contextlib
import contextvars
from pathlib import Path
import mcp_access as access
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

server: Server = Server("nautilus-compass", version="3.3.1-mac-scoped")


@server.list_tools()
async def _list_tools() -> list[types.Tool]:
    out: list[types.Tool] = []
    for meta in cmp.TOOLS.values():
        s = meta["schema"]
        if not access.visible(_current_scopes.get(), s["name"]):
            continue
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
    arguments = access.authorize(
        _current_scopes.get(), name, arguments, lambda: cmp.resolve_project(None),
        cmp.PROJECTS_DIR,
    )
    # compass fns are SYNC and do blocking socket I/O to the BGE daemon —
    # never run them directly on the event loop.
    result = await anyio.to_thread.run_sync(meta["fn"], arguments or {})
    return [types.TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2),
    )]


# ─── auth ───────────────────────────────────────────────────────────

_current_scopes = contextvars.ContextVar('compass_http_scopes', default=frozenset())

def _load_tokens():
    path = os.environ.get('COMPASS_TOKENS_FILE', '/etc/compass/tokens.json')
    try:
        data = json.loads(Path(path).read_text())
        if isinstance(data, dict) and 'tokens' not in data:
            return {str(k): access.parse_scopes(v) for k, v in data.items()}
        # Explicit legacy bare-token files retain their documented full access.
        tokens = data.get('tokens', []) if isinstance(data, dict) else data
        if isinstance(tokens, list) and all(isinstance(t, str) for t in tokens):
            return {t: frozenset({'*'}) for t in tokens}
        return {}
    except FileNotFoundError:
        return {t: frozenset({'*'}) for t in
                os.environ.get('COMPASS_MCP_TOKENS', '').split(',') if t}
    except (OSError, ValueError):
        return {}

class _BearerAuth(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not request.url.path.startswith('/mcp'):
            return await call_next(request)
        auth = request.headers.get('authorization', '')
        tok = auth[7:] if auth.lower().startswith('bearer ') else request.headers.get('x-agent-key', '')
        scopes = _load_tokens().get(tok, frozenset())
        if not scopes:
            return JSONResponse({'error': 'unauthorized'}, status_code=401)
        marker = _current_scopes.set(scopes)
        try:
            return await call_next(request)
        finally:
            _current_scopes.reset(marker)


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

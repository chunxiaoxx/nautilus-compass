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
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

server: Server = Server("nautilus-compass", version="3.1.0")


@server.list_tools()
async def _list_tools() -> list[types.Tool]:
    out: list[types.Tool] = []
    internal = _is_internal_token(_current_scopes.get())
    for meta in cmp.TOOLS.values():
        s = meta["schema"]
        if s["name"] not in PUBLIC_TOOLS and not internal:
            continue  # platform-internal tools stay off the public surface
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
    # 2026-09-05 · public-surface guard: non-public platform tools are not
    # callable by self-service tokens even by known name (mirror of _list_tools)
    if name not in PUBLIC_TOOLS and not _is_internal_token(_current_scopes.get()):
        return [types.TextContent(
            type="text",
            text=json.dumps({"ok": False, "error": "forbidden: tool not public"},
                            ensure_ascii=False),
        )]
    # 2026-08-28 · scoped-token 强制执行（fail-closed）
    deny = _check_scope(_current_scopes.get(), name, arguments)
    if deny:
        return [types.TextContent(
            type="text",
            text=json.dumps({"ok": False, "error": f"forbidden: {deny}"},
                            ensure_ascii=False),
        )]
    # Self-service tokens: an unqualified project must EXECUTE against the
    # holder's own space — otherwise the call falls through to whatever
    # process-level default the tool/daemon side has (9/5 incident:外部
    # token 读到 daemon 默认内部用户空间 = 跨租户读). Mirror of the
    # _check_scope default-project resolution; immutable args copy.
    owner = _current_user.get()
    if owner and not (arguments or {}).get("project"):
        arguments = {**(arguments or {}), "project": owner}
    # compass fns are SYNC and do blocking socket I/O to the BGE daemon —
    # never run them directly on the event loop.
    result = await anyio.to_thread.run_sync(meta["fn"], arguments or {})
    return [types.TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2),
    )]


# ─── auth ───────────────────────────────────────────────────────────
#
# 2026-08-28 · scoped tokens（workbuddy 接入暴露的安全模型洞）：
#   旧模型 = token 只查存在性，'tools.read'/'tools.write' 声明是摆设，
#   任何持 token 者（而 quickstart 曾允许任何能 ssh cloud 的进程自签 token）
#   可 recall/ingest 任意 project 甚至 scope=user 全域。
#   新模型 = tokens.json 值可带 scopes：
#     {"cmp_x": {"scopes": ["read:Proj", "write:Proj"]}}   → 只列出的项目
#     {"cmp_y": ["tools.read", "tools.write"]}             → 旧格式 = read:*+write:*（兼容过渡）
#   缺省新签 token 应由 ops/compass_token_admin.py 按 scope 签发。

import contextvars

# set by auth middleware; read by _call_tool for scope enforcement
_current_scopes: contextvars.ContextVar[frozenset] = contextvars.ContextVar(
    "compass_scopes", default=frozenset())
# owning user of a self-service token ("" for ops-issued tokens); lets an
# unqualified project argument resolve to the holder's own default space
_current_user: contextvars.ContextVar[str] = contextvars.ContextVar(
    "compass_user", default="")

# hosted 公网工具面(2026-09-05,launch_plan §12.1):仅 8 个用户工具对外;
# governance_×5/submit_platform_task/proof_of_impact/add_worker/long_task/
# ingest_platform_task_result 等平台内部工具退出公网清单。
# 内部放行判据 = ops 旧格式 token 的 scopes 标志(tokens.json 实测全为
# tools.read/tools.write 组合,无 "admin" 字样——§12.1 原假设有误,9/5 部署时
# 实测纠偏);自助 token(read:{uid}/write:{uid})不含这些标志 → 只见公开面。
PUBLIC_TOOLS = {
    "ingest_obs", "recall", "session_search", "thread_recall",
    "profile", "drift_check", "drift_history", "feedback_log",
}


def _is_internal_token(scopes: frozenset) -> bool:
    """ops-issued tokens.json tokens carry the legacy tools.* flags;
    self-service tokens carry only read:{uid}/write:{uid} (+admin, future)."""
    return bool(scopes & {"admin", "tools.read", "tools.write"})

READ_TOOLS = {
    "recall", "session_search", "thread_recall", "drift_check", "drift_history",
    "profile", "proof_of_impact", "governance_audit", "governance_lock_check",
}
WRITE_TOOLS = {
    "ingest_obs", "feedback_log", "long_task", "submit_platform_task",
    "ingest_platform_task_result", "add_worker",
    "governance_plan", "governance_dispatch",
}
# 其余工具（若有）默认视为 write 级——fail-closed。


def _scopes_from_value(val) -> frozenset:
    """tokens.json 值 → scope 集合。旧格式(list)与 dict 均支持。"""
    if isinstance(val, dict):
        return frozenset(str(s) for s in val.get("scopes", []))
    if isinstance(val, list):
        # 旧格式: 非空 list = 旧的全权语义（read:* + write:*）
        return frozenset({"read:*", "write:*"}) if val else frozenset()
    return frozenset()


def _load_tokens() -> dict[str, frozenset]:
    """token → scopes。复用 TCP 服务同一 tokens.json。"""
    path = os.environ.get("COMPASS_TOKENS_FILE", "/etc/compass/tokens.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "tokens" not in data:
            return {str(k): _scopes_from_value(v) for k, v in data.items()}
        if isinstance(data, dict):
            return {str(k): frozenset({"read:*", "write:*"})
                    for k in data.get("tokens", [])}
        if isinstance(data, list):
            return {str(k): frozenset({"read:*", "write:*"}) for k in data}
    except Exception:
        pass
    return {t: frozenset({"read:*", "write:*"})
            for t in filter(None, os.environ.get("COMPASS_MCP_TOKENS", "").split(","))}


VALID_TOKENS: dict[str, frozenset] = _load_tokens()
_tokens_mtime: float = 0.0
try:
    _tokens_path = os.environ.get("COMPASS_TOKENS_FILE", "/etc/compass/tokens.json")
    _tokens_mtime = os.path.getmtime(_tokens_path)
except OSError:
    pass


def _tokens_reload_if_stale() -> None:
    """2026-08-28(workbuddy 反馈 P1·2.1): tokens.json 曾不热加载,新签 token
    必须重启服务。改 mtime 懒重载——每请求 O(1) stat,变更即重读,无需 systemd
    restart(也无需 inotify 依赖)。"""
    global VALID_TOKENS, _tokens_mtime
    try:
        m = os.path.getmtime(_tokens_path)
    except OSError:
        return
    if m != _tokens_mtime:
        VALID_TOKENS = _load_tokens()
        _tokens_mtime = m


def _check_scope(scopes: frozenset, tool_name: str, arguments: dict) -> str | None:
    """返回 None=放行；否则拒绝原因。未列项目一律 fail-closed。"""
    want_read = tool_name in READ_TOOLS
    want_write = tool_name not in READ_TOOLS  # write 类 + 未知工具
    if tool_name in WRITE_TOOLS:
        want_read, want_write = False, True
    if "admin" in scopes:
        return None
    project = str((arguments or {}).get("project")
                  or _current_user.get() or "")
    if want_read:
        if "read:*" in scopes:
            return None
        # scope=user 跨项目全域读 → 需 read:*（普通 scoped token 不给）
        if str((arguments or {}).get("scope") or "") == "user":
            return "scope=user requires read:*"
        if f"read:{project}" in scopes:
            return None
        return f"token lacks read scope for project '{project}'"
    if want_write:
        if "write:*" in scopes:
            return None
        if f"write:{project}" in scopes:
            return None
        return f"token lacks write scope for project '{project}'"
    return None


def _scopes_for_token(tok: str) -> frozenset | None:
    """tokens.json first (ops-issued, hot-reloaded); then SQLite self-service
    tokens (MVP-3, sha256 lookup, revoked filtered). None = unknown token."""
    scopes = VALID_TOKENS.get(tok)
    if scopes is not None:
        return scopes
    if not tok.startswith("cmp_live_"):
        return None
    import hashlib
    h = hashlib.sha256(tok.encode()).hexdigest()
    conn = _db_conn()
    try:
        row = _st.find_token_by_hash(conn, h)
    finally:
        conn.close()
    if row is None:
        return None
    return frozenset(s for s in row["scopes"].split(",") if s)


def _owner_for_token(tok: str) -> str:
    """Self-service token → owning user_id (default-project fallback for
    scope checks); ops-issued tokens.json tokens → "" (no default space)."""
    if not tok.startswith("cmp_live_"):
        return ""
    import hashlib
    h = hashlib.sha256(tok.encode()).hexdigest()
    conn = _db_conn()
    try:
        row = _st.find_token_by_hash(conn, h)
    finally:
        conn.close()
    return str(row["user_id"]) if row is not None else ""


class _BearerAuth(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/mcp"):
            _tokens_reload_if_stale()
            auth = request.headers.get("authorization", "")
            tok = auth[7:] if auth.lower().startswith("bearer ") \
                else request.headers.get("x-agent-key", "")
            scopes = _scopes_for_token(tok) if tok else None
            if not scopes:
                return JSONResponse({"error": "unauthorized"}, status_code=401)
            _current_scopes.set(scopes)
            _current_user.set(_owner_for_token(tok) if tok else "")
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

# ─── MVP multitenant: signup / login (JWT) ──────────────────────────
# Storage + auth live in mcp_storage / auth_api; DB path overridable for tests.
import auth_api as _auth  # noqa: E402
import email_sender  # noqa: E402
import mcp_pages as _pages  # noqa: E402
import mcp_storage as _st  # noqa: E402


def _db_conn():
    return _st.init_db(os.environ.get("COMPASS_MVP_DB", "./mvp_users.db"))


class _JsonBody(dict):
    pass


async def _signup(request):
    body = await request.json()
    conn = _db_conn()
    try:
        out = _auth.signup_user(conn, email=body.get("email", ""),
                                passphrase=body.get("passphrase", ""),
                                region=body.get("region", ""))
        return JSONResponse(out)
    except _auth.ConflictError:
        return JSONResponse({"error": "email already registered"}, status_code=409)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=422)
    except email_sender.EmailSendError as e:
        return JSONResponse({"error":
                             f"could not send verification email: {e}"},
                            status_code=503)
    except email_sender.EmailNotConfigured:
        return JSONResponse({"error":
                             "verification email unavailable — try again later"},
                            status_code=503)
    finally:
        conn.close()


async def _login(request):
    body = await request.json()
    conn = _db_conn()
    try:
        out = _auth.login_user(conn, email=body.get("email", ""),
                               passphrase=body.get("passphrase", ""))
        return JSONResponse(out)
    except _auth.AuthError:
        return JSONResponse({"error": "invalid credentials"}, status_code=401)
    except _auth.UnverifiedError:
        return JSONResponse(
            {"error": "email not verified — enter the 6-digit code we sent"
                      " (POST /verify {email, code}, or /verify/resend)"},
            status_code=403)
    finally:
        conn.close()


async def _verify(request):
    body = await request.json()
    conn = _db_conn()
    try:
        if not _auth.email_required():
            return JSONResponse({"verified": True})
        _auth.verify_email(conn, email=str(body.get("email", "")),
                           code=str(body.get("code", "")))
        return JSONResponse({"verified": True})
    except _auth.VerificationError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    finally:
        conn.close()


async def _verify_resend(request):
    body = await request.json()
    conn = _db_conn()
    try:
        if not _auth.email_required():
            return JSONResponse({"error": "verification disabled"}, status_code=400)
        # Unknown/verified emails are silent no-ops inside; rate limits are
        # swallowed too, so this response shape never leaks account existence.
        _auth.resend_verification(conn, email=str(body.get("email", "")))
        return JSONResponse({"sent": True})
    except email_sender.EmailSendError as e:
        return JSONResponse({"error": f"could not send email: {e}"},
                            status_code=503)
    except email_sender.EmailNotConfigured:
        return JSONResponse({"error": "email sending unavailable"},
                            status_code=503)
    finally:
        conn.close()


def _require_user(request) -> str:
    return _auth.require_user(request.headers.get("authorization", ""))


async def _tokens_create(request):
    try:
        user_id = _require_user(request)
    except _auth.AuthError:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    body = await request.json() if request.headers.get("content-length") else {}
    conn = _db_conn()
    try:
        return JSONResponse(_auth.issue_api_token(
            conn, user_id=user_id, name=str(body.get("name", ""))[:64]))
    finally:
        conn.close()


async def _tokens_list(request):
    try:
        user_id = _require_user(request)
    except _auth.AuthError:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    conn = _db_conn()
    try:
        return JSONResponse({"tokens": _auth.list_api_tokens(conn, user_id)})
    finally:
        conn.close()


async def _tokens_revoke(request):
    try:
        user_id = _require_user(request)
    except _auth.AuthError:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    token_id = request.path_params.get("token_id", "")
    conn = _db_conn()
    try:
        ok = _st.revoke_token(conn, user_id, token_id)
        return JSONResponse({"revoked": bool(ok)},
                            status_code=200 if ok else 404)
    finally:
        conn.close()


app = Starlette(
    routes=[
        Mount("/mcp", app=_handle),
        Route("/signup", _signup, methods=["POST"]),
        Route("/login", _login, methods=["POST"]),
        Route("/verify", _verify, methods=["POST"]),
        Route("/verify/resend", _verify_resend, methods=["POST"]),
        Route("/tokens", _tokens_create, methods=["POST"]),
        Route("/tokens", _tokens_list, methods=["GET"]),
        Route("/tokens/{token_id}", _tokens_revoke, methods=["DELETE"]),
        Route("/signup", lambda req: HTMLResponse(_pages.signup_page()),
              methods=["GET"]),
        Route("/console", lambda req: HTMLResponse(_pages.console_page()),
              methods=["GET"]),
    ],
    middleware=[Middleware(_BearerAuth)],
    lifespan=_lifespan,
)

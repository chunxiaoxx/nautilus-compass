#!/usr/bin/env python3
"""Stdio MCP → cloud TCP MCP proxy · for Claude Code .mcp.json registration.

Bridges Claude Code's stdio MCP transport (which is the only transport it
supports natively) to the compass cloud TCP MCP server. This lets the
dialog session register `nautilus-compass-cloud` in its .mcp.json and
call compass.recall(), compass.drift_check(), compass.thread_recall(),
etc. as native MCP tools instead of via subprocess.run python -c.

Setup (one-time):
  1. Start SSH tunnel:
       ssh -fN -L 9877:127.0.0.1:9877 cloud
  2. Set env vars:
       export COMPASS_CLOUD_HOST=127.0.0.1
       export COMPASS_CLOUD_PORT=9877
       export COMPASS_CLOUD_TOKEN=cmp_claude_code_compass_dialog_...
       export COMPASS_AGENT_TYPE=claude-code-compass-dialog
  3. Register in ~/.claude/.mcp.json:
       "nautilus-compass-cloud": {
         "command": "python3",
         "args": ["~/.claude/plugins/nautilus-compass/ops/mcp_stdio_to_cloud.py"],
         "env": {
           "COMPASS_CLOUD_HOST": "127.0.0.1",
           "COMPASS_CLOUD_PORT": "9877",
           "COMPASS_CLOUD_TOKEN": "cmp_...",
           "COMPASS_AGENT_TYPE": "claude-code-compass-dialog"
         }
       }

Wire behavior:
  - Reads JSON-RPC lines from stdin.
  - Injects `params.authToken` into every outgoing request.
  - Forwards to cloud TCP server.
  - Forwards cloud responses back to stdout line-by-line.
  - Tunnel down or cloud unreachable → emits one -32603 error per
    pending request, then exits 1.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import threading


HOST = os.environ.get("COMPASS_CLOUD_HOST", "127.0.0.1")
PORT = int(os.environ.get("COMPASS_CLOUD_PORT", "9877"))
TOKEN = os.environ.get("COMPASS_CLOUD_TOKEN")
AGENT_TYPE = os.environ.get("COMPASS_AGENT_TYPE", "claude-code-cloud-proxy")
# v1.6 · local-first recall via GPU BGE daemon
LOCAL_PORT = int(os.environ.get("COMPASS_LOCAL_PORT", "9876"))
# v1.7.2 · raise 5→20 + retry: recall 稳态 <1s,但 daemon 与 prompt-hook 并发时偶发
# 突发延迟会超 5s → 误判不可达。20s + 1 retry 吸收瞬时阻塞(2026-05-27 实证 transient,非稳态慢)。
LOCAL_TIMEOUT = float(os.environ.get("COMPASS_LOCAL_TIMEOUT", "20"))
LOCAL_RETRIES = int(os.environ.get("COMPASS_LOCAL_RETRIES", "2"))
# Tools that can be served locally (recall/drift only · ingest always goes cloud)
_LOCAL_TOOLS = {"recall", "drift_check", "thread_recall"}
# Debug · set COMPASS_BRIDGE_LOG=/path/to/file to trace every line in/out
LOG_PATH = os.environ.get("COMPASS_BRIDGE_LOG", "")
_log_fh = None
if LOG_PATH:
    try:
        _log_fh = open(LOG_PATH, "a", encoding="utf-8", buffering=1)
        _log_fh.write(f"\n=== bridge start · pid={os.getpid()} · agent={AGENT_TYPE} ===\n")
    except Exception:
        _log_fh = None


def _trace(tag: str, data) -> None:
    if not _log_fh:
        return
    try:
        import time as _t
        ts = _t.strftime("%H:%M:%S")
        s = data if isinstance(data, str) else data.decode("utf-8", errors="replace")
        _log_fh.write(f"{ts} {tag}: {s[:500]}\n")
    except Exception:
        pass

if not TOKEN:
    sys.stderr.write(
        "mcp_stdio_to_cloud · COMPASS_CLOUD_TOKEN env required\n"
    )
    sys.exit(2)


def _open_cloud() -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10.0)
    s.connect((HOST, PORT))
    # Connect done · switch to blocking mode for the live session.
    # If we leave 10s timeout, recv times out after server idles 10s
    # (which it always does between requests) · bridge exits · MCP fails.
    s.settimeout(None)
    return s


def _inject_auth(line: str) -> str:
    """Add authToken + agent_type to outgoing JSON-RPC requests.

    v1.3 (#104) · also injects COMPASS_AGENT_TYPE into tools/call arguments
    so the cloud daemon can log per-agent verification entries.
    """
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return line
    if isinstance(msg, dict) and msg.get("method"):
        params = msg.get("params")
        if not isinstance(params, dict):
            params = {}
        params["authToken"] = TOKEN
        # Inject agent_type into tool call arguments
        if msg.get("method") == "tools/call":
            args = params.get("arguments")
            if not isinstance(args, dict):
                args = {}
            args.setdefault("agent_type", AGENT_TYPE)
            params["arguments"] = args
        msg["params"] = params
    return json.dumps(msg)


# v1.5.2 · Claude Code calls these MCP standard methods after initialize.
# Cloud server doesn't implement them (returns -32601 method not found) which
# Claude treats as fatal connection failure. We short-circuit locally with
# empty list responses — fully spec-compliant per MCP 2024-11-05.
_LOCAL_STUB_METHODS = {
    "prompts/list":              {"prompts": []},
    "resources/templates/list":  {"resourceTemplates": []},
    "resources/list":            {"resources": []},
}

# v1.6 · MCP initialize response for local-only mode (cloud=None)
_MCP_CAPABILITIES = {
    "capabilities": {
        "tools": {},
    },
    "protocolVersion": "2024-11-05",
    "serverInfo": {"name": "nautilus-compass-local", "version": "1.6.0"},
}

# v1.6 · Full tool list for local-only mode (mirrors cloud mcp_server.py)
# Tools handled locally: recall, drift_check, thread_recall
# Tools requiring cloud: all others (return error in local-only mode)
_MCP_TOOLS = [
    {"name": "recall", "description": "Semantic recall over user's persistent memory (BGE-m3). Returns top-k matches by cosine similarity.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "Natural language search query"}, "project": {"type": "string", "description": "Project memory dir name"}, "scope": {"type": "string", "enum": ["project", "user"], "default": "user"}, "top_k": {"type": "integer", "default": 5}}, "required": ["query"]}},
    {"name": "drift_check", "description": "Check behavioral drift against anchor profile", "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "Text to check for drift"}, "project": {"type": "string"}, "scope": {"type": "string", "enum": ["project", "user"], "default": "user"}, "anchors_path": {"type": "string", "description": "Path to anchors JSON"}}, "required": ["query"]}},
    {"name": "thread_recall", "description": "Recall memories related to a thread", "inputSchema": {"type": "object", "properties": {"thread_id": {"type": "string"}, "query": {"type": "string"}, "top_k": {"type": "integer", "default": 10}}, "required": []}},
    {"name": "ingest_obs", "description": "Write one observation to cross-agent memory. Includes drift self-audit.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string", "description": "8-15 char title"}, "description": {"type": "string"}, "body": {"type": "string"}, "type": {"type": "string", "enum": ["bugfix","feature","refactor","discovery","decision","change"], "default": "discovery"}, "concept": {"type": "string", "enum": ["gotcha","pattern","trade-off","how-it-works","why-it-exists","problem-solution","what-changed"], "default": "pattern"}, "drift": {"type": "string", "enum": ["green","yellow","red"], "default": "green"}, "drift_signals": {"type": "array", "items": {"type": "string"}, "default": []}, "agent_type": {"type": "string"}, "project": {"type": "string"}, "thread_id": {"type": "string"}, "thread_role": {"type": "string", "enum": ["outbound","inbound","self_note"]}}, "required": ["name"]}},
    {"name": "drift_history", "description": "Cross-project AI drift timeline. green/yellow/red counts, top RED sessions.", "inputSchema": {"type": "object", "properties": {"days": {"type": "integer", "default": 30}, "project_filter": {"type": "string"}}}},
    {"name": "session_search", "description": "Keyword search across all session_*.md files. Supports drift/type filter.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "drift": {"type": "string", "enum": ["green","yellow","red"]}, "type": {"type": "string", "enum": ["bugfix","feature","refactor","discovery","decision","change"]}, "days": {"type": "integer", "default": 60}, "top_k": {"type": "integer", "default": 5}}, "required": ["query"]}},
    {"name": "profile", "description": "User profile derived from session aggregate (top projects, work types, drift dist).", "inputSchema": {"type": "object", "properties": {"days": {"type": "integer", "default": 90}}}},
    {"name": "feedback_log", "description": "Log true-positive or false-positive signal for anchor retraining.", "inputSchema": {"type": "object", "properties": {"direction": {"type": "string", "enum": ["good", "bad"]}, "reason": {"type": "string"}}, "required": ["direction"]}},
    {"name": "long_task", "description": "Demo tool for notifications/progress + cancelled.", "inputSchema": {"type": "object", "properties": {"steps": {"type": "integer", "default": 3}}}},
    {"name": "submit_platform_task", "description": "Queue a task for Nautilus platform (V5 cycle / platform_agents).", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "channels": {"type": "array", "items": {"type": "string"}, "default": []}, "payload": {"type": "object"}, "anchor_pack_hint": {"type": "string"}, "priority": {"type": "string", "enum": ["low","normal","high"], "default": "normal"}}, "required": ["name"]}},
    {"name": "ingest_platform_task_result", "description": "Platform agent reports completed task back to compass.", "inputSchema": {"type": "object", "properties": {"task_id": {"type": "string"}, "result_summary": {"type": "string"}, "channels_published": {"type": "array", "items": {"type": "object"}, "default": []}, "drift": {"type": "string", "enum": ["green","yellow","red"], "default": "green"}, "agent_id": {"type": "string"}, "project": {"type": "string"}}, "required": ["task_id"]}},
    {"name": "governance_dispatch", "description": "V7 governance · Decompose multi-channel task into routed sub-tasks.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "channels": {"type": "array", "items": {"type": "string"}}, "payload": {"type": "object"}, "anchor_pack_hint": {"type": "string"}, "priority": {"type": "string", "enum": ["low","normal","high"], "default": "normal"}}, "required": ["name", "channels"]}},
    {"name": "governance_audit", "description": "V7 governance · Cross-agent fake-closure audit.", "inputSchema": {"type": "object", "properties": {"days": {"type": "integer", "default": 7}, "project": {"type": "string"}}}},
    {"name": "governance_lock_check", "description": "V7 governance · L0/L1 hash lock verification.", "inputSchema": {"type": "object", "properties": {"bootstrap": {"type": "boolean", "default": False}}}},
    {"name": "governance_plan", "description": "V7 v0.2 · Capability-driven complex-task plan with DAG routing.", "inputSchema": {"type": "object", "properties": {"goal": {"type": "string"}, "domain_hint": {"type": "string"}, "anchor_pack_hint": {"type": "string"}, "payload": {"type": "object"}, "priority": {"type": "string", "enum": ["low","normal","high"], "default": "normal"}, "dry_run": {"type": "boolean", "default": False}}, "required": ["goal"]}},
]


def _try_local_stub(line: str, cloud_available: bool = True):
    """If method is in _LOCAL_STUB_METHODS or (cloud unavailable and method is
    initialize/tools/list), return JSON-RPC response bytes.
    Returns None otherwise (caller forwards to cloud or local daemon)."""
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(msg, dict):
        return None
    method = msg.get("method")

    # Always handle these locally (cloud doesn't implement them)
    if method in _LOCAL_STUB_METHODS:
        if "id" not in msg:
            return b""
        resp = {
            "jsonrpc": "2.0",
            "id": msg["id"],
            "result": _LOCAL_STUB_METHODS[method],
        }
        return (json.dumps(resp) + "\n").encode("utf-8")

    # v1.6 · in local-only mode, handle MCP lifecycle methods locally
    if not cloud_available:
        if method == "initialize":
            if "id" not in msg:
                return b""
            resp = {"jsonrpc": "2.0", "id": msg["id"], "result": _MCP_CAPABILITIES}
            return (json.dumps(resp) + "\n").encode("utf-8")
        if method == "tools/list":
            if "id" not in msg:
                return b""
            resp = {"jsonrpc": "2.0", "id": msg["id"], "result": {"tools": _MCP_TOOLS}}
            return (json.dumps(resp) + "\n").encode("utf-8")
        if method == "notifications/initialized":
            # Client notification · no response needed
            return b""

    return None


_stdout_lock = threading.Lock()


def _try_local_daemon(line: str):
    """v1.6 · local-first recall/drift via GPU BGE daemon on LOCAL_PORT.

    For tools/call with name in _LOCAL_TOOLS:
      1. Map MCP arguments → daemon JSON-line protocol
      2. TCP connect 127.0.0.1:LOCAL_PORT · send · recv
      3. If ok=true → wrap as MCP JSON-RPC response bytes
      4. If fail → return None (caller falls through to cloud)

    Returns bytes (response to write to stdout) or None (fallback).
    """
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(msg, dict):
        return None
    if msg.get("method") != "tools/call":
        return None
    params = msg.get("params") or {}
    tool_name = params.get("name", "")
    if tool_name not in _LOCAL_TOOLS:
        return None
    if "id" not in msg:
        return None

    args = params.get("arguments") or {}

    # Map MCP tool arguments → daemon protocol
    if tool_name == "recall":
        daemon_req = {
            "action": "recall",
            "query": args.get("query", ""),
            "project": args.get("project", ""),
            "scope": args.get("scope", "user"),
            "top_k": int(args.get("top_k", 5)),
            "agent_type": args.get("agent_type", AGENT_TYPE),
        }
    elif tool_name == "drift_check":
        daemon_req = {
            "action": "drift",
            "query": args.get("query", ""),
            "project": args.get("project", ""),
            "scope": args.get("scope", "user"),
            "agent_type": args.get("agent_type", AGENT_TYPE),
        }
        if args.get("anchors_path"):
            daemon_req["anchors_path"] = args["anchors_path"]
    elif tool_name == "thread_recall":
        daemon_req = {
            "action": "recall",
            "query": args.get("thread_id", args.get("query", "")),
            "scope": "user",
            "top_k": int(args.get("top_k", 10)),
            "agent_type": args.get("agent_type", AGENT_TYPE),
        }
    else:
        return None

    if not daemon_req.get("query"):
        return None

    # TCP call to local daemon · v1.7.2 · retry on transient timeout/io
    buf = b""
    last_err = None
    for attempt in range(LOCAL_RETRIES):
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(LOCAL_TIMEOUT)
            s.connect(("127.0.0.1", LOCAL_PORT))
            s.sendall((json.dumps(daemon_req) + "\n").encode("utf-8"))
            buf = b""
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
                if b"\n" in buf:
                    break
            s.close()
            break  # success
        except Exception as e:
            last_err = e
            _trace("LOCAL_RETRY", f"attempt {attempt + 1}/{LOCAL_RETRIES}: {e!r}")
            try:
                if s:
                    s.close()
            except Exception:
                pass
            buf = b""
    else:
        _trace("LOCAL_FAIL", f"connect/io error after {LOCAL_RETRIES} tries: {last_err!r}")
        return None

    # Parse daemon response
    try:
        daemon_resp = json.loads(buf.decode("utf-8").strip())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        _trace("LOCAL_FAIL", f"json parse: {e!r}")
        return None

    if not daemon_resp.get("ok"):
        _trace("LOCAL_FAIL", f"daemon ok=false: {daemon_resp.get('error', '?')}")
        return None

    # Wrap as MCP JSON-RPC success response
    # The cloud MCP server returns tool results as {"content": [{"type":"text","text":"..."}]}
    mcp_result = {"content": [{"type": "text", "text": json.dumps(daemon_resp, ensure_ascii=False)}]}
    rpc_resp = {
        "jsonrpc": "2.0",
        "id": msg["id"],
        "result": mcp_result,
    }
    _trace("LOCAL_OK", f"tool={tool_name} hits={len(daemon_resp.get('recall', []))}")
    return (json.dumps(rpc_resp, ensure_ascii=False) + "\n").encode("utf-8")


def _write_stdout(payload: bytes) -> None:
    """Single point for writing to stdout · serialized so stub responses and
    cloud forwards never interleave bytes mid-frame."""
    with _stdout_lock:
        sys.stdout.buffer.write(payload)
        sys.stdout.buffer.flush()


def _make_rpc_error(msg_id, code: int, message: str) -> bytes:
    """Build a JSON-RPC error response."""
    resp = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}
    return (json.dumps(resp) + "\n").encode("utf-8")


def _decode_line(raw: bytes) -> str:
    """Decode one stdin line as UTF-8 — the MCP JSON-RPC stream is ALWAYS UTF-8.

    Do NOT rely on text-mode sys.stdin: on a Chinese Windows host it defaults to
    gbk + surrogateescape, which turns a CJK obs name's UTF-8 bytes into lone
    surrogates (\\udcXX). Those survive json.dumps (as \\uXXXX escapes) and then
    detonate cloud-side on strict utf-8 re-encode → "tool ingest_obs failed:
    surrogates not allowed" (the 跨设备 obs ingest bug, 2026-06-05). errors=
    'replace' keeps the bridge crash-proof on a stray non-utf8 byte without ever
    producing a surrogate."""
    return raw.decode("utf-8", errors="replace")


def _pump_in_to_cloud(cloud) -> None:
    """stdin → (local stub | local daemon | inject auth → cloud TCP) / stdout.

    v1.6: cloud may be None (cloud-optional mode). If local handles the
    request, cloud is never needed. If local fails and cloud is None,
    return a JSON-RPC error to the caller.
    """
    cloud_available = cloud is not None
    # read BINARY stdin and decode UTF-8 ourselves · text-mode sys.stdin uses the
    # Windows console code page (gbk) which corrupts CJK into lone surrogates.
    for raw_bytes in sys.stdin.buffer:
        raw = _decode_line(raw_bytes)
        if not raw.strip():
            continue
        line = raw.rstrip("\n")
        _trace("STDIN", line)
        stub = _try_local_stub(line, cloud_available)
        if stub is not None:
            if stub:
                _trace("STUB", stub)
                _write_stdout(stub)
            continue
        # v1.6 · try local GPU daemon first for recall/drift
        local_resp = _try_local_daemon(line)
        if local_resp is not None:
            _write_stdout(local_resp)
            continue
        # Local didn't handle it · forward to cloud
        if cloud is None:
            # Cloud unavailable · return error for requests with id
            try:
                msg = json.loads(line)
                if isinstance(msg, dict) and "id" in msg:
                    err = _make_rpc_error(
                        msg["id"], -32603,
                        "cloud compass unreachable and local daemon did not handle this request"
                    )
                    _write_stdout(err)
                    _trace("NO_CLOUD", f"id={msg['id']} method={msg.get('method')}")
            except json.JSONDecodeError:
                pass
            continue
        out = _inject_auth(line)
        try:
            cloud.sendall((out + "\n").encode("utf-8"))
            _trace("→CLOUD", out)
        except Exception as e:
            sys.stderr.write(f"send fail: {e!r}\n")
            _trace("ERR", f"send fail: {e!r}")
            return
    _trace("STDIN", "<eof>")
    if cloud:
        try:
            cloud.shutdown(socket.SHUT_WR)
        except Exception:
            pass


def _pump_cloud_to_out(cloud: socket.socket) -> None:
    """cloud TCP → stdout (line-buffered, raw bytes · bypass platform encoding)."""
    buf = b""
    while True:
        try:
            chunk = cloud.recv(65536)
        except Exception as e:
            sys.stderr.write(f"recv fail: {e!r}\n")
            _trace("ERR", f"recv fail: {e!r}")
            return
        if not chunk:
            _trace("CLOUD", "<eof>")
            return
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            if not line.strip():
                continue
            _trace("CLOUD→", line)
            _write_stdout(line + b"\n")


def _heartbeat(cloud: socket.socket) -> None:
    """v1.5.5 · send empty newline every 60s when idle · prevents TCP middlebox
    or sshd channel timeout from killing 2-5 min idle connection.
    mcp_server.py accept-loop skips empty/non-JSON lines safely."""
    import time as _t
    while True:
        _t.sleep(60)
        try:
            cloud.sendall(b"\n")
            _trace("HEARTBEAT", "tick")
        except Exception as e:
            _trace("ERR", f"heartbeat send fail: {e!r}")
            return


def main() -> int:
    # v1.6 · cloud connection is optional · local daemon can serve independently
    cloud = None
    try:
        cloud = _open_cloud()
        sys.stderr.write(
            f"mcp_stdio_to_cloud · connected {HOST}:{PORT} "
            f"· agent_type={AGENT_TYPE} · mode=local+cloud\n"
        )
    except Exception as e:
        sys.stderr.write(
            f"mcp_stdio_to_cloud · cloud {HOST}:{PORT} unreachable ({e!r})\n"
            f"  · running in LOCAL-ONLY mode (GPU daemon on :{LOCAL_PORT})\n"
            f"  · recall/drift_check/thread_recall served locally\n"
            f"  · ingest_obs will fail until cloud is restored\n"
        )

    t_in = threading.Thread(target=_pump_in_to_cloud, args=(cloud,), daemon=True)
    t_in.start()

    if cloud:
        t_out = threading.Thread(target=_pump_cloud_to_out, args=(cloud,), daemon=True)
        t_hb = threading.Thread(target=_heartbeat, args=(cloud,), daemon=True)
        t_out.start()
        t_hb.start()
        t_out.join()  # exit when cloud closes
        try:
            cloud.close()
        except Exception:
            pass
    else:
        # Local-only mode · keep alive until stdin closes
        t_in.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())

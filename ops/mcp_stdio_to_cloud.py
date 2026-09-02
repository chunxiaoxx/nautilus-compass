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
# v1.9 · tools whose re-send on reconnect is duplicate-SAFE (read-only). Writes are
# NOT here: cloud mcp_server.tool_ingest_obs does a timestamped direct file write
# with NO idempotency key (verified 2026-06-23) → a re-send across a minute boundary
# would write a 2nd obs file. So only read-only tools are silently re-sent; pending
# writes are errored back to the client on reconnect (no silent duplicate, no silent loss).
_IDEMPOTENT_TOOLS = {
    "recall", "drift_check", "thread_recall",
    "drift_history", "session_search", "profile",
    "governance_audit", "governance_lock_check",
}


def _line_is_idempotent(line: str) -> bool:
    """v1.9 · True only for requests safe to silently re-send on reconnect.
    Only read-only tools/call (name in _IDEMPOTENT_TOOLS) qualify; everything
    else (writes, unknown tools, non-tools/call requests) is treated as unsafe."""
    try:
        msg = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return False
    if not isinstance(msg, dict) or msg.get("method") != "tools/call":
        return False
    return ((msg.get("params") or {}).get("name")) in _IDEMPOTENT_TOOLS
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


def _recv_one_line(sock, timeout: float = 10.0) -> bytes:
    """Read one newline-terminated frame · used to swallow the duplicate
    initialize reply after a reconnect handshake so it never reaches stdout."""
    try:
        sock.settimeout(timeout)
    except Exception:
        pass
    buf = b""
    while b"\n" not in buf:
        chunk = sock.recv(65536)
        if not chunk:
            break
        buf += chunk
    try:
        sock.settimeout(None)
    except Exception:
        pass
    return buf


class _CloudLink:
    """Owns the cloud socket with auto-reconnect + initialize replay (v1.8).

    Why: the bridge used to connect once in main() and exit the whole process
    the instant the cloud socket dropped (SSH tunnel death / VM hiccup) — which
    is why only this MCP server "disconnects" and needs a manual /mcp. The
    forward watchdog (compass_forward_watchdog.ps1) heals the tunnel/service
    within 5min but can't resurrect the bridge subprocess. This class lets the
    bridge survive a drop and reconnect once the tunnel is back.

    Cloud constraint (mcp_server.py _serve): every NEW connection's FIRST
    message must be `initialize` + authToken, else -32001 + close. So on
    reconnect we replay the cached initialize and swallow its duplicate reply.
    """

    def __init__(self, opener=None) -> None:
        self._opener = opener or _open_cloud
        self._sock = None
        self._lock = threading.Lock()
        self._init_line = None
        self._closed = False
        # v1.9 · in-flight requests awaiting a cloud reply, keyed by json-rpc id.
        # Re-sent after the initialize replay on reconnect so a request the cloud
        # received-but-never-answered (dropped mid-flight) is not lost forever.
        self._pending = {}

    @property
    def init_line(self):
        return self._init_line

    @property
    def is_closed(self) -> bool:
        return self._closed

    def note_outgoing(self, line: str) -> None:
        """Cache the first `initialize` request so reconnect can replay it.
        First initialize wins · later ones never clobber the cached handshake."""
        if self._init_line is not None:
            return
        try:
            msg = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            return
        if isinstance(msg, dict) and msg.get("method") == "initialize":
            self._init_line = line

    def note_request(self, line: str) -> None:
        """v1.9 · track a request expecting a reply (has method + id, not
        initialize) so reconnect can re-send it. initialize is replayed via
        _init_line; tracking it here would double-send it on reconnect."""
        try:
            msg = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            return
        if not isinstance(msg, dict) or msg.get("method") == "initialize":
            return
        if msg.get("method") is not None and "id" in msg:
            with self._lock:
                self._pending[msg["id"]] = line

    def note_reply(self, line: str) -> None:
        """v1.9 · a reply (has id + result/error) clears its pending request."""
        try:
            msg = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            return
        if not isinstance(msg, dict):
            return
        if "id" in msg and ("result" in msg or "error" in msg):
            with self._lock:
                self._pending.pop(msg["id"], None)

    def pending_lines(self):
        """v1.9 · snapshot of in-flight request lines (auth already injected)."""
        with self._lock:
            return list(self._pending.values())

    def connect(self, replay: bool = True):
        """(Re)open the cloud socket. On reconnect (replay=True) re-auth by
        replaying the cached initialize and discarding its reply. The very
        first connect uses replay=False — Claude's real initialize authenticates
        it as it flows through normally."""
        s = self._opener()
        if replay and self._init_line:
            try:
                s.sendall((_inject_auth(self._init_line) + "\n").encode("utf-8"))
                _recv_one_line(s)  # swallow duplicate initialize reply
                # v1.9 · handle in-flight requests lost across the drop. Read-only
                # tools are duplicate-safe → silently re-sent (auth already injected).
                # Writes (ingest_obs etc.) have NO cloud-side idempotency (verified
                # 2026-06-23: mcp_server.tool_ingest_obs = timestamped direct file
                # write) → re-sending could duplicate, so we DON'T silently re-send
                # them; we error them back so the client can consciously retry.
                with self._lock:
                    pend = list(self._pending.items())
                lost = []
                for mid, pl in pend:
                    if _line_is_idempotent(pl):
                        s.sendall((pl + "\n").encode("utf-8"))
                    else:
                        lost.append(mid)
                if lost:
                    with self._lock:
                        for mid in lost:
                            self._pending.pop(mid, None)
                    for mid in lost:
                        _write_stdout(_make_rpc_error(
                            mid, -32603,
                            "compass cloud dropped mid-request; non-idempotent write "
                            "not auto-retried on reconnect — re-issue if it did not take effect"))
            except Exception:
                try:
                    s.close()
                except Exception:
                    pass
                raise
        with self._lock:
            self._sock = s
        return s

    def current(self):
        with self._lock:
            return self._sock

    def send(self, line: str) -> None:
        with self._lock:
            s = self._sock
        if s is None:
            raise ConnectionError("cloud link down")
        s.sendall((line + "\n").encode("utf-8"))

    def mark_down(self) -> None:
        with self._lock:
            s, self._sock = self._sock, None
        if s is not None:
            try:
                s.close()
            except Exception:
                pass

    def close(self) -> None:
        self._closed = True
        self.mark_down()


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

    # v3.0.10 · local daemon 9876 requires token (ping exempt)
    if "token" not in daemon_req:
        try:
            with open(os.path.expanduser("~/.claude/.cache/compass_daemon_token"),
                      encoding="utf-8") as _f:
                daemon_req["token"] = _f.read().strip()
        except OSError:
            pass

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


def _rewrite_init_version(line: str) -> str:
    """v2.0 · Claude Code 2.1.x requests protocolVersion 2025-11-25; cloud answers
    2024-11-05 and the client then aborts the connection right after the initialize
    reply (2026-08-24 bridge_cloud.log: no follow-up request, EOF+10053 ~16s later).
    Echo the client-requested version in the initialize RESULT so the client accepts
    the handshake. Cloud still speaks 2024-11-05 semantics; JSON-RPC wire format is
    identical (line-delimited), so this version-string patch is the only divergence."""
    try:
        msg = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return line
    # v2.2 · id-agnostic: Claude Code's initialize request id is not guaranteed 0
    # (2.1.x may use other ids); keying the rewrite on id==0 let the raw cloud
    # reply (2024-11-05 + _eid) through for non-zero ids → client aborts after
    # handshake (2026-08-24 platform report). Detect the initialize RESULT by
    # shape (result.serverInfo), not by id.
    if (isinstance(msg, dict) and "result" in msg
            and isinstance(msg.get("result"), dict)
            and "serverInfo" in msg["result"]):
        # v2.1 · rebuild a spec-clean InitializeResult: client 2.1.239 still aborts
        # with the raw cloud reply even after the version echo (2026-08-24), so
        # besides the version patch we also drop unknown fields (_eid etc.).
        if isinstance(msg["result"], dict):
            cleaned = {
                "protocolVersion": _client_init_version or msg["result"].get("protocolVersion", "2024-11-05"),
                "capabilities": msg["result"].get("capabilities", {"tools": {}}),
                "serverInfo": msg["result"].get("serverInfo", {"name": "nautilus-compass", "version": "2.3.0"}),
            }
            msg["result"] = cleaned
            # v2.2 · ALSO strip protocol-foreign TOP-LEVEL fields (cloud adds
            # "_eid": N beside jsonrpc/id/result). CC 2.1.x is a strict JSON-RPC
            # client and aborts the handshake on unknown top-level members —
            # this, not the version string, is why v2.1 still failed (8/24).
            return json.dumps({"jsonrpc": msg.get("jsonrpc", "2.0"),
                               "id": msg.get("id"),
                               "result": msg["result"]}, ensure_ascii=False)
    return line


# v2.0 · protocolVersion the CLIENT asked for in initialize (parsed by
# note_outgoing; used to patch the cloud's initialize reply — see above).
_client_init_version = None


def _parse_client_init_version(line: str) -> None:
    global _client_init_version
    try:
        msg = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return
    if isinstance(msg, dict) and msg.get("method") == "initialize":
        v = (msg.get("params") or {}).get("protocolVersion")
        if isinstance(v, str):
            _client_init_version = v


def _strip_top_level_eid(line: str) -> str:
    """v3.0.12 · belt-and-braces 剥离顶层 `_eid`(自 8/24 b29d0f7 主循环内联段提取,
    供测试直接钉契约)。协议外顶层字段会让 CC 2.1 严格客户端弃连(f01f9f0 根因)。
    非 JSON / 非对象 / 无 `_eid` 的行原样返回;CJK 用 ensure_ascii=False 保字节。
    """
    if '"_eid"' not in line:
        return line
    try:
        m = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return line
    if not isinstance(m, dict):
        return line
    m.pop("_eid", None)
    return json.dumps(m, ensure_ascii=False)


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


def _pump_in_to_cloud(link: "_CloudLink") -> None:
    """stdin → (local stub | local daemon | inject auth → cloud link) / stdout.

    v1.8: forwards via _CloudLink. A transient cloud drop no longer kills the
    process — link.send() raises, we error that one request with -32603, and the
    cloud→out pump reconnects in the background. Process exits on stdin EOF.
    """
    # read BINARY stdin and decode UTF-8 ourselves · text-mode sys.stdin uses the
    # Windows console code page (gbk) which corrupts CJK into lone surrogates.
    for raw_bytes in sys.stdin.buffer:
        raw = _decode_line(raw_bytes)
        if not raw.strip():
            continue
        line = raw.rstrip("\n")
        _trace("STDIN", line)
        _parse_client_init_version(line)  # v2.0 · capture for init-reply version patch
        link.note_outgoing(line)  # cache initialize so reconnect can replay it
        cloud_up = link.current() is not None
        stub = _try_local_stub(line, cloud_up)
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
        # Local didn't handle it · forward to cloud via the link
        out = _inject_auth(line)
        try:
            link.send(out)
            link.note_request(out)  # v1.9 · track in-flight so reconnect re-sends
            _trace("→CLOUD", out)
        except Exception as e:
            # cloud down or mid-reconnect · do NOT exit · error this one request
            _trace("NO_CLOUD", f"send fail: {e!r}")
            try:
                msg = json.loads(line)
                if isinstance(msg, dict) and "id" in msg:
                    _write_stdout(_make_rpc_error(
                        msg["id"], -32603,
                        "cloud compass unreachable (reconnecting) and local daemon did not handle this request"))
            except json.JSONDecodeError:
                pass
            continue
    _trace("STDIN", "<eof>")
    link.close()  # stops the reconnect pump + closes the socket


def _pump_cloud_to_out(link: "_CloudLink") -> None:
    """cloud link → stdout with auto-reconnect (v1.8).

    Reads the current cloud socket; on EOF/error marks the link down and
    reconnects with exponential backoff (capped 30s), replaying the cached
    initialize. Only exits when the link is closed (stdin EOF). This is what
    lets the bridge survive a tunnel/VM blip without a manual /mcp."""
    import time as _t
    backoff = 1.0
    while not link.is_closed:
        s = link.current()
        if s is None:
            try:
                s = link.connect(replay=True)
                backoff = 1.0
                _trace("RECONNECT", "ok")
                sys.stderr.write(f"mcp_stdio_to_cloud · reconnected {HOST}:{PORT}\n")
            except Exception as e:
                _trace("RECONNECT", f"fail: {e!r} · sleep {backoff}s")
                _t.sleep(backoff)
                backoff = min(backoff * 2, 30.0)
                continue
        buf = b""
        while not link.is_closed:
            try:
                chunk = s.recv(65536)
            except Exception as e:
                _trace("ERR", f"recv fail: {e!r}")
                break
            if not chunk:
                _trace("CLOUD", "<eof>")
                break
            buf += chunk
            while b"\n" in buf:
                cl, buf = buf.split(b"\n", 1)
                if not cl.strip():
                    continue
                _trace("CLOUD→", cl)
                link.note_reply(cl.decode("utf-8", errors="replace"))  # v1.9 · clear pending
                out_line = _rewrite_init_version(cl.decode("utf-8", errors="replace"))
                # v2.2 · belt-and-braces: strip protocol-foreign top-level "_eid"
                # from ANY cloud line (observed on initialize; be safe for all).
                out_line = _strip_top_level_eid(out_line)
                _write_stdout((out_line + "\n").encode("utf-8"))
        link.mark_down()  # socket dead · outer loop reconnects unless closed


def _heartbeat(link: "_CloudLink") -> None:
    """v1.5.5/v1.8 · send empty newline every 60s when idle · prevents TCP
    middlebox or sshd channel timeout from killing a 2-5min idle connection.
    On send failure it just logs — the cloud→out pump owns reconnect."""
    import time as _t
    while not link.is_closed:
        _t.sleep(60)
        s = link.current()
        if s is None:
            continue
        try:
            s.sendall(b"\n")
            _trace("HEARTBEAT", "tick")
        except Exception as e:
            _trace("ERR", f"heartbeat send fail: {e!r}")


def main() -> int:
    # v1.8 · cloud connection is optional AND auto-reconnecting. The bridge no
    # longer exits when the cloud socket drops — the cloud→out pump reconnects in
    # the background (the forward watchdog heals the tunnel within ~5min), so the
    # user no longer needs a manual /mcp after a transient drop.
    link = _CloudLink()
    try:
        link.connect(replay=False)  # first connect · Claude's real initialize authenticates it
        sys.stderr.write(
            f"mcp_stdio_to_cloud · connected {HOST}:{PORT} "
            f"· agent_type={AGENT_TYPE} · mode=local+cloud · auto-reconnect on\n"
        )
    except Exception as e:
        sys.stderr.write(
            f"mcp_stdio_to_cloud · cloud {HOST}:{PORT} unreachable ({e!r})\n"
            f"  · LOCAL-ONLY for now (GPU daemon on :{LOCAL_PORT}) · will auto-reconnect\n"
            f"  · recall/drift_check/thread_recall served locally · cloud tools retry on reconnect\n"
        )

    t_in = threading.Thread(target=_pump_in_to_cloud, args=(link,), daemon=True)
    t_out = threading.Thread(target=_pump_cloud_to_out, args=(link,), daemon=True)
    t_hb = threading.Thread(target=_heartbeat, args=(link,), daemon=True)
    t_in.start()
    t_out.start()
    t_hb.start()
    t_in.join()  # exit when STDIN closes (Claude done) · NOT when cloud drops
    link.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

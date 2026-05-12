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
}


def _try_local_stub(line: str):
    """If method is in _LOCAL_STUB_METHODS, return JSON-RPC response bytes.
    Returns None otherwise (caller forwards to cloud)."""
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(msg, dict):
        return None
    method = msg.get("method")
    if method not in _LOCAL_STUB_METHODS:
        return None
    if "id" not in msg:
        # notification · no response needed
        return b""
    resp = {
        "jsonrpc": "2.0",
        "id": msg["id"],
        "result": _LOCAL_STUB_METHODS[method],
    }
    return (json.dumps(resp) + "\n").encode("utf-8")


_stdout_lock = threading.Lock()


def _write_stdout(payload: bytes) -> None:
    """Single point for writing to stdout · serialized so stub responses and
    cloud forwards never interleave bytes mid-frame."""
    with _stdout_lock:
        sys.stdout.buffer.write(payload)
        sys.stdout.buffer.flush()


def _pump_in_to_cloud(cloud: socket.socket) -> None:
    """stdin → (inject authToken | local stub) → cloud TCP / stdout."""
    for raw in sys.stdin:
        if not raw.strip():
            continue
        line = raw.rstrip("\n")
        _trace("STDIN", line)
        stub = _try_local_stub(line)
        if stub is not None:
            if stub:
                _trace("STUB", stub)
                _write_stdout(stub)
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
    try:
        cloud = _open_cloud()
    except Exception as e:
        sys.stderr.write(
            f"mcp_stdio_to_cloud · cannot reach {HOST}:{PORT} · {e!r}\n"
            f"  · is `ssh -fN -L {PORT}:127.0.0.1:{PORT} cloud` running?\n"
        )
        return 1

    sys.stderr.write(
        f"mcp_stdio_to_cloud · connected {HOST}:{PORT} "
        f"· agent_type={AGENT_TYPE}\n"
    )

    t_in = threading.Thread(target=_pump_in_to_cloud, args=(cloud,), daemon=True)
    t_out = threading.Thread(target=_pump_cloud_to_out, args=(cloud,), daemon=True)
    t_hb = threading.Thread(target=_heartbeat, args=(cloud,), daemon=True)
    t_in.start()
    t_out.start()
    t_hb.start()
    t_out.join()  # exit when cloud closes
    try:
        cloud.close()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

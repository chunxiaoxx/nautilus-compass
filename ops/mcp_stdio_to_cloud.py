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

if not TOKEN:
    sys.stderr.write(
        "mcp_stdio_to_cloud · COMPASS_CLOUD_TOKEN env required\n"
    )
    sys.exit(2)


def _open_cloud() -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10.0)
    s.connect((HOST, PORT))
    return s


def _inject_auth(line: str) -> str:
    """Add authToken to params of any JSON-RPC request from stdin."""
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return line
    if isinstance(msg, dict) and msg.get("method"):
        params = msg.get("params")
        if not isinstance(params, dict):
            params = {}
        params["authToken"] = TOKEN
        msg["params"] = params
    return json.dumps(msg)


def _pump_in_to_cloud(cloud: socket.socket) -> None:
    """stdin → (inject authToken) → cloud TCP."""
    for raw in sys.stdin:
        if not raw.strip():
            continue
        out = _inject_auth(raw.rstrip("\n"))
        try:
            cloud.sendall((out + "\n").encode("utf-8"))
        except Exception as e:
            sys.stderr.write(f"send fail: {e!r}\n")
            return
    # stdin closed · half-close cloud send
    try:
        cloud.shutdown(socket.SHUT_WR)
    except Exception:
        pass


def _pump_cloud_to_out(cloud: socket.socket) -> None:
    """cloud TCP → stdout (line-buffered, raw bytes · bypass platform encoding)."""
    out = sys.stdout.buffer  # write bytes directly · Windows GBK proof
    buf = b""
    while True:
        try:
            chunk = cloud.recv(65536)
        except Exception as e:
            sys.stderr.write(f"recv fail: {e!r}\n")
            return
        if not chunk:
            return
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            if not line.strip():
                continue
            out.write(line + b"\n")
            out.flush()


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
    t_in.start()
    t_out.start()
    t_out.join()  # exit when cloud closes
    try:
        cloud.close()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

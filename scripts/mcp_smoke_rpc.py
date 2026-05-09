"""Smoke-test the nautilus-compass MCP server over raw JSON-RPC.

Supports both transports:
  stdio: spawn mcp_server.py as a subprocess (default · no daemon needed)
  tcp:   dial a running `mcp_server.py --transport tcp` on HOST:PORT

No external deps · no pytest · useful as a sanity check when onboarding a
non-Claude MCP client or bringing up cross-machine A2A.

Usage:
    python scripts/mcp_smoke_rpc.py
    python scripts/mcp_smoke_rpc.py --tool recall --query "last auth change"
    python scripts/mcp_smoke_rpc.py --transport tcp --host host.internal --port 8766 --token $TOK
    python scripts/mcp_smoke_rpc.py --transport tcp --port 8766 --token $TOK --tool drift_check --query "..."

Exit codes:
    0   initialize + tools/list both returned a well-formed JSON-RPC result
    1   handshake failed (transport error, malformed JSON, or non-2.0 reply)
    2   tools/list returned 0 tools — server is up but something is broken
"""
from __future__ import annotations

import argparse
import contextlib
import json
import socket
import subprocess
import sys
from pathlib import Path


class Transport:
    def send_recv(self, msg: dict) -> dict: ...
    def close(self) -> None: ...


class StdioTransport(Transport):
    def __init__(self, server_path: Path) -> None:
        self.proc = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
        )

    def send_recv(self, msg: dict) -> dict:
        assert self.proc.stdin is not None and self.proc.stdout is not None
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError(f"server closed stdout before replying to {msg.get('method')}")
        return json.loads(line)

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self.proc.stdin.close()  # type: ignore[union-attr]
        try:
            self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.kill()


class TcpTransport(Transport):
    def __init__(self, host: str, port: int, timeout: float = 5.0) -> None:
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        self._buf = b""

    def send_recv(self, msg: dict) -> dict:
        self.sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))
        while b"\n" not in self._buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError(f"server closed socket before replying to {msg.get('method')}")
            self._buf += chunk
        line, _, self._buf = self._buf.partition(b"\n")
        return json.loads(line.decode("utf-8"))

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self.sock.close()


def _server_path() -> Path:
    return Path(__file__).resolve().parent.parent / "mcp_server.py"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--transport", choices=["stdio", "tcp"], default="stdio")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8766)
    p.add_argument("--token", default=None,
                   help="Sent as initialize.params.authToken (TCP mode with auth).")
    p.add_argument("--tool", help="Optional: also call tools/call with this tool name")
    p.add_argument("--query", default="smoke test")
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--status", action="store_true",
                   help="Print one-line server/status summary after handshake.")
    p.add_argument("--keepalive", type=float, default=None, metavar="SEC",
                   help="After handshake, send `ping` every SEC seconds. "
                        "Prints round-trip latency. Exits non-zero on any timeout / closed socket.")
    p.add_argument("--keepalive-timeout", type=float, default=3.0,
                   help="Max seconds to wait for each ping reply (default 3).")
    p.add_argument("--keepalive-limit", type=int, default=0,
                   help="Stop after N pings (default 0 = run until Ctrl-C).")
    args = p.parse_args()

    if args.transport == "stdio":
        server = _server_path()
        if not server.exists():
            print(f"ERR · mcp_server.py not found at {server}", file=sys.stderr)
            return 1
        t: Transport = StdioTransport(server)
    else:
        try:
            t = TcpTransport(args.host, args.port)
        except (ConnectionRefusedError, OSError) as e:
            print(f"ERR · cannot connect to {args.host}:{args.port} · {e}", file=sys.stderr)
            return 1

    try:
        init_params: dict = {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "mcp-smoke-rpc", "version": "0.2.0"},
        }
        if args.token:
            init_params["authToken"] = args.token

        init = t.send_recv({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": init_params})
        if init.get("jsonrpc") != "2.0" or "result" not in init:
            print(f"ERR · initialize failed: {init}", file=sys.stderr)
            return 1
        server_info = init["result"].get("serverInfo", {})
        print(f"OK  · initialize → {server_info.get('name')} v{server_info.get('version')} via {args.transport}")

        listing = t.send_recv({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = listing.get("result", {}).get("tools", [])
        if not tools:
            print("ERR · tools/list returned 0 tools", file=sys.stderr)
            return 2
        names = [tt["name"] for tt in tools]
        print(f"OK  · tools/list → {len(tools)} tools: {', '.join(names)}")

        if args.status:
            st = t.send_recv({"jsonrpc": "2.0", "id": 10, "method": "server/status"})
            r = st.get("result", {})
            print(f"OK  · server/status → "
                  f"uptime={r.get('uptime_seconds')}s "
                  f"conns active={r.get('active_connections')}/total={r.get('total_connections')} "
                  f"auth_fail={r.get('auth_failures')} "
                  f"msgs={r.get('messages_handled')}")

        if args.tool:
            if args.tool not in names:
                print(f"ERR · requested tool '{args.tool}' not in {names}", file=sys.stderr)
                return 1
            call_args: dict = {}
            if args.tool == "drift_check":
                call_args["prompt"] = args.query
            elif args.tool in {"recall", "session_search"}:
                call_args["query"] = args.query
                call_args["top_k"] = args.top_k
            reply = t.send_recv({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                 "params": {"name": args.tool, "arguments": call_args}})
            if "error" in reply:
                err = reply["error"]
                print(f"WARN· tools/call({args.tool}) → error {err.get('code')}: {err.get('message')}")
            else:
                content = reply.get("result", {}).get("content", [])
                text = content[0]["text"] if content else "(empty)"
                print(f"OK  · tools/call({args.tool}) → {text[:200]}...")

        if args.keepalive is not None:
            # Enter keepalive loop · each iteration sends `ping`, measures RTT, sleeps.
            # Bail on any exception (timeout, closed socket, non-2.0 reply).
            import time as _time
            # Tighten socket timeout for TCP so hung server trips quickly.
            if isinstance(t, TcpTransport):
                t.sock.settimeout(args.keepalive_timeout)
            rid = 1000
            n = 0
            try:
                while True:
                    rid += 1
                    n += 1
                    t0 = _time.perf_counter()
                    try:
                        r = t.send_recv({"jsonrpc": "2.0", "id": rid, "method": "ping"})
                    except Exception as e:
                        dt = (_time.perf_counter() - t0) * 1000
                        print(f"ERR · ping#{n} after {dt:.0f}ms · {type(e).__name__}: {e}",
                              file=sys.stderr)
                        return 1
                    dt_ms = (_time.perf_counter() - t0) * 1000
                    if r.get("result") != {}:
                        print(f"ERR · ping#{n} unexpected reply: {r}", file=sys.stderr)
                        return 1
                    print(f"OK  · ping#{n} rtt={dt_ms:.1f}ms")
                    if args.keepalive_limit and n >= args.keepalive_limit:
                        return 0
                    _time.sleep(args.keepalive)
            except KeyboardInterrupt:
                print(f"\nOK  · keepalive stopped after {n} pings")
                return 0

        return 0
    finally:
        t.close()


if __name__ == "__main__":
    sys.exit(main())

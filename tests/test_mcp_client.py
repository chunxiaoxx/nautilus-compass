"""v1.0 · MCPClient tests (Task #46).

Covers:
  - basic handshake + tool calls against a live TCP server
  - auth failure raises MCPClientError (not a silent retry loop)
  - reconnect path: kill server mid-session, restart, next call succeeds
  - backoff telemetry (reconnect_count, last_reconnect_reason) increments
"""
from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from mcp_client import MCPClient, MCPClientError  # noqa: E402


def _free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _spawn_server(port: int, token: str | None = None) -> subprocess.Popen:
    cmd = [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
           "--transport", "tcp", "--host", "127.0.0.1", "--port", str(port)]
    if token is not None:
        cmd += ["--token", token]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    # Generous readiness deadline. Idle cold-start is ~0.7-1.2s, but under full-suite
    # load / cold import cache the first spawn can take several seconds — a tight 3s
    # deadline flaked (~50% on a loaded run). 15s only waits longer in the slow case;
    # the happy path returns immediately on "listening on". readline() blocks until a
    # line or EOF, so a server that dies before announcing breaks out via EOF below.
    deadline = time.time() + 15.0
    captured: list[bytes] = []
    while time.time() < deadline:
        line = proc.stderr.readline() if proc.stderr else b""
        if not line:  # EOF → server exited before announcing readiness
            break
        captured.append(line)
        if b"listening on" in line:
            return proc
    proc.kill()
    rc = proc.poll()
    tail = b"".join(captured[-10:]).decode("utf-8", "replace")
    raise RuntimeError(
        f"server never announced readiness within 15s (exit={rc}); stderr tail:\n{tail}")


@contextlib.contextmanager
def _server(token: str | None = None):
    port = _free_port()
    proc = _spawn_server(port, token)
    try:
        yield port, proc
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_client_basic_handshake_and_tools_list():
    with _server() as (port, _):
        with MCPClient(port=port) as c:
            tools = c.list_tools()
            names = [t["name"] for t in tools]
            assert len(tools) >= 7
            assert {"recall", "drift_check", "ingest_obs"} <= set(names)


def test_client_ping_returns_latency_ms():
    with _server() as (port, _):
        with MCPClient(port=port) as c:
            rtt = c.ping()
            assert rtt >= 0
            assert rtt < 1000  # loopback should be << 1s


def test_client_status_returns_counters():
    with _server() as (port, _):
        with MCPClient(port=port) as c:
            c.ping()
            c.list_tools()
            st = c.status()
            assert st["server"]["name"] == "nautilus-compass"
            assert st["total_connections"] >= 1
            assert st["messages_handled"] >= 2  # ping + list at least


def test_client_bad_token_raises():
    with _server(token="correct") as (port, _):
        client = MCPClient(port=port, token="WRONG", max_retries=0)
        with pytest.raises(MCPClientError) as ei:
            client.__enter__()
        assert "unauthorized" in str(ei.value).lower() or "-32001" in str(ei.value)


def test_client_reconnects_after_server_restart():
    """Kill the server mid-session · restart it on the same port · next call succeeds."""
    port = _free_port()
    srv1 = _spawn_server(port)
    client = MCPClient(port=port, max_retries=10, backoff_base_s=0.05, backoff_max_s=0.3)
    try:
        client.__enter__()
        # Warm call · proves connection works.
        assert client.list_tools()
        baseline = client.reconnect_count

        # Yank the server out from under the client.
        srv1.kill()
        srv1.wait(timeout=2)

        # Bring up a fresh server on the same port. Small delay to let TCP
        # release the socket cleanly.
        time.sleep(0.2)
        srv2 = _spawn_server(port)
        try:
            # This call must transparently: detect the broken socket, reconnect,
            # re-run initialize, replay the request.
            tools = client.list_tools()
            assert len(tools) >= 7
            assert client.reconnect_count > baseline
            assert client.last_reconnect_reason is not None
        finally:
            srv2.terminate()
            try:
                srv2.wait(timeout=2)
            except subprocess.TimeoutExpired:
                srv2.kill()
    finally:
        client.close()


def test_client_gives_up_after_max_retries_when_server_gone_forever():
    port = _free_port()
    srv = _spawn_server(port)
    client = MCPClient(port=port, max_retries=2, backoff_base_s=0.05, backoff_max_s=0.1,
                       connect_timeout_s=0.3)
    try:
        client.__enter__()
        client.list_tools()  # warm
        srv.kill()
        srv.wait(timeout=2)
        t0 = time.perf_counter()
        with pytest.raises(MCPClientError) as ei:
            client.list_tools()
        elapsed = time.perf_counter() - t0
        assert "exhausted" in str(ei.value)
        # Bounded mainly by connect_timeout_s × retries + backoffs. Not a
        # strict latency test · just ensures we don't hang forever.
        assert elapsed < 5.0
    finally:
        client.close()

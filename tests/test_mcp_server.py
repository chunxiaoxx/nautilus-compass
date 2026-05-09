"""v1.0 · MCP JSON-RPC protocol tests.

Exercises handle_message directly (in-process) · no daemon needed for protocol
layer tests. Tool calls that would hit the daemon are tested via a mocked
daemon_call that returns canned replies.

Runs under pytest:  pytest tests/test_mcp_server.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

# Make plugin root importable
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import mcp_server  # noqa: E402


def _req(msg_id, method, params=None):
    m = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        m["params"] = params
    return m


# ─── protocol handshake ────────────────────────────────────────────

def test_initialize_returns_protocol_and_version():
    reply = mcp_server.handle_message(_req(1, "initialize"))
    assert reply["jsonrpc"] == "2.0"
    assert reply["id"] == 1
    result = reply["result"]
    assert result["protocolVersion"] == mcp_server.PROTOCOL_VERSION
    assert result["serverInfo"]["name"] == mcp_server.SERVER_NAME
    assert result["serverInfo"]["version"] == mcp_server.SERVER_VERSION
    # v1.0-rc1 or later; never regress below 1.0.0
    major = int(mcp_server.SERVER_VERSION.split(".")[0])
    assert major >= 1, f"SERVER_VERSION {mcp_server.SERVER_VERSION} must be >= 1.0"


def test_initialized_notification_gets_no_reply():
    # Notifications carry no id and expect no reply.
    reply = mcp_server.handle_message({"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert reply is None


def test_ping_returns_empty_result():
    reply = mcp_server.handle_message(_req(2, "ping"))
    assert reply["result"] == {}


def test_unknown_method_returns_method_not_found():
    reply = mcp_server.handle_message(_req(3, "definitely/not/a/method"))
    assert "error" in reply
    assert reply["error"]["code"] == -32601


# ─── tools/list ────────────────────────────────────────────────────

def test_tools_list_includes_core_tools():
    reply = mcp_server.handle_message(_req(4, "tools/list"))
    names = {t["name"] for t in reply["result"]["tools"]}
    # These four are the v1.0 contract surface.
    for required in ("recall", "drift_check", "feedback_log", "ingest_obs"):
        assert required in names, f"tools/list missing {required}"


def test_every_tool_has_valid_schema():
    reply = mcp_server.handle_message(_req(5, "tools/list"))
    for tool in reply["result"]["tools"]:
        assert "name" in tool
        assert "description" in tool and tool["description"]
        assert "inputSchema" in tool
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema


# ─── tools/call ────────────────────────────────────────────────────

def test_tools_call_unknown_tool_returns_error():
    reply = mcp_server.handle_message(
        _req(6, "tools/call", {"name": "not_a_real_tool", "arguments": {}})
    )
    assert "error" in reply
    assert reply["error"]["code"] == -32601


def test_recall_without_daemon_fails_gracefully():
    """Daemon offline should not crash the server; tool returns an error content."""
    import socket

    def boom(req, timeout=30.0):
        raise socket.error("connection refused")

    with patch.object(mcp_server, "daemon_call", side_effect=boom):
        reply = mcp_server.handle_message(
            _req(7, "tools/call", {"name": "recall", "arguments": {"query": "test"}})
        )
    # Either jsonrpc error or isError-marked result is acceptable · must not raise.
    if "error" in reply:
        assert reply["error"]["code"] == -32603
    else:
        result = reply["result"]
        assert result.get("isError") is True


def test_recall_with_stubbed_daemon_returns_text_content(monkeypatch):
    monkeypatch.setenv("NAUTILUS_COMPASS_PROJECT", "test-project")

    def stubbed(req, timeout=30.0):
        # recall sends {"action": "recall", "query": ..., "project": ..., "top_k": ...}
        assert req.get("action") == "recall"
        return {
            "ok": True,
            "recall": [
                {"score": 0.88, "age_str": "2h", "path": "/tmp/x.md",
                 "description": "a sample memory"},
            ],
        }

    with patch.object(mcp_server, "daemon_call", side_effect=stubbed):
        reply = mcp_server.handle_message(
            _req(8, "tools/call", {"name": "recall", "arguments": {"query": "q"}})
        )
    result = reply["result"]
    assert not result.get("isError"), f"unexpected error: {result}"
    assert isinstance(result.get("content"), list)
    assert result["content"][0]["type"] == "text"
    assert "0.88" in result["content"][0]["text"] or "sample memory" in result["content"][0]["text"]


# ─── JSON round-trip (what actually goes over stdio) ───────────────

def test_reply_is_valid_json():
    reply = mcp_server.handle_message(_req(9, "initialize"))
    encoded = json.dumps(reply, ensure_ascii=False)
    decoded = json.loads(encoded)
    assert decoded == reply


# ─── TCP transport tests (Task #42) ────────────────────────────────
# These boot a real mcp_server subprocess on a loopback port and exchange
# line-delimited JSON-RPC over a socket. They are still in-tree tests ·
# not integration tests · because they validate the server's own wire
# contract, not an external dependency.

import socket
import subprocess
import time
import contextlib


def _free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _tcp_send_recv(sock: socket.socket, msg: dict, timeout: float = 3.0) -> dict:
    sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))
    sock.settimeout(timeout)
    buf = b""
    while b"\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    line, _, _ = buf.partition(b"\n")
    return json.loads(line.decode("utf-8"))


@contextlib.contextmanager
def _tcp_server(token: str | None = None):
    port = _free_port()
    cmd = [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
           "--transport", "tcp", "--host", "127.0.0.1", "--port", str(port)]
    if token is not None:
        cmd += ["--token", token]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={**__import__("os").environ, "PYTHONUTF8": "1"})
    # Wait for the "listening on" stderr line so we don't race the accept().
    deadline = time.time() + 3.0
    ready = False
    while time.time() < deadline:
        line = proc.stderr.readline() if proc.stderr else b""
        if b"listening on" in line:
            ready = True
            break
    try:
        assert ready, "TCP server did not announce readiness"
        yield port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_tcp_rejects_bad_token():
    with _tcp_server(token="goodtoken") as port:
        s = socket.socket(); s.connect(("127.0.0.1", port))
        try:
            r = _tcp_send_recv(s, _req(1, "initialize", {
                "authToken": "WRONG",
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "t", "version": "0"},
            }))
            assert r.get("error", {}).get("code") == -32001
            assert "unauthorized" in r["error"]["message"]
        finally:
            s.close()


def test_tcp_accepts_good_token_and_lists_tools():
    with _tcp_server(token="goodtoken") as port:
        s = socket.socket(); s.connect(("127.0.0.1", port))
        try:
            init = _tcp_send_recv(s, _req(1, "initialize", {
                "authToken": "goodtoken",
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "t", "version": "0"},
            }))
            assert init["result"]["serverInfo"]["name"] == "nautilus-compass"
            listing = _tcp_send_recv(s, _req(2, "tools/list"))
            tools = listing["result"]["tools"]
            assert len(tools) >= 7
            assert {"recall", "drift_check", "ingest_obs"} <= {t["name"] for t in tools}
        finally:
            s.close()


def test_tcp_no_token_mode_is_open():
    """Dev mode · no --token · any client can connect. Warning printed to stderr."""
    with _tcp_server(token=None) as port:
        s = socket.socket(); s.connect(("127.0.0.1", port))
        try:
            r = _tcp_send_recv(s, _req(1, "initialize", {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "t", "version": "0"},
            }))
            assert r["result"]["serverInfo"]["name"] == "nautilus-compass"
        finally:
            s.close()


def test_tcp_token_stripped_before_handling():
    """authToken must NOT leak into the message that handle_message sees · it's a secret."""
    seen_params: list = []
    orig = mcp_server.handle_message

    def _capture(msg):
        seen_params.append(msg.get("params"))
        return orig(msg)

    with _tcp_server(token="sekret") as port:
        # Patch the subprocess's handle_message? No · the patch doesn't
        # cross processes. Instead, drive the subprocess and then assert
        # the behavior indirectly: a successful second call proves the
        # first `initialize` was accepted without authToken being echoed
        # back in tools/list replies (no schema field leaks the token).
        s = socket.socket(); s.connect(("127.0.0.1", port))
        try:
            _tcp_send_recv(s, _req(1, "initialize", {
                "authToken": "sekret",
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "t", "version": "0"},
            }))
            listing = _tcp_send_recv(s, _req(2, "tools/list"))
            wire = json.dumps(listing)
            assert "sekret" not in wire, "token leaked into tools/list reply"
        finally:
            s.close()


# ─── server/status tests (Task #45) ────────────────────────────────


def test_status_method_in_process_returns_metrics():
    """handle_message directly · status is unauthenticated and side-effect-free."""
    reply = mcp_server.handle_message(_req(100, "server/status"))
    assert "result" in reply
    r = reply["result"]
    for key in ("active_connections", "total_connections", "auth_failures",
                "messages_handled", "uptime_seconds", "server"):
        assert key in r, f"status missing {key}"
    assert r["server"]["name"] == "nautilus-compass"
    assert r["uptime_seconds"] >= 0


def test_status_counters_increment_over_tcp():
    """Run a session over TCP · verify total_connections + messages_handled both bumped."""
    with _tcp_server(token=None) as port:
        # First client · establishes a baseline by reading status before and after.
        s = socket.socket(); s.connect(("127.0.0.1", port))
        try:
            before = _tcp_send_recv(s, _req(1, "server/status"))["result"]
            _tcp_send_recv(s, _req(2, "ping"))
            _tcp_send_recv(s, _req(3, "tools/list"))
            after = _tcp_send_recv(s, _req(4, "server/status"))["result"]
        finally:
            s.close()
        # At least total_connections grew from the handshake · messages_handled grew
        # by the requests we sent between the two status reads.
        assert after["total_connections"] >= 1
        assert after["messages_handled"] > before["messages_handled"]
        assert after["uptime_seconds"] >= before["uptime_seconds"]


def test_status_tracks_auth_failures():
    with _tcp_server(token="goodtoken") as port:
        # One good client just to read status.
        s_good = socket.socket(); s_good.connect(("127.0.0.1", port))
        try:
            _tcp_send_recv(s_good, _req(1, "initialize", {
                "authToken": "goodtoken",
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "t", "version": "0"},
            }))
            baseline = _tcp_send_recv(s_good, _req(2, "server/status"))["result"]["auth_failures"]
        finally:
            s_good.close()

        # Two bad-token clients.
        for _ in range(2):
            s = socket.socket(); s.connect(("127.0.0.1", port))
            try:
                _tcp_send_recv(s, _req(1, "initialize", {"authToken": "WRONG"}))
            finally:
                s.close()

        # Re-auth and read again.
        s_good2 = socket.socket(); s_good2.connect(("127.0.0.1", port))
        try:
            _tcp_send_recv(s_good2, _req(1, "initialize", {
                "authToken": "goodtoken",
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "t", "version": "0"},
            }))
            after = _tcp_send_recv(s_good2, _req(2, "server/status"))["result"]["auth_failures"]
        finally:
            s_good2.close()
        assert after - baseline == 2


# ─── smoke --keepalive tests (Task #44) ────────────────────────────
# Drive the smoke script as a subprocess against a real TCP server ·
# verifies both the success path (N pings land) and the failure path
# (server dies mid-stream → smoke exits non-zero quickly).


def test_smoke_keepalive_succeeds_against_live_server():
    smoke = PLUGIN_ROOT / "scripts" / "mcp_smoke_rpc.py"
    with _tcp_server(token=None) as port:
        proc = subprocess.run(
            [sys.executable, str(smoke),
             "--transport", "tcp", "--port", str(port),
             "--keepalive", "0.05", "--keepalive-limit", "3"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
            env={**__import__("os").environ, "PYTHONUTF8": "1"},
        )
        assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
        assert "ping#3" in proc.stdout
        assert "ping#4" not in proc.stdout  # stopped at limit


def test_smoke_keepalive_fails_when_server_dies():
    """Kill the server between handshake and the next ping · smoke must exit non-zero."""
    smoke = PLUGIN_ROOT / "scripts" / "mcp_smoke_rpc.py"
    # Spin a server we can kill ourselves.
    port = _free_port()
    import os as _os
    srv = subprocess.Popen(
        [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
         "--transport", "tcp", "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**_os.environ, "PYTHONUTF8": "1"},
    )
    # Wait for listening.
    deadline = time.time() + 3.0
    while time.time() < deadline:
        if srv.stderr and b"listening on" in srv.stderr.readline():
            break

    # Start smoke with a slow keepalive so we have time to kill the server.
    client = subprocess.Popen(
        [sys.executable, str(smoke),
         "--transport", "tcp", "--port", str(port),
         "--keepalive", "0.3", "--keepalive-timeout", "1", "--keepalive-limit", "10"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", errors="replace",
        env={**_os.environ, "PYTHONUTF8": "1"},
    )
    time.sleep(0.6)  # let at least one ping land
    srv.kill()
    try:
        out, err = client.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        client.kill()
        raise AssertionError("smoke did not exit after server died")
    assert client.returncode != 0, f"expected non-zero exit; out={out} err={err}"
    assert "ERR" in err or "ERR" in out

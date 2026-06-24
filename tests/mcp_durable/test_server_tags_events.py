"""Task 2 · TCP server outbound frames carry a monotonic EventStore `_eid`.

Boots a real mcp_server subprocess on a loopback port in dev/no-auth mode
(``token_table=None``), drives a raw socket through ``initialize`` + a couple
of simple methods, and asserts every server→client frame is tagged with an
integer ``_eid`` that strictly increases across frames.

The stdio path stays untagged (covered by existing tests not seeing `_eid`);
this test only pins the TCP wire contract that Last-Event-ID replay (Task 3)
will build on.
"""
from __future__ import annotations

import contextlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


def _req(msg_id, method, params=None):
    m = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        m["params"] = params
    return m


def _free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _send_recv(sock: socket.socket, msg: dict, timeout: float = 3.0) -> dict:
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
def _tcp_server():
    """Dev/no-auth TCP server (token_table=None) on an ephemeral port."""
    port = _free_port()
    cmd = [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
           "--transport", "tcp", "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={**os.environ, "PYTHONUTF8": "1"})
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


def test_tcp_server_frames_carry_strictly_increasing_eid():
    with _tcp_server() as port:
        s = socket.socket(); s.connect(("127.0.0.1", port))
        try:
            frames = [
                _send_recv(s, _req(1, "initialize", {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "t", "version": "0"},
                })),
                _send_recv(s, _req(2, "ping")),
                _send_recv(s, _req(3, "tools/list")),
            ]
        finally:
            s.close()

        # Every server frame must carry an integer _eid.
        for fr in frames:
            assert "_eid" in fr, f"frame missing _eid: {fr}"
            assert isinstance(fr["_eid"], int), f"_eid not int: {fr['_eid']!r}"
            assert not isinstance(fr["_eid"], bool)

        eids = [fr["_eid"] for fr in frames]
        # Strictly increasing across frames (EventStore assigns 1,2,3,...).
        assert eids == sorted(eids)
        assert len(set(eids)) == len(eids), f"duplicate _eids: {eids}"
        assert all(b > a for a, b in zip(eids, eids[1:])), f"not strictly increasing: {eids}"

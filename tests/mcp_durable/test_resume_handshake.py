"""Task 3 · session-scoped EventStore registry + Last-Event-ID resume.

A per-CONNECTION EventStore dies with the connection, so on reconnect there is
nothing to replay. Task 3 moves the store to be SESSION-scoped: kept in a
process-global registry keyed by session identity, looked up at `initialize`
time, and surviving transport drops. The `initialize` message may carry
`params.sessionId` (dev/no-auth key) and `params.lastEventId` (resume marker).

These tests boot a real mcp_server subprocess in dev/no-auth mode (token_table
is None) on a loopback port, reusing the harness shape from
test_server_tags_events.py, then exercise reconnect-and-resume.
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
    """Send one frame, read exactly one reply frame (one line)."""
    sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))
    return _recv_one(sock, timeout)


def _recv_one(sock: socket.socket, timeout: float = 3.0, _buf=None) -> dict:
    """Read a single line-delimited JSON frame off the socket."""
    sock.settimeout(timeout)
    buf = b""
    while b"\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    line, _, _ = buf.partition(b"\n")
    return json.loads(line.decode("utf-8"))


def _recv_n(sock: socket.socket, n: int, timeout: float = 3.0) -> list[dict]:
    """Read exactly n line-delimited JSON frames (handles multiple per recv)."""
    sock.settimeout(timeout)
    frames: list[dict] = []
    buf = b""
    while len(frames) < n:
        while b"\n" in buf and len(frames) < n:
            line, buf = buf.split(b"\n", 1)
            line = line.strip()
            if line:
                frames.append(json.loads(line.decode("utf-8")))
        if len(frames) >= n:
            break
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return frames


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


def _connect(port: int) -> socket.socket:
    s = socket.socket()
    s.connect(("127.0.0.1", port))
    return s


def test_resume_replays_missed_frames():
    """Reconnect with same sessionId + lastEventId=k replays frames _eid > k.

    Replayed frames keep their ORIGINAL _eid (not renumbered) and arrive in
    ascending order BEFORE the initialize reply (which carries resumed=true).
    """
    with _tcp_server() as port:
        s1 = _connect(port)
        try:
            init = _send_recv(s1, _req(1, "initialize", {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "t", "version": "0"},
                "sessionId": "s1",
            }))
            # Drive a few methods so the store accumulates frames.
            f2 = _send_recv(s1, _req(2, "ping"))
            f3 = _send_recv(s1, _req(3, "tools/list"))
            f4 = _send_recv(s1, _req(4, "ping"))
            seen = [init, f2, f3, f4]
            eids = [fr["_eid"] for fr in seen]
            assert eids == sorted(eids) and len(set(eids)) == len(eids)
        finally:
            s1.close()

        # k = second-to-last observed id · expect frames with _eid > k replayed.
        k = eids[-2]
        expected_replay = [e for e in eids if e > k]
        assert expected_replay, "test needs at least one frame past k"

        s2 = _connect(port)
        try:
            # Server first writes the missed frames RAW, then the init reply.
            n_total = len(expected_replay) + 1
            frames = _recv_after_send(s2, _req(1, "initialize", {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "t", "version": "0"},
                "sessionId": "s1",
                "lastEventId": k,
            }), n_total)
        finally:
            s2.close()

        # Last frame is the initialize reply.
        init_reply = frames[-1]
        replayed = frames[:-1]
        replayed_eids = [fr["_eid"] for fr in replayed]
        assert replayed_eids == expected_replay, (
            f"replayed {replayed_eids} != expected {expected_replay}")
        # Ascending, original ids (not renumbered).
        assert replayed_eids == sorted(replayed_eids)
        assert init_reply.get("id") == 1
        assert init_reply["result"].get("resumed") is True


def _recv_after_send(sock, msg, n, timeout=3.0):
    sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))
    return _recv_n(sock, n, timeout)


def test_stale_last_event_id_resumed_false():
    """A lastEventId on a brand-new session key → resumed=false, no replay.

    The store for "fresh-key" is created fresh at initialize; the client claims
    to have seen event 999 that this server never emitted → identity mismatch →
    full-resync. No replay frames precede the init reply.
    """
    with _tcp_server() as port:
        s = _connect(port)
        try:
            reply = _send_recv(s, _req(1, "initialize", {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "t", "version": "0"},
                "sessionId": "fresh-key",
                "lastEventId": 999,
            }))
        finally:
            s.close()
        # The very first frame back must BE the init reply (no replay frames).
        assert reply.get("id") == 1
        assert reply["result"].get("resumed") is False


def test_no_last_event_id_is_fresh():
    """Plain initialize (no lastEventId) → reply has no `resumed` key."""
    with _tcp_server() as port:
        s = _connect(port)
        try:
            reply = _send_recv(s, _req(1, "initialize", {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "t", "version": "0"},
                "sessionId": "plain",
            }))
        finally:
            s.close()
        assert reply.get("id") == 1
        assert "resumed" not in reply["result"]
        assert "_eid" in reply  # still tagged


def test_different_session_is_isolated():
    """s2 never receives s1's frames on resume."""
    with _tcp_server() as port:
        # Populate s1.
        s1 = _connect(port)
        try:
            _send_recv(s1, _req(1, "initialize", {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "t", "version": "0"},
                "sessionId": "s1",
            }))
            _send_recv(s1, _req(2, "ping"))
            _send_recv(s1, _req(3, "ping"))
        finally:
            s1.close()

        # New session s2 resumes with a lastEventId — must NOT get s1's frames.
        s2 = _connect(port)
        try:
            reply = _send_recv(s2, _req(1, "initialize", {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "t", "version": "0"},
                "sessionId": "s2",
                "lastEventId": 1,
            }))
        finally:
            s2.close()
        # s2 is a fresh key → resumed=false and the first frame is the reply.
        assert reply.get("id") == 1
        assert reply["result"].get("resumed") is False

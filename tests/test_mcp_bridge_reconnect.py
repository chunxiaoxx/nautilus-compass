"""Bridge auto-reconnect · _CloudLink unit tests (零网络·注入 fake opener).

Root cause (read-confirmed 2026-06-18): mcp_stdio_to_cloud connects once in
main(); when the cloud TCP socket drops (SSH tunnel death / VM hiccup), the
cloud→out pump returns → process exits → Claude Code sees MCP disconnected →
user must run /mcp. The watchdog (compass_forward_watchdog.ps1) already heals
the tunnel/service within 5min, but it can't resurrect the bridge subprocess.

Cloud-side constraint (read from mcp_server.py _serve): every NEW connection
must send `initialize` + valid authToken as its FIRST message, else the server
replies -32001 and closes. So on reconnect the bridge MUST replay the cached
initialize and swallow its (duplicate) reply before resuming forwarding.

These tests pin the _CloudLink state machine that delivers that.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
os.environ.setdefault("COMPASS_CLOUD_TOKEN", "test-dummy-token")
bridge = importlib.import_module("ops.mcp_stdio_to_cloud")


class _FakeSock:
    """Records sends; serves canned recv replies; tracks close."""

    def __init__(self, replies: list[bytes] | None = None) -> None:
        self.sent: list[bytes] = []
        self._replies = list(replies or [])
        self.closed = False

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def recv(self, n: int) -> bytes:
        return self._replies.pop(0) if self._replies else b""

    def settimeout(self, *_a, **_k) -> None:
        pass

    def close(self) -> None:
        self.closed = True


def _opener_factory(socks: list[_FakeSock]):
    """Returns an opener() that hands out the queued fake sockets in order."""
    seq = list(socks)

    def _open():
        if not seq:
            raise ConnectionError("no more sockets")
        return seq.pop(0)
    return _open


def test_cloudlink_class_exists():
    assert hasattr(bridge, "_CloudLink")


def test_send_raises_when_no_socket():
    link = bridge._CloudLink(opener=_opener_factory([]))
    try:
        link.send('{"x":1}')
        assert False, "expected ConnectionError when link has no socket"
    except (ConnectionError, OSError):
        pass


def test_initial_connect_does_not_replay_init():
    """First connect = the real Claude initialize flows through normally;
    the link must NOT inject its own initialize on the very first connect."""
    s = _FakeSock()
    link = bridge._CloudLink(opener=_opener_factory([s]))
    link.note_outgoing('{"jsonrpc":"2.0","id":0,"method":"initialize","params":{}}')
    link.connect(replay=False)
    assert s.sent == []  # nothing replayed on first connect


def test_reconnect_replays_cached_init_and_swallows_reply():
    """On reconnect the link sends the cached initialize (authToken injected)
    and consumes exactly one reply line so the duplicate never reaches stdout."""
    init = '{"jsonrpc":"2.0","id":7,"method":"initialize","params":{}}'
    reply = (json.dumps({"jsonrpc": "2.0", "id": 7, "result": {}}) + "\n").encode()
    s = _FakeSock(replies=[reply])
    link = bridge._CloudLink(opener=_opener_factory([s]))
    link.note_outgoing(init)
    link.connect(replay=True)
    # exactly one frame sent = the replayed initialize, with authToken injected
    assert len(s.sent) == 1
    sent = json.loads(s.sent[0].decode().strip())
    assert sent.get("method") == "initialize"
    assert sent.get("params", {}).get("authToken")  # _inject_auth ran


def test_note_outgoing_caches_initialize_only():
    link = bridge._CloudLink(opener=_opener_factory([]))
    link.note_outgoing('{"method":"tools/call","id":1}')
    assert link.init_line is None  # non-initialize ignored
    link.note_outgoing('{"method":"initialize","id":2}')
    assert link.init_line is not None
    # first initialize wins · later ones don't clobber
    link.note_outgoing('{"method":"initialize","id":3}')
    assert '"id":2' in link.init_line


def test_mark_down_clears_socket_so_send_raises():
    s = _FakeSock()
    link = bridge._CloudLink(opener=_opener_factory([s]))
    link.connect(replay=False)
    link.send('{"a":1}')  # ok while up
    assert s.sent  # delivered
    link.mark_down()
    try:
        link.send('{"a":2}')
        assert False, "expected raise after mark_down"
    except (ConnectionError, OSError):
        pass


def test_close_marks_closed():
    link = bridge._CloudLink(opener=_opener_factory([_FakeSock()]))
    assert not link.is_closed
    link.close()
    assert link.is_closed


# ── v1.9 · in-flight request durability ───────────────────────────────
# Gap: link.send() puts a request on the wire; if cloud drops AFTER receiving
# but BEFORE replying, v1.8 only replays initialize on reconnect → that
# request's reply is lost forever and Claude waits on a dead id. v1.9 tracks
# pending requests and re-sends them after the initialize replay.

def test_note_request_tracks_method_with_id():
    link = bridge._CloudLink(opener=_opener_factory([]))
    link.note_request('{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{}}')
    assert link.pending_lines()  # one in-flight


def test_note_request_ignores_initialize():
    # initialize is replayed via _init_line, not pending (else double-sent on reconnect)
    link = bridge._CloudLink(opener=_opener_factory([]))
    link.note_request('{"jsonrpc":"2.0","id":0,"method":"initialize","params":{}}')
    assert link.pending_lines() == []


def test_note_request_ignores_notification_without_id():
    link = bridge._CloudLink(opener=_opener_factory([]))
    link.note_request('{"jsonrpc":"2.0","method":"notifications/initialized"}')
    assert link.pending_lines() == []

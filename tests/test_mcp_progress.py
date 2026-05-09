"""notifications/progress + cancelled · Task #58.

Unit tests hit handle_message directly (no socket) · e2e tests drive
the full TCP transport through MCPClient to confirm frames actually
flow over the wire and reach the user callback in order.
"""
from __future__ import annotations

import socket
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mcp_server
from mcp_server import handle_message, tool_long_task
from mcp_client import MCPClient


# ─── server-side unit tests ───────────────────────────────────────

def test_long_task_default_3_frames():
    fired = []
    reply = tool_long_task({}, emit=lambda **kw: fired.append(kw),
                           is_cancelled=lambda: False)
    assert len(fired) == 3
    assert [f["progress"] for f in fired] == [1, 2, 3]
    assert all(f["total"] == 3 for f in fired)
    assert "done" in reply["content"][0]["text"]


def test_long_task_respects_cancellation_mid_run():
    fired = []
    # Cancel after 2nd frame.
    counter = {"n": 0}

    def _is_cancelled():
        counter["n"] += 1
        return counter["n"] > 2

    reply = tool_long_task({"steps": 10}, emit=lambda **kw: fired.append(kw),
                           is_cancelled=_is_cancelled)
    assert len(fired) == 2
    assert "cancelled" in reply["content"][0]["text"]


def test_long_task_steps_clamped():
    reply = tool_long_task({"steps": 999}, emit=None, is_cancelled=None)
    assert "20" in reply["content"][0]["text"]  # clamp ceiling


def test_handle_message_emits_progress_when_token_set():
    emitted = []
    msg = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {
            "name": "long_task",
            "arguments": {"steps": 3},
            "_meta": {"progressToken": "pt-xyz"},
        },
    }
    reply = handle_message(msg, emit_notification=emitted.append)
    assert reply["id"] == 1
    # Filter to progress frames · long_task also emits notifications/message
    # (Task #59) which we cover in test_mcp_logging.
    progress = [f for f in emitted if f["method"] == "notifications/progress"]
    assert len(progress) == 3
    for i, frame in enumerate(progress, start=1):
        assert frame["params"]["progressToken"] == "pt-xyz"
        assert frame["params"]["progress"] == i
        assert frame["params"]["total"] == 3


def test_handle_message_skips_progress_when_no_token():
    emitted = []
    msg = {
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "long_task", "arguments": {"steps": 3}},
    }
    reply = handle_message(msg, emit_notification=emitted.append)
    assert reply["id"] == 2
    # No progress frames when client didn't opt in (log frames are OK ·
    # they're gated by logging/setLevel, not by progressToken).
    assert [f for f in emitted if f["method"] == "notifications/progress"] == []


def test_notifications_cancelled_marks_request_id():
    cancel_msg = {
        "jsonrpc": "2.0",
        "method": "notifications/cancelled",
        "params": {"requestId": 42, "reason": "user abort"},
    }
    reply = handle_message(cancel_msg)
    assert reply is None  # notifications have no reply
    assert mcp_server._is_cancelled(42)
    mcp_server._clear_cancelled(42)


def test_cancelled_mid_flight_shortens_emission():
    # Pre-seed cancellation for requestId 77 · tool sees it on frame 1.
    mcp_server._mark_cancelled(77)
    emitted = []
    msg = {
        "jsonrpc": "2.0", "id": 77, "method": "tools/call",
        "params": {
            "name": "long_task",
            "arguments": {"steps": 5},
            "_meta": {"progressToken": "pt-77"},
        },
    }
    reply = handle_message(msg, emit_notification=emitted.append)
    assert reply["id"] == 77
    progress = [f for f in emitted if f["method"] == "notifications/progress"]
    assert len(progress) == 0  # cancelled before first emit
    assert "cancelled" in reply["result"]["content"][0]["text"]
    # handle_message must clear the id on reply so a replay isn't stuck.
    assert not mcp_server._is_cancelled(77)


def test_long_task_registered_in_schema():
    assert "long_task" in mcp_server.TOOLS
    spec = mcp_server.TOOLS["long_task"]
    assert spec.get("progress") is True
    assert spec["schema"]["name"] == "long_task"


# ─── e2e client ↔ server over TCP ────────────────────────────────

def _pick_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def tcp_server():
    port = _pick_port()
    t = threading.Thread(
        target=mcp_server._tcp_loop,
        args=("127.0.0.1", port),
        kwargs={"token_table": None, "ssl_ctx": None},
        daemon=True,
    )
    t.start()
    # Wait for bind.
    for _ in range(40):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.05)
    yield port


def test_e2e_progress_cb_receives_frames_in_order(tcp_server):
    got = []
    with MCPClient(host="127.0.0.1", port=tcp_server) as c:
        reply = c.call_tool("long_task", {"steps": 4},
                            progress_cb=got.append)
    assert [f["progress"] for f in got] == [1, 2, 3, 4]
    assert all(f["total"] == 4 for f in got)
    assert "done" in reply["content"][0]["text"]


def test_e2e_progress_cb_none_returns_final_only(tcp_server):
    with MCPClient(host="127.0.0.1", port=tcp_server) as c:
        # No progress_cb · server must not emit frames (no token injected).
        reply = c.call_tool("long_task", {"steps": 3})
    assert "done" in reply["content"][0]["text"]


def test_e2e_cancel_wire_form(tcp_server):
    # This exercises the cancel() helper · server should accept and ack
    # by returning no error. Since the dispatch is sync, by the time our
    # cancel arrives the tool has already finished · that's fine, we're
    # asserting wire acceptance not real interruption.
    with MCPClient(host="127.0.0.1", port=tcp_server) as c:
        reply = c.call_tool("long_task", {"steps": 2})
        c.cancel(999, reason="test")
        # Server survives · next call still works.
        reply2 = c.call_tool("long_task", {"steps": 1})
    assert "done" in reply["content"][0]["text"]
    assert "done" in reply2["content"][0]["text"]


def test_e2e_progress_cb_exception_doesnt_break_rpc(tcp_server):
    calls = {"n": 0}

    def _bad_cb(_frame):
        calls["n"] += 1
        raise RuntimeError("cb boom")

    with MCPClient(host="127.0.0.1", port=tcp_server) as c:
        reply = c.call_tool("long_task", {"steps": 3},
                            progress_cb=_bad_cb)
    assert calls["n"] == 3  # all frames still dispatched
    assert "done" in reply["content"][0]["text"]


def test_e2e_progress_token_is_unique_per_call(tcp_server):
    seen = []
    with MCPClient(host="127.0.0.1", port=tcp_server) as c:
        c.call_tool("long_task", {"steps": 1},
                    progress_cb=lambda f: seen.append(f["progressToken"]))
        c.call_tool("long_task", {"steps": 1},
                    progress_cb=lambda f: seen.append(f["progressToken"]))
    assert len(seen) == 2
    assert seen[0] != seen[1]

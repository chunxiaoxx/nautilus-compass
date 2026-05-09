"""MCP logging/setLevel + notifications/message · Task #59.

Locks in the spec 2024-11-05 logging surface:

  - capabilities.logging present in initialize
  - logging/setLevel happy path returns empty result
  - invalid level rejected with -32602
  - emit_log threshold filtering drops below-threshold records
  - logging_state propagation: a setLevel call in this connection
    affects subsequent emit_log calls in the same connection
  - mid-flight setLevel takes effect: between two log emissions of
    a long-running tool, the threshold change is visible
  - long_task end-to-end: with logging_state at "debug" the tool
    emits the per-step debug frames; at "info" they are filtered
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mcp_server  # noqa: E402


def _init_msg(msg_id: int = 1) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"},
    }


def _set_level_msg(level, msg_id: int = 2) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "method": "logging/setLevel",
        "params": {"level": level},
    }


def _call_long_task(steps: int, msg_id: int = 3) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "method": "tools/call",
        "params": {
            "name": "long_task",
            "arguments": {"steps": steps},
            "_meta": {"progressToken": f"tok-{msg_id}"},
        },
    }


# ── 1. capabilities ───────────────────────────────────────────────


def test_initialize_advertises_logging_capability():
    reply = mcp_server.handle_message(_init_msg())
    caps = reply["result"]["capabilities"]
    assert "logging" in caps, f"capabilities missing 'logging': {caps}"


# ── 2. setLevel happy path ────────────────────────────────────────


def test_set_level_happy_path_returns_empty_result():
    state: dict = {}
    reply = mcp_server.handle_message(_set_level_msg("warning"),
                                      logging_state=state)
    assert reply["id"] == 2
    assert reply["result"] == {}, f"expected empty result, got {reply}"
    assert state["level"] == "warning"


def test_set_level_accepts_all_spec_levels():
    state: dict = {}
    for level in ("debug", "info", "notice", "warning",
                  "error", "critical", "alert", "emergency"):
        reply = mcp_server.handle_message(_set_level_msg(level),
                                          logging_state=state)
        assert "result" in reply, f"{level} rejected: {reply}"
        assert state["level"] == level


# ── 3. invalid level rejected ─────────────────────────────────────


def test_set_level_invalid_returns_invalid_params():
    state: dict = {}
    reply = mcp_server.handle_message(_set_level_msg("loud"),
                                      logging_state=state)
    assert "error" in reply, f"expected error, got {reply}"
    assert reply["error"]["code"] == -32602, reply["error"]
    # State must NOT have been mutated by a rejected level.
    assert "level" not in state or state.get("level") != "loud"


def test_set_level_non_string_rejected():
    state: dict = {}
    reply = mcp_server.handle_message(_set_level_msg(42),
                                      logging_state=state)
    assert reply.get("error", {}).get("code") == -32602


# ── 4. emit_log threshold filtering ───────────────────────────────


def test_emit_log_drops_below_threshold():
    captured: list = []
    sent = mcp_server.emit_log(captured.append, "info", "debug", "noisy")
    assert sent is False
    assert captured == [], "debug record leaked under info threshold"


def test_emit_log_passes_at_threshold():
    captured: list = []
    sent = mcp_server.emit_log(captured.append, "info", "info", "hi")
    assert sent is True
    assert len(captured) == 1
    frame = captured[0]
    assert frame["method"] == "notifications/message"
    assert frame["params"]["level"] == "info"
    assert frame["params"]["data"] == "hi"


def test_emit_log_passes_above_threshold():
    captured: list = []
    sent = mcp_server.emit_log(captured.append, "warning", "error", "bad")
    assert sent is True
    assert captured[0]["params"]["level"] == "error"


def test_emit_log_with_no_emitter_is_noop():
    """stdio loops can't push notifications back · must not raise."""
    sent = mcp_server.emit_log(None, "info", "info", "hi")
    assert sent is False


def test_emit_log_normalizes_unknown_level():
    """Unknown levels fall back to default rather than crashing."""
    captured: list = []
    # "fatal" isn't in LOG_LEVELS · gets normalized to default ("info")
    sent = mcp_server.emit_log(captured.append, "info", "fatal", "x")
    assert sent is True
    assert captured[0]["params"]["level"] == mcp_server.DEFAULT_LOG_LEVEL


# ── 5. logging_state propagation ──────────────────────────────────


def test_long_task_respects_initial_logging_state():
    """At default ('info') threshold, long_task emits info start +
    warning if cancelled, but its per-step 'debug' frames are dropped.
    """
    captured: list = []
    state: dict = {"level": "info"}
    mcp_server.handle_message(
        _call_long_task(steps=3),
        emit_notification=captured.append,
        logging_state=state,
    )
    msg_frames = [f for f in captured
                  if f["method"] == "notifications/message"]
    levels = [f["params"]["level"] for f in msg_frames]
    # Start info gets through; per-step debugs are filtered.
    assert "info" in levels, f"info start missing: {levels}"
    assert "debug" not in levels, (
        f"debug should be filtered at info threshold: {levels}"
    )


def test_long_task_at_debug_threshold_emits_per_step_frames():
    captured: list = []
    state: dict = {"level": "debug"}
    mcp_server.handle_message(
        _call_long_task(steps=3),
        emit_notification=captured.append,
        logging_state=state,
    )
    msg_frames = [f for f in captured
                  if f["method"] == "notifications/message"]
    debug_frames = [f for f in msg_frames
                    if f["params"]["level"] == "debug"]
    assert len(debug_frames) == 3, (
        f"expected 3 debug frames at debug threshold, got "
        f"{len(debug_frames)}: {debug_frames}"
    )


def test_long_task_at_warning_threshold_drops_info_and_debug():
    captured: list = []
    state: dict = {"level": "warning"}
    mcp_server.handle_message(
        _call_long_task(steps=2),
        emit_notification=captured.append,
        logging_state=state,
    )
    msg_frames = [f for f in captured
                  if f["method"] == "notifications/message"]
    levels = [f["params"]["level"] for f in msg_frames]
    assert "info" not in levels, levels
    assert "debug" not in levels, levels


# ── 6. mid-flight setLevel takes effect ───────────────────────────


def test_mid_flight_set_level_changes_subsequent_emissions():
    """Server reads the level dict on each emit_log call, so a
    setLevel between two tool invocations on the same connection
    must change what the next tool emits.
    """
    state: dict = {"level": "warning"}

    # First long_task: only warning+ get through
    captured1: list = []
    mcp_server.handle_message(
        _call_long_task(steps=2, msg_id=10),
        emit_notification=captured1.append,
        logging_state=state,
    )
    info_frames_1 = [f for f in captured1
                     if f["method"] == "notifications/message"
                     and f["params"]["level"] == "info"]
    assert info_frames_1 == [], (
        f"warning threshold should drop info: {info_frames_1}"
    )

    # Lower threshold mid-session
    mcp_server.handle_message(_set_level_msg("debug", msg_id=11),
                              logging_state=state)
    assert state["level"] == "debug"

    # Second long_task: now debug+ gets through
    captured2: list = []
    mcp_server.handle_message(
        _call_long_task(steps=2, msg_id=12),
        emit_notification=captured2.append,
        logging_state=state,
    )
    debug_frames_2 = [f for f in captured2
                      if f["method"] == "notifications/message"
                      and f["params"]["level"] == "debug"]
    assert len(debug_frames_2) == 2, (
        f"after lowering to debug, expected 2 step frames, "
        f"got {len(debug_frames_2)}"
    )

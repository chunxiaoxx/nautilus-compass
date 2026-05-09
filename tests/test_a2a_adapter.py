"""v1.0 · A2A adapter protocol tests.

Exercises handle_a2a_message directly · no HTTP server needed.
Internal MCP tool calls are patched so tests don't touch the daemon.

Runs under pytest:  pytest tests/test_a2a_adapter.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

# Make sdk/ importable (a2a_adapter lives there and itself imports from plugin root)
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SDK_DIR = PLUGIN_ROOT / "sdk"
for p in (str(PLUGIN_ROOT), str(SDK_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import a2a_adapter  # noqa: E402


def _envelope(msg_type: str, payload=None, msg_id: str = "test-1",
              from_agent: str = "ag_test") -> dict:
    return {
        "protocol": "a2a/v1",
        "from": from_agent,
        "to": "compass-memory",
        "msg_id": msg_id,
        "type": msg_type,
        "payload": payload or {},
    }


# ─── protocol validation ───────────────────────────────────────────

def test_wrong_protocol_rejected():
    bad = _envelope("STORE_OBS")
    bad["protocol"] = "v2-future"
    reply = a2a_adapter.handle_a2a_message(bad)
    assert reply["status"] == "err"
    assert "protocol" in reply["error"].lower()


def test_unknown_message_type_rejected():
    reply = a2a_adapter.handle_a2a_message(_envelope("NONSENSE_TYPE"))
    assert reply["status"] == "err"
    assert "unknown" in reply["error"].lower()


def test_reply_envelope_fields_are_set():
    reply = a2a_adapter.handle_a2a_message(_envelope("DISCOVER_CAPABILITIES"))
    assert reply["protocol"] == "a2a/v1"
    assert reply["from"] == "compass-memory"
    assert reply["to"] == "ag_test"  # mirror of orig 'from'
    assert reply["in_reply_to"] == "test-1"
    assert reply["type"] == "REPLY"
    assert "ts" in reply


# ─── DISCOVER_CAPABILITIES ─────────────────────────────────────────

def test_discover_capabilities_lists_core_types():
    reply = a2a_adapter.handle_a2a_message(_envelope("DISCOVER_CAPABILITIES"))
    assert reply["status"] == "ok"
    caps = reply["payload"]["capabilities"]
    for required in ("STORE_OBS", "RETRIEVE_MEMORY", "QUERY_PROFILE",
                     "QUERY_DRIFT_HISTORY", "DISCOVER_CAPABILITIES"):
        assert required in caps, f"DISCOVER_CAPABILITIES missing {required}"


def test_discover_capabilities_is_zero_side_effect():
    """Must not require MCP tools or daemon to respond."""
    # If _call_mcp_tool were invoked, this patch would have it raise.
    def explode(*a, **kw):
        raise AssertionError("DISCOVER_CAPABILITIES should not touch MCP tools")

    with patch.object(a2a_adapter, "_call_mcp_tool", side_effect=explode):
        reply = a2a_adapter.handle_a2a_message(_envelope("DISCOVER_CAPABILITIES"))
    assert reply["status"] == "ok"


# ─── STORE_OBS (delegates to MCP ingest_obs) ───────────────────────

def test_store_obs_delegates_to_ingest_obs():
    seen = {}

    def fake(tool_name, args):
        seen["tool"] = tool_name
        seen["args"] = args
        return "obs_id=xyz · stored ok"

    payload = {
        "name": "a2a test obs",
        "description": "stored via a2a",
        "body": "body text",
        "type": "feature",
        "concept": "how-it-works",
        "drift": "green",
    }
    with patch.object(a2a_adapter, "_call_mcp_tool", side_effect=fake):
        reply = a2a_adapter.handle_a2a_message(_envelope("STORE_OBS", payload))

    assert seen["tool"] == "ingest_obs"
    assert seen["args"] == payload
    assert reply["status"] == "ok"
    assert "xyz" in reply["payload"]["result"]


# ─── RETRIEVE_MEMORY (delegates to MCP session_search) ────────────

def test_retrieve_memory_passes_top_k_and_drift_filter():
    captured = {}

    def fake(tool_name, args):
        captured["tool"] = tool_name
        captured["args"] = args
        return "hit 1\nhit 2"

    payload = {"query": "what was decided?", "top_k": 3, "drift_filter": "green"}
    with patch.object(a2a_adapter, "_call_mcp_tool", side_effect=fake):
        reply = a2a_adapter.handle_a2a_message(_envelope("RETRIEVE_MEMORY", payload))

    assert captured["tool"] == "session_search"
    assert captured["args"]["query"] == "what was decided?"
    assert captured["args"]["top_k"] == 3
    assert captured["args"]["drift"] == "green"
    assert reply["status"] == "ok"


# ─── QUERY_DRIFT_HISTORY ──────────────────────────────────────────

def test_query_drift_history_delegates():
    def fake(tool_name, args):
        assert tool_name == "drift_history"
        assert args == {"days": 7}
        return "counts · green=5 yellow=2 red=0"

    with patch.object(a2a_adapter, "_call_mcp_tool", side_effect=fake):
        reply = a2a_adapter.handle_a2a_message(_envelope("QUERY_DRIFT_HISTORY", {"days": 7}))
    assert reply["status"] == "ok"
    assert "green=5" in reply["payload"]["result"]


# ─── version contract ─────────────────────────────────────────────

def test_capabilities_map_documents_inputs_and_outputs():
    """Every capability must document both input and output shapes."""
    for name, spec in a2a_adapter.CAPABILITIES.items():
        assert "description" in spec, f"{name} missing description"
        assert "input" in spec, f"{name} missing input"
        assert "output" in spec, f"{name} missing output"

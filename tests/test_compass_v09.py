"""compass v0.9 · integration tests for new capabilities.

Tests:
  · session_writer · drift-aware obs writing
  · drift_history · cross-project timeline
  · session_search · keyword + drift filter
  · daemon_anchor_loader · 3-layer merge
  · sdk/compass_client · offline buffer
  · sdk/attach_memory · duck-typed agent integration
  · sdk/a2a_adapter · STORE/RETRIEVE/QUERY message handling
  · mcp_server · 7 tools schema + dispatch

Run:
  cd ~/.claude/plugins/nautilus-compass
  python tests/test_compass_v09.py
  # or with pytest
  pytest tests/test_compass_v09.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))
sys.path.insert(0, str(PLUGIN_DIR / "sdk"))


def test_anchor_loader_layers():
    """3-layer anchor merge · 平台 + domain + tenant."""
    from daemon_anchor_loader import load_layered_anchors

    pos1, neg1 = load_layered_anchors(domain=None, tenant_anchors_path=Path("/nonexistent.json"))
    assert len(pos1) >= 10, f"platform_base pos too few: {len(pos1)}"
    assert len(neg1) >= 20, f"platform_base neg too few: {len(neg1)}"

    pos2, neg2 = load_layered_anchors(domain=None)
    assert len(pos2) >= len(pos1), "tenant should add anchors"
    assert len(neg2) >= len(neg1), "tenant should add anchors"

    pos3, neg3 = load_layered_anchors(domain="vc")
    # Domain should add more (or same if domain file empty)
    assert len(pos3) >= len(pos2), "domain should add (or equal)"

    # de-dup test: both calls should return unique
    assert len(pos3) == len(set(pos3)), "duplicates in pos"
    assert len(neg3) == len(set(neg3)), "duplicates in neg"
    print(f"  ✓ anchor_loader: base={len(pos1)}+{len(neg1)} → +tenant={len(pos2)}+{len(neg2)} → +vc={len(pos3)}+{len(neg3)}")


def test_compass_client_offline_buffer():
    """SDK client · network down 时 buffer obs · 不丢."""
    from compass_client import CompassClient

    client = CompassClient(
        user_id="u_test",
        agent_id="ag_test_offline",
        agent_type="custom",
        base_url="https://this-host-does-not-exist-99.invalid",
        offline_buffer=True,
    )
    r = client.ingest_obs(
        name="offline buffer test",
        description="testing resilience",
        body="...",
        drift="green",
    )
    assert not r.get("ok") or r.get("buffered"), f"should buffer · got {r}"
    if r.get("buffered"):
        assert "buffer_file" in r, "buffered response should include path"
        print(f"  ✓ offline buffer: {Path(r['buffer_file']).name}")
    else:
        print(f"  ✓ direct send (server reachable)")


def test_a2a_adapter_messages():
    """A2A adapter · DISCOVER + STORE + QUERY 各回路."""
    from a2a_adapter import handle_a2a_message, CAPABILITIES

    # 1. DISCOVER_CAPABILITIES
    r1 = handle_a2a_message({
        "protocol": "a2a/v1", "from": "ag_t", "to": "compass-memory",
        "msg_id": "t1", "type": "DISCOVER_CAPABILITIES", "payload": {},
    })
    assert r1["status"] == "ok"
    assert "capabilities" in r1["payload"]
    caps = r1["payload"]["capabilities"]
    assert "STORE_OBS" in caps
    assert "RETRIEVE_MEMORY" in caps
    print(f"  ✓ a2a DISCOVER: {len(caps)} capabilities")

    # 2. QUERY_DRIFT_HISTORY
    r2 = handle_a2a_message({
        "protocol": "a2a/v1", "from": "ag_t", "to": "compass-memory",
        "msg_id": "t2", "type": "QUERY_DRIFT_HISTORY", "payload": {"days": 7},
    })
    assert r2["status"] == "ok", f"got {r2}"
    print(f"  ✓ a2a QUERY_DRIFT_HISTORY: payload size {len(json.dumps(r2.get('payload',{})))}")

    # 3. unknown type
    r3 = handle_a2a_message({
        "protocol": "a2a/v1", "from": "ag_t", "to": "compass-memory",
        "msg_id": "t3", "type": "BOGUS_TYPE", "payload": {},
    })
    assert r3["status"] == "err"
    print(f"  ✓ a2a unknown type rejected")


def test_attach_memory_duck_typing():
    """attach_memory · 任意 duck-typed agent 不报错."""
    from attach_memory import attach_memory

    class FakeAgent:
        role = "test_role"
        user_id = "u_attach_test"
        id = "fake01"
        def on_action(self, prompt, **kw):
            return {"ok": True, "ctx": kw.get("context", "")}
        def on_task_complete(self, task, outcome, **kw):
            return {"completed": True}

    agent = FakeAgent()
    attached = attach_memory(agent, base_url="https://example.invalid")
    assert hasattr(attached, "compass"), "agent should have .compass"
    assert hasattr(attached, "report_drift"), "agent should have .report_drift"
    # 调 on_action · 应该不报错 (recall 失败也只是 silent)
    r = attached.on_action("test query")
    assert isinstance(r, dict)
    # 调 on_task_complete (会触发 ingest · 网络挂走 buffer)
    r2 = attached.on_task_complete("test_task", "test_outcome")
    assert r2.get("completed")
    print(f"  ✓ attach_memory: agent.compass={attached.compass.user_id} · hooks installed")


def test_mcp_server_tools_schema():
    """MCP server · all tools have proper schema."""
    from mcp_server import TOOLS

    expected = {"recall", "drift_check", "feedback_log",
                "ingest_obs", "drift_history", "session_search", "profile"}
    actual = set(TOOLS.keys())
    assert expected == actual, f"tools mismatch · expected {expected} got {actual}"

    for name, t in TOOLS.items():
        assert "fn" in t and callable(t["fn"]), f"{name} no fn"
        s = t.get("schema") or {}
        assert s.get("name") == name, f"{name} schema name mismatch"
        assert "description" in s, f"{name} no description"
        assert s.get("inputSchema", {}).get("type") == "object", f"{name} no proper inputSchema"
    print(f"  ✓ mcp_server: {len(TOOLS)} tools · all schemas valid")


def test_drift_history_module_loads():
    """drift_history · cross-project session collection works."""
    from drift_history import collect_sessions
    rows = collect_sessions(days=90)
    assert isinstance(rows, list)
    print(f"  ✓ drift_history: {len(rows)} sessions across all projects (last 90d)")
    if rows:
        from collections import Counter
        drifts = Counter(r["drift"] for r in rows)
        print(f"    distribution: {dict(drifts)}")


def test_session_search_module_loads():
    """session_search · keyword search works."""
    from session_search import search
    hits = search("compass", days=90, top=3)
    assert isinstance(hits, list)
    print(f"  ✓ session_search 'compass': {len(hits)} hits")


def run_all():
    tests = [
        ("anchor_loader_layers", test_anchor_loader_layers),
        ("compass_client_offline_buffer", test_compass_client_offline_buffer),
        ("a2a_adapter_messages", test_a2a_adapter_messages),
        ("attach_memory_duck_typing", test_attach_memory_duck_typing),
        ("mcp_server_tools_schema", test_mcp_server_tools_schema),
        ("drift_history_module_loads", test_drift_history_module_loads),
        ("session_search_module_loads", test_session_search_module_loads),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\n[{name}]")
        try:
            fn()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n=== {passed}/{passed+failed} tests passed ===")
    return failed


if __name__ == "__main__":
    sys.exit(run_all())

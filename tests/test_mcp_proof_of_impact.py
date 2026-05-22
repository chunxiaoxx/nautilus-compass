"""S4 module 4 · tool_proof_of_impact smoke tests."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _import_tool():
    """Lazy import · mcp_server has many imports · only test tool function."""
    from mcp_server import tool_proof_of_impact, TOOLS
    return tool_proof_of_impact, TOOLS


def test_1_tool_registered():
    _, TOOLS = _import_tool()
    assert "proof_of_impact" in TOOLS
    schema = TOOLS["proof_of_impact"]["schema"]
    assert schema["name"] == "proof_of_impact"
    props = schema["inputSchema"]["properties"]
    required = schema["inputSchema"]["required"]
    assert set(required) == {"action_id", "agent_id", "cited_memory_paths"}
    assert props["action_outcome"]["enum"] == ["success", "failure", "partial", "pending"]
    print("OK 1 tool registered in TOOLS")


def test_2_missing_action_id_errors():
    tool, _ = _import_tool()
    r = tool({"agent_id": "a", "cited_memory_paths": ["x.md"]})
    assert r.get("isError") is True
    print("OK 2 missing action_id rejected")


def test_3_empty_cited_paths_errors():
    tool, _ = _import_tool()
    r = tool({"action_id": "b", "agent_id": "a", "cited_memory_paths": []})
    assert r.get("isError") is True
    print("OK 3 empty cited_paths rejected")


def test_4_invalid_outcome_errors():
    tool, _ = _import_tool()
    r = tool({
        "action_id": "b", "agent_id": "a",
        "cited_memory_paths": ["x.md"],
        "action_outcome": "bogus",
    })
    assert r.get("isError") is True
    print("OK 4 invalid outcome rejected")


def test_5_full_flow_with_isolation():
    """Real PoI flow · isolated cache + memory dir via os.environ + monkey-patch."""
    import proof.poi_emitter as emitter
    tool, _ = _import_tool()
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m = tmp / "memory.md"
        m.write_text("---\nname: m\nagent_type: other\ndrift: green\n---\nbody\n",
                     encoding="utf-8")
        # Redirect default cache dir
        original_cache = emitter.DEFAULT_CACHE_DIR
        emitter.DEFAULT_CACHE_DIR = tmp / "_cache"
        try:
            r = tool({
                "action_id": "b-real",
                "agent_id": "acting",
                "cited_memory_paths": [str(m)],
                "action_outcome": "success",
                "notes": "smoke test",
            })
            assert r.get("isError") is not True
            assert "PoI recorded" in r["content"][0]["text"]
        finally:
            emitter.DEFAULT_CACHE_DIR = original_cache
    print("OK 5 full flow recorded")


if __name__ == "__main__":
    tests = [test_1_tool_registered, test_2_missing_action_id_errors,
             test_3_empty_cited_paths_errors, test_4_invalid_outcome_errors,
             test_5_full_flow_with_isolation]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} tool_proof_of_impact smoke pass")

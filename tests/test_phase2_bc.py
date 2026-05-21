"""
v1.7.1 · Phase 2.B (add_worker) + Phase 2.C (RRF fusion) smoke tests · deterministic · no LLM

See mcp_server.py:tool_add_worker · recall.py:rrf_fusion
See paper/LLM_WIKI2_FUSE_DESIGN.md · plan §4 Phase 2.

Run:
    python tests/test_phase2_bc.py
"""
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

# Make repo root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mcp_server
from mcp_server import tool_add_worker, TOOLS
from recall import rrf_fusion


# ─── Phase 2.B · add_worker tests ────────────────────────────────────────────

def test_b1_name_required():
    """B1 · add_worker rejects empty name."""
    result = tool_add_worker({"name": "", "spec_type": "cron"})
    assert result.get("isError") is True, "expected error for empty name"
    print("✅ B1 · add_worker name required")


def test_b2_default_spec_type_custom():
    """B2 · add_worker default spec_type=custom for unknown values."""
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(Path, "home", return_value=Path(tmp)):
            result = tool_add_worker({"name": "test-worker", "spec_type": "bogus"})
            assert result.get("isError") is not True
            jsonl = Path(tmp) / ".claude" / "plugins" / "nautilus-compass" / ".cache" / "workers.jsonl"
            entry = json.loads(jsonl.read_text(encoding="utf-8").strip())
            assert entry["spec_type"] == "custom"
    print("✅ B2 · unknown spec_type defaults to custom")


def test_b3_record_persisted():
    """B3 · add_worker persists full record to workers.jsonl."""
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(Path, "home", return_value=Path(tmp)):
            tool_add_worker({
                "name": "iii-cron-daily",
                "spec_type": "cron",
                "description": "fires 09:00 daily",
                "config": {"schedule": "0 9 * * *"},
                "agent_type": "v5-singleton",
            })
            jsonl = Path(tmp) / ".claude" / "plugins" / "nautilus-compass" / ".cache" / "workers.jsonl"
            entry = json.loads(jsonl.read_text(encoding="utf-8").strip())
            assert entry["name"] == "iii-cron-daily"
            assert entry["spec_type"] == "cron"
            assert entry["config"]["schedule"] == "0 9 * * *"
            assert entry["agent_type"] == "v5-singleton"
            assert entry["registered_by"] == "compass_mcp"
            assert "registered_at" in entry
    print("✅ B3 · record persisted with all fields")


def test_b4_multiple_workers_append():
    """B4 · multiple add_worker calls append to same jsonl."""
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(Path, "home", return_value=Path(tmp)):
            tool_add_worker({"name": "w1", "spec_type": "cron"})
            tool_add_worker({"name": "w2", "spec_type": "pubsub"})
            tool_add_worker({"name": "w3", "spec_type": "queue"})
            jsonl = Path(tmp) / ".claude" / "plugins" / "nautilus-compass" / ".cache" / "workers.jsonl"
            lines = jsonl.read_text(encoding="utf-8").strip().splitlines()
            assert len(lines) == 3
            assert json.loads(lines[0])["name"] == "w1"
            assert json.loads(lines[2])["spec_type"] == "queue"
    print("✅ B4 · multiple workers append correctly")


def test_b5_registered_in_tools():
    """B5 · add_worker registered in TOOLS dict."""
    assert "add_worker" in TOOLS, "add_worker missing from TOOLS"
    assert TOOLS["add_worker"]["fn"] is tool_add_worker
    schema = TOOLS["add_worker"]["schema"]
    assert schema["name"] == "add_worker"
    assert "spec_type" in schema["inputSchema"]["properties"]
    enum = schema["inputSchema"]["properties"]["spec_type"]["enum"]
    assert set(enum) == {"cron", "pubsub", "queue", "http", "custom"}
    print("✅ B5 · add_worker registered in TOOLS dict")


# ─── Phase 2.C · RRF fusion tests ────────────────────────────────────────────

def test_c1_basic_fusion_overlap_wins():
    """C1 · entry in both lists at top rank wins over single-list top."""
    list_a = [(0.9, {"path": "x.md"}), (0.8, {"path": "y.md"})]
    list_b = [(0.9, {"path": "y.md"}), (0.8, {"path": "x.md"})]
    result = rrf_fusion(list_a, list_b, k=60, top_k=5, session_diversify=False)
    # Both x.md and y.md appear in both lists · scores equal
    paths = [e[1]["path"] for e in result]
    assert "x.md" in paths and "y.md" in paths
    print("✅ C1 · basic fusion 2 lists · overlap included")


def test_c2_single_list_works():
    """C2 · single-list input works · 1/(k+rank+1) formula."""
    lst = [(0.9, {"path": "a.md"}), (0.8, {"path": "b.md"})]
    result = rrf_fusion(lst, k=60, top_k=5, session_diversify=False)
    # rank 0 · score = 1/61 ≈ 0.01639
    assert abs(result[0][0] - 1/61) < 1e-6, f"expected 1/61 · got {result[0][0]}"
    assert result[0][1]["path"] == "a.md"
    print("✅ C2 · single list · 1/(k+rank+1) formula")


def test_c3_empty_lists_handled():
    """C3 · empty list inputs · returns empty list gracefully."""
    result = rrf_fusion([], [], top_k=5)
    assert result == [], "expected empty result"
    print("✅ C3 · empty lists handled")


def test_c4_top_k_limits():
    """C4 · top_k limits final output."""
    lst = [(0.9 - i*0.1, {"path": f"f{i}.md"}) for i in range(10)]
    result = rrf_fusion(lst, top_k=3, session_diversify=False)
    assert len(result) == 3
    print("✅ C4 · top_k=3 limits output")


def test_c5_session_diversify_caps_max_3():
    """C5 · session_diversify caps 3 per session_id."""
    # All entries in same session
    entries = [(0.9 - i*0.01, {"path": f"f{i}.md", "session_id": "S1"}) for i in range(10)]
    result = rrf_fusion(entries, top_k=10, session_diversify=True, max_per_session=3)
    assert len(result) == 3, f"expected 3 · got {len(result)}"
    print("✅ C5 · session diversify caps max 3 per session")


def test_c6_session_diversify_across_sessions():
    """C6 · diversify spreads across sessions correctly."""
    entries = [
        (0.99, {"path": "s1a.md", "session_id": "S1"}),
        (0.98, {"path": "s1b.md", "session_id": "S1"}),
        (0.97, {"path": "s2a.md", "session_id": "S2"}),
        (0.96, {"path": "s2b.md", "session_id": "S2"}),
        (0.95, {"path": "s3a.md", "session_id": "S3"}),
    ]
    result = rrf_fusion(entries, top_k=10, session_diversify=True, max_per_session=1)
    assert len(result) == 3
    sessions = {e[1]["session_id"] for e in result}
    assert sessions == {"S1", "S2", "S3"}
    print("✅ C6 · diversify spreads across sessions")


def test_c7_entries_without_path_skipped():
    """C7 · entries lacking 'path' key are silently skipped (no crash)."""
    valid = [(0.9, {"path": "valid.md"})]
    broken = [(0.9, {"description": "no path"}), (0.8, {"path": "ok.md"})]
    result = rrf_fusion(valid, broken, top_k=5, session_diversify=False)
    paths = {e[1]["path"] for e in result}
    assert "valid.md" in paths and "ok.md" in paths
    print("✅ C7 · entries without path silently skipped")


def test_c8_k_parameter_affects_scores():
    """C8 · changing k parameter changes fused scores predictably."""
    lst = [(0.9, {"path": "a.md"})]
    r60 = rrf_fusion(lst, k=60, top_k=1, session_diversify=False)
    r10 = rrf_fusion(lst, k=10, top_k=1, session_diversify=False)
    # Smaller k → higher score (1/(10+0+1)=0.0909 > 1/(60+0+1)=0.0164)
    assert r10[0][0] > r60[0][0]
    print("✅ C8 · k parameter affects scores")


if __name__ == "__main__":
    tests = [
        test_b1_name_required,
        test_b2_default_spec_type_custom,
        test_b3_record_persisted,
        test_b4_multiple_workers_append,
        test_b5_registered_in_tools,
        test_c1_basic_fusion_overlap_wins,
        test_c2_single_list_works,
        test_c3_empty_lists_handled,
        test_c4_top_k_limits,
        test_c5_session_diversify_caps_max_3,
        test_c6_session_diversify_across_sessions,
        test_c7_entries_without_path_skipped,
        test_c8_k_parameter_affects_scores,
    ]
    failures = []
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failures.append((t.__name__, str(e)))
            print(f"❌ {t.__name__}: {e}")
        except Exception as e:
            failures.append((t.__name__, f"{type(e).__name__}: {e}"))
            print(f"❌ {t.__name__}: {type(e).__name__}: {e}")
    if failures:
        print(f"\n❌ {len(failures)}/{len(tests)} failures")
        sys.exit(1)
    print(f"\n✅ {len(tests)}/{len(tests)} Phase 2.B + 2.C smoke tests pass")

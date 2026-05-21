"""
v1.7.1 · agentmemory fuse · 9 lifecycle hooks smoke tests · deterministic · no LLM

See stop_hook.py:357-490 for hook implementation.
See paper/LLM_WIKI2_FUSE_DESIGN.md §3 for tier/promote_after schema.

Run:
    python tests/test_hook_dispatch.py
"""
import sys
import os
import json
import tempfile
from pathlib import Path

# Make repo root importable (tests/ → parent)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stop_hook import (
    HOOK_DISPATCH,
    hook_session_start,
    hook_user_prompt_submit,
    hook_pre_tool_use,
    hook_post_tool_use,
    hook_post_tool_use_failure,
    hook_pre_compact,
    hook_subagent_start,
    hook_subagent_stop,
    hook_session_end,
    _emit_lifecycle_event,
    dispatch_hook,
)


def test_1_nine_hooks_registered():
    """Case 1 · HOOK_DISPATCH 真 9 hook names verbatim from agentmemory."""
    expected = {
        "SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse",
        "PostToolUseFailure", "PreCompact", "SubagentStart", "SubagentStop",
        "SessionEnd",
    }
    assert set(HOOK_DISPATCH.keys()) == expected, \
        f"missing/extra: {set(HOOK_DISPATCH.keys()) ^ expected}"
    print("✅ Case 1 · 9 hooks registered (agentmemory verbatim)")


def test_2_event_schema_complete():
    """Case 2 · _emit_lifecycle_event 真 returns 12 required frontmatter fields."""
    event = _emit_lifecycle_event("SessionStart", {"summary": "test"})
    required = {
        "hook", "ts", "name", "type", "concept", "drift",
        "tier", "decay_rate", "promote_after", "reinforce_count",
        "declaration_type", "payload_summary",
    }
    missing = required - set(event.keys())
    assert not missing, f"missing fields: {missing}"
    print("✅ Case 2 · event schema 12 fields complete")


def test_3_session_start_tier_working():
    """Case 3 · SessionStart 真 tier=working · default promote_after=1_access."""
    event = hook_session_start({})
    assert event["tier"] == "working"
    assert event["promote_after"] == "1_access"
    assert event["drift"] == "green"
    print("✅ Case 3 · SessionStart tier=working · default promote_after")


def test_4_post_tool_failure_drift_yellow():
    """Case 4 · PostToolUseFailure 真 drift=yellow (signal of failure)."""
    event = hook_post_tool_use_failure({"summary": "error in Bash"})
    assert event["drift"] == "yellow", f"expected yellow · got {event['drift']}"
    print("✅ Case 4 · PostToolUseFailure drift=yellow")


def test_5_pre_compact_tier_episodic():
    """Case 5 · PreCompact + SubagentStop + SessionEnd 真 tier=episodic."""
    assert hook_pre_compact({})["tier"] == "episodic"
    assert hook_subagent_stop({})["tier"] == "episodic"
    assert hook_session_end({})["tier"] == "episodic"
    print("✅ Case 5 · 3 hooks tier=episodic correct")


def test_6_payload_summary_truncate():
    """Case 6 · payload summary 真 truncate at 200 chars."""
    long_text = "x" * 500
    event = _emit_lifecycle_event("UserPromptSubmit", {"summary": long_text})
    assert len(event["payload_summary"]) == 200, \
        f"expected 200 · got {len(event['payload_summary'])}"
    print("✅ Case 6 · payload summary truncate at 200")


def test_7_thread_id_propagate():
    """Case 7 · payload thread_id 真 propagate to event."""
    event = _emit_lifecycle_event("PreToolUse", {"thread_id": "thread-abc-123"})
    assert event["thread_id"] == "thread-abc-123"
    print("✅ Case 7 · thread_id propagate")


def test_8_dispatch_unknown_hook_fail_soft():
    """Case 8 · unknown hook 真 fail-soft (return 0 · not raise)."""
    rc = dispatch_hook("NonExistentHook", {})
    assert rc == 0, f"expected exit 0 · got {rc}"
    print("✅ Case 8 · unknown hook fail-soft")


def test_9_dispatch_writes_jsonl():
    """Case 9 · dispatch_hook 真 write event to .cache/hook_events.jsonl."""
    import stop_hook
    with tempfile.TemporaryDirectory() as tmp:
        # Redirect HOOK_EVENTS_FILE to temp
        original = stop_hook.HOOK_EVENTS_FILE
        stop_hook.HOOK_EVENTS_FILE = Path(tmp) / "hook_events.jsonl"
        try:
            rc = dispatch_hook("SessionStart", {"summary": "test write"})
            assert rc == 0
            content = stop_hook.HOOK_EVENTS_FILE.read_text(encoding="utf-8")
            entry = json.loads(content.strip().splitlines()[-1])
            assert entry["hook"] == "SessionStart"
            assert entry["tier"] == "working"
            assert entry["payload_summary"] == "test write"
        finally:
            stop_hook.HOOK_EVENTS_FILE = original
    print("✅ Case 9 · dispatch writes jsonl correctly")


def test_10_default_agent_type():
    """Case 10 · default agent_type=claude-code · payload override OK."""
    e1 = _emit_lifecycle_event("PreToolUse", {})
    assert e1["agent_type"] == "claude-code"
    e2 = _emit_lifecycle_event("PreToolUse", {"agent_type": "hermes"})
    assert e2["agent_type"] == "hermes"
    print("✅ Case 10 · agent_type default + override")


if __name__ == "__main__":
    tests = [
        test_1_nine_hooks_registered,
        test_2_event_schema_complete,
        test_3_session_start_tier_working,
        test_4_post_tool_failure_drift_yellow,
        test_5_pre_compact_tier_episodic,
        test_6_payload_summary_truncate,
        test_7_thread_id_propagate,
        test_8_dispatch_unknown_hook_fail_soft,
        test_9_dispatch_writes_jsonl,
        test_10_default_agent_type,
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
    print(f"\n✅ {len(tests)}/{len(tests)} hook dispatch smoke tests pass")

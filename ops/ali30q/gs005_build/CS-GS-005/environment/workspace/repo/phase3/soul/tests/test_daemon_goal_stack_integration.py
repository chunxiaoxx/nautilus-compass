"""Daemon goal_stack integration · select_goal_with_source returns from new entry-point."""
from __future__ import annotations
from soul.goal_stack import GoalSource


def test_daemon_select_goal_with_source_returns_p2_dispatch(monkeypatch):
    """When goal_stack returns P2, daemon's new wrapper threads the source through."""
    fake_goal = {"id": "dispatch-42", "agent_id": 9000002, "task_spec_hash": "abc123", "task_type": "code"}
    monkeypatch.setattr("soul.goal_stack.next_goal",
                        lambda: (fake_goal, GoalSource.P2_AGENT_DISPATCH))
    from soul.daemon import select_goal_with_source
    goal, source = select_goal_with_source()
    assert goal == fake_goal
    assert source == GoalSource.P2_AGENT_DISPATCH


def test_daemon_select_goal_with_source_returns_none_when_stack_empty(monkeypatch):
    """When all 3 sources empty, wrapper returns (None, None)."""
    monkeypatch.setattr("soul.goal_stack.next_goal", lambda: (None, None))
    from soul.daemon import select_goal_with_source
    goal, source = select_goal_with_source()
    assert goal is None
    assert source is None


def test_emit_goal_source_noop_when_db_unset(monkeypatch):
    """_emit_goal_source_to_outcome must not raise when DATABASE_URL unset."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from soul.daemon import _emit_goal_source_to_outcome
    # Must not raise · fail-open on no DB
    _emit_goal_source_to_outcome("test-cycle-id", GoalSource.P1_GOVERNANCE)


def test_emit_goal_source_noop_when_source_none(monkeypatch):
    """_emit_goal_source_to_outcome must not raise when source is None."""
    from soul.daemon import _emit_goal_source_to_outcome
    # Must not raise · short-circuits on None source
    _emit_goal_source_to_outcome("test-cycle-id", None)

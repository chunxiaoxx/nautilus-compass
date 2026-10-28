"""W4.2 (daemon side) · the soul daemon's P1 governance path must atomically
claim an accepted proposal before shipping, and resolve/release the claim.

Pairs with phase3/backend/tests/test_double_ship_claim.py (executor side). The
daemon claims via _claim_governance right before ship; on success it resolves
the claim to 'executed_ok', and on any abort it releases back to 'accepted' so
the row stays retryable (no silent drop into a stuck 'claiming' state).
"""
from __future__ import annotations
from soul import daemon
from soul.goal_stack import GoalSource


class _FakeResult:
    def __init__(self, passed=True, applied=True, files=None, git_commit="abc1234"):
        self.check_result = {"passed": passed}
        self.applied = applied
        self.git_commit = git_commit
        self.files_planned = files or [{"path": "phase3/soul/__init__.py", "size": 200}]


def _fake_git(monkeypatch):
    def fake_run(cmd, **kw):
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()
    monkeypatch.setattr(daemon.subprocess, "run", fake_run)


def _baseline_gates(monkeypatch):
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: False)
    monkeypatch.setattr(daemon.budget_gate, "under_cap", lambda: True)
    monkeypatch.setattr(daemon.budget_gate, "record_cost", lambda *a, **k: None)
    monkeypatch.setattr(daemon.pr_gate, "has_open_pr_for", lambda gid: False)
    monkeypatch.setattr(daemon.pr_gate, "check_paths", lambda c: (True, "ok"))
    monkeypatch.setattr(daemon.pr_gate, "check_diff_loc", lambda n, m=None: (True, "ok"))
    monkeypatch.setattr(daemon.goal_selector, "mark_done", lambda gid: True)
    monkeypatch.setattr(daemon, "_run_pytest", lambda base, paths: None)
    monkeypatch.setattr(daemon.failure_track, "record_success", lambda: None)
    monkeypatch.setattr(daemon.failure_track, "record_failure", lambda x: None)
    monkeypatch.setattr(daemon, "_emit_goal_source_to_outcome", lambda cid, src: None)
    monkeypatch.setattr(daemon, "_record_l4_proposal", lambda **k: None)
    monkeypatch.setattr(daemon, "_compute_snapshot", lambda repo: {})
    monkeypatch.setattr(daemon, "_stamp_fitness", lambda cid, d: None)


def _fake_p1():
    return {"id": "gov-42", "proposal_id": 42,
            "proposed_change": "Add input validation."}


def _wire_p1(monkeypatch):
    monkeypatch.setattr("soul.goal_stack.next_goal",
                        lambda: (_fake_p1(), GoalSource.P1_GOVERNANCE))


def test_daemon_skips_when_claim_lost(monkeypatch):
    """If another consumer already claimed the row, the daemon must NOT ship."""
    _baseline_gates(monkeypatch)
    _wire_p1(monkeypatch)
    _fake_git(monkeypatch)
    monkeypatch.setattr(daemon, "_claim_governance", lambda pid: False)

    ship_calls = []
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: ship_calls.append(a) or _FakeResult()))
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr", lambda b, t, body: "http://pr/x")

    rc = daemon.run_once()
    assert rc == 0, "lost-claim cycle exits cleanly without shipping"
    assert ship_calls == [], "must not ship a proposal claimed by another consumer"


def test_daemon_resolves_claim_executed_ok_on_success(monkeypatch):
    _baseline_gates(monkeypatch)
    _wire_p1(monkeypatch)
    _fake_git(monkeypatch)
    monkeypatch.setattr(daemon, "_claim_governance", lambda pid: True)

    resolved = []
    monkeypatch.setattr(daemon, "_resolve_governance",
                        lambda pid, status: resolved.append((pid, status)))
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(), lambda *a, **k: _FakeResult()))
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr", lambda b, t, body: "http://pr/gov-42")

    rc = daemon.run_once()
    assert rc == 0
    assert (42, "executed_ok") in resolved, "successful P1 ship resolves claim → executed_ok"


def test_daemon_releases_claim_on_abort(monkeypatch):
    """A shipped-but-rejected proposal must be released back to 'accepted' so it
    stays retryable (not stuck in 'claiming')."""
    _baseline_gates(monkeypatch)
    _wire_p1(monkeypatch)
    _fake_git(monkeypatch)
    monkeypatch.setattr(daemon, "_claim_governance", lambda pid: True)
    # pr_gate rejects → abort path after claim
    monkeypatch.setattr(daemon.pr_gate, "check_paths", lambda c: (False, "blocked"))

    resolved = []
    monkeypatch.setattr(daemon, "_resolve_governance",
                        lambda pid, status: resolved.append((pid, status)))
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(), lambda *a, **k: _FakeResult()))
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr", lambda b, t, body: "http://pr/x")

    rc = daemon.run_once()
    assert rc == 1
    assert (42, "accepted") in resolved, "aborted P1 ship releases claim → accepted (retryable)"

"""Slice B followup sentinel · daemon.run_once must pick P2 agent_dispatch row
when yaml is empty, then propagate task_spec → ship + mark dispatch shipped.

End-to-end product loop closure for Inc 3 Slice A wiring gap:
  - Slice A added select_goal_with_source() + _emit_goal_source_to_outcome()
    helpers but never wired them into run_once (line 345 still called the bare
    goal_selector.select_goal()).
  - Slice B HTTP-only added POST /api/soul/dispatch + agent_dispatch_log INSERT
    but the rows never reached the daemon (no consumer).
  - This sentinel guards the wire: agent → /api/soul/dispatch → DB row → daemon
    next tick → ship → draft PR → mark row shipped.

P2 row shape diverges from yaml goal: it has `task_spec` (the actual code goal
text from the dispatcher) but no `description`. The daemon must adapt by
copying task_spec → description before running the shared ship path.
"""
from __future__ import annotations
from soul import daemon
from soul.goal_stack import GoalSource


class _FakeResult:
    """Mirror of test_daemon._FakeResult · keeps this file self-contained."""
    def __init__(self, passed=True, applied=True, files=None, git_commit="abc1234"):
        self.check_result = {"passed": passed}
        self.applied = applied
        self.git_commit = git_commit
        self.files_planned = files or [{"path": "phase3/soul/__init__.py", "size": 200}]


def _fake_git(monkeypatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)

        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    monkeypatch.setattr(daemon.subprocess, "run", fake_run)
    return calls


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
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: _FakeResult(passed=True, applied=True)))


def test_daemon_picks_p2_dispatch_when_yaml_empty(monkeypatch):
    """Wire gate: when goal_stack returns P2 dispatch row, daemon runs the
    shared yaml-path with task_spec as description, opens a draft PR, then
    persists goal_source on the cycle outcome AND marks the dispatch row
    shipped with the PR url as cycle_id."""
    _baseline_gates(monkeypatch)

    fake_p2 = {
        "id": "dispatch-99",
        "agent_id": 9000002,
        "task_spec": "Add a one-line module docstring to phase3/soul/__init__.py",
        "task_spec_hash": "a" * 64,
        "task_type": "code",
    }
    monkeypatch.setattr(
        "soul.goal_stack.next_goal",
        lambda: (fake_p2, GoalSource.P2_AGENT_DISPATCH),
    )

    ship_calls = []
    ship_kwargs = []

    def _fake_ship(engine, task_desc, repo, **kw):
        ship_calls.append(task_desc)
        ship_kwargs.append(kw)
        return _FakeResult(passed=True, applied=True)

    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(), _fake_ship))

    _fake_git(monkeypatch)

    pr_calls = []
    monkeypatch.setattr(
        daemon.pr_gate, "create_draft_pr",
        lambda b, t, body: (pr_calls.append((b, t, body)), "http://pr/p2-99")[1],
    )

    emitted = []
    monkeypatch.setattr(daemon, "_emit_goal_source_to_outcome",
                        lambda cid, src: emitted.append((cid, src)))

    marked = []

    def _record_mark(dispatch_id, outcome, cycle_id):
        marked.append((dispatch_id, outcome, cycle_id))

    monkeypatch.setattr(daemon, "_mark_dispatch_shipped", _record_mark)

    rc = daemon.run_once()

    # cycle completes happily
    assert rc == 0
    assert len(pr_calls) == 1, "exactly one draft PR opened for P2 dispatch"
    assert len(ship_calls) == 1, "ship called exactly once"

    # P2 row carries task_spec, not description · adapter must copy it through
    assert fake_p2["task_spec"] in ship_calls[0], (
        "task_spec must reach engine.ship as the goal description"
    )

    # Daemon must thread its cycle_id into ship · otherwise ship generates its own
    # YYYYMMDD_hex id and the later _mark_dispatch_shipped FK to
    # engine_cycle_outcomes(cycle_id) violates.
    assert "cycle_id" in ship_kwargs[0], (
        "daemon must pass cycle_id to ship so engine_cycle_outcomes shares the key"
    )
    daemon_cycle_id = ship_kwargs[0]["cycle_id"]
    assert daemon_cycle_id and daemon_cycle_id.isdigit()

    # goal_source telemetry written with P2 enum
    assert len(emitted) == 1
    cycle_id_emit, src = emitted[0]
    assert src == GoalSource.P2_AGENT_DISPATCH

    # dispatch row marked shipped · cycle_id is the daemon's epoch cycle_id
    # (matches engine_cycle_outcomes FK · NOT the PR url, which would violate
    # the agent_dispatch_log.cycle_id REFERENCES engine_cycle_outcomes(cycle_id)
    # foreign key added in the Slice A migration).
    assert len(marked) == 1
    dispatch_id, outcome, cycle_id_mark = marked[0]
    assert dispatch_id == 99, "parse dispatch_id from 'dispatch-99' id"
    assert outcome == "shipped"
    assert cycle_id_mark == cycle_id_emit, (
        "mark_dispatch_shipped and emit_goal_source must use the same cycle_id "
        "so the FK chain stays consistent"
    )
    assert cycle_id_mark and cycle_id_mark.isdigit(), (
        "cycle_id must be the daemon's epoch-seconds string"
    )


def test_daemon_p3_yaml_still_works_after_wire(monkeypatch):
    """Regression guard: existing yaml-path (P3 via goal_selector.select_goal)
    keeps working unchanged after the select_goal_with_source wire. The
    yaml-goal flow must still open one draft PR and not invoke the dispatch
    bookkeeping helper."""
    _baseline_gates(monkeypatch)

    yaml_goal = {"id": "g1", "description": "do x", "source": "yaml"}
    # Drive the new wrapper through its P3 path · the existing select_goal mock
    # must still be honored. _next_p3_self_reflection delegates to select_goal.
    monkeypatch.setattr(daemon.goal_selector, "select_goal", lambda **k: yaml_goal)

    _fake_git(monkeypatch)
    pr_calls = []
    monkeypatch.setattr(
        daemon.pr_gate, "create_draft_pr",
        lambda b, t, body: (pr_calls.append(b), "http://pr/yaml")[1],
    )

    marked = []
    monkeypatch.setattr(daemon, "_mark_dispatch_shipped",
                        lambda *a, **k: marked.append(a))

    rc = daemon.run_once()
    assert rc == 0
    assert len(pr_calls) == 1
    # yaml goal is NOT a P2 dispatch · helper must not fire
    assert marked == []


def test_daemon_emit_runs_only_on_success_but_mark_runs_on_abort_too(monkeypatch):
    """Ordering guard:
    - `_emit_goal_source_to_outcome` runs only AFTER pr_gate.create_draft_pr
      opens the PR (it UPDATES engine_cycle_outcomes which exists only on the
      happy path). On a path reject, the cycle outcome row never made it past
      ship_status='fail' (or was never inserted), so no UPDATE fires.
    - `_mark_dispatch_shipped` on the abort path stamps the dispatch row with
      the failure outcome (`pr_gate_reject` here) so the queue does not block.
      This is the backlog-blocker fix · without it the same doomed row gets
      re-picked every cycle.
    """
    _baseline_gates(monkeypatch)

    fake_p2 = {
        "id": "dispatch-7",
        "agent_id": 9000002,
        "task_spec": "Trivial change to phase3/soul/__init__.py",
        "task_spec_hash": "b" * 64,
        "task_type": "code",
    }
    monkeypatch.setattr(
        "soul.goal_stack.next_goal",
        lambda: (fake_p2, GoalSource.P2_AGENT_DISPATCH),
    )

    # Force pr_gate.check_paths to reject → branch aborts before PR opens
    monkeypatch.setattr(daemon.pr_gate, "check_paths", lambda c: (False, "blocked"))

    _fake_git(monkeypatch)
    pr_calls = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: pr_calls.append(b))

    emitted = []
    monkeypatch.setattr(daemon, "_emit_goal_source_to_outcome",
                        lambda cid, src: emitted.append((cid, src)))
    marked = []
    monkeypatch.setattr(daemon, "_mark_dispatch_shipped",
                        lambda did, outcome, cycle_id=None: marked.append((did, outcome, cycle_id)))
    monkeypatch.setattr(daemon.failure_track, "record_failure", lambda x: None)

    rc = daemon.run_once()
    assert rc == 1, "rejected path returns failure rc"
    assert len(pr_calls) == 0, "no PR opened on path reject"
    assert emitted == [], "no goal_source emit when PR never opens"
    # Abort-path stamp · backlog-blocker fix · row must not stay NULL
    assert len(marked) == 1
    did, outcome, cycle_id = marked[0]
    assert did == 7
    assert outcome == "pr_gate_reject"
    assert cycle_id is None, "no engine_cycle_outcomes row exists for abort path"

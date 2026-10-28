from soul import daemon


def test_daemon_skips_when_paused(monkeypatch):
    """人工 pause(letters_blocked=True)= 人监门至上,全停。

    9/25 熔断分层后语义收窄:本测试从"任何 pause 全停"改为"人工 pause 全停";
    breaker 自动熔断的分层行为见 test_breaker_pause_* 三例。"""
    monkeypatch.setattr(daemon.pause_check, "letters_blocked", lambda: True)
    rc = daemon.run_once()
    assert rc == 0  # graceful skip


# --- 熔断分层(9/25 用户批):breaker 自动熔断只断 ship 高危路径 ---


def test_breaker_pause_letter_reply_still_runs(monkeypatch):
    """breaker 熔断下回函型任务仍执行——组织不失联(9/25 静默 17h 病根根治)。"""
    monkeypatch.setattr(daemon.pause_check, "letters_blocked", lambda: False)
    monkeypatch.setattr(daemon.pause_check, "ship_blocked", lambda: True)
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: True)
    monkeypatch.setattr(daemon.budget_gate, "under_cap", lambda: True)
    monkeypatch.setattr(daemon, "select_goal_with_source",
                        lambda: ({"id": "mailbox-901", "task_type": "discussion",
                                  "task_spec": "x"}, None))
    replied = []
    monkeypatch.setattr(daemon, "_run_letter_reply",
                        lambda g: replied.append(g["id"]) or 0)
    rc = daemon.run_once()
    assert rc == 0
    assert replied == ["mailbox-901"]


def test_breaker_pause_ship_goal_skipped(monkeypatch):
    """breaker 熔断下 patch-ship 型目标跳过(高危动作断)。"""
    monkeypatch.setattr(daemon.pause_check, "letters_blocked", lambda: False)
    monkeypatch.setattr(daemon.pause_check, "ship_blocked", lambda: True)
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: True)
    monkeypatch.setattr(daemon.budget_gate, "under_cap", lambda: True)
    monkeypatch.setattr(daemon, "select_goal_with_source",
                        lambda: ({"id": "g-ship", "description": "do x"}, None))
    git_calls = _fake_git(monkeypatch)
    rc = daemon.run_once()
    assert rc == 0
    assert not any("-b" in c for c in git_calls)  # no branch created


def test_breaker_pause_self_improve_skipped(monkeypatch):
    """breaker 熔断下 selfimprove 路径跳过。"""
    monkeypatch.setattr(daemon.pause_check, "letters_blocked", lambda: False)
    monkeypatch.setattr(daemon.pause_check, "ship_blocked", lambda: True)
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: True)
    monkeypatch.setattr(daemon.budget_gate, "under_cap", lambda: True)
    monkeypatch.setattr(daemon, "select_goal_with_source", lambda: (None, None))
    rc = daemon.run_once()
    assert rc == 0


def test_daemon_skips_when_over_budget(monkeypatch):
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: False)
    monkeypatch.setattr(daemon.budget_gate, "under_cap", lambda: False)
    rc = daemon.run_once()
    assert rc == 0


def test_daemon_no_goal_engine_unavailable_skips(monkeypatch):
    """Engine import fails (no engine package) → graceful skip, rc 0."""
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: False)
    monkeypatch.setattr(daemon.budget_gate, "under_cap", lambda: True)
    monkeypatch.setattr(daemon.goal_selector, "select_goal", lambda **k: None)
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (_ for _ in ()).throw(ImportError("no engine")))
    rc = daemon.run_once()
    assert rc == 0


# --- apply path (Task 1) ---

class _FakeResult:
    def __init__(self, passed=True, applied=True, files=None, git_commit="abc1234"):
        self.check_result = {"passed": passed}
        self.applied = applied
        self.git_commit = git_commit
        self.files_planned = files or [{"path": "phase3/backend/engine/text_utils.py", "size": 400}]


def _gates_pass(monkeypatch):
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: False)
    monkeypatch.setattr(daemon.budget_gate, "under_cap", lambda: True)
    monkeypatch.setattr(daemon.budget_gate, "record_cost", lambda *a, **k: None)
    monkeypatch.setattr(daemon.goal_selector, "select_goal",
                        lambda **k: {"id": "g1", "description": "do x", "source": "yaml"})
    monkeypatch.setattr(daemon.pr_gate, "has_open_pr_for", lambda gid: False)


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


def test_apply_path_opens_draft_pr(monkeypatch):
    _gates_pass(monkeypatch)
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: _FakeResult(passed=True, applied=True)))
    git_calls = _fake_git(monkeypatch)
    monkeypatch.setattr(daemon.pr_gate, "check_paths", lambda c: (True, "ok"))
    monkeypatch.setattr(daemon.pr_gate, "check_diff_loc", lambda n, m=None: (True, "ok"))
    pr_calls = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: (pr_calls.append(b), "http://pr/1")[1])
    monkeypatch.setattr(daemon.failure_track, "record_success", lambda: None)
    monkeypatch.setattr(daemon.goal_selector, "mark_done", lambda gid: True)
    monkeypatch.setattr(daemon, "_run_pytest", lambda base, paths: None)
    rc = daemon.run_once()
    assert rc == 0
    assert any("-b" in c for c in git_calls)  # isolated branch created
    assert any("goals.yaml" in str(c) for c in git_calls)  # done-mark committed on branch
    assert len(pr_calls) == 1  # exactly one draft PR opened


def test_apply_path_pr_gate_reject_deletes_branch(monkeypatch):
    _gates_pass(monkeypatch)
    # blacklisted path → real pr_gate.check_paths rejects
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: _FakeResult(passed=True, applied=True,
                                                             files=[{"path": ".env", "size": 10}])))
    git_calls = _fake_git(monkeypatch)
    pr_calls = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: pr_calls.append(b))
    fails = []
    monkeypatch.setattr(daemon.failure_track, "record_failure", lambda x: fails.append(x))
    monkeypatch.setattr(daemon, "_run_pytest", lambda base, paths: None)
    rc = daemon.run_once()
    # 2026-09-10 · gate rejection is a business outcome, not a unit failure:
    # exit 0 so systemd doesn't mark the service failed (alert fatigue).
    assert rc == 0
    assert len(pr_calls) == 0  # no PR on reject
    assert any("-D" in c for c in git_calls)  # throwaway branch deleted
    assert len(fails) == 1


def test_apply_path_checks_fail_no_pr(monkeypatch):
    _gates_pass(monkeypatch)
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: _FakeResult(passed=False, applied=False)))
    git_calls = _fake_git(monkeypatch)
    pr_calls = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: pr_calls.append(b))
    monkeypatch.setattr(daemon.failure_track, "record_failure", lambda x: None)
    rc = daemon.run_once()
    assert rc == 0  # gate rejection = business outcome · exit 0 (9/10 semantics fix)
    assert len(pr_calls) == 0  # checks failed → no PR
    assert any("-D" in c for c in git_calls)  # branch cleaned up


def test_apply_path_skips_when_pr_already_open(monkeypatch):
    _gates_pass(monkeypatch)
    monkeypatch.setattr(daemon.pr_gate, "has_open_pr_for", lambda gid: True)
    git_calls = _fake_git(monkeypatch)
    rc = daemon.run_once()
    assert rc == 0  # graceful skip (not a failure)
    assert not any("-b" in c for c in git_calls)  # no branch created (anti-duplicate)


def test_apply_path_noop_opens_mark_only_pr(monkeypatch):
    _gates_pass(monkeypatch)
    # no git_commit = ship produced no code change (goal already satisfied)
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: _FakeResult(passed=True, applied=True, git_commit=None)))
    _fake_git(monkeypatch)
    monkeypatch.setattr(daemon.pr_gate, "check_paths", lambda c: (True, "ok"))
    monkeypatch.setattr(daemon.pr_gate, "check_diff_loc", lambda n, m=None: (True, "ok"))
    monkeypatch.setattr(daemon.goal_selector, "mark_done", lambda gid: True)
    bodies = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: (bodies.append(body), "http://pr/2")[1])
    monkeypatch.setattr(daemon.failure_track, "record_success", lambda: None)
    monkeypatch.setattr(daemon, "_run_pytest", lambda base, paths: None)
    rc = daemon.run_once()
    assert rc == 0
    assert len(bodies) == 1  # mark-only PR still opened (advances queue)
    assert "mark-only" in bodies[0]  # body flags no code change


# --- pytest gate (Task 2) ---

def test_pytest_gate_fail_aborts_branch_no_pr(monkeypatch):
    """run_pytest_for_changed returns False → abort branch, record_failure, no PR."""
    _gates_pass(monkeypatch)
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: _FakeResult(passed=True, applied=True)))
    git_calls = _fake_git(monkeypatch)
    monkeypatch.setattr(daemon.pr_gate, "check_paths", lambda c: (True, "ok"))
    monkeypatch.setattr(daemon.pr_gate, "check_diff_loc", lambda n, m=None: (True, "ok"))
    pr_calls = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: pr_calls.append(b))
    fails = []
    monkeypatch.setattr(daemon.failure_track, "record_failure", lambda x: fails.append(x))
    # pytest returns False → tests fail
    monkeypatch.setattr(daemon, "_run_pytest", lambda base, paths: False)
    rc = daemon.run_once()
    assert rc == 0  # pytest red = gate rejection · business outcome, exit 0
    assert len(pr_calls) == 0  # no PR when tests are red
    assert any("-D" in c for c in git_calls)  # throwaway branch deleted
    assert len(fails) == 1


def test_pytest_gate_none_proceeds_to_pr(monkeypatch):
    """run_pytest_for_changed returns None (no tests / timeout) → proceed normally."""
    _gates_pass(monkeypatch)
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: _FakeResult(passed=True, applied=True)))
    _fake_git(monkeypatch)
    monkeypatch.setattr(daemon.pr_gate, "check_paths", lambda c: (True, "ok"))
    monkeypatch.setattr(daemon.pr_gate, "check_diff_loc", lambda n, m=None: (True, "ok"))
    monkeypatch.setattr(daemon.goal_selector, "mark_done", lambda gid: True)
    pr_calls = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: (pr_calls.append(b), "http://pr/3")[1])
    monkeypatch.setattr(daemon.failure_track, "record_success", lambda: None)
    # pytest returns None → no tests found or timeout → must NOT block
    monkeypatch.setattr(daemon, "_run_pytest", lambda base, paths: None)
    rc = daemon.run_once()
    assert rc == 0
    assert len(pr_calls) == 1  # PR still opened


# --- self-improve path (Task 5) ---

def _self_improve_gates(monkeypatch):
    """Set up gates so select_goal returns None → triggers self-improve path."""
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: False)
    monkeypatch.setattr(daemon.budget_gate, "under_cap", lambda: True)
    monkeypatch.setattr(daemon.budget_gate, "record_cost", lambda *a, **k: None)
    # No yaml goal → self-improve path
    monkeypatch.setattr(daemon.goal_selector, "select_goal", lambda **k: None)
    monkeypatch.setattr(daemon.pr_gate, "has_open_pr_for", lambda gid: False)


def _fake_engine_with_llm():
    """Return a fake NautilusEngine class + ship function for self-improve tests."""
    class _FakeLLM:
        def chat(self, prompt, system="", **kw):
            return "fake-llm-response"

    class _FakeEngine:
        def __init__(self, **kw):
            self.llm = _FakeLLM()

        def _ensure_llm(self):
            pass

    def _fake_ship(engine, task_desc, repo, apply=False, git_commit_msg="", **kw):
        return _FakeResult(passed=True, applied=True)

    return _FakeEngine, _fake_ship


def test_self_improve_full_path_opens_draft_pr(monkeypatch, tmp_path):
    """No yaml goal + reviewer returns review + council returns winner → draft PR opened
    with the council winner's proposal as the task description passed to ship."""
    _self_improve_gates(monkeypatch)

    class _FakeLLM:
        def chat(self, prompt, system="", **kw):
            return "fake-llm-response"

    class _FakeEngine:
        def __init__(self, **kw):
            self.llm = _FakeLLM()

        def _ensure_llm(self):
            pass

    # Capture what task_description reaches ship (positional arg 1)
    ship_calls = []

    def _fake_ship(engine, task_desc, repo, apply=False, git_commit_msg="", **kw):
        ship_calls.append(task_desc)
        return _FakeResult(passed=True, applied=True)

    monkeypatch.setattr(daemon, "_load_engine", lambda: (_FakeEngine, _fake_ship))
    git_calls = _fake_git(monkeypatch)

    # reviewer picks a target and returns a review
    target_path = tmp_path / "budget_gate.py"
    target_path.write_text("# fake module\n")
    monkeypatch.setattr(daemon.reviewer, "pick_target", lambda soul_dir, **kw: target_path)
    monkeypatch.setattr(daemon.reviewer, "review",
                        lambda gfn, path: {
                            "target": str(path),
                            "purpose": "manages budget",
                            "description": "add type hints to public functions",
                        })

    # council produces proposals and a winning convergence
    proposals = [
        {"persona": "performance", "proposal": "add type hints", "raw": "add type hints"},
        {"persona": "robustness", "proposal": "NONE", "raw": "NONE"},
    ]
    winner = {"persona": "performance", "proposal": "add type hints",
              "raw": "add type hints", "score": 8, "reason": "improves tooling"}
    monkeypatch.setattr(daemon.council, "propose", lambda gfn, task, context, **kw: proposals)
    monkeypatch.setattr(daemon.council, "converge", lambda gfn, props, task: winner)

    monkeypatch.setattr(daemon.pr_gate, "check_paths", lambda c: (True, "ok"))
    monkeypatch.setattr(daemon.pr_gate, "check_diff_loc", lambda n, m=None: (True, "ok"))
    monkeypatch.setattr(daemon, "_run_pytest", lambda base, paths: None)
    pr_calls = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: (pr_calls.append((b, t, body)), "http://pr/si")[1])
    monkeypatch.setattr(daemon.failure_track, "record_success", lambda: None)

    rc = daemon.run_once()
    assert rc == 0
    assert any("-b" in c for c in git_calls)           # isolated branch created
    assert len(pr_calls) == 1                            # exactly one draft PR opened
    _, title, body = pr_calls[0]
    assert "budget_gate" in title                        # title references the target module
    assert "add type hints" in body                      # winning proposal in PR body
    # verify council winner's proposal + target path are in the ship task_description
    assert len(ship_calls) == 1
    assert winner["proposal"] in ship_calls[0]           # proposal embedded in ship task
    assert "budget_gate" in ship_calls[0]                # target path included (engine context + minimal-change)
    assert "COMPLETE" in ship_calls[0]                   # explicit full-file instruction (avoids prose/parse_error)


def test_self_improve_reviewer_returns_none_skips(monkeypatch, tmp_path):
    """reviewer.review returns None (module already good) → skip, rc 0, no branch."""
    _self_improve_gates(monkeypatch)

    FakeEngine, fake_ship = _fake_engine_with_llm()
    monkeypatch.setattr(daemon, "_load_engine", lambda: (FakeEngine, fake_ship))
    git_calls = _fake_git(monkeypatch)

    target_path = tmp_path / "pause_check.py"
    target_path.write_text("# fake\n")
    monkeypatch.setattr(daemon.reviewer, "pick_target", lambda soul_dir, **kw: target_path)
    monkeypatch.setattr(daemon.reviewer, "review", lambda gfn, path: None)  # already good

    pr_calls = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: pr_calls.append(b))

    rc = daemon.run_once()
    assert rc == 0
    assert not any("-b" in c for c in git_calls)  # no branch created
    assert len(pr_calls) == 0                       # no PR


def test_self_improve_council_none_proposal_skips(monkeypatch, tmp_path):
    """council winner proposal == 'NONE' → skip, rc 0, no PR."""
    _self_improve_gates(monkeypatch)

    FakeEngine, fake_ship = _fake_engine_with_llm()
    monkeypatch.setattr(daemon, "_load_engine", lambda: (FakeEngine, fake_ship))
    git_calls = _fake_git(monkeypatch)

    target_path = tmp_path / "pr_gate.py"
    target_path.write_text("# fake\n")
    monkeypatch.setattr(daemon.reviewer, "pick_target", lambda soul_dir, **kw: target_path)
    monkeypatch.setattr(daemon.reviewer, "review",
                        lambda gfn, path: {
                            "target": str(path),
                            "purpose": "manages prs",
                            "description": "improve pr gate",
                        })

    proposals = [
        {"persona": "performance", "proposal": "NONE", "raw": "NONE"},
    ]
    # council couldn't find a real proposal
    winner = {"persona": "performance", "proposal": "NONE",
              "raw": "NONE", "score": 0, "reason": "nothing to improve"}
    monkeypatch.setattr(daemon.council, "propose", lambda gfn, task, context, **kw: proposals)
    monkeypatch.setattr(daemon.council, "converge", lambda gfn, props, task: winner)

    pr_calls = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: pr_calls.append(b))

    rc = daemon.run_once()
    assert rc == 0
    assert not any("-b" in c for c in git_calls)  # no branch created
    assert len(pr_calls) == 0                       # no PR


def test_self_improve_pick_target_none_skips(monkeypatch):
    """reviewer.pick_target returns None → skip gracefully, rc 0, no branch."""
    _self_improve_gates(monkeypatch)

    FakeEngine, fake_ship = _fake_engine_with_llm()
    monkeypatch.setattr(daemon, "_load_engine", lambda: (FakeEngine, fake_ship))
    git_calls = _fake_git(monkeypatch)

    # No eligible module found
    monkeypatch.setattr(daemon.reviewer, "pick_target", lambda soul_dir, **kw: None)

    pr_calls = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: pr_calls.append(b))

    rc = daemon.run_once()
    assert rc == 0
    assert not any("-b" in c for c in git_calls)  # no branch created
    assert len(pr_calls) == 0                       # no PR


def test_self_improve_exception_in_review_returns_1_no_crash(monkeypatch, tmp_path):
    """reviewer.review raises → daemon catches it, returns 1, does NOT propagate."""
    _self_improve_gates(monkeypatch)

    FakeEngine, fake_ship = _fake_engine_with_llm()
    monkeypatch.setattr(daemon, "_load_engine", lambda: (FakeEngine, fake_ship))
    _fake_git(monkeypatch)

    target_path = tmp_path / "budget_gate.py"
    target_path.write_text("# fake module\n")
    monkeypatch.setattr(daemon.reviewer, "pick_target", lambda soul_dir, **kw: target_path)
    monkeypatch.setattr(daemon.reviewer, "review",
                        lambda gfn, path: (_ for _ in ()).throw(RuntimeError("LLM creds missing")))

    fails = []
    monkeypatch.setattr(daemon.failure_track, "record_failure", lambda x: fails.append(x))
    pr_calls = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: pr_calls.append(b))

    # Must not raise — daemon contract: every cycle returns an int rc
    rc = daemon.run_once()
    assert rc == 1          # graceful failure
    assert len(pr_calls) == 0  # no PR opened on error
    assert len(fails) == 1  # failure recorded


def test_self_improve_make_generate_fn_is_monkeypatchable(monkeypatch, tmp_path):
    """_make_generate_fn is a module-level helper that can be replaced in tests."""
    _self_improve_gates(monkeypatch)

    FakeEngine, fake_ship = _fake_engine_with_llm()
    monkeypatch.setattr(daemon, "_load_engine", lambda: (FakeEngine, fake_ship))
    _fake_git(monkeypatch)

    # Capture the generate_fn passed to reviewer.review
    captured = {}

    target_path = tmp_path / "goal_selector.py"
    target_path.write_text("# fake\n")
    monkeypatch.setattr(daemon.reviewer, "pick_target", lambda soul_dir, **kw: target_path)

    def _capture_review(gfn, path):
        captured["gfn"] = gfn
        return None  # skip rest of path

    monkeypatch.setattr(daemon.reviewer, "review", _capture_review)

    # Override _make_generate_fn to inject a sentinel generate_fn
    sentinel_fn = lambda prompt, system="": "sentinel"
    monkeypatch.setattr(daemon, "_make_generate_fn", lambda engine: sentinel_fn)

    rc = daemon.run_once()
    assert rc == 0
    assert captured.get("gfn") is sentinel_fn  # the sentinel was used


# --- Task 3: early dedup + collision-safe goal_id ---

def test_goal_id_for_includes_parent_dir():
    """_goal_id_for returns selfimprove-<parent_dir>-<stem> (disambiguated by parent dir)."""
    from pathlib import Path
    assert (daemon._goal_id_for(Path("/repo/phase3/soul/config.py"))
            == "selfimprove-soul-config")
    assert (daemon._goal_id_for(Path("/repo/phase3/backend/engine/config.py"))
            == "selfimprove-engine-config")


# --- _diff_loc: gate on real diff, not whole-file size ---

def test_diff_loc_sums_numstat_ignoring_binary_and_filenames(monkeypatch):
    """_diff_loc parses git numstat: sums added+deleted, ignores binary (-) + filenames."""
    class _R:
        returncode = 0
        # 3+1 (foo.py) + 10+0 (bar.py) = 14; binary line (- - bin.dat) ignored
        stdout = "3\t1\tfoo.py\n10\t0\tbar.py\n-\t-\tbin.dat\n"
        stderr = ""

    monkeypatch.setattr(daemon, "_git", lambda repo, *args: _R())
    assert daemon._diff_loc("/repo") == 14


def test_diff_loc_fails_open_to_zero_on_git_error(monkeypatch):
    """Non-zero git returncode → 0 (fail-open; a missed cap is recoverable)."""
    class _R:
        returncode = 1
        stdout = "3\t1\tfoo.py\n"  # must be ignored when returncode != 0
        stderr = "fatal: bad revision"

    monkeypatch.setattr(daemon, "_git", lambda repo, *args: _R())
    assert daemon._diff_loc("/repo") == 0


def test_diff_loc_small_for_minimal_change_to_large_file(tmp_path):
    """Real git repo: a 2-line change to a large file yields a small diff LOC,
    NOT the whole-file size (the bug this fix exists to prevent)."""
    import subprocess as _sp

    def g(*args):
        return _sp.run(["git", "-C", str(tmp_path), *args],
                       capture_output=True, text=True)

    g("init", "-q")
    g("config", "user.email", "t@t.t")
    g("config", "user.name", "t")
    g("checkout", "-b", "master")
    big = tmp_path / "big.py"
    big.write_text("\n".join(f"x = {i}" for i in range(200)) + "\n")
    g("add", "big.py")
    g("commit", "-q", "-m", "init")
    g("checkout", "-q", "-b", "cycle")
    lines = big.read_text().splitlines()
    lines[5] = "x = 9999"   # change 1 line
    lines.append("y = 1")   # add 1 line
    big.write_text("\n".join(lines) + "\n")
    g("add", "big.py")
    g("commit", "-q", "-m", "minimal change")

    loc = daemon._diff_loc(str(tmp_path), base="master")
    assert loc > 0
    assert loc < 20  # small real diff, NOT the 200-line whole-file size


def test_self_improve_early_dedup_skips_before_review(monkeypatch, tmp_path):
    """When has_open_pr_for is True, skip BEFORE any review/council LLM call."""
    _self_improve_gates(monkeypatch)

    FakeEngine, fake_ship = _fake_engine_with_llm()
    monkeypatch.setattr(daemon, "_load_engine", lambda: (FakeEngine, fake_ship))
    git_calls = _fake_git(monkeypatch)

    target_path = tmp_path / "config.py"
    target_path.write_text("# fake\n")
    monkeypatch.setattr(daemon.reviewer, "pick_target", lambda soul_dir, **kw: target_path)

    # If review runs, this flag flips — it must STAY False (early dedup).
    review_ran = {"flag": False}

    def _flag_review(gfn, path):
        review_ran["flag"] = True
        return {"target": str(path), "purpose": "p", "description": "d"}

    monkeypatch.setattr(daemon.reviewer, "review", _flag_review)
    # generate_fn must not even be needed before dedup
    monkeypatch.setattr(daemon, "_make_generate_fn",
                        lambda engine: (lambda prompt, system="": "x"))
    # PR already open → must skip immediately
    monkeypatch.setattr(daemon.pr_gate, "has_open_pr_for", lambda gid: True)

    pr_calls = []
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: pr_calls.append(b))

    rc = daemon.run_once()
    assert rc == 0
    assert review_ran["flag"] is False  # review never ran (dedup is early)
    assert not any("-b" in c for c in git_calls)  # no branch created
    assert len(pr_calls) == 0


# --- Task 4: integration · scoped rotation reaches engine modules ---

def test_scoped_rotation_reaches_engine_module(tmp_path):
    """With soul modules already reviewed, the next scoped pick is an engine module."""
    import json as _json
    import time as _time
    from soul import reviewer

    soul = tmp_path / "phase3" / "soul"
    soul.mkdir(parents=True)
    (soul / "config.py").write_text("# soul config\n")
    (soul / "daemon.py").write_text("# soul daemon\n")
    engine = tmp_path / "phase3" / "backend" / "engine"
    engine.mkdir(parents=True)
    (engine / "ship.py").write_text("# engine ship\n")
    (engine / "config.py").write_text("# engine config\n")

    globs = ("phase3/soul/*.py", "phase3/backend/engine/*.py")
    state_file = tmp_path / "state.json"

    # Mark all soul modules reviewed recently → engine is least-recently-reviewed
    now = _time.time()
    state_file.write_text(_json.dumps({
        "phase3/soul/config.py": now,
        "phase3/soul/daemon.py": now,
    }))

    chosen = reviewer.pick_target(soul, state_file=state_file,
                                  scope_globs=globs, repo_root=tmp_path)
    assert chosen is not None
    rel = chosen.relative_to(tmp_path).as_posix()
    assert rel.startswith("phase3/backend/engine/")  # rotation reached engine

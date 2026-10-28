from soul import pr_gate


def test_blacklist_rejects():
    ok, reason = pr_gate.check_paths([".env", "phase3/soul/daemon.py"])
    assert ok is False
    assert ".env" in reason


def test_clean_paths_pass():
    ok, reason = pr_gate.check_paths(["phase3/soul/daemon.py", "README.md"])
    assert ok is True


def test_diff_cap_rejects():
    ok, reason = pr_gate.check_diff_loc(600)
    assert ok is False


def test_diff_cap_allows():
    ok, reason = pr_gate.check_diff_loc(400)
    assert ok is True


def test_create_draft_pr_invokes_gh(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)

        class R:
            returncode = 0
            stdout = "https://github.com/chunxiaoxx/nautilus-core/pull/123\n"
            stderr = ""

        return R()

    monkeypatch.setattr(pr_gate.subprocess, "run", fake_run)
    url = pr_gate.create_draft_pr("soul/cycle-x", "Soul: test", "body text")
    assert "pull/123" in url
    # confirm --draft flag present in the gh pr create call
    assert any("--draft" in c for c in calls if isinstance(c, list))


def test_has_open_pr_for_detects_existing(monkeypatch):
    """Exact title 'soul: <goal_id>' must dedup."""
    def fake_run(cmd, **kwargs):
        class R:
            returncode = 0
            stdout = '[{"number": 5, "title": "soul: c1"}]'
            stderr = ""
        return R()
    monkeypatch.setattr(pr_gate.subprocess, "run", fake_run)
    assert pr_gate.has_open_pr_for("c1") is True


def test_has_open_pr_for_none(monkeypatch):
    def fake_run(cmd, **kwargs):
        class R:
            returncode = 0
            stdout = "[]"
            stderr = ""
        return R()
    monkeypatch.setattr(pr_gate.subprocess, "run", fake_run)
    assert pr_gate.has_open_pr_for("c1") is False


def test_has_open_pr_for_ignores_fuzzy_gh_search_match(monkeypatch):
    """Slice B followup regression · gh search tokenizes the title query, so a
    PR titled 'feat(soul): ... /api/soul/dispatch ...' lands in the result
    set for goal_id='dispatch-3'. Post-fetch title check must reject it · only
    titles that start with the exact 'soul: <goal_id>' prefix count as a real
    dedup hit."""
    def fake_run(cmd, **kwargs):
        class R:
            returncode = 0
            # gh search returned a fuzzy match — different title, not a real dedup
            stdout = (
                '[{"number": 81, '
                '"title": "feat(soul): Inc 3 Slice B · /api/soul/dispatch + daemon wire"}]'
            )
            stderr = ""
        return R()
    monkeypatch.setattr(pr_gate.subprocess, "run", fake_run)
    assert pr_gate.has_open_pr_for("dispatch-3") is False, (
        "fuzzy gh search hit must not block · exact prefix is the gate"
    )


def test_has_open_pr_for_fail_open(monkeypatch):
    def fake_run(cmd, **kwargs):
        class R:
            returncode = 1
            stdout = ""
            stderr = "gh error"
        return R()
    monkeypatch.setattr(pr_gate.subprocess, "run", fake_run)
    assert pr_gate.has_open_pr_for("c1") is False  # fail-open

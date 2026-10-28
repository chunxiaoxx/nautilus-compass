"""Slice D-precursor · fitness function infrastructure.

After honest 5/29 diagnosis: the recursive self-improvement loop is
mechanically wired (Slice A/B/C) but has no reward signal · daemon LLM
proposes changes without ground truth that says 'this improved anything'.

This test suite locks the minimum scaffolding needed to compute a fitness
signal per cycle:

  before_snap = {ruff_warnings: N, pytest_collect: M}   # captured pre-ship
  after_snap  = {ruff_warnings: N',pytest_collect: M'}  # captured post-ship
  fitness_delta = (N - N') + (M' - M)                   # warnings down good, tests up good

  -> persisted to engine_cycle_outcomes.fitness_delta NUMERIC(8,3)

Honest scope · this PR ships the MECHANISM only.
Whether the fitness signal carries useful information is a separate
empirical question (needs 10+ daemon cycles with the metric live to see
the delta distribution). Do NOT declare 'fitness function works' from
this PR alone · only 'mechanism wired + 1 cycle stamp verified'.
"""
from __future__ import annotations
from soul import daemon


# ---------------------------------------------------------------------------
# _compute_snapshot · subprocess wrappers (ruff + pytest collect)
# ---------------------------------------------------------------------------


def test_compute_snapshot_returns_ruff_and_pytest_counts(monkeypatch, tmp_path):
    """_compute_snapshot calls ruff + pytest collect, returns the parsed counts."""
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)

        class R:
            returncode = 0
            stderr = ""

            @property
            def stdout(self):
                if "ruff" in cmd:
                    # ruff check --statistics output: trailing line "Found N errors."
                    return "Found 42 errors.\n"
                if "pytest" in cmd:
                    return "100 tests collected in 0.10s\n"
                return ""

        return R()

    monkeypatch.setattr(daemon.subprocess, "run", fake_run)
    snap = daemon._compute_snapshot(str(tmp_path))
    assert snap == {"ruff_warnings": 42, "pytest_collect": 100}


def test_compute_snapshot_fail_open_on_ruff_error(monkeypatch, tmp_path):
    """ruff non-zero exit -> ruff_warnings=0 · NEVER raise."""
    def fake_run(cmd, **kw):
        class R:
            returncode = 1
            stderr = "ruff not installed"
            stdout = ""
        return R()
    monkeypatch.setattr(daemon.subprocess, "run", fake_run)
    snap = daemon._compute_snapshot(str(tmp_path))
    assert snap["ruff_warnings"] == 0
    assert snap["pytest_collect"] == 0


def test_compute_snapshot_handles_unparseable_output(monkeypatch, tmp_path):
    """If ruff/pytest output cannot be parsed, return 0 not None · the fitness
    formula tolerates 0 better than None (subtraction would raise)."""
    def fake_run(cmd, **kw):
        class R:
            returncode = 0
            stderr = ""
            stdout = "garbage with no numbers at all\n"
        return R()
    monkeypatch.setattr(daemon.subprocess, "run", fake_run)
    snap = daemon._compute_snapshot(str(tmp_path))
    assert snap["ruff_warnings"] == 0
    assert snap["pytest_collect"] == 0


# ---------------------------------------------------------------------------
# _fitness_delta · pure math
# ---------------------------------------------------------------------------


def test_fitness_delta_warnings_down_tests_up_is_positive():
    before = {"ruff_warnings": 50, "pytest_collect": 100}
    after = {"ruff_warnings": 45, "pytest_collect": 103}
    # warnings down by 5, tests up by 3 -> +8
    assert daemon._fitness_delta(before, after) == 8.0


def test_fitness_delta_warnings_up_is_negative():
    before = {"ruff_warnings": 10, "pytest_collect": 100}
    after = {"ruff_warnings": 15, "pytest_collect": 100}
    # warnings up by 5 -> -5
    assert daemon._fitness_delta(before, after) == -5.0


def test_fitness_delta_no_change_is_zero():
    snap = {"ruff_warnings": 30, "pytest_collect": 100}
    assert daemon._fitness_delta(snap, snap) == 0.0


def test_fitness_delta_missing_key_treated_as_zero():
    """A snapshot missing a key (e.g. tool not installed yet) does not crash."""
    before = {"ruff_warnings": 5}
    after = {"ruff_warnings": 3, "pytest_collect": 100}
    # warnings: 5-3 = +2; tests: 100 - 0 (missing treated as 0) = +100; total +102
    assert daemon._fitness_delta(before, after) == 102.0


# ---------------------------------------------------------------------------
# _stamp_fitness · psycopg2 UPDATE on engine_cycle_outcomes
# ---------------------------------------------------------------------------


def test_stamp_fitness_updates_outcome_row(monkeypatch):
    """_stamp_fitness UPDATES engine_cycle_outcomes.fitness_delta for the
    given cycle_id · fail-open on DB error."""
    import sys
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")

    sql_calls = []

    class _Cursor:
        def execute(self, sql, args):
            sql_calls.append((sql, args))

    class _Conn:
        def cursor(self):
            return _Cursor()

        def commit(self):
            pass

        def close(self):
            pass

    fake_pg = type(sys)("psycopg2")
    fake_pg.connect = lambda dsn: _Conn()
    monkeypatch.setitem(sys.modules, "psycopg2", fake_pg)

    daemon._stamp_fitness("1780062515", 7.5)

    assert len(sql_calls) == 1
    sql, args = sql_calls[0]
    assert "engine_cycle_outcomes" in sql
    assert "fitness_delta" in sql
    assert args == (7.5, "1780062515")


def test_stamp_fitness_noop_when_db_unset(monkeypatch):
    """No DATABASE_URL -> silent no-op · no exception."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    daemon._stamp_fitness("anything", 1.0)  # must not raise


def test_stamp_fitness_noop_when_delta_is_none(monkeypatch):
    """Calling with None delta (snapshot failed both sides) is a no-op."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")
    import sys
    sql_calls = []

    class _Cursor:
        def execute(self, sql, args):
            sql_calls.append((sql, args))

    class _Conn:
        def cursor(self):
            return _Cursor()

        def commit(self):
            pass

        def close(self):
            pass

    fake_pg = type(sys)("psycopg2")
    fake_pg.connect = lambda dsn: _Conn()
    monkeypatch.setitem(sys.modules, "psycopg2", fake_pg)
    daemon._stamp_fitness("cycle-x", None)
    assert sql_calls == [], "None delta must NOT trigger an UPDATE"

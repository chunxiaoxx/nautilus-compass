"""L4 close-loop · daemon ship → INSERT platform_improvement_proposals so
on_pr_merge_hook fires NAU settlement when a human merges the soul PR.

Design (anchor #2 · 递归自我提升闭环):
- daemon-PR bypasses L3 vote (autonomous · no governance review happened),
  but it consumes the SAME L4 settlement machinery via a synthetic
  proposal row written with status='executed_ok' / resolved_by='soul'.
- agent_id=9000002 (V5 Nautilus Prime seed) is reused as the credited
  author until a dedicated soul agent seed exists.
- Fail-open · any DB error logs + swallows; the cycle stays alive and
  the PR is still mergeable manually.

Tests cover the three callable contracts of _record_l4_proposal:
1. happy path · INSERT issued with expected proposal_id + JSONB payload
2. no DSN · early-return without import attempt
3. psycopg2 raise · swallowed (logger.warning · cycle does not crash)
"""
import sys
from unittest.mock import MagicMock

import pytest

from soul import daemon


@pytest.fixture(autouse=True)
def _isolate_psycopg2(monkeypatch):
    """Remove any prior cached psycopg2 module so tests can inject mocks."""
    yield
    sys.modules.pop("psycopg2", None)


def test_record_l4_proposal_inserts_row_when_dsn_present(monkeypatch):
    """Happy path · with DATABASE_URL set, helper issues one INSERT carrying the
    daemon proposal_id, the soul resolved_by stamp, and a JSONB payload that
    embeds pr_url + cycle_id so on_pr_merge_hook can correlate later."""
    fake_conn = MagicMock()
    fake_cur = MagicMock()
    fake_conn.cursor.return_value = fake_cur

    fake_psyco = MagicMock()
    fake_psyco.connect.return_value = fake_conn
    monkeypatch.setitem(sys.modules, "psycopg2", fake_psyco)
    monkeypatch.setenv("DATABASE_URL", "postgresql://test@localhost/test")

    daemon._record_l4_proposal(
        pr_url="https://github.com/chunxiaoxx/nautilus-core/pull/99",
        pr_number=99,
        cycle_id="1780099999",
        source_value="soul_daemon",
        goal_id="selfimprove-engine-foo",
        dispatch_id=None,
    )

    fake_cur.execute.assert_called_once()
    sql_arg, params = fake_cur.execute.call_args[0]
    assert "INSERT INTO platform_improvement_proposals" in sql_arg
    assert "ON CONFLICT" in sql_arg  # idempotent guard
    assert "executed_ok" in sql_arg  # status hard-coded
    assert "soul" in sql_arg  # resolved_by hard-coded

    # proposal_id is the first positional param · matches the daemon-pr-N-CYCLE pattern
    assert params[0] == "daemon-pr-99-1780099999"
    # JSON payload embeds correlation keys
    payload = params[2]
    assert "https://github.com/chunxiaoxx/nautilus-core/pull/99" in payload
    assert "1780099999" in payload
    assert "selfimprove-engine-foo" in payload

    fake_conn.commit.assert_called_once()
    fake_conn.close.assert_called_once()


def test_record_l4_proposal_no_op_when_no_dsn(monkeypatch):
    """Without DATABASE_URL, helper returns without attempting psycopg2 import."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    sentinel_psyco = MagicMock()
    sentinel_psyco.connect.side_effect = AssertionError(
        "psycopg2.connect must NOT be called when DATABASE_URL is absent"
    )
    monkeypatch.setitem(sys.modules, "psycopg2", sentinel_psyco)

    # Must not raise.
    daemon._record_l4_proposal(
        pr_url="https://github.com/repo/pull/1",
        pr_number=1,
        cycle_id="cyc",
        source_value=None,
        goal_id="g",
        dispatch_id=None,
    )
    sentinel_psyco.connect.assert_not_called()


def test_record_l4_proposal_swallows_psycopg_errors(monkeypatch):
    """Any DB error during INSERT must not propagate (cycle stays alive)."""
    fake_psyco = MagicMock()
    fake_psyco.connect.side_effect = RuntimeError("connection refused")
    monkeypatch.setitem(sys.modules, "psycopg2", fake_psyco)
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")

    # Must not raise · fail-open contract identical to _emit_goal_source_to_outcome.
    daemon._record_l4_proposal(
        pr_url="https://github.com/repo/pull/1",
        pr_number=1,
        cycle_id="cyc",
        source_value=None,
        goal_id="g",
        dispatch_id=None,
    )


def test_record_l4_proposal_no_op_when_pr_number_missing(monkeypatch):
    """If ship returned no PR (None url), helper returns silently. Guards against
    pr_gate.create_draft_pr returning None on the rare GH outage."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    fake_psyco = MagicMock()
    fake_psyco.connect.side_effect = AssertionError(
        "psycopg2.connect must NOT be called when pr_url is missing"
    )
    monkeypatch.setitem(sys.modules, "psycopg2", fake_psyco)

    daemon._record_l4_proposal(
        pr_url="",
        pr_number=None,
        cycle_id="cyc",
        source_value=None,
        goal_id="g",
        dispatch_id=None,
    )
    fake_psyco.connect.assert_not_called()

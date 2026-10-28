"""Inc 2 Slice 5 · blessing mechanism · 3 cases per design Section 6.

Cases:
  (a) test_blessing_rejected_blesser_below_80
  (b) test_blessing_rejected_proposer_above_60
  (c) test_blessing_amplifies_at_settle  · E2E rep_voting + proposer bonus

Tests seed two fresh test agents (PROPOSER_ID + BLESSER_ID) so V5/Kairos/V7
rows are untouched. Cleanup uses DELETE on those agent IDs; FK chain via
proposal_blessings → proposal_id is also cleaned.

Postgres-only via DATABASE_URL gate (matches sibling Inc 2 tests).
"""
from __future__ import annotations

import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from services.inc2_settlement import (
    bless_proposal,
    settle_blessings_for,
    _apply_proposer_blessing_bonus,
)


pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="Postgres-only"
)


# Test sentinel IDs · 9_100_5xx range to avoid V5 (9_000_002) etc collisions
PROPOSER_ID = 9100501
BLESSER_ID = 9100502


@pytest.fixture
def db():
    engine = create_engine(os.environ["DATABASE_URL"])
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.rollback()
    s.close()


def _seed_agent(
    db, agent_id: int, name: str,
    rep_proposing: float = 50.0,
    rep_voting: float = 50.0,
) -> None:
    """Idempotent agent seed · upsert rep values for deterministic state."""
    db.execute(text(
        "INSERT INTO agents (id, agent_id, owner, name, reputation, "
        " rep_proposing, rep_voting, created_at) "
        "VALUES (:id, :aid, :owner, :name, 50, :rp, :rv, NOW()) "
        "ON CONFLICT (id) DO UPDATE "
        "SET rep_proposing = EXCLUDED.rep_proposing, "
        "    rep_voting    = EXCLUDED.rep_voting"
    ), {
        "id": agent_id,
        "aid": agent_id,
        "owner": f"0xtest{agent_id:040x}"[:42],
        "name": name,
        "rp": rep_proposing,
        "rv": rep_voting,
    })
    db.commit()


def _seed_proposal(db, pid: str, agent_id: int) -> None:
    db.execute(text(
        "INSERT INTO platform_improvement_proposals "
        "(id, task_id, agent_id, root_cause, proposed_change, "
        " expected_impact, rollback_plan, status, vote_score, vote_count, "
        " created_at, tenant_id, resolved_by) "
        "VALUES (:id, 9000001, :aid, 'slice5-test', "
        "        '{\"type\":\"code\",\"task\":\"noop\"}'::jsonb, "
        "        'test', 'noop', 'executed_ok', 7, 3, NOW(), 'default', 'soul')"
    ), {"id": pid, "aid": agent_id})
    db.commit()


def _cleanup(db, pid: str) -> None:
    db.execute(text("DELETE FROM proposal_blessings WHERE proposal_id = :p"), {"p": pid})
    db.execute(text("DELETE FROM pending_nau_rewards WHERE source_id = :s"), {"s": pid})
    db.execute(text("DELETE FROM proposal_outcomes WHERE proposal_id = :p"), {"p": pid})
    db.execute(text("DELETE FROM platform_improvement_proposals WHERE id = :p"), {"p": pid})
    db.execute(text("DELETE FROM agents WHERE id IN (:p, :b)"), {"p": PROPOSER_ID, "b": BLESSER_ID})
    db.commit()


# ---------------------------------------------------------------------------
# (a) blesser rep_voting < 80 → rejected
# ---------------------------------------------------------------------------
def test_blessing_rejected_blesser_below_80(db):
    pid = "inc2-slice5-test-blesser-untrusted-1"
    try:
        # Proposer is UNTRUSTED (rep_proposing < 60) so the OTHER guard passes;
        # only the blesser guard should fire.
        _seed_agent(db, PROPOSER_ID, "test-proposer", rep_proposing=45.0, rep_voting=50.0)
        _seed_agent(db, BLESSER_ID, "test-blesser-untrusted", rep_proposing=50.0, rep_voting=79.99)
        _seed_proposal(db, pid, PROPOSER_ID)

        result = bless_proposal(db, proposal_id=pid, blesser_id=BLESSER_ID)
        assert result["blessed"] is False
        assert "blesser rep_voting" in result["reason"]
        assert "not TRUSTED" in result["reason"]

        # Verify no proposal_blessings row was inserted
        row = db.execute(text(
            "SELECT COUNT(*) FROM proposal_blessings WHERE proposal_id = :p"
        ), {"p": pid}).scalar()
        assert row == 0
    finally:
        _cleanup(db, pid)


# ---------------------------------------------------------------------------
# (b) proposer rep_proposing >= 60 → rejected (already TRUSTED · no mentor needed)
# ---------------------------------------------------------------------------
def test_blessing_rejected_proposer_above_60(db):
    pid = "inc2-slice5-test-proposer-trusted-1"
    try:
        # Proposer is TRUSTED · blesser is TRUSTED (so other guard passes)
        _seed_agent(db, PROPOSER_ID, "test-proposer-trusted", rep_proposing=72.0, rep_voting=50.0)
        _seed_agent(db, BLESSER_ID, "test-blesser-trusted", rep_proposing=50.0, rep_voting=88.0)
        _seed_proposal(db, pid, PROPOSER_ID)

        result = bless_proposal(db, proposal_id=pid, blesser_id=BLESSER_ID)
        assert result["blessed"] is False
        assert "proposer rep_proposing" in result["reason"]
        assert "not UNTRUSTED" in result["reason"]

        row = db.execute(text(
            "SELECT COUNT(*) FROM proposal_blessings WHERE proposal_id = :p"
        ), {"p": pid}).scalar()
        assert row == 0
    finally:
        _cleanup(db, pid)


# ---------------------------------------------------------------------------
# (c) happy path · settle amplifies blesser rep_voting + proposer bonus
# ---------------------------------------------------------------------------
def test_blessing_amplifies_at_settle(db):
    pid = "inc2-slice5-test-settle-amplify-1"
    try:
        # Setup: proposer UNTRUSTED (45.0) · blesser TRUSTED (85.0)
        _seed_agent(db, PROPOSER_ID, "test-proposer-untrusted",
                    rep_proposing=45.0, rep_voting=50.0)
        _seed_agent(db, BLESSER_ID, "test-blesser-trusted",
                    rep_proposing=50.0, rep_voting=85.0)
        _seed_proposal(db, pid, PROPOSER_ID)

        # 1. Bless · stake = 85.0 × 0.1 = 8.5
        bless_result = bless_proposal(db, proposal_id=pid, blesser_id=BLESSER_ID)
        assert bless_result["blessed"] is True
        assert abs(bless_result["stake_amount"] - 8.5) < 1e-6

        row = db.execute(text(
            "SELECT settled, settled_outcome, stake_amount "
            "FROM proposal_blessings WHERE proposal_id = :p"
        ), {"p": pid}).fetchone()
        assert row[0] is False
        assert row[1] is None
        assert abs(float(row[2]) - 8.5) < 1e-6

        # 2. Idempotent re-bless → reason='already blessed'
        re_bless = bless_proposal(db, proposal_id=pid, blesser_id=BLESSER_ID)
        assert re_bless["blessed"] is False
        assert "already blessed" in re_bless["reason"]

        # 3. settle_blessings_for · composite_delta = +1.0
        #    expected blesser delta = +1.0 × sqrt(1.0) × 3.0 = +3.0
        #    expected new rep_voting = 85.0 + 3.0 = 88.0
        settle_results = settle_blessings_for(db, pid, composite_delta=1.0)
        db.commit()
        assert len(settle_results) == 1
        sr = settle_results[0]
        assert sr["blesser_id"] == BLESSER_ID
        assert abs(sr["rep_delta"] - 3.0) < 1e-6
        assert abs(sr["new_rep_voting"] - 88.0) < 1e-6
        assert sr["settled_outcome"] == '+'

        # Verify DB state
        rv = db.execute(text(
            "SELECT rep_voting FROM agents WHERE id = :aid"
        ), {"aid": BLESSER_ID}).scalar()
        assert abs(float(rv) - 88.0) < 1e-6

        row = db.execute(text(
            "SELECT settled, settled_outcome FROM proposal_blessings WHERE proposal_id = :p"
        ), {"p": pid}).fetchone()
        assert row[0] is True
        assert row[1] == '+'

        # 4. Idempotent settle on already-settled blessings → empty list
        again = settle_blessings_for(db, pid, composite_delta=1.0)
        assert again == []

        # 5. Proposer blessing bonus · expected delta = +1.0 × 1.0 × 2.0 = +2.0
        bonus = _apply_proposer_blessing_bonus(db, PROPOSER_ID, composite_delta=1.0)
        db.commit()
        assert bonus["applied"] is True
        assert abs(bonus["rep_delta"] - 2.0) < 1e-6
        assert abs(bonus["new_rep_proposing"] - 47.0) < 1e-6

        rp = db.execute(text(
            "SELECT rep_proposing FROM agents WHERE id = :aid"
        ), {"aid": PROPOSER_ID}).scalar()
        assert abs(float(rp) - 47.0) < 1e-6
    finally:
        _cleanup(db, pid)

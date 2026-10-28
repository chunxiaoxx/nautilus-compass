"""Inc 2 Slice 6 · collaborative authorship · 3 cases per design Section 6.

Cases:
  (a) test_single_author_backfill_weight_1 · legacy proposal helper fallback
  (b) test_multi_author_nau_split_by_weight · on_pr_merge_hook splits NAU
      per contribution_weight; settle path applies D4 rep × weight per author
  (c) test_multi_author_self_vote_prevention_all · vote endpoint blocks ALL
      authors (not just primary submitter)

Postgres-gated via DATABASE_URL skipif. Test agent IDs 9_100_6xx to avoid
collision with Slice 5 (9_100_5xx), V5/Kairos/V7, and seed sentinels.
"""
from __future__ import annotations

import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from services.inc2_settlement import (
    _get_proposal_authors,
    on_pr_merge_hook,
    grade_pending_settlements,
    process_graded_settlements,
)


pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="Postgres-only"
)


AUTHOR_A_ID = 9100601
AUTHOR_B_ID = 9100602
LEGACY_AUTHOR_ID = 9100603


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
    db.execute(text(
        "INSERT INTO agents (id, agent_id, owner, name, reputation, "
        " rep_proposing, rep_voting, created_at) "
        "VALUES (:id, :aid, :owner, :name, 50, :rp, :rv, NOW()) "
        "ON CONFLICT (id) DO UPDATE "
        "SET rep_proposing = EXCLUDED.rep_proposing, "
        "    rep_voting    = EXCLUDED.rep_voting"
    ), {
        "id": agent_id, "aid": agent_id,
        "owner": f"0xtest{agent_id:040x}"[:42],
        "name": name, "rp": rep_proposing, "rv": rep_voting,
    })
    db.commit()


def _seed_proposal(db, pid: str, primary_agent_id: int) -> None:
    db.execute(text(
        "INSERT INTO platform_improvement_proposals "
        "(id, task_id, agent_id, root_cause, proposed_change, "
        " expected_impact, rollback_plan, status, vote_score, vote_count, "
        " created_at, tenant_id, resolved_by) "
        "VALUES (:id, 9000001, :aid, 'slice6-test', "
        "        '{\"type\":\"code\",\"task\":\"noop\"}'::jsonb, "
        "        'test', 'noop', 'executed_ok', 7, 3, NOW(), 'default', 'soul')"
    ), {"id": pid, "aid": primary_agent_id})
    db.commit()


def _seed_proposal_authors(db, pid: str, authors: list[tuple[int, float]]) -> None:
    for aid, w in authors:
        db.execute(text(
            "INSERT INTO proposal_authors (proposal_id, agent_id, contribution_weight) "
            "VALUES (:p, :a, :w) "
            "ON CONFLICT (proposal_id, agent_id) DO NOTHING"
        ), {"p": pid, "a": aid, "w": w})
    db.commit()


def _cleanup(db, pid: str, agent_ids: list[int]) -> None:
    db.execute(text("DELETE FROM proposal_authors WHERE proposal_id = :p"), {"p": pid})
    db.execute(text("DELETE FROM pending_nau_rewards WHERE source_id = :p"), {"p": pid})
    db.execute(text("DELETE FROM proposal_outcomes WHERE proposal_id = :p"), {"p": pid})
    db.execute(text("DELETE FROM platform_improvement_proposals WHERE id = :p"), {"p": pid})
    if agent_ids:
        db.execute(text("DELETE FROM agents WHERE id = ANY(:ids)"), {"ids": agent_ids})
    db.commit()


# ---------------------------------------------------------------------------
# (a) legacy proposal helper falls back to weight=1.0 even without
#     proposal_authors row (defensive · works pre-migration too)
# ---------------------------------------------------------------------------
def test_single_author_backfill_weight_1(db):
    pid = "inc2-slice6-test-legacy-1"
    try:
        _seed_agent(db, LEGACY_AUTHOR_ID, "test-legacy-author")
        _seed_proposal(db, pid, LEGACY_AUTHOR_ID)
        # Note: deliberately do NOT insert into proposal_authors. The helper
        # should fall back to (LEGACY_AUTHOR_ID, 1.0).
        # Clean any pre-existing proposal_authors row in case Slice 6 migration
        # backfill on this proposal id was already run.
        db.execute(text(
            "DELETE FROM proposal_authors WHERE proposal_id = :p"
        ), {"p": pid})
        db.commit()

        authors = _get_proposal_authors(db, pid)
        assert authors == [(LEGACY_AUTHOR_ID, 1.0)], f"got {authors}"
    finally:
        _cleanup(db, pid, [LEGACY_AUTHOR_ID])


# ---------------------------------------------------------------------------
# (b) multi-author proposal: on_pr_merge_hook splits NAU by weight
# ---------------------------------------------------------------------------
def test_multi_author_nau_split_by_weight(db):
    pid = "inc2-slice6-test-multi-split-1"
    try:
        _seed_agent(db, AUTHOR_A_ID, "test-author-A", rep_proposing=50.0)
        _seed_agent(db, AUTHOR_B_ID, "test-author-B", rep_proposing=50.0)
        _seed_proposal(db, pid, AUTHOR_A_ID)  # A is primary submitter
        _seed_proposal_authors(db, pid, [(AUTHOR_A_ID, 0.6), (AUTHOR_B_ID, 0.4)])

        # Verify authors helper returns both rows
        authors = _get_proposal_authors(db, pid)
        author_map = dict(authors)
        assert abs(author_map[AUTHOR_A_ID] - 0.6) < 1e-6
        assert abs(author_map[AUTHOR_B_ID] - 0.4) < 1e-6

        # on_pr_merge_hook with nau_amount=100 → 60 + 40
        result = on_pr_merge_hook(
            db, proposal_id=pid,
            merged_pr_url="https://example.invalid/pr/1",
            nau_amount=100,
        )
        assert result["pending_created"] is True
        assert result["outcomes_created"] is True
        assert set(result["authors_credited"]) == {AUTHOR_A_ID, AUTHOR_B_ID}

        # Verify 2 pending rows with split amounts
        rows = db.execute(text(
            "SELECT agent_id, amount, status FROM pending_nau_rewards "
            "WHERE source_id = :p ORDER BY agent_id"
        ), {"p": pid}).fetchall()
        assert len(rows) == 2
        amts = {int(r[0]): int(r[1]) for r in rows}
        assert amts[AUTHOR_A_ID] == 60
        assert amts[AUTHOR_B_ID] == 40
        assert all(r[2] == "pending" for r in rows)

        # Re-run hook idempotent · no new rows
        result_2 = on_pr_merge_hook(
            db, proposal_id=pid,
            merged_pr_url="https://example.invalid/pr/1",
            nau_amount=100,
        )
        assert result_2["authors_credited"] == []  # nothing new
        cnt = db.execute(text(
            "SELECT COUNT(*) FROM pending_nau_rewards WHERE source_id = :p"
        ), {"p": pid}).scalar()
        assert cnt == 2

        # End-to-end settle: grade with stale_hours=0 then process · assert
        # per-author D4 rep_delta scaled by weight.
        # composite_delta will be 0.5 (no_revert bonus 0.5 + 0 rate delta)
        # author A delta = +sqrt(0.5) × 5.0 × 0.6 ≈ +2.121
        # author B delta = +sqrt(0.5) × 5.0 × 0.4 ≈ +1.414
        graded = grade_pending_settlements(db, stale_hours=0)
        assert graded == 2  # both rows graded together (proposal_outcomes row)
        results = process_graded_settlements(db, limit=10)
        assert len(results) == 2
        # Verify each result reports weight + per-author rep_delta
        by_aid = {r["agent_id"]: r for r in results}
        rep_a = by_aid[AUTHOR_A_ID]["rep_update"]["rep_delta"]
        rep_b = by_aid[AUTHOR_B_ID]["rep_update"]["rep_delta"]
        assert rep_a > 0 and rep_b > 0
        assert abs(rep_a / rep_b - (0.6 / 0.4)) < 1e-3, f"ratio: rep_a={rep_a} rep_b={rep_b}"
        # Each author got positive ledger entry (delta>0 fulfills)
        assert by_aid[AUTHOR_A_ID]["status"] == "fulfilled"
        assert by_aid[AUTHOR_B_ID]["status"] == "fulfilled"
    finally:
        _cleanup(db, pid, [AUTHOR_A_ID, AUTHOR_B_ID])


# ---------------------------------------------------------------------------
# (c) vote endpoint rejects ALL authors (Slice 6 extends self-vote check)
# ---------------------------------------------------------------------------
def test_multi_author_self_vote_prevention_all(db):
    """Direct service-layer check + endpoint round-trip via TestClient."""
    pid = "inc2-slice6-test-vote-block-1"
    try:
        _seed_agent(db, AUTHOR_A_ID, "test-author-A")
        _seed_agent(db, AUTHOR_B_ID, "test-author-B")
        _seed_proposal(db, pid, AUTHOR_A_ID)
        _seed_proposal_authors(db, pid, [(AUTHOR_A_ID, 0.5), (AUTHOR_B_ID, 0.5)])

        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)

        # Both authors → blocked
        for aid in (AUTHOR_A_ID, AUTHOR_B_ID):
            resp = client.post(
                f"/api/platform/proposals/{pid}/vote",
                json={"agent_id": aid, "vote": 1},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["success"] is False, f"author {aid} should be blocked: {body}"
            assert "self-vote forbidden" in body["error"], body

        # No vote rows persisted
        cnt = db.execute(text(
            "SELECT COUNT(*) FROM platform_proposal_votes WHERE proposal_id = :p"
        ), {"p": pid}).scalar()
        assert cnt == 0
    finally:
        _cleanup(db, pid, [AUTHOR_A_ID, AUTHOR_B_ID])

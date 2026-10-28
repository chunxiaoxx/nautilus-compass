"""Inc 2 Slice 1 · on_pr_merge_hook · happy + idempotent paths."""
import os
import pytest
import psycopg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from services.inc2_settlement import on_pr_merge_hook

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="Postgres-only"
)


@pytest.fixture
def db():
    engine = create_engine(os.environ["DATABASE_URL"])
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.rollback()
    s.close()


def _seed_proposal(db, pid: str, agent_id: int = 9000002) -> None:
    db.execute(text(
        "INSERT INTO platform_improvement_proposals "
        "(id, task_id, agent_id, root_cause, proposed_change, "
        " expected_impact, rollback_plan, status, vote_score, vote_count, "
        " created_at, tenant_id, resolved_by) "
        "VALUES (:id, 9000001, :aid, 'test', "
        "        '{\"type\":\"code\",\"task\":\"noop\"}'::jsonb, "
        "        'test', 'noop', 'executed_ok', 7, 3, NOW(), 'default', 'soul')"
    ), {"id": pid, "aid": agent_id})
    db.commit()


def _cleanup(db, pid: str) -> None:
    db.execute(text("DELETE FROM pending_nau_rewards WHERE source_id = :sid"), {"sid": pid})
    db.execute(text("DELETE FROM proposal_outcomes WHERE proposal_id = :id"), {"id": pid})
    db.execute(text("DELETE FROM platform_improvement_proposals WHERE id = :id"), {"id": pid})
    db.commit()


def test_hook_creates_outcomes_and_pending(db):
    pid = "inc2-slice1-test-happy-1"
    _seed_proposal(db, pid)
    try:
        result = on_pr_merge_hook(
            db,
            proposal_id=pid,
            merged_pr_url="https://github.com/x/y/pull/999",
            nau_amount=10,
        )
        # Verify proposal_outcomes
        row = db.execute(text(
            "SELECT pre_snapshot, composite_delta, no_revert FROM proposal_outcomes WHERE proposal_id = :id"
        ), {"id": pid}).fetchone()
        assert row is not None, "proposal_outcomes row missing"
        assert row[0] is not None, "pre_snapshot must be non-null"
        assert row[1] is None, "composite_delta must be null until Slice 2 grades it"
        assert row[2] is None, "no_revert must be null until Slice 2 grades it"
        # Verify pending_nau_rewards
        pending = db.execute(text(
            "SELECT amount, status, source_id FROM pending_nau_rewards WHERE source_id = :sid"
        ), {"sid": pid}).fetchone()
        assert pending is not None, "pending_nau_rewards row missing"
        assert pending[0] == 10, f"amount expected 10 got {pending[0]}"
        assert pending[1] == "pending", f"status expected pending got {pending[1]}"
        # Verify result
        assert result["proposal_id"] == pid
        assert result["pending_created"] is True
        assert result["outcomes_created"] is True
    finally:
        _cleanup(db, pid)


def test_hook_is_idempotent(db):
    pid = "inc2-slice1-test-idempotent-1"
    _seed_proposal(db, pid)
    try:
        on_pr_merge_hook(db, proposal_id=pid, merged_pr_url="https://x/y/pr/1", nau_amount=10)
        # Second call MUST NOT create duplicate rows
        result = on_pr_merge_hook(db, proposal_id=pid, merged_pr_url="https://x/y/pr/1", nau_amount=10)
        # Verify counts unchanged
        outcomes_count = db.execute(text(
            "SELECT COUNT(*) FROM proposal_outcomes WHERE proposal_id = :id"
        ), {"id": pid}).scalar()
        pending_count = db.execute(text(
            "SELECT COUNT(*) FROM pending_nau_rewards WHERE source_id = :sid"
        ), {"sid": pid}).scalar()
        assert outcomes_count == 1
        assert pending_count == 1
        # Second call result must signal duplicate
        assert result["pending_created"] is False
        assert result["outcomes_created"] is False
    finally:
        _cleanup(db, pid)

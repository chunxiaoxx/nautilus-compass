"""Inc 2 Slice 1 · merge-callback endpoint smoke test."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="Postgres-only"
)


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


def test_merge_callback_endpoint_creates_pending(client):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(os.environ["DATABASE_URL"])
    Session = sessionmaker(bind=engine)
    db = Session()
    pid = "inc2-slice1-endpoint-test-1"
    # Seed
    db.execute(text(
        "INSERT INTO platform_improvement_proposals "
        "(id, task_id, agent_id, root_cause, proposed_change, "
        " expected_impact, rollback_plan, status, vote_score, vote_count, "
        " created_at, tenant_id, resolved_by) "
        "VALUES (:id, 9000001, 9000002, 'test', "
        "        '{\"type\":\"code\",\"task\":\"noop\"}'::jsonb, "
        "        'test', 'noop', 'executed_ok', 7, 3, NOW(), 'default', 'soul')"
    ), {"id": pid})
    db.commit()
    try:
        resp = client.post(
            f"/api/platform/proposals/{pid}/merge-callback",
            json={"merged_pr_url": "https://x/y/pr/1", "nau_amount": 10},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["pending_created"] is True
        assert body["data"]["outcomes_created"] is True
    finally:
        db.execute(text("DELETE FROM pending_nau_rewards WHERE source_id = :s"), {"s": pid})
        db.execute(text("DELETE FROM proposal_outcomes WHERE proposal_id = :p"), {"p": pid})
        db.execute(text("DELETE FROM platform_improvement_proposals WHERE id = :p"), {"p": pid})
        db.commit()
        db.close()

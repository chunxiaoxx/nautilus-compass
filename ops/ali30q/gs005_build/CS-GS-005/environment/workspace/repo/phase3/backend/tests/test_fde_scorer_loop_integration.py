"""W-D end-to-end: produced → soul scoring poller → verdict-bus → settled.

Wires the REAL FastAPI app (fde_dispatch + fde_verdict routers, sqlite) and drives
the actual HTTP loop with services.fde_scorer_poll.poll_and_score:

    dispatch → claim → report(output)  →  [poller] GET produced → score → POST verdict
                                       →  GET /tasks shows the task 'settled'

The only injected fake is the LLM judge (score_fn) — non-deterministic effect, proven
historically by data_001..006. Everything else (HTTP source, verdict ingest, the
settled-join) is the real production code. This is the closed-loop proof the
feishu_card 首验 would exercise on production (G-cloud).
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 · register relationship target
from models.fde_dispatch import FdeDispatch  # noqa: F401
from models.fde_verdict import FdeVerdict  # noqa: F401
from utils.database import get_db
from api.fde_dispatch import router as fde_dispatch_router
from api.fde_verdict import router as fde_verdict_router
from services.fde_scorer_poll import poll_and_score


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(fde_dispatch_router)
    app.include_router(fde_verdict_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _http_source(client):
    """ProducedTaskSource backed by the real GET /tasks?status=produced."""
    class _Src:
        def list_produced_tasks(self):
            r = client.get("/api/platform/fde/tasks", params={"status": "produced"})
            return r.json()["data"]["tasks"]
    return _Src()


def _http_verdict_fn(client):
    def verdict_fn(body):
        r = client.post("/api/platform/fde/verdict", json=body)
        assert r.status_code == 200, r.text
        return r.json()["data"]
    return verdict_fn


def _passing_judge(task):
    """Stand-in for the soul RUBRIC scorer (real one proven via data_001..006)."""
    return {
        "score": 1.0, "passed": 2, "total": 2,
        "veto_failed": False, "overall_pass": True,
        "items": [{"id": "c1", "pass": True, "veto": False, "reason": "ok"}],
        "checklist_uid": "ck-毛利率",
    }


def test_produced_task_becomes_settled_after_soul_scoring(client):
    # 1. a buyer task flows to produced with a real output (V5 producer's job)
    client.post("/api/platform/fde/dispatch",
                json={"task_uid": "feishu_card_demo", "title": "毛利率分析", "description": "毛利率…"})
    client.post("/api/platform/fde/claim",
                json={"task_uid": "feishu_card_demo", "agent_id": "nautilus-prime-001"})
    client.post("/api/platform/fde/report",
                json={"task_uid": "feishu_card_demo", "agent_id": "nautilus-prime-001",
                      "output": {"text": "毛利率 = (营收-成本)/营收 = 42.3%", "metrics": {"gm": 0.423}}})

    # produced, not yet settled
    before = client.get("/api/platform/fde/tasks").json()["data"]
    t0 = next(x for x in before["tasks"] if x["task_uid"] == "feishu_card_demo")
    assert t0["status"] == "produced"
    assert t0["verdict"] is None

    # 2. soul scoring poller runs the real HTTP loop
    result = poll_and_score(_http_source(client), _passing_judge, _http_verdict_fn(client))
    assert result["scored"] == ["feishu_card_demo"]

    # 3. the task is now settled with a soul verdict (loop closed)
    after = client.get("/api/platform/fde/tasks").json()["data"]
    t1 = next(x for x in after["tasks"] if x["task_uid"] == "feishu_card_demo")
    assert t1["status"] == "settled"
    assert t1["verdict"]["overall_pass"] is True
    assert t1["verdict"]["source"] == "soul"
    assert after["summary"]["settled"] >= 1


def test_soul_verdict_is_idempotent_across_poll_runs(client):
    """Re-running the poller does not double-write (deterministic verdict_id)."""
    client.post("/api/platform/fde/dispatch",
                json={"task_uid": "data_idem", "title": "t", "description": "d"})
    client.post("/api/platform/fde/claim", json={"task_uid": "data_idem", "agent_id": "a1"})
    client.post("/api/platform/fde/report",
                json={"task_uid": "data_idem", "agent_id": "a1", "output": {"text": "x"}})

    poll_and_score(_http_source(client), _passing_judge, _http_verdict_fn(client))
    # second run: task already settled → still scorable but ingest is idempotent
    poll_and_score(_http_source(client), _passing_judge, _http_verdict_fn(client))

    verdicts = client.get("/api/platform/fde/verdict/data_idem").json()["data"]
    assert len(verdicts) == 1  # one verdict row, not two

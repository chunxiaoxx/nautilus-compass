"""Phase-3 full-loop proof: split-form identity → produced → verdict → external verify.

This end-to-end test exercises the three critical seams together:
1) dispatch/claim/report in the FDE substrate
2) poller scoring writes verdict and auto-resolves producer from dispatch.claimed_by
3) external verify resolves producer again if needed and records income.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401
import models.fde_dispatch  # noqa: F401
import models.fde_verdict  # noqa: F401
from models.agent_survival import AgentSurvival, AgentTransaction
from models.database import Agent
from utils.database import get_db
from api.fde_dispatch import router as fde_dispatch_router
from api.fde_verdict import router as fde_verdict_router
from services.fde_scorer_poll import poll_and_score

import pytest


@pytest.fixture
def db_and_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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
    return TestingSessionLocal, TestClient(app)


def _http_source(client: TestClient):
    """HTTP source that matches the real poller contract."""
    class _Src:
        def list_produced_tasks(self):
            body = client.get("/api/platform/fde/tasks", params={"status": "produced"}).json()["data"]
            return body["tasks"]
    return _Src()


def _http_verdict_fn(client: TestClient):
    def verdict_fn(body: dict):
        r = client.post("/api/platform/fde/verdict", json=body)
        assert r.status_code == 200, r.text
        return r.json()["data"]
    return verdict_fn


def _judge_always_pass(task: dict) -> dict:
    return {
        "score": 1.0,
        "passed": 2,
        "total": 2,
        "veto_failed": False,
        "overall_pass": True,
        "items": [{"id": "c1", "pass": True, "veto": False, "reason": "ok"}],
        "checklist_uid": "ck-closed-loop",
    }


def test_full_loop_auto_resolves_external_expert_and_records_income(db_and_client):
    Session, client = db_and_client
    task_uid = "phase3-closed-loop-auto-id"

    db = Session()
    db.add(Agent(agent_id=9010001, owner="0x1234", name="open_id_901"))
    db.commit()
    db.close()

    # 1) dispatch → claim with external-facing identity token pattern → report output
    r1 = client.post("/api/platform/fde/dispatch", json={
        "task_uid": task_uid,
        "title": "闭环测试任务",
        "description": "{\"line\": \"2\", \"kind\": \"doc-review\"}",
    })
    assert r1.status_code == 200, r1.text

    r2 = client.post("/api/platform/fde/claim", json={
        "task_uid": task_uid,
        "agent_id": "expert:open_id_901",
    })
    assert r2.status_code == 200, r2.text

    output = {"text": "交付正文: 结论是方案可执行。"}
    r3 = client.post("/api/platform/fde/report", json={
        "task_uid": task_uid,
        "agent_id": "expert:open_id_901",
        "output": output,
    })
    assert r3.status_code == 200

    # 2) poller scoring: produced→verdict and settled view
    result = poll_and_score(_http_source(client), _judge_always_pass, _http_verdict_fn(client))
    assert result["scored"] == [task_uid]

    produced_to_settled = client.get("/api/platform/fde/tasks", params={"status": "produced"}).json()["data"]
    assert not any(t["task_uid"] == task_uid for t in produced_to_settled["tasks"])
    settled_data = client.get("/api/platform/fde/tasks").json()["data"]
    task_view = next(t for t in settled_data["tasks"] if t["task_uid"] == task_uid)
    assert task_view["status"] == "settled"
    assert task_view["verdict"]["source"] == "soul"
    verdict = client.get(f"/api/platform/fde/verdict/{task_uid}").json()["data"][0]
    assert verdict["artifacts"]["producer_agent_id"] == 9010001

    # 3) auto-verify can resolve producer id from claim, then mint income
    verdict_id = (
        client.get(f"/api/platform/fde/verdict/{task_uid}")
        .json()["data"][0]["verdict_id"]
    )
    r4 = client.patch(
        f"/api/platform/fde/verdict/{verdict_id}/external-verify",
        json={"verifier_source": "soul-canonical-verify"},
    )
    assert r4.status_code == 200, r4.text
    payload = r4.json()["data"]
    assert payload["income_recorded"] is True
    assert payload["amount"] == 1
    assert payload["verdict"]["external_verified"] is True

    db = Session()
    surv = db.query(AgentSurvival).filter_by(agent_id=9010001).first()
    assert surv is not None
    assert surv.total_income >= 1
    tx = db.query(AgentTransaction).filter_by(agent_id=9010001, type="INCOME",
                                             category="fde_external_verified",
                                             task_id=task_uid).first()
    assert tx is not None
    db.close()

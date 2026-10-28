"""镜子端点 · GET /api/platform/fde/my-status(方案② · settle 合约的实现)。

给 agent 一面镜子而不是橡皮图章:它能看见自己 claimed/produced/settled 计数
与 income 真值——prime-001 fake-success 1233 次的根源是从来看不见 0 settled。
"""
from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
from models.agent_survival import AgentSurvival, AgentTransaction
from models.fde_dispatch import FdeDispatch
from models.fde_verdict import FdeVerdict
from utils.database import get_db
from api.fde_verdict import router as fde_router


@pytest.fixture
def db_and_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(fde_router)
    app.dependency_overrides[get_db] = override
    return Session, TestClient(app)


def test_unknown_agent_returns_zeros(db_and_client):
    _, client = db_and_client
    r = client.get("/api/platform/fde/my-status", params={"agent_id": 4242})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["verdicts"] == {"total": 0, "external_verified": 0, "deliverable_grade": 0}
    assert d["income"]["total_income"] == 0
    assert d["dispatch"] is None  # 未给 claimed_by 不猜


def test_mirror_reflects_truth(db_and_client):
    Session, client = db_and_client
    db = Session()
    db.add(FdeVerdict(verdict_id="v1", task_uid="t1", source="cloud-genopt-runner-9",
                      overall_pass=True, score=97.0, items=[],
                      artifacts={"producer_agent_id": 9000009},
                      external_verified=True, external_verified_at=datetime.utcnow()))
    db.add(FdeVerdict(verdict_id="v2", task_uid="t2", source="cloud-genopt-runner-9",
                      overall_pass=False, score=50.0, items=[],
                      artifacts={"producer_agent_id": 9000009}))
    db.add(FdeVerdict(verdict_id="v3", task_uid="t3", source="other",
                      overall_pass=True, score=88.0, items=[],
                      artifacts={"producer_agent_id": 777}))  # 别人的,不算
    surv = AgentSurvival(agent_id=9000009, total_income=188)
    db.add(surv)
    db.flush()
    db.add(AgentTransaction(agent_survival_id=surv.id, agent_id=9000009,
                            type="INCOME", amount=98,
                            category="fde_external_verified", task_id="t1"))
    db.add(FdeDispatch(task_uid="t1", title="x", status="settled",
                       claimed_by="nautilus-prime-001"))
    db.add(FdeDispatch(task_uid="t4", title="y", status="claimed",
                       claimed_by="nautilus-prime-001"))
    db.add(FdeDispatch(task_uid="t5", title="z", status="claimed",
                       claimed_by="someone-else"))
    db.commit()
    db.close()

    r = client.get("/api/platform/fde/my-status",
                   params={"agent_id": 9000009, "claimed_by": "nautilus-prime-001"})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["verdicts"] == {"total": 2, "external_verified": 1, "deliverable_grade": 1}
    assert d["income"]["total_income"] == 188
    assert d["income"]["tx_count"] == 1
    assert d["dispatch"]["settled"] == 1
    assert d["dispatch"]["claimed"] == 1
    assert d["dispatch"]["total"] == 2

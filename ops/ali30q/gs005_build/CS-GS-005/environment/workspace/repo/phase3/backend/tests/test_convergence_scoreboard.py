"""方案④ 收敛记分牌 · GET /api/platform/convergence。

"有效收敛"从叙事变 5 个数字:verified / income / producer 自治率 /
settle 含金量 / 交付进度。核心 = producer_autonomy_ratio(7/7 现值 0%)。
"""
from __future__ import annotations

from datetime import datetime, timedelta

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
from api.control_plane import router as cp_router


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
    app.include_router(cp_router)
    app.dependency_overrides[get_db] = override
    return Session, TestClient(app)


def test_scoreboard_numbers(db_and_client):
    Session, client = db_and_client
    db = Session()
    now = datetime.utcnow()
    # 2 条 verified(1 条 autonomous·1 条手摇)+ 1 条未验证
    db.add(FdeVerdict(verdict_id="v-auto", task_uid="t-auto", source="agent-cycle",
                      overall_pass=True, score=90, items=[],
                      artifacts={"producer_agent_id": 9000009, "autonomous": True},
                      external_verified=True, external_verified_at=now))
    db.add(FdeVerdict(verdict_id="v-hand", task_uid="t-hand", source="cloud-runner",
                      overall_pass=True, score=98, items=[],
                      artifacts={"producer_agent_id": 9000009},
                      external_verified=True,
                      external_verified_at=now - timedelta(days=10)))
    db.add(FdeVerdict(verdict_id="v-un", task_uid="t-un", source="x",
                      overall_pass=False, score=0, items=[], artifacts={}))
    surv = AgentSurvival(agent_id=9000009, total_income=188)
    db.add(surv)
    db.flush()
    db.add(AgentTransaction(agent_survival_id=surv.id, agent_id=9000009,
                            type="INCOME", amount=98, category="fde_external_verified",
                            task_id="t-hand", created_at=now - timedelta(days=10)))
    db.add(AgentTransaction(agent_survival_id=surv.id, agent_id=9000009,
                            type="INCOME", amount=90, category="fde_external_verified",
                            task_id="t-auto", created_at=now))
    # dispatch:2 settled(1 条有 verified 背书·1 条自循环时代)+ 1 claimed
    db.add(FdeDispatch(task_uid="t-auto", title="a", status="settled"))
    db.add(FdeDispatch(task_uid="t-selfloop", title="b", status="settled"))
    db.add(FdeDispatch(task_uid="t-open", title="c", status="claimed"))
    db.commit()
    db.close()

    r = client.get("/api/platform/convergence")
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["external_verified"]["total"] == 2
    assert d["external_verified"]["last_7d"] == 1
    assert d["income"]["total"] == 188
    assert d["income"]["delta_7d"] == 90
    assert d["producer_autonomy"]["autonomous_verified"] == 1
    assert d["producer_autonomy"]["ratio"] == 0.5
    assert d["settle_integrity"]["settled_total"] == 2
    assert d["settle_integrity"]["externally_backed"] == 1
    assert d["settle_integrity"]["ratio"] == 0.5
    assert d["delivery_progress"]["delivered"] is None  # feishu turf · 诚实 null

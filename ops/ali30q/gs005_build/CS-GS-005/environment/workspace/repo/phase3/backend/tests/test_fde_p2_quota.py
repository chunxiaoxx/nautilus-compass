"""A2 五件套 P2 · 交付率换拉单权(561 平台半边)——0 交付→0 配额。

最小一行逻辑:claim 时查该 agent 在 fde_dispatch 的历史,
claimed≥3 且 produced=0 → 403(reborn 半成品出局);有 produced 放行;
新 agent(claimed<3)冷启动放行。不掺判分结果(settled 是判分方的事)。
"""
from __future__ import annotations

from datetime import datetime

import pytest  # noqa: F401
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 — mapper dependency
from api.fde_dispatch import router
from models.fde_dispatch import FdeDispatch
from utils.database import get_db


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()
    engine.dispose()


@pytest.fixture
def client(db):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def _seed(db, uid, status="open", claimed_by=None):
    db.add(FdeDispatch(task_uid=uid, title=f"T {uid}", status=status, claimed_by=claimed_by,
                       created_at=datetime.utcnow()))
    db.commit()


def test_new_agent_cold_start_allowed(db, client):
    _seed(db, "t-open-1")
    r = client.post("/api/platform/fde/claim",
                    json={"task_uid": "t-open-1", "agent_id": "agent-new"})
    assert r.status_code == 200, r.text


def test_zero_produced_after_three_claims_denied(db, client):
    for i in range(3):
        _seed(db, f"t-dead-{i}", status="claimed", claimed_by="agent-reborn")
    _seed(db, "t-open-2")
    r = client.post("/api/platform/fde/claim",
                    json={"task_uid": "t-open-2", "agent_id": "agent-reborn"})
    assert r.status_code == 403
    assert "P2 quota" in r.json()["error"]


def test_produced_history_beats_quota_gate(db, client):
    _seed(db, "t-p1", status="produced", claimed_by="agent-good")
    _seed(db, "t-p2", status="claimed", claimed_by="agent-good")
    _seed(db, "t-p3", status="settled", claimed_by="agent-good")  # settled 也算交付
    _seed(db, "t-open-3")
    r = client.post("/api/platform/fde/claim",
                    json={"task_uid": "t-open-3", "agent_id": "agent-good"})
    assert r.status_code == 200, r.text


def test_two_dead_claims_still_allowed(db, client):
    # 阈值 3 前不卡:给慢 agent 容错(2 单在手可能只是慢,非半成品)
    _seed(db, "t-slow-1", status="claimed", claimed_by="agent-slow")
    _seed(db, "t-slow-2", status="claimed", claimed_by="agent-slow")
    _seed(db, "t-open-4")
    r = client.post("/api/platform/fde/claim",
                    json={"task_uid": "t-open-4", "agent_id": "agent-slow"})
    assert r.status_code == 200, r.text


def test_quota_gate_counts_only_own_history(db, client):
    # 别人的 claimed 不算到自己头上
    _seed(db, "t-x1", status="claimed", claimed_by="agent-other")
    _seed(db, "t-x2", status="claimed", claimed_by="agent-other")
    _seed(db, "t-x3", status="claimed", claimed_by="agent-other")
    _seed(db, "t-open-5")
    r = client.post("/api/platform/fde/claim",
                    json={"task_uid": "t-open-5", "agent_id": "agent-new"})
    assert r.status_code == 200, r.text

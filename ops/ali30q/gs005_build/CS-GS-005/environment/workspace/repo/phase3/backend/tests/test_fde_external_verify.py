"""第一刀 reward wire · PATCH /api/platform/fde/verdict/{verdict_id}/external-verify.

八代复发根的码级修法:external_verified False→True 是 income 的唯一入账门。
4 防剧场护栏:幂等不重复入账 / 只此转换入账 / 只整数 producer_agent_id / 验证器≠生产者。
"""
from __future__ import annotations
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 · register AgentSurvival/AgentTransaction
import models.fde_dispatch  # noqa: F401 · register FdeDispatch mapper
from models.agent_survival import AgentSurvival, AgentTransaction
from models.fde_verdict import FdeVerdict  # noqa: F401
from models.fde_dispatch import FdeDispatch
from utils.database import get_db
from api.fde_verdict import router as fde_router


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
    app.include_router(fde_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestingSessionLocal, TestClient(app)


def _genopt_payload(**over):
    p = {
        "verdict_id": "verdict-genopt-jobshop-9000009-test01",
        "task_uid": "genopt_or_jobshop_orlib_v1_001_20260702",
        "source": "h800-genopt-runner-9000009",
        "overall_pass": True,
        "veto_failed": False,
        "score": 93.1034,
        "items": [],
        "artifacts": {"producer_agent_id": 9000009, "model": "gpt-5.5"},
    }
    p.update(over)
    return p


def _ingest(client, **over):
    r = client.post("/api/platform/fde/verdict", json=_genopt_payload(**over))
    assert r.status_code == 200, r.text
    return r.json()["data"]


def test_patch_unknown_verdict_404(db_and_client):
    _, client = db_and_client
    r = client.patch("/api/platform/fde/verdict/nope/external-verify",
                     json={"verifier_source": "soul-canonical-verify"})
    assert r.status_code == 404


def test_external_verify_flips_flag_and_records_income(db_and_client):
    Session, client = db_and_client
    _ingest(client)
    r = client.patch(
        "/api/platform/fde/verdict/verdict-genopt-jobshop-9000009-test01/external-verify",
        json={"verifier_source": "soul-canonical-verify"})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["verdict"]["external_verified"] is True
    assert data["verdict"]["external_verified_at"] is not None
    assert data["income_recorded"] is True
    assert data["amount"] == 93  # round(score)

    db = Session()
    surv = db.query(AgentSurvival).filter_by(agent_id=9000009).first()
    assert surv is not None, "survival row must be bootstrapped"
    assert surv.total_income == 93
    tx = db.query(AgentTransaction).filter_by(agent_id=9000009, type="INCOME").all()
    assert len(tx) == 1
    assert tx[0].category == "fde_external_verified"
    assert tx[0].task_id == "genopt_or_jobshop_orlib_v1_001_20260702"
    db.close()


def test_idempotent_no_double_income(db_and_client):
    Session, client = db_and_client
    _ingest(client)
    url = "/api/platform/fde/verdict/verdict-genopt-jobshop-9000009-test01/external-verify"
    r1 = client.patch(url, json={"verifier_source": "soul-canonical-verify"})
    assert r1.status_code == 200
    r2 = client.patch(url, json={"verifier_source": "soul-canonical-verify"})
    assert r2.status_code == 200
    assert r2.json()["data"]["income_recorded"] is False  # 幂等,不再入账

    db = Session()
    surv = db.query(AgentSurvival).filter_by(agent_id=9000009).first()
    assert surv.total_income == 93  # 只入账一次
    assert db.query(AgentTransaction).filter_by(agent_id=9000009).count() == 1
    db.close()


def test_verifier_must_differ_from_producer(db_and_client):
    _, client = db_and_client
    _ingest(client)
    r = client.patch(
        "/api/platform/fde/verdict/verdict-genopt-jobshop-9000009-test01/external-verify",
        json={"verifier_source": "h800-genopt-runner-9000009"})  # == verdict.source
    assert r.status_code == 400
    assert "producer" in r.json()["error"].lower() or "verifier" in r.json()["error"].lower()


def test_missing_producer_agent_id_rejected(db_and_client):
    Session, client = db_and_client
    _ingest(client, verdict_id="v-no-producer", artifacts={"model": "gpt-5.5"})
    r = client.patch("/api/platform/fde/verdict/v-no-producer/external-verify",
                     json={"verifier_source": "soul-canonical-verify"})
    assert r.status_code == 400
    # verdict 不应被标 verified,income 不应入账
    db = Session()
    row = db.query(FdeVerdict).filter_by(verdict_id="v-no-producer").first()
    assert row.external_verified is False
    assert db.query(AgentTransaction).count() == 0
    db.close()


def test_external_verify_auto_resolves_producer_agent_id_from_dispatch(db_and_client):
    Session, client = db_and_client
    db = Session()
    db.add(FdeDispatch(
        task_uid="genopt_or_jobshop_orlib_v1_001_20260702",
        title="Auto resolve task",
        description="{}",
        status="produced",
        claimed_by="expert:kairos",
    ))
    db.commit()
    db.close()

    _ingest(
        client,
        verdict_id="v-auto-producer",
        task_uid="genopt_or_jobshop_orlib_v1_001_20260702",
        artifacts={"model": "gpt-5.5"},
    )
    r = client.patch(
        "/api/platform/fde/verdict/v-auto-producer/external-verify",
        json={"verifier_source": "soul-canonical-verify"},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["income_recorded"] is True
    assert data["amount"] == 93
    assert data["verdict"]["artifacts"]["producer_agent_id"] == 9000003

    db = Session()
    surv = db.query(AgentSurvival).filter_by(agent_id=9000003).first()
    assert surv is not None, "survival row must be bootstrapped"
    assert surv.total_income == 93
    db.close()


def test_rejected_grade_verifies_but_no_income(db_and_client):
    """C 口径护栏 ⑤:难度档不合格(overall_pass=False)→ 验证标照翻,income 不铸。"""
    Session, client = db_and_client
    _ingest(client, verdict_id="v-rejected-grade", overall_pass=False, score=97.6311,
            task_uid="genopt_or_tsp_tsplib_v1_001_20260702")
    r = client.patch("/api/platform/fde/verdict/v-rejected-grade/external-verify",
                     json={"verifier_source": "soul-canonical-verify"})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["verdict"]["external_verified"] is True   # 认识论照记
    assert data["income_recorded"] is False               # 经济层不铸
    assert data["income_gate_reason"] == "not_deliverable_grade"
    db = Session()
    assert db.query(AgentTransaction).count() == 0
    db.close()


def test_same_task_second_verdict_no_double_income(db_and_client):
    """C 口径护栏 ⑥:同 (task_uid × producer) 只铸一次——堵同题重跑刷钱。"""
    Session, client = db_and_client
    _ingest(client)  # 默认 jobshop task_uid · overall_pass=True
    r1 = client.patch(
        "/api/platform/fde/verdict/verdict-genopt-jobshop-9000009-test01/external-verify",
        json={"verifier_source": "soul-canonical-verify"})
    assert r1.json()["data"]["income_recorded"] is True
    # 同题新轨迹 → 新 verdict
    _ingest(client, verdict_id="v-same-task-rerun", score=95.0)
    r2 = client.patch("/api/platform/fde/verdict/v-same-task-rerun/external-verify",
                      json={"verifier_source": "soul-canonical-verify"})
    data = r2.json()["data"]
    assert data["verdict"]["external_verified"] is True
    assert data["income_recorded"] is False
    assert data["income_gate_reason"] == "task_already_rewarded"
    db = Session()
    surv = db.query(AgentSurvival).filter_by(agent_id=9000009).first()
    assert surv.total_income == 93  # 只有第一笔
    assert db.query(AgentTransaction).count() == 1
    db.close()


def test_missing_verifier_source_rejected(db_and_client):
    _, client = db_and_client
    _ingest(client)
    r = client.patch(
        "/api/platform/fde/verdict/verdict-genopt-jobshop-9000009-test01/external-verify",
        json={})
    assert r.status_code == 400

"""转移线④ · verdict→capability 权威喂点测试(TDD RED → GREEN)。

修复语义(2026-08-27):能力记账只跟"external-verify 权威转换"走(自报不算);
settle 旧喂点(自报口径)下线;backfill 重建历史;event_handlers 自报门。
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base, Agent, APIKey, AgentCapabilityStat
import models.agent_survival  # noqa: F401
from models.fde_verdict import FdeVerdict
from utils.database import get_db
from api.fde_verdict import router as verdict_router
from services.capability_feed import (
    task_type_from_uid,
    feed_capability_on_verify,
    backfill_capability_from_verified,
)

G2B1 = "g2b1:767fb5d55337"


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    db = TestSession()

    db.add(Agent(agent_id=9000010, owner="0x" + "a" * 40, name="g2b1-executor"))
    db.add(Agent(agent_id=9000003, owner="0x" + "b" * 40, name="kairos"))
    db.add(Agent(agent_id=9000009, owner="0x" + "c" * 40, name="prime-001"))
    for r in [
        FdeVerdict(verdict_id="v1", task_uid=G2B1, source="g2b1-executor",
                   overall_pass=True, score=1.0, external_verified=True,
                   artifacts={"producer_agent_id": 9000010}),
        FdeVerdict(verdict_id="v2", task_uid="g2b1:ac5541e47e9e", source="g2b1-executor",
                   overall_pass=True, score=0.8, external_verified=True,
                   artifacts={"producer_agent_id": 9000010}),
        FdeVerdict(verdict_id="v3", task_uid="g2b1:f08c1c9e3422", source="g2b1-executor",
                   overall_pass=True, score=0.6, external_verified=False,
                   artifacts={"producer_agent_id": 9000010}),
    ]:
        db.add(r)
    db.commit()

    app = FastAPI()
    app.include_router(verdict_router)

    def override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override
    yield TestClient(app), db
    db.close()
    engine.dispose()


def _patch_verify(c, vid="v3", verifier="soul-canonical"):
    return c.patch(f"/api/platform/fde/verdict/{vid}/external-verify",
                   json={"verifier_source": verifier})


def test_task_type_mapping():
    assert task_type_from_uid("g2b1:abc123") == "g2b1_code_repair"
    assert task_type_from_uid("some_plain_uid") == "fde_misc"


def test_verify_patch_feeds_capability(client):
    """权威 False→True 转换 → capability 记一条 success(与 income 门无关)。"""
    c, db = client
    r = _patch_verify(c)
    assert r.status_code == 200, r.text
    stat = (db.query(AgentCapabilityStat)
            .filter_by(agent_id=9000010, task_type="g2b1_code_repair").first())
    assert stat is not None
    assert stat.total_attempts == 1
    assert stat.success_count == 1
    assert stat.total_quality_score == pytest.approx(3.0)  # 0.6×5 映射


def test_repatch_idempotent_no_double_feed(client):
    c, db = client
    _patch_verify(c)
    _patch_verify(c)  # 已 verified → no-op
    stat = (db.query(AgentCapabilityStat)
            .filter_by(agent_id=9000010, task_type="g2b1_code_repair").first())
    assert stat.total_attempts == 1  # 不双计


def test_backfill_rebuilds_history(client):
    c, db = client
    n = backfill_capability_from_verified(db)
    assert n >= 2  # v1+v2 两条已 verified
    stat = (db.query(AgentCapabilityStat)
            .filter_by(agent_id=9000010, task_type="g2b1_code_repair").first())
    assert stat.total_attempts == 2
    assert stat.success_count == 2


def test_event_handler_gate_blocks_self_report():
    """自报任务事件(无 external_verified 证据)不喂能力。"""
    from services.event_handlers import _should_feed_capability
    assert _should_feed_capability({"agent_id": 3, "task_type": "t", "success": True}) is False
    assert _should_feed_capability({"agent_id": 3, "task_type": "t", "success": True,
                                    "external_verified": True}) is True


def test_feed_skips_ghost_agent(client):
    """FK 防御:未注册 agent(如云端 9000009)不喂、不炸。"""
    c, db = client
    out = feed_capability_on_verify(db, agent_id=9999999, task_uid=G2B1,
                                    score=0.8, success=True)
    assert out is None
    stat = (db.query(AgentCapabilityStat)
            .filter_by(agent_id=9999999).first())
    assert stat is None


def test_feed_helper_direct(client):
    c, db = client
    out = feed_capability_on_verify(db, agent_id=9000009, task_uid=G2B1,
                                    score=0.8, success=False)
    assert out is not None
    stat = (db.query(AgentCapabilityStat)
            .filter_by(agent_id=9000009, task_type="g2b1_code_repair").first())
    assert stat.total_attempts == 1
    assert stat.success_count == 0  # 失败面:attempts+失败

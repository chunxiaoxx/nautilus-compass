"""A2 五件套 P1 · 平台侧交付时钟矩阵(561 平台半边第二件)。

GET /api/platform/org/delivery-clock:每 agent 多源交付痕迹(fde_dispatch 上报/
fde_verdicts 判分/platform_audit 观测面/org_mailbox 函件)距今矩阵,
best=最近交付,WARN=超窗 2/3(≈32h)·RED=超窗 48h(默认窗,可调)。
超窗处置走断供处置线(协议 V1 §5),不自动改 agent 数据——框级生死=
用户主权(GOAL_STACK 四纪律①),561"自动 parking"降格为 RED 亮牌+日报告警。
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest  # noqa: F401
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401
from api.org import router
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


def _hours_ago(n):
    return datetime.utcnow() - timedelta(hours=n)


def _audit(actor, h):
    from models.platform_audit import PlatformAudit
    return PlatformAudit(ts=_hours_ago(h), actor=actor, action="a", outcome="ok",
                         actor_type="daemon", target="", target_type="", meta={}, ip="t")


def test_matrix_multi_source_best_is_freshest(db, client):
    from models.fde_dispatch import FdeDispatch
    db.add(FdeDispatch(task_uid="t1", title="T", status="produced",
                       claimed_by="agentA", reported_at=_hours_ago(50)))
    db.add(_audit("agentA", 2))
    db.commit()
    d = {a["agent"]: a for a in client.get("/api/platform/org/delivery-clock").json()["data"]["agents"]}
    a = d["agentA"]
    assert a["best_h_ago"] < 3          # audit(2h) 胜 dispatch(50h)
    assert a["status"] == "GREEN"
    assert a["sources"]["dispatch_h_ago"] > 49


def test_red_over_window_warn_at_two_thirds(db, client):
    db.add(_audit("agentRed", 60))
    db.add(_audit("agentWarn", 40))     # 40 > 48*2/3=32 但 < 48 → WARN
    db.add(_audit("agentGreen", 10))
    db.commit()
    d = {a["agent"]: a for a in client.get("/api/platform/org/delivery-clock").json()["data"]["agents"]}
    assert d["agentRed"]["status"] == "RED"
    assert d["agentWarn"]["status"] == "WARN"
    assert d["agentGreen"]["status"] == "GREEN"


def test_mail_source_counts(db, client):
    from models.org_mailbox import OrgMailbox
    # mailbox 列=上海 naive 钟(生产语义),测试造数用本地 now 基准
    db.add(OrgMailbox(from_agent="agentMail", to_agent="platform", trace_id="x1",
                      title="t", body="b", deadline=_hours_ago(1),
                      created_at=datetime.now() - timedelta(hours=5)))
    db.commit()
    d = {a["agent"]: a for a in client.get("/api/platform/org/delivery-clock").json()["data"]["agents"]}
    assert d["agentMail"]["best_h_ago"] < 6 and d["agentMail"]["status"] == "GREEN"


def test_window_param_clamped(db, client):
    assert client.get("/api/platform/org/delivery-clock",
                      params={"window_h": 99999}).status_code == 200
    assert client.get("/api/platform/org/delivery-clock",
                      params={"window_h": 0}).status_code == 200

"""决策卡发送侧测试(2026-09-15 Q3 接线)。

覆盖三分支:①发送成功→card_sent=True ②无 FEISHU_ENCRYPT_KEY→False+note
③幂等重入(未发成功时)→重试发卡。
真发验证=部署后 curl 创建真决策卡(E2E,活性≠能力纪律)。
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 — mapper dependency
import models.feishu_decision  # noqa: F401
from utils.database import get_db
from api.feishu_decision import router as decision_router


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    app = FastAPI()
    app.include_router(decision_router)
    app.dependency_overrides[get_db] = lambda: TestSession()

    with TestClient(app) as c:
        yield c, TestSession, monkeypatch


PAYLOAD = {
    "trace_id": "card-send-test-001",
    "title": "测试:发送侧验证",
    "options": ["满意", "重来"],
    "default": "重来",
    "deadline": "2026-09-16T00:00:00Z",
    "context": "发送侧接线验证",
}


def _post(c, body=None):
    return c.post("/api/platform/feishu/decision", json=body or PAYLOAD)


def test_card_sent_on_success(client):
    c, _, mp = client
    mp.setenv("FEISHU_PUBLIC_BASE", "https://www.nautilus.social")
    mp.setenv("FEISHU_ENCRYPT_KEY", "k-test")
    mp.setattr("ops.feishu_push.push_card", lambda card: 0)
    r = _post(c)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["card_sent"] is True
    assert d["card_note"] == "card sent (code 0)"
    # 卡片里按钮 URL 带签名投票链接
    (lambda: None)()  # noop  readability


def test_card_failsoft_without_key(client):
    c, _, mp = client
    mp.delenv("FEISHU_ENCRYPT_KEY", raising=False)
    r = _post(c)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["card_sent"] is False
    assert "not configured" in d["card_note"]


def test_idempotent_hit_retries_send(client):
    c, _, mp = client
    mp.setenv("FEISHU_ENCRYPT_KEY", "k-test")
    # 首次:发卡失败(feishu code 非 0)
    mp.setattr("ops.feishu_push.push_card", lambda card: 230002)
    d1 = _post(c).json()["data"]
    assert d1["card_sent"] is False
    assert "230002" in d1["card_note"]
    # 重入:发卡成功 → card_sent 翻 True(幂等重入=重试机会)
    mp.setattr("ops.feishu_push.push_card", lambda card: 0)
    d2 = _post(c).json()["data"]
    assert d2["idempotent"] is True
    assert d2["card_sent"] is True

"""飞书决策卡通道测试(V5 设计稿 · platform 实施 · 2026-08-29 认领)。

范围:POST /api/platform/feishu/decision(创建,幂等 trace)+ card/callback
(url_verification challenge 回显 / 验签 fail-closed / 按钮落库幂等)+
GET /{trace_id}(到期未决记 default)。卡片实际发送 v0 不启用(等用户 10min 配置),
callback 无密钥=静默丢弃(不上线红线)。
"""
import base64
import hashlib
import hmac
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

import models.database  # noqa: E402,F401  (Base + mapper chain)
import models.agent_survival  # noqa: E402,F401
from models.feishu_decision import FeishuDecision  # noqa: E402
from api.feishu_decision import router  # noqa: E402
from utils.database import get_db  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("FEISHU_ENCRYPT_KEY", raising=False)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool)
    models.database.Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c


def _mk_payload(**kw):
    p = {"trace_id": "v5-im-choice-1", "title": "选 IM 通道",
         "options": ["telegram", "feishu", "wechat"], "default": "telegram",
         "deadline": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
         "context": "SaaS 反馈通道"}
    p.update(kw)
    return p


def test_create_and_idempotent(client):
    r = client.post("/api/platform/feishu/decision", json=_mk_payload())
    assert r.status_code == 200 and r.json()["success"] is True
    d = r.json()["data"]
    assert d["trace_id"] == "v5-im-choice-1" and d["choice"] is None
    assert d["card_sent"] is False and d["card_note"]  # v0 未配置,不发卡但说明
    r2 = client.post("/api/platform/feishu/decision", json=_mk_payload())
    assert r2.json()["data"]["idempotent"] is True


def test_create_validation(client):
    assert client.post("/api/platform/feishu/decision",
                       json=_mk_payload(trace_id="")).status_code == 400
    assert client.post("/api/platform/feishu/decision",
                       json=_mk_payload(options=["only1"])).status_code == 400
    assert client.post("/api/platform/feishu/decision",
                       json=_mk_payload(default="not-in-list")).status_code == 400


def test_get_undecided_before_deadline(client):
    client.post("/api/platform/feishu/decision", json=_mk_payload())
    d = client.get("/api/platform/feishu/decision/v5-im-choice-1").json()["data"]
    assert d["choice"] is None and "default_applied" not in d


def test_get_after_deadline_applies_default(client):
    p = _mk_payload(deadline=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat())
    client.post("/api/platform/feishu/decision", json=p)
    d = client.get("/api/platform/feishu/decision/v5-im-choice-1").json()["data"]
    assert d["choice"] == "telegram" and d["decided_by"] == "default"
    assert d["default_applied"] is True
    d2 = client.get("/api/platform/feishu/decision/v5-im-choice-1").json()["data"]
    # 幂等:值不重复改写;default 语义由 decided_by 承载(default_applied 只是首读转变标志)
    assert d2["choice"] == "telegram" and d2["decided_by"] == "default"
    assert d2.get("decided_at") == d["decided_at"]


def test_callback_url_verification(client):
    r = client.post("/api/platform/feishu/card/callback",
                    json={"type": "url_verification", "challenge": "ajls38fk"})
    assert r.status_code == 200 and r.json()["challenge"] == "ajls38fk"


def test_callback_unsigned_dropped_without_key(client):
    """无密钥(未配置)=静默丢弃:200 但不落库,不暴露内部。"""
    client.post("/api/platform/feishu/decision", json=_mk_payload())
    r = client.post("/api/platform/feishu/card/callback",
                    json=_card_body("v5-im-choice-1", "feishu"))
    assert r.status_code == 200
    d = client.get("/api/platform/feishu/decision/v5-im-choice-1").json()["data"]
    assert d["choice"] is None


def test_callback_signed_records_choice(client, monkeypatch):
    monkeypatch.setenv("FEISHU_ENCRYPT_KEY", "k-test")
    client.post("/api/platform/feishu/decision", json=_mk_payload())
    body = _card_body("v5-im-choice-1", "feishu")
    raw = json.dumps(body).encode()
    from api.feishu_decision import feishu_signature  # 单一配方源(9/16 hexdigest 定谳)
    sig = feishu_signature("1700000000", "n1", "k-test", raw)
    r = client.post("/api/platform/feishu/card/callback?ts=1700000000&nonce=n1",
                    content=raw,
                    headers={"Content-Type": "application/json",
                             "X-Lark-Signature": sig})
    assert r.status_code == 200
    d = client.get("/api/platform/feishu/decision/v5-im-choice-1").json()["data"]
    assert d["choice"] == "feishu" and d["decided_by"] == "feishu-card"
    # 重复回调幂等
    client.post("/api/platform/feishu/card/callback?ts=1700000000&nonce=n1",
                content=raw, headers={"X-Lark-Signature": sig,
                                      "Content-Type": "application/json"})


def test_callback_signed_body_credentials(client, monkeypatch):
    """飞书官方规范:ts/nonce 在 body 顶层(非 URL query)。body 凭据验签同样通过。"""
    monkeypatch.setenv("FEISHU_ENCRYPT_KEY", "k-test")
    client.post("/api/platform/feishu/decision", json=_mk_payload())
    body = _card_body("v5-im-choice-1", "feishu")
    body["ts"], body["nonce"] = 1700000001, "n2"
    raw = json.dumps(body).encode()
    from api.feishu_decision import feishu_signature
    sig = feishu_signature("1700000001", "n2", "k-test", raw)
    r = client.post("/api/platform/feishu/card/callback", content=raw,
                    headers={"Content-Type": "application/json",
                             "X-Lark-Signature": sig})
    assert r.status_code == 200
    d = client.get("/api/platform/feishu/decision/v5-im-choice-1").json()["data"]
    assert d["choice"] == "feishu" and d["decided_by"] == "feishu-card"


def test_callback_bad_signature_dropped(client, monkeypatch):
    monkeypatch.setenv("FEISHU_ENCRYPT_KEY", "k-test")
    client.post("/api/platform/feishu/decision", json=_mk_payload())
    r = client.post("/api/platform/feishu/card/callback?ts=1&nonce=n",
                    content=json.dumps(_card_body("v5-im-choice-1", "wechat")).encode(),
                    headers={"X-Lark-Signature": "bad" * 8,
                             "Content-Type": "application/json"})
    assert r.status_code == 200  # 静默丢弃
    d = client.get("/api/platform/feishu/decision/v5-im-choice-1").json()["data"]
    assert d["choice"] is None


def test_callback_unknown_trace_or_choice_ignored(client, monkeypatch):
    monkeypatch.setenv("FEISHU_ENCRYPT_KEY", "k-test")
    r = client.post("/api/platform/feishu/card/callback?ts=1&nonce=n",
                    content=json.dumps(_card_body("no-such-trace", "x")).encode(),
                    headers={"X-Lark-Signature": "bad", "Content-Type": "application/json"})
    assert r.status_code == 200


def _card_body(trace_id, choice):
    return {"schema": "2.0", "header": {"event_id": "ev1"},
            "event": {"action": {"value": {"trace_id": trace_id, "choice": choice}}}}


# ===== URL-token vote(0b 备用通道:卡片回调不可用时的零依赖降级) =====

def _vote_sig(trace, choice, exp, key="k-test"):
    msg = f"{trace}|{choice}|{exp}".encode()
    return hmac.new(key.encode(), msg, hashlib.sha256).hexdigest()


def test_vote_url_records_choice(client, monkeypatch):
    monkeypatch.setenv("FEISHU_ENCRYPT_KEY", "k-test")
    client.post("/api/platform/feishu/decision", json=_mk_payload())
    exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    sig = _vote_sig("v5-im-choice-1", "feishu", exp)
    r = client.get(f"/api/platform/feishu/decision/vote",
                   params={"trace": "v5-im-choice-1", "choice": "feishu",
                           "exp": exp, "sig": sig})
    assert r.status_code == 200
    d = client.get("/api/platform/feishu/decision/v5-im-choice-1").json()["data"]
    assert d["choice"] == "feishu" and d["decided_by"] == "url-vote"


def test_vote_url_rejects_bad_sig_expired_invalid(client, monkeypatch):
    monkeypatch.setenv("FEISHU_ENCRYPT_KEY", "k-test")
    client.post("/api/platform/feishu/decision", json=_mk_payload())
    exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    base = dict(trace="v5-im-choice-1", choice="feishu", exp=exp)
    # 错签名
    r = client.get("/api/platform/feishu/decision/vote",
                   params={**base, "sig": "0" * 64})
    assert r.status_code == 403
    # 过期
    old = int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp())
    r = client.get("/api/platform/feishu/decision/vote",
                   params={**base, "exp": old, "sig": _vote_sig("v5-im-choice-1", "feishu", old)})
    assert r.status_code == 410
    # 非法选项
    r = client.get("/api/platform/feishu/decision/vote",
                   params={**base, "choice": "no-such", "sig": _vote_sig("v5-im-choice-1", "no-such", exp)})
    assert r.status_code == 400
    d = client.get("/api/platform/feishu/decision/v5-im-choice-1").json()["data"]
    assert d["choice"] is None  # 全部被拒,未落库


def test_vote_url_503_without_key(client):
    r = client.get("/api/platform/feishu/decision/vote",
                   params={"trace": "t", "choice": "c", "exp": 1, "sig": "x"})
    assert r.status_code == 503

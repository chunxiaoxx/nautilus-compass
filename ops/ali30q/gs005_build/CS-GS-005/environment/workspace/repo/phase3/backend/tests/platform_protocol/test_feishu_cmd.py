"""贾维斯 v0 指令入口测试(2026-09-15 · V5 248 同意接线后平台侧落地)。

覆盖:challenge 回显/坏签名丢弃/非白名单群聊丢弃/p2p 未知会话放行/旧 schema
兼容/help/status/ask(LLM mock)/event_id 幂等/应答走响应体(回执由 8092 发)。
"""
from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 — mapper dependency
import models.org_mailbox  # noqa: F401
from utils.database import get_db
from api.feishu_cmd import router as cmd_router, _cmd_chat_id
from api.feishu_decision import feishu_signature

CHAT = "oc_test_p2p_1"
KEY = "k-cmd-test"


def _event(text="help", event_id="evt_abcdefgh1234", chat_id=CHAT,
           chat_type="p2p", with_header=True):
    msg = {"chat_id": chat_id, "chat_type": chat_type, "message_type": "text",
           "content": json.dumps({"text": text})}
    if not with_header:  # 旧版 schema:无顶层 header,消息体同形
        msg["message_id"] = event_id
    ev = {"event": {"message": msg}, "ts": "1700000000", "nonce": "n-1"}
    if with_header:
        ev = {"header": {"event_id": event_id, "event_type": "im.message.receive_v1"},
              "event": {"message": msg}, "ts": "1700000000", "nonce": "n-1"}
    return ev


def _signed_headers(body_bytes: bytes, ts="1700000000", nonce="n-1"):
    return {"X-Lark-Signature": feishu_signature(ts, nonce, KEY, body_bytes)}


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    app = FastAPI()
    app.include_router(cmd_router)
    app.dependency_overrides[get_db] = lambda: TestSession()
    monkeypatch.setenv("FEISHU_ENCRYPT_KEY", KEY)
    monkeypatch.setenv("FEISHU_CMD_CHAT_ID", CHAT)
    with TestClient(app) as c:
        yield c, TestSession, monkeypatch


def _post(client, event):
    body = json.dumps(event).encode()
    return client.post("/api/platform/feishu/cmd", content=body,
                       headers=_signed_headers(body, event["ts"], event["nonce"]))


def test_url_verification_echo(client):
    c, _, _ = client
    r = c.post("/api/platform/feishu/cmd",
               json={"type": "url_verification", "challenge": "ch-42"})
    assert r.json()["challenge"] == "ch-42"


def test_bad_signature_dropped(client):
    c, _, _ = client
    body = json.dumps(_event()).encode()
    r = c.post("/api/platform/feishu/cmd", content=body,
               headers={"X-Lark-Signature": "bogus"})
    assert "dropped" in r.json()["note"]


def test_non_whitelisted_chat_dropped(client):
    c, _, _ = client
    r = _post(c, _event(chat_id="oc_other_group", chat_type="group"))
    assert "whitelisted" in r.json()["note"]


def test_p2p_unknown_chat_allowed(client):
    """用户对 scorer app 的私聊 chat_id 不在白名单——p2p 即用户本人,放行。"""
    c, _, _ = client
    r = _post(c, _event(chat_id="oc_scorer_p2p_new"))
    assert "handled" in r.json()["note"]
    assert "贾维斯" in r.json()["reply"]


def test_old_schema_event_handled(client):
    """旧版 schema(无顶层 header):event_id 兜底 message_id,幂等台账照落。"""
    c, Session, _ = client
    r = _post(c, _event("help", event_id="evt_oldsch0001", chat_id="oc_old_p2p",
                        with_header=False))
    assert "handled" in r.json()["note"]
    s = Session()
    assert s.query(models.org_mailbox.OrgMailbox).filter_by(
        trace_id="feishu-cmd-dsch0001").count() == 1  # message_id 尾 8 位
    s.close()


def test_help_replies_and_ledgers(client):
    c, Session, _ = client
    r = _post(c, _event("help"))
    assert "handled" in r.json()["note"]
    assert "贾维斯" in r.json()["reply"]
    s = Session()
    assert s.query(models.org_mailbox.OrgMailbox).filter_by(
        trace_id="feishu-cmd-efgh1234").count() == 1  # event_id 尾 8 位
    s.close()


def test_status_snapshot(client):
    c, Session, _ = client
    r = _post(c, _event("status", event_id="evt_status00001"))
    assert "handled" in r.json()["note"]
    assert "待处理" in r.json()["reply"]


def test_ask_uses_llm(client, monkeypatch):
    c, _, mp = client
    mp.setattr("agent_engine.llm.client.get_llm_client",
               lambda: type("FakeLLM", (), {"chat": staticmethod(
                   lambda prompt, system="", max_tokens=0: "组织现状:五框运转中。")})())
    r = _post(c, _event("ask 组织现在怎么样", event_id="evt_ask0000001"))
    assert "五框运转" in r.json()["reply"]


def test_duplicate_event_id_dropped(client):
    c, _, _ = client
    r1 = _post(c, _event("help", event_id="evt_dup000001"))
    r2 = _post(c, _event("help", event_id="evt_dup000001"))
    assert "handled" in r1.json()["note"]
    assert "duplicate" in r2.json()["note"]


def test_free_text_routes_to_v5(client):
    """v0.2(9/17 壳脑分工,300 确认):自由文本路由 v5 脑,明文随响应体回 8092。"""
    c, _, _ = client
    r = _post(c, _event("你现在能做什么事", event_id="evt_free0000001"))
    j = r.json()
    assert j.get("route") == "v5"
    assert j.get("text") == "你现在能做什么事"
    assert j.get("chat_id") == CHAT
    assert "routed" in j["note"]


def test_explicit_ask_still_uses_local_llm(client, monkeypatch):
    c, _, mp = client
    mp.setattr("agent_engine.llm.client.get_llm_client",
               lambda: type("FakeLLM", (), {"chat": staticmethod(
                   lambda prompt, system="", max_tokens=0: f"答:{prompt}")})())
    r = _post(c, _event("ask 介绍一下自己", event_id="evt_ask0000002"))
    assert "答:" in r.json()["reply"]


def test_encrypted_event_handled(client):
    """加密事件(官方 SDK 格式:IV=密文前16字节前置):验签对密文 raw,解密后执行。"""
    pytest.importorskip("cryptography")
    import base64
    import hashlib
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    inner = _event("help", event_id="evt_encr0000001", chat_id="oc_enc_p2p",
                   chat_type="p2p")
    aes_key = hashlib.sha256(KEY.encode()).digest()
    pad_n = 16 - (len(json.dumps(inner).encode()) % 16)
    padded = json.dumps(inner).encode() + bytes([pad_n]) * pad_n
    iv = b"0123456789abcdef"  # 官方格式:IV 前置在密文里
    enc = Cipher(algorithms.AES(aes_key), modes.CBC(iv)).encryptor()
    cipher_b64 = base64.b64encode(iv + enc.update(padded) + enc.finalize()).decode()
    payload = {"encrypt": cipher_b64}
    body = json.dumps(payload).encode()
    c, _, _ = client
    # 复刻 8092 透传形状:ts/nonce 在请求头(密文 payload 里无字段)
    r = c.post("/api/platform/feishu/cmd", content=body,
               headers={**_signed_headers(body),
                        "X-Lark-Request-Timestamp": "1700000000",
                        "X-Lark-Request-Nonce": "n-1"})
    assert "handled" in r.json()["note"]
    assert "贾维斯" in r.json()["reply"]
    assert r.json()["chat_id"] == "oc_enc_p2p"


# --- 裁决指令(9/17 壳脑分工:批准 T-xxx + 二次确认制 + from='user' 落函) ---
def _seed_task(session):
    from models.org_mailbox import OrgMailbox as OM
    from datetime import datetime, timedelta
    now = datetime.now()
    row = OM(from_agent="platform", to_agent="flywheel", trace_id="m1-b009-convert_lerobot",
             title="[M1·b009] LeRobot 转换", body="b",
             deadline=now + timedelta(hours=2), created_at=now,
             task_meta={"task_type": "convert_lerobot", "consumer": "flywheel", "chain": "m1",
                        "batch": "b009"})
    session.add(row)
    session.commit()
    return row.id


def test_approve_flow_confirm_lands_user_letter(client):
    c, S, _ = client
    tid = _seed_task(S())
    r1 = _post(c, _event(text=f"批准 {tid}", event_id="evt_appr000001"))
    assert "将批准" in r1.json()["reply"] and str(tid) in r1.json()["reply"]
    r2 = _post(c, _event(text="确认", event_id="evt_appr000002"))
    assert "已批准" in r2.json()["reply"] and "flywheel" in r2.json()["reply"]
    s = S()
    from models.org_mailbox import OrgMailbox as OM
    approved = (s.query(OM).filter(OM.trace_id.like(f"jarvis-approved-{tid}-%")).first())
    assert approved is not None and approved.from_agent == "user"  # 人类拍板身份
    assert approved.to_agent == "flywheel"                          # 路由到任务 consumer


def test_approve_cancel_clears_pending(client):
    c, S, _ = client
    tid = _seed_task(S())
    _post(c, _event(text=f"批准 {tid}", event_id="evt_appr000003"))
    r = _post(c, _event(text="取消", event_id="evt_appr000004"))
    assert "已取消 1" in r.json()["reply"]
    r2 = _post(c, _event(text="确认", event_id="evt_appr000005"))
    assert "没有待确认" in r2.json()["reply"]


def test_approve_unknown_task_lists_recent(client):
    c, _, _ = client
    r = _post(c, _event(text="批准 T-nosuch", event_id="evt_appr000006"))
    assert "未找到" in r.json()["reply"]


# --- @框直达指令(9/18 接口层收口) ---
def test_at_frame_routes_as_user(client):
    c, S, _ = client
    r = _post(c, _event("@flywheel UMI 并行推进,补课闭环后台继续", event_id="evt_atfr0001"))
    assert "已转达 flywheel" in r.json()["reply"]
    s = S()
    from models.org_mailbox import OrgMailbox as OM
    row = (s.query(OM).filter(OM.trace_id.like("jarvis-direct-flywheel-%"))
           .order_by(OM.id.desc()).first())
    assert row is not None and row.from_agent == "user" and row.to_agent == "flywheel"
    assert (row.task_meta or {}).get("task_type") == "jarvis_direct"  # 进哨兵E4监控
    assert "UMI" in row.body
    s.close()


def test_at_unknown_frame_rejected_as_free_text(client):
    c, _, _ = client
    r = _post(c, _event("@nobody 你好", event_id="evt_atfr0002"))
    assert r.json().get("route") == "v5"  # 非 fifo 框名不吞,走脑

"""W6 RSI soul 半边 · grounding 暴露端纯核 extract_grounding.

跨 fde_verdicts 行展平打回项(pass is False)→ 可检索 grounding feed。
只读派生·fail-soft·无语义检索(compass turf)。
"""
from __future__ import annotations

from services.fde_grounding import extract_grounding


def _verdict(task_uid, source, items, *, checklist_uid="cl", score=0.5,
             created_at="2026-06-08T10:00:00"):
    return {"task_uid": task_uid, "source": source, "checklist_uid": checklist_uid,
            "score": score, "created_at": created_at, "items": items}


def test_emits_only_failed_items_with_reason_and_keys():
    rows = [_verdict("data_002", "soul", [
        {"id": "c1", "pass": True, "veto": True, "reason": ""},
        {"id": "c5", "pass": False, "veto": True,
         "reason": "veto: xlsx 与 docx 客户数不一致"},
        {"id": "c8", "pass": False, "veto": False, "reason": "图表缺单位"},
    ])]
    out = extract_grounding(rows)
    assert len(out) == 2                      # 只 c5 + c8 打回项·c1 pass 跳过
    c5 = next(r for r in out if r["item_id"] == "c5")
    assert c5["reason"] == "veto: xlsx 与 docx 客户数不一致"
    assert c5["task_uid"] == "data_002"
    assert c5["checklist_uid"] == "cl"
    assert c5["veto"] is True
    assert c5["source"] == "soul"
    assert c5["score"] == 0.5
    assert c5["created_at"] == "2026-06-08T10:00:00"


def test_veto_only_filters_to_hard_rules():
    rows = [_verdict("t", "soul", [
        {"id": "c5", "pass": False, "veto": True, "reason": "硬约束违反"},
        {"id": "c8", "pass": False, "veto": False, "reason": "软缺陷"},
    ])]
    out = extract_grounding(rows, veto_only=True)
    assert [r["item_id"] for r in out] == ["c5"]


def test_source_and_since_and_limit_filters():
    rows = [
        _verdict("a", "soul", [{"id": "x", "pass": False, "veto": False, "reason": "r1"}],
                 created_at="2026-06-01T00:00:00"),
        _verdict("b", "v5", [{"id": "y", "pass": False, "veto": False, "reason": "r2"}],
                 created_at="2026-06-08T00:00:00"),
    ]
    assert [r["item_id"] for r in extract_grounding(rows, source="v5")] == ["y"]
    assert [r["item_id"] for r in extract_grounding(rows, since="2026-06-05T00:00:00")] == ["y"]
    assert len(extract_grounding(rows, limit=1)) == 1


def test_fail_soft_on_malformed_items():
    rows = [
        {"task_uid": "t", "source": "soul", "items": None},          # items 非 list
        {"task_uid": "t", "source": "soul", "items": ["notadict",    # item 非 dict
            {"id": "z", "pass": False, "reason": "ok"}]},            # 缺 veto/checklist_uid
    ]
    out = extract_grounding(rows)
    assert len(out) == 1
    assert out[0]["item_id"] == "z"
    assert out[0]["veto"] is False        # 缺 veto → False
    assert out[0]["reason"] == "ok"


def test_pass_none_is_not_a_failure():
    rows = [{"task_uid": "t", "source": "soul",
             "items": [{"id": "q", "pass": None, "reason": "未判"}]}]
    assert extract_grounding(rows) == []   # pass is not False → 不算打回


# ---- Task 2: GET /api/platform/fde/grounding 薄路由(只读暴露 feed) ----
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 · register mappers
from models.fde_verdict import FdeVerdict  # noqa: F401
from utils.database import get_db
from api.fde_verdict import router as verdict_router
from api.fde_grounding import router as grounding_router


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(verdict_router)
    app.include_router(grounding_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _ingest(client, verdict_id, task_uid, source, items, score=0.5):
    return client.post("/api/platform/fde/verdict", json={
        "verdict_id": verdict_id, "task_uid": task_uid, "source": source,
        "checklist_uid": task_uid + "-cl", "overall_pass": False,
        "veto_failed": True, "score": score, "items": items})


def test_grounding_endpoint_returns_failed_items_across_tasks(client):
    _ingest(client, "v1", "data_002", "soul", [
        {"id": "c5", "pass": False, "veto": True, "reason": "客户数不一致"},
        {"id": "c1", "pass": True, "veto": True, "reason": ""}])
    _ingest(client, "v2", "data_009", "v5", [
        {"id": "c3", "pass": False, "veto": False, "reason": "缺单位"}])

    r = client.get("/api/platform/fde/grounding")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    reasons = {g["item_id"]: g["reason"] for g in body["data"]}
    assert reasons == {"c5": "客户数不一致", "c3": "缺单位"}   # 跨 2 题·只打回项


def test_grounding_endpoint_veto_only_and_source_filters(client):
    _ingest(client, "v1", "t", "soul", [
        {"id": "c5", "pass": False, "veto": True, "reason": "硬"},
        {"id": "c8", "pass": False, "veto": False, "reason": "软"}])
    r = client.get("/api/platform/fde/grounding?veto_only=true")
    assert [g["item_id"] for g in r.json()["data"]] == ["c5"]
    r2 = client.get("/api/platform/fde/grounding?source=v5")
    assert r2.json()["data"] == []


def test_grounding_endpoint_empty_when_no_verdicts(client):
    r = client.get("/api/platform/fde/grounding")
    assert r.status_code == 200
    assert r.json()["data"] == []

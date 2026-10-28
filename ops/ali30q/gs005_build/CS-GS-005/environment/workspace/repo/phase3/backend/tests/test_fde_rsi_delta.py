"""ΔReward → PoI fuel substrate (Horizon 2 · cnt_c3) · POST/GET /fde/rsi_delta.

The external objective RSI fitness: grounded-vs-bare ΔReward on a reproduced
benchmark. compass PoI consumes ONLY escapes_noise=True rows (don't credit noise).
Idempotent on delta_id. Mirrors the fde_verdict-bus pattern.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 · register mappers
from models.fde_rsi_delta import FdeRsiDelta  # noqa: F401
from utils.database import get_db
from api.fde_rsi_delta import router as rsi_router


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
    app.include_router(rsi_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _payload():
    # 第一个真外部 RSI 增量(radix_sort·全分布 escapes=True)
    return {
        "delta_id": "autolab_radix_sort|deepseek-chat|run-gv2",
        "benchmark": "autolab_radix_sort",
        "task_uid": "radix_sort",
        "producer_model": "deepseek-chat",
        "n_bare": 13, "n_grounded": 13,
        "bare_mean": 0.1835, "grounded_mean": 0.2568,
        "delta_reward": 0.0734, "p_value": 0.0215,
        "escapes_noise": True,
        "grounding_source": {"corpus": "autolab_avoid_radix_sort.md",
                             "round": 2, "policy": "correctness-first"},
    }


def test_post_persists_and_get_reads_back(client):
    r = client.post("/api/platform/fde/rsi_delta", json=_payload())
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True
    assert r.json()["data"]["escapes_noise"] is True

    g = client.get("/api/platform/fde/rsi_delta/radix_sort")
    rows = g.json()["data"]
    assert len(rows) == 1
    assert rows[0]["delta_reward"] == 0.0734
    assert rows[0]["benchmark"] == "autolab_radix_sort"
    assert rows[0]["grounding_source"]["policy"] == "correctness-first"


def test_idempotent_on_delta_id(client):
    client.post("/api/platform/fde/rsi_delta", json=_payload())
    r2 = client.post("/api/platform/fde/rsi_delta", json=_payload())
    assert r2.status_code == 200
    assert r2.json()["data"].get("idempotent") is True
    g = client.get("/api/platform/fde/rsi_delta/radix_sort")
    assert len(g.json()["data"]) == 1


def test_missing_required_rejected(client):
    bad = _payload()
    del bad["delta_reward"]
    r = client.post("/api/platform/fde/rsi_delta", json=bad)
    assert r.status_code == 400
    assert r.json()["success"] is False


def test_escapes_false_persists_but_filtered_from_poi_feed(client):
    # round-1 净负(escapes=False)·落库透明但 PoI 不消费
    client.post("/api/platform/fde/rsi_delta", json=_payload())
    neg = _payload()
    neg["delta_id"] = "autolab_radix_sort|deepseek-chat|run-v1-neg"
    neg["delta_reward"] = -0.0607
    neg["escapes_noise"] = False
    neg["p_value"] = 0.852
    client.post("/api/platform/fde/rsi_delta", json=neg)

    all_rows = client.get("/api/platform/fde/rsi_delta/radix_sort").json()["data"]
    assert len(all_rows) == 2  # 两条都落库(透明)

    poi = client.get("/api/platform/fde/rsi_delta/radix_sort?escapes_only=true").json()["data"]
    assert len(poi) == 1                      # 只 escapes=True 进 PoI feed
    assert poi[0]["escapes_noise"] is True
    assert poi[0]["delta_reward"] == 0.0734


def test_get_unknown_task_empty(client):
    g = client.get("/api/platform/fde/rsi_delta/nonexistent")
    assert g.status_code == 200
    assert g.json()["data"] == []

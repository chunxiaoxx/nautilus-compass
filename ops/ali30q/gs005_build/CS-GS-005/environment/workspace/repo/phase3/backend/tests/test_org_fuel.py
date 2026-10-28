# -*- coding: utf-8 -*-
"""fuel 轨迹通道(轨迹→燃料采集器·涡轮增压第一环·2026-10-04)。

schema 校验本地测(不触 DB);DB 行为(插入/幂等/读数)云端测试库跑后实测。
schema 正本=v5 FUEL_ORDER_SPEC_V1 §二(判据主权在 v5 四验门,平台只收档)。
"""
import asyncio
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app  # noqa: E402

client = TestClient(app)

_VALID = {
    "traj_id": "tr-test-0001",
    "bounty_id": "b-turbo-f999",
    "submitter": "9000018",
    "qid": "grpo-test-q1",
    "context": "tools schema + full dialogue",
    "trajectory": [{"role": "user", "content": "fix it"},
                   {"role": "assistant", "tool_calls": [{"name": "submit"}]}],
    "verdict": "pass",
    "label_origin": "verifier",
}


def test_reject_verdict_not_three_state():
    r = client.post("/api/platform/org/fuel/trajectories",
                    json={**_VALID, "verdict": "looks_good"})
    assert r.status_code == 422


def test_reject_llm_self_label():
    # FUEL_ORDER_SPEC: label_origin 禁 LLM 自报 → 只认 verifier/official_answer
    r = client.post("/api/platform/org/fuel/trajectories",
                    json={**_VALID, "label_origin": "llm_self_report"})
    assert r.status_code == 422


def test_reject_empty_trajectory():
    r = client.post("/api/platform/org/fuel/trajectories",
                    json={**_VALID, "trajectory": []})
    assert r.status_code == 422


def test_reject_empty_context():
    # 四验门第1条 render 非空 → context 空串在 schema 层就拒
    r = client.post("/api/platform/org/fuel/trajectories",
                    json={**_VALID, "context": ""})
    assert r.status_code == 422


def test_pipeline_readings_shape(monkeypatch):
    import api.org_fuel as m
    monkeypatch.setattr(m, "_load_turbo_registry", lambda: {
        "schema": "turbo_pipeline.v1",
        "stages": [{"id": "fuel-production", "stage": "燃料生产"},
                   {"id": "four-gates", "stage": "四验门"}]})
    db = MagicMock()
    seq = [
        MagicMock(fetchall=lambda: [("scored", 29), ("submitted", 7)]),
        MagicMock(fetchall=lambda: [("received", 3), ("gated", 1)]),
        MagicMock(fetchone=lambda: (2,)),
    ]
    db.execute.side_effect = lambda *a, **k: seq.pop(0)
    resp = asyncio.run(m.fuel_pipeline(db))
    assert resp["success"] is True
    rd = resp["data"]["readings"]
    assert rd["bounty_stage"]["scored"] == 29
    assert rd["pool_stage"]["received"] == 3
    assert rd["fuel_threshold"] == 50
    assert len(resp["data"]["stages"]) == 2

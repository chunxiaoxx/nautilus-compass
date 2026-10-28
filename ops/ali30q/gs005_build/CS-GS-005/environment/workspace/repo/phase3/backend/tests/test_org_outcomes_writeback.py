# -*- coding: utf-8 -*-
"""org_outcomes writeback 端点测试(U13 断奶第一刀)——云端 PG 测试库跑。
用例:①正常写回+回读 ②幂等二次投递全 skip ③短号无匹配进 misaligned 不硬填。
"""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

client = TestClient(app)


def _mk_proposal(db) -> str:
    pid = str(uuid4())
    db.execute(text(
        "INSERT INTO platform_improvement_proposals (id, root_cause, status, created_at, updated_at) "
        "VALUES (:i, 'writeback-test', 'pending', now(), now())"), {"i": pid})
    db.commit()
    return pid


@pytest.fixture(scope="module")
def seeded():
    db = SessionLocal()
    ids = [_mk_proposal(db) for _ in range(2)]
    yield ids
    for t in ("proposal_outcomes", "platform_improvement_proposals"):
        db.execute(text(f"DELETE FROM {t} WHERE id LIKE '%' "
                        "AND (root_cause='writeback-test' OR graded_by LIKE '%writeback-test%')"
                        if t == "platform_improvement_proposals" else
                        f"DELETE FROM {t} WHERE graded_by='writeback-test'"))
    db.commit()
    db.close()


def test_writeback_insert_and_readback(seeded):
    pid1, pid2 = seeded
    r = client.post("/api/platform/org/outcomes/writeback", json={
        "pack_id": "wb-test-1", "graded_by": "writeback-test",
        "pre_snapshot": {"week": "T"}, "post_snapshot": {"B4": 0.7},
        "items": [{"ticket": pid1[:8], "batch": "t", "fix_commit": "abc1234"}]})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["inserted"] == 1 and d["skipped"] == 0 and d["misaligned"] == []
    db = SessionLocal()
    row = db.execute(text("SELECT pre_snapshot->>'week', post_snapshot->>'fix_commit' "
                          "FROM proposal_outcomes WHERE proposal_id=:p"), {"p": pid1}).fetchone()
    db.close()
    assert row == ("T", "abc1234")


def test_writeback_idempotent(seeded):
    pid1, _ = seeded
    r = client.post("/api/platform/org/outcomes/writeback", json={
        "pack_id": "wb-test-2", "graded_by": "writeback-test",
        "pre_snapshot": {"week": "T"}, "post_snapshot": {},
        "items": [{"ticket": pid1[:8]}]})
    d = r.json()["data"]
    assert d["inserted"] == 0 and d["skipped"] == 1


def test_writeback_misaligned_no_hardfill(seeded):
    r = client.post("/api/platform/org/outcomes/writeback", json={
        "pack_id": "wb-test-3", "graded_by": "writeback-test",
        "pre_snapshot": {}, "post_snapshot": {},
        "items": [{"ticket": "zzzzzz99"}]})
    d = r.json()["data"]
    assert d["inserted"] == 0 and "zzzzzz99" in d["misaligned"]

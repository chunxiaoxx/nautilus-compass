"""compass v0.9.5 · /v1/recall semantic ranking (bge-m3 cosine) + keyword fallback.

Verifies:
  1. When the daemon is reachable (_daemon_score returns scores), recall ranks
     hits by bge-m3 cosine and reports ranker == "bge-m3".
  2. When the daemon is unreachable (_daemon_score returns None), recall falls
     back to the original keyword scoring (zero regression) and reports
     ranker == "keyword".

DB seeding follows the repo convention (test_http_server_e2e.py): isolated temp
DB via COMPASS_DB_PATH, force-reimport the module, seed observations through the
real /v1/observations endpoint, then drive /v1/recall over TestClient.

Run:
  PYTHONUTF8=1 python -m pytest tests/test_recall_semantic.py -v
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))
sys.path.insert(0, str(PLUGIN_DIR / "sdk"))


def _make_test_module(tmp_db: Path):
    """Build an isolated compass_http_v09 module bound to a temp DB.

    Mirrors test_http_server_e2e._make_test_app but returns the module so the
    test can monkeypatch module-level _daemon_score.
    """
    os.environ["COMPASS_DB_PATH"] = str(tmp_db)
    os.environ["NAUTILUS_JWT_SECRET"] = "test-secret-not-for-prod"
    os.environ["COMPASS_REGION"] = "cn-shanghai"

    for mod in list(sys.modules.keys()):
        if mod.startswith("compass_http_v09"):
            del sys.modules[mod]

    import compass_http_v09
    compass_http_v09.DB_PATH = tmp_db
    compass_http_v09.init_db()
    compass_http_v09.init_audit_table()
    return compass_http_v09


@pytest.fixture()
def app_ctx():
    from fastapi.testclient import TestClient

    # ignore_cleanup_errors: on Windows the sqlite/audit-thread handle can keep
    # the temp db file open past teardown · cleanup failure must not fail tests.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Path(tmp) / "test.db"
        srv = _make_test_module(db)
        client = TestClient(srv.app)

        # signup → token
        r = client.post("/v1/auth/signup", json={
            "email": "ranker@test.local",
            "passphrase": "correct horse battery staple",
            "region": "cn-shanghai",
        })
        assert r.status_code == 201, r.text
        signup = r.json()
        user_id = signup["user_id"]
        headers = {"Authorization": f"Bearer {signup['token']}"}

        # seed two observations (keyword score would be equal -> 0.5 each for 'gravity')
        for obs_id, agent_id, content in [
            ("ob_sem_001", "ag_test_a", {"name": "alpha note", "description": "first", "body": "apples"}),
            ("ob_sem_002", "ag_test_b", {"name": "beta note", "description": "second", "body": "oranges"}),
        ]:
            rr = client.post("/v1/observations", headers=headers, json={
                "obs_id": obs_id,
                "user_id": user_id,
                "agent_id": agent_id,
                "agent_type": "claude-code",
                "ts": "2026-05-05T10:00:00Z",
                "meta": {"type": "discovery", "concept": "pattern", "drift": "green",
                         "drift_signals": []},
                "content": content,
            })
            assert rr.status_code == 201, rr.text

        yield srv, client, headers, user_id


def test_recall_ranks_by_cosine_when_daemon_up(app_ctx, monkeypatch):
    srv, client, headers, user_id = app_ctx

    # daemon scores the candidates · over-fetch is ORDER BY ts DESC so the more
    # recently inserted obs (ob_sem_002) comes first in `rows`. We give the
    # FIRST row a LOW score and the SECOND row a HIGH score, so a correct cosine
    # ranking must reorder them (and prove it is not just the DB order).
    def fake_score(query, candidates, timeout=5.0):
        assert candidates, "candidates should be non-empty"
        # candidates align with rows order; make the last one win
        scores = [0.1] * len(candidates)
        scores[-1] = 0.95
        return scores

    monkeypatch.setattr(srv, "_daemon_score", fake_score)

    r = client.get("/v1/recall", headers=headers, params={"q": "gravity"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ranker"] == "bge-m3", body
    hits = body["hits"]
    assert len(hits) == 2
    # top hit must be the one we gave 0.95
    assert hits[0]["score"] == 0.95
    assert hits[1]["score"] == 0.1
    assert hits[0]["score"] >= hits[1]["score"], "hits not sorted by cosine desc"


def test_recall_falls_back_to_keyword_when_daemon_down(app_ctx, monkeypatch):
    srv, client, headers, user_id = app_ctx

    # daemon unreachable → _daemon_score returns None → keyword path (zero regression)
    monkeypatch.setattr(srv, "_daemon_score", lambda *a, **k: None)

    r = client.get("/v1/recall", headers=headers, params={"q": "alpha"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ranker"] == "keyword", body
    hits = body["hits"]
    assert len(hits) == 2
    # keyword path: 'alpha' is in ob_sem_001 content -> score 1.0, other -> 0.5
    top = hits[0]
    assert top["obs_id"] == "ob_sem_001", hits
    assert top["score"] == 1.0
    assert hits[1]["score"] == 0.5

import json, sqlite3
import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]


def _load_cron():
    spec = importlib.util.spec_from_file_location("poi_reconcile_cron", _HERE / "ops" / "poi_reconcile_cron.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


CREATE = ("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, cumulative_impact REAL "
          "NOT NULL DEFAULT 0, event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")


def _cand(actor="a1", project="proj", memory="m.md", creator="other", ts="2026-06-03T00:00:00+00:00", qh="q"):
    return {"kind": "candidate", "actor": actor, "project": project, "memory": memory,
            "creator": creator, "query_hash": qh, "ts": ts, "rank": 0, "score": 0.9}


def test_settle_and_snapshot_writes_credit_and_snapshot(tmp_path):
    cron = _load_cron()
    conn = sqlite3.connect(":memory:"); conn.execute(CREATE)
    snap = tmp_path / "poi_credit_cache.json"
    outcomes = [{"agent_id": "a1", "success": True, "ts": "2026-06-03T00:10:00+00:00"}]
    res = cron.settle_and_snapshot(conn, [_cand()], outcomes, set(),
                                   snapshot_path=snap, placeholder="?")
    assert res["settled"] == 1
    data = json.loads(snap.read_text(encoding="utf-8"))
    assert "proj/m.md" in data and data["proj/m.md"] > 0


def test_settle_and_snapshot_no_match_writes_empty_snapshot(tmp_path):
    cron = _load_cron()
    conn = sqlite3.connect(":memory:"); conn.execute(CREATE)
    snap = tmp_path / "poi_credit_cache.json"
    # outcome ts far outside the default window → no match
    outcomes = [{"agent_id": "a1", "success": True, "ts": "2027-01-01T00:00:00+00:00"}]
    res = cron.settle_and_snapshot(conn, [_cand()], outcomes, set(),
                                   snapshot_path=snap, placeholder="?")
    assert res["settled"] == 0
    assert res["skipped_no_match"] == 1
    data = json.loads(snap.read_text(encoding="utf-8"))
    assert data == {}

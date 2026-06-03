import sqlite3
from proof.poi_reconciler import reconcile_central

CREATE = ("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, cumulative_impact REAL "
          "NOT NULL DEFAULT 0, event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")


def _conn():
    c = sqlite3.connect(":memory:"); c.execute(CREATE); return c


def _cand(actor="a1", project="proj", memory="m.md", creator="other", ts="2026-06-03T00:00:00+00:00", qh="q"):
    return {"kind": "candidate", "actor": actor, "project": project, "memory": memory,
            "creator": creator, "query_hash": qh, "ts": ts, "rank": 0, "score": 0.9}


def test_settle_writes_central_no_file_needed():
    # 云端 memory · 本地无文件 · 仍 settle(M1 松绑)
    conn = _conn(); settled = set()
    outcomes = [{"agent_id": "a1", "success": True, "ts": "2026-06-03T00:10:00+00:00"}]
    r = reconcile_central([_cand()], outcomes, conn=conn, settled_keys=settled, placeholder="?")
    assert r["settled"] == 1
    row = conn.execute("SELECT cumulative_impact FROM poi_credit WHERE memory_key='proj/m.md'").fetchone()
    assert row and row[0] > 0


def test_rerun_idempotent_no_double_count():
    conn = _conn(); settled = set()
    outcomes = [{"agent_id": "a1", "success": True, "ts": "2026-06-03T00:10:00+00:00"}]
    reconcile_central([_cand()], outcomes, conn=conn, settled_keys=settled, placeholder="?")
    reconcile_central([_cand()], outcomes, conn=conn, settled_keys=settled, placeholder="?")
    row = conn.execute("SELECT event_count FROM poi_credit WHERE memory_key='proj/m.md'").fetchone()
    assert row[0] == 1  # 第二次被 settled_keys 挡住


def test_selfcite_dropped():
    conn = _conn(); settled = set()
    outcomes = [{"agent_id": "a1", "success": True, "ts": "2026-06-03T00:10:00+00:00"}]
    r = reconcile_central([_cand(creator="a1")], outcomes, conn=conn, settled_keys=settled, placeholder="?")
    assert r["settled"] == 0 and r.get("skipped_selfcite") == 1

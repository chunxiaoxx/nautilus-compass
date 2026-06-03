import sqlite3
from proof.poi_reconciler import reconcile_central, central_candidate_key, candidate_key

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


def test_central_key_matches_what_settle_persists():
    # The key the cron pre-filter computes (central_candidate_key on the RAW
    # candidate) must equal the key reconcile_central actually persists into
    # settled_keys. Otherwise the pre-filter never matches → unbounded re-work.
    conn = _conn(); settled = set()
    raw = _cand()
    outcomes = [{"agent_id": "a1", "success": True, "ts": "2026-06-03T00:10:00+00:00"}]
    r = reconcile_central([raw], outcomes, conn=conn, settled_keys=settled, placeholder="?")
    assert r["settled"] == 1
    # what the cron pre-filter would compute IS in the persisted set
    assert central_candidate_key(raw) in settled
    # and it differs from the raw key (proves the original bug: raw != central)
    assert central_candidate_key(raw) != candidate_key(raw)


def test_dry_run_does_not_write_db():
    # dry_run=True counts what WOULD settle but writes nothing to the DB
    conn = _conn()
    outcomes = [{"agent_id": "a1", "success": True, "ts": "2026-06-03T00:10:00+00:00"}]
    r = reconcile_central([_cand()], outcomes, conn=conn, settled_keys=set(),
                          placeholder="?", dry_run=True)
    assert r["settled"] == 1
    cnt = conn.execute("SELECT COUNT(*) FROM poi_credit").fetchone()[0]
    assert cnt == 0

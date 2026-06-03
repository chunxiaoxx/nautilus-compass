import json, sqlite3
from pathlib import Path
from proof.poi_credit_store import (
    upsert_credit, fetch_all_credits, write_snapshot_atomic, load_snapshot,
)

CREATE_SQLITE = (
    "CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
    "cumulative_impact REAL NOT NULL DEFAULT 0, event_count INTEGER NOT NULL DEFAULT 0, "
    "last_impact_at TEXT)"
)

def _conn():
    c = sqlite3.connect(":memory:")
    c.execute(CREATE_SQLITE)
    return c

def test_upsert_accumulates():
    c = _conn()
    upsert_credit(c, "proj/a.md", 0.5, "2026-06-03T00:00:00+00:00", placeholder="?")
    upsert_credit(c, "proj/a.md", 0.3, "2026-06-03T01:00:00+00:00", placeholder="?")
    row = c.execute("SELECT cumulative_impact, event_count FROM poi_credit WHERE memory_key='proj/a.md'").fetchone()
    assert round(row[0], 4) == 0.8 and row[1] == 2

def test_fetch_all_credits_dict():
    c = _conn()
    upsert_credit(c, "proj/a.md", 0.5, "t", placeholder="?")
    upsert_credit(c, "proj/b.md", -0.2, "t", placeholder="?")
    d = fetch_all_credits(c)
    assert d == {"proj/a.md": 0.5, "proj/b.md": -0.2}

def test_snapshot_atomic_roundtrip(tmp_path):
    snap = tmp_path / "poi_credit_cache.json"
    write_snapshot_atomic(snap, {"proj/a.md": 0.8})
    assert not list(tmp_path.glob("*.tmp"))
    assert load_snapshot(snap) == {"proj/a.md": 0.8}

def test_load_snapshot_missing_returns_empty(tmp_path):
    assert load_snapshot(tmp_path / "nope.json") == {}

def test_load_snapshot_corrupt_returns_empty(tmp_path):
    p = tmp_path / "bad.json"; p.write_text("{not json", encoding="utf-8")
    assert load_snapshot(p) == {}

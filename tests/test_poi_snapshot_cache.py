import json, time
from pathlib import Path
import recall_pkg.poi_snapshot_cache as C

def _write(p, d):
    p.write_text(json.dumps(d), encoding="utf-8")

def test_loads_then_caches(tmp_path, monkeypatch):
    snap = tmp_path / "poi_credit_cache.json"
    _write(snap, {"proj/a.md": 1.0})
    monkeypatch.setenv("COMPASS_POI_CREDIT_SNAPSHOT", str(snap))
    C.reset_cache()
    assert C.get_credit_snapshot() == {"proj/a.md": 1.0}
    # second call returns same dict without needing the file
    assert C.get_credit_snapshot() == {"proj/a.md": 1.0}

def test_reloads_on_mtime_change(tmp_path, monkeypatch):
    snap = tmp_path / "poi_credit_cache.json"
    _write(snap, {"proj/a.md": 1.0})
    monkeypatch.setenv("COMPASS_POI_CREDIT_SNAPSHOT", str(snap))
    C.reset_cache()
    assert C.get_credit_snapshot() == {"proj/a.md": 1.0}
    time.sleep(0.01)
    _write(snap, {"proj/a.md": 2.0, "proj/b.md": 5.0})
    # force a different mtime (some filesystems are coarse)
    import os
    st = snap.stat()
    os.utime(snap, (st.st_atime + 5, st.st_mtime + 5))
    assert C.get_credit_snapshot() == {"proj/a.md": 2.0, "proj/b.md": 5.0}

def test_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPASS_POI_CREDIT_SNAPSHOT", str(tmp_path / "nope.json"))
    C.reset_cache()
    assert C.get_credit_snapshot() == {}

def test_corrupt_reload_keeps_last_good(tmp_path, monkeypatch):
    snap = tmp_path / "poi_credit_cache.json"
    _write(snap, {"proj/a.md": 1.0})
    monkeypatch.setenv("COMPASS_POI_CREDIT_SNAPSHOT", str(snap))
    C.reset_cache()
    assert C.get_credit_snapshot() == {"proj/a.md": 1.0}
    # corrupt + bump mtime → reload attempts, fails, keeps last good
    snap.write_text("{bad json", encoding="utf-8")
    import os
    st = snap.stat(); os.utime(snap, (st.st_atime + 5, st.st_mtime + 5))
    assert C.get_credit_snapshot() == {"proj/a.md": 1.0}

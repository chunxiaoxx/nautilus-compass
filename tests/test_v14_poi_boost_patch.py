"""Exec-test the cloud v14 PoI boost helper (BOOST_HELPER string deployed into
compass_http_v09.py). Mirrors the emission patch test: exec the helper into a
namespace supplying _v14_os, then assert rerank behavior. NO daemon needed."""
import os
import json

from ops.patch_v14_recall_poi_boost import BOOST_HELPER


def _load_helper():
    ns = {"_v14_os": os}
    exec(BOOST_HELPER, ns)
    return ns["_v14_poi_boost"]


def test_boost_reranks_credited(tmp_path, monkeypatch):
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps({"proj/hi.md": 5.0}), encoding="utf-8")  # boost clamp 0.5 → ×1.5
    monkeypatch.setenv("COMPASS_CLOUD_POI_BOOST", "1")
    monkeypatch.setenv("COMPASS_POI_CREDIT_SNAPSHOT", str(snap))
    boost = _load_helper()
    hits = [{"project": "other", "path": "lo.md", "score": 0.6},
            {"project": "proj", "path": "hi.md", "score": 0.45}]
    boost(hits)
    assert hits[0]["path"] == "hi.md"               # 0.45*1.5=0.675 > 0.6 → reranked top
    assert round(hits[0]["score"], 4) == 0.675


def test_boost_env_off_is_noop(tmp_path, monkeypatch):
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps({"proj/hi.md": 5.0}), encoding="utf-8")
    monkeypatch.delenv("COMPASS_CLOUD_POI_BOOST", raising=False)
    monkeypatch.setenv("COMPASS_POI_CREDIT_SNAPSHOT", str(snap))
    boost = _load_helper()
    hits = [{"project": "proj", "path": "hi.md", "score": 0.45}]
    boost(hits)
    assert hits[0]["score"] == 0.45                 # boost off → untouched


def test_boost_missing_snapshot_is_noop(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPASS_CLOUD_POI_BOOST", "1")
    monkeypatch.setenv("COMPASS_POI_CREDIT_SNAPSHOT", str(tmp_path / "nope.json"))
    boost = _load_helper()
    hits = [{"project": "p", "path": "a.md", "score": 0.5}]
    boost(hits)
    assert hits[0]["score"] == 0.5                  # no snapshot → graceful no-op


def test_boost_only_credited_hits(tmp_path, monkeypatch):
    snap = tmp_path / "s.json"
    snap.write_text(json.dumps({"proj/hi.md": 3.0}), encoding="utf-8")  # ×1.3
    monkeypatch.setenv("COMPASS_CLOUD_POI_BOOST", "1")
    monkeypatch.setenv("COMPASS_POI_CREDIT_SNAPSHOT", str(snap))
    boost = _load_helper()
    hits = [{"project": "proj", "path": "hi.md", "score": 0.5},
            {"project": "x", "path": "y.md", "score": 0.4}]
    boost(hits)
    d = {h["path"]: h["score"] for h in hits}
    assert round(d["hi.md"], 4) == 0.65 and d["y.md"] == 0.4  # uncredited unchanged


def test_boost_normalizes_windows_project(tmp_path, monkeypatch):
    snap = tmp_path / "s.json"
    snap.write_text(json.dumps({"C--Users-chunx/m.md": 5.0}), encoding="utf-8")
    monkeypatch.setenv("COMPASS_CLOUD_POI_BOOST", "1")
    monkeypatch.setenv("COMPASS_POI_CREDIT_SNAPSHOT", str(snap))
    boost = _load_helper()
    hits = [{"project": "C:\\Users\\chunx", "path": "m.md", "score": 0.4}]
    boost(hits)
    assert round(hits[0]["score"], 4) == 0.6        # raw windows project normalized → matched

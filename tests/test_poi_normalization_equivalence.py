"""Drift guard: the project-normalization logic exists in THREE places —
  1. proof/poi_memory_key._normalize_project  (local · importable)
  2. ops/patch_v14_recall_poi_boost.BOOST_HELPER      (cloud · inline raw-string)
  3. ops/patch_v14_recall_poi_candidate.EMIT_HELPER   (cloud · inline raw-string)
Copies 2/3 are injected verbatim into the cloud server (proof/ isn't importable
there). If any copy drifts, cloud keys silently desync from local keys and joins
against compass.poi_credit break with NO unit test catching it. This test execs
the deployed cloud helpers and asserts byte-for-byte identical normalization to
the local source of truth across a fixed corpus, so any drift fails CI.
"""
from __future__ import annotations

import json
import os

import pytest

from proof.poi_memory_key import _normalize_project
from ops.patch_v14_recall_poi_boost import BOOST_HELPER
from ops.patch_v14_recall_poi_candidate import EMIT_HELPER


# project inputs spanning every branch of the normalization guard
CORPUS = [
    "C:\\Users\\chunx",   # windows backslash → encoded
    "C:/Users/chunx",     # windows forward slash → encoded
    "C--Users-chunx",     # already encoded → unchanged
    "cycle-59717-auto",   # plain segment → unchanged
    "/home/ubuntu/x",     # posix abs, no ':'/'\\' → guard false → unchanged
    "a/b/c",              # rel slash, guard false → unchanged
    "",                   # empty → ""
]


def _load_boost():
    ns = {"_v14_os": os}
    exec(BOOST_HELPER, ns)
    return ns["_v14_poi_boost"]


def _load_emit():
    ns = {"_v14_os": os, "_v14_json": json}
    exec(EMIT_HELPER, ns)
    return ns["_v14_emit_poi_candidate"]


@pytest.mark.parametrize("project", CORPUS)
def test_boost_normalization_matches_local(project, tmp_path, monkeypatch):
    """boost helper finds the credit iff its normalization == _normalize_project."""
    expected = _normalize_project(project)
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps({expected + "/m.md": 5.0}), encoding="utf-8")  # ×1.5 (clamp 0.5)
    monkeypatch.setenv("COMPASS_CLOUD_POI_BOOST", "1")
    monkeypatch.setenv("COMPASS_POI_CREDIT_SNAPSHOT", str(snap))
    boost = _load_boost()
    hits = [{"project": project, "path": "m.md", "score": 0.4}]
    boost(hits)
    # matched key → boosted 0.4×1.5=0.6; any normalization drift → miss → stays 0.4
    assert round(hits[0]["score"], 4) == 0.6, (
        f"boost normalization drifted for {project!r}: expected key prefix {expected!r}")


@pytest.mark.parametrize("project", CORPUS)
def test_emit_normalization_matches_local(project, tmp_path, monkeypatch):
    """emit helper writes a project field == _normalize_project(project)."""
    expected = _normalize_project(project)
    monkeypatch.setenv("COMPASS_POI_CACHE_DIR", str(tmp_path))
    emit = _load_emit()
    emit([{"path": "m.md", "project": project, "score": 0.5}], "q", "actor")
    rec = json.loads((tmp_path / "poi_candidates.jsonl").read_text(encoding="utf-8").strip())
    assert rec["project"] == expected, (
        f"emit normalization drifted for {project!r}: got {rec['project']!r} want {expected!r}")

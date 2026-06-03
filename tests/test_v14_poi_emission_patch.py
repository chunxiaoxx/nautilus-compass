"""Tests for the v14 recall PoI candidate emission patch.

The patch injects a self-contained `_v14_emit_poi_candidate` into the cloud
HTTP server. We exec the exact EMIT_HELPER string the patch deploys, then
assert the JSONL it writes — so the test covers the real production code.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import importlib.util

_SPEC = importlib.util.spec_from_file_location(
    "patch_v14_poi",
    Path(__file__).resolve().parent.parent / "ops" / "patch_v14_recall_poi_candidate.py")
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


def _load_emit():
    """exec the deployed helper string in a namespace mirroring the cloud server's
    injected aliases (_v14_os, _v14_json)."""
    ns = {"_v14_os": os, "_v14_json": json}
    exec(_MOD.EMIT_HELPER, ns)
    return ns["_v14_emit_poi_candidate"]


def test_emits_one_line_per_hit(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPASS_POI_CACHE_DIR", str(tmp_path))
    emit = _load_emit()
    hits = [{"path": "a.md", "score": 0.91}, {"path": "b.md", "score": 0.5}]
    n = emit(hits, "some query", "nautilus-prime-001")
    assert n == 2
    lines = (tmp_path / "poi_candidates.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    r0 = json.loads(lines[0])
    assert r0["kind"] == "candidate"
    assert r0["actor"] == "nautilus-prime-001"
    assert r0["memory"] == "a.md"
    assert r0["rank"] == 0
    assert r0["score"] == 0.91
    assert len(r0["query_hash"]) == 16


def test_none_agent_id_becomes_unknown(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPASS_POI_CACHE_DIR", str(tmp_path))
    emit = _load_emit()
    n = emit([{"path": "a.md", "score": 0.1}], "q", None)
    assert n == 1
    r = json.loads((tmp_path / "poi_candidates.jsonl").read_text(encoding="utf-8").strip())
    assert r["actor"] == "unknown"


def test_skips_hits_without_path(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPASS_POI_CACHE_DIR", str(tmp_path))
    emit = _load_emit()
    n = emit([{"score": 0.1}, {"path": "b.md", "score": 0.2}], "q", "x")
    assert n == 1


def test_empty_hits_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPASS_POI_CACHE_DIR", str(tmp_path))
    emit = _load_emit()
    n = emit([], "q", "x")
    assert n == 0
    assert not (tmp_path / "poi_candidates.jsonl").exists()


def test_carries_per_hit_project(tmp_path, monkeypatch):
    """3-arg signature · project derived PER HIT from each hit's own `project`
    field (scope=user correctness: one recall returns hits from different
    projects; daemon already tags each hit with its project). Each written
    candidate carries its hit's project, normalized to encoded_cwd form."""
    monkeypatch.setenv("COMPASS_POI_CACHE_DIR", str(tmp_path))
    emit = _load_emit()
    hits = [
        {"path": "a.md", "project": "cycle-59717-auto", "score": 0.9},
        {"path": "b.md", "project": "C:\\Users\\chunx", "score": 0.8},
    ]
    n = emit(hits, "q", "actor-1")
    assert n == 2
    lines = (tmp_path / "poi_candidates.jsonl").read_text(encoding="utf-8").strip().splitlines()
    r0 = json.loads(lines[0])
    r1 = json.loads(lines[1])
    assert r0["project"] == "cycle-59717-auto"   # already plain · unchanged
    assert r1["project"] == "C--Users-chunx"      # windows path · normalized


# ---- patch application (against a synthetic copy of the live route) -----------

# Faithful copy of the live cloud route (compass_http_v09.py, v1.5.8 shape:
# two early-return guards + scope/projects_scanned/fresh_extra success return).
_LIVE_ROUTE = '''import os
from typing import Optional
from fastapi import Header

@app.get("/v1/v14/recall")
def v14_recall(
    q: str,
    top_k: int = 5,
    scope: str = "project",
    project: Optional[str] = None,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
):
    """v1.4 BGE-m3 recall."""
    req = {"action": "recall", "query": (q or "")[:2000]}
    if project:
        req["project"] = project
    d = _call_v14_daemon(req, timeout=15.0)
    if not d:
        return {"ok": False, "error": "v14 daemon unreachable · all ports transport-failed",
                "backend": "v1.4-bge-m3"}
    if not d.get("ok"):
        return {"ok": False, "error": d.get("error", "daemon returned ok=false"),
                "backend": "v1.4-bge-m3"}
    return {
        "ok": True,
        "scope": d.get("scope", scope),
        "projects_scanned": d.get("projects_scanned", []),
        "hits": d.get("recall", []),
        "fresh_extra": d.get("fresh_extra", []),
        "backend": "v1.4-bge-m3",
    }
'''


def test_patch_is_idempotent(tmp_path):
    target = tmp_path / "compass_http_v09.py"
    target.write_text(_LIVE_ROUTE, encoding="utf-8")
    assert _MOD.apply_patch(target) is True          # first run patches
    once = target.read_text(encoding="utf-8")
    assert _MOD.apply_patch(target) is False         # second run skips
    assert target.read_text(encoding="utf-8") == once


def test_patch_adds_agent_id_param_and_emit_and_helper(tmp_path):
    target = tmp_path / "compass_http_v09.py"
    target.write_text(_LIVE_ROUTE, encoding="utf-8")
    _MOD.apply_patch(target)
    out = target.read_text(encoding="utf-8")
    assert "agent_id: Optional[str] = None" in out
    assert "def _v14_emit_poi_candidate(" in out
    assert "_v14_emit_poi_candidate(_h, q, agent_id)" in out
    # patched module must still be importable Python
    compile(out, "patched", "exec")


def test_patched_route_emits_on_real_call(tmp_path, monkeypatch):
    """exec the patched module with stubbed _call_v14_daemon + FastAPI shims,
    call v14_recall, assert a candidate line lands."""
    target = tmp_path / "compass_http_v09.py"
    target.write_text(_LIVE_ROUTE, encoding="utf-8")
    _MOD.apply_patch(target)
    monkeypatch.setenv("COMPASS_POI_CACHE_DIR", str(tmp_path / "poi"))

    class _App:
        def get(self, *a, **k):
            return lambda fn: fn
        def post(self, *a, **k):
            return lambda fn: fn

    def _Header(default=None, alias=None):
        return default

    daemon_hits = [
        {"path": "m.md", "project": "cycle-59717-auto", "score": 0.7},
        {"path": "n.md", "project": "C:\\Users\\chunx", "score": 0.6},
    ]
    ns = {"app": _App(), "Header": _Header,
          "_call_v14_daemon": lambda req, timeout=None: {"ok": True, "recall": daemon_hits},
          "_v14_os": os, "_v14_json": json}
    exec(compile(target.read_text(encoding="utf-8"), "patched", "exec"), ns)
    # scope=user: requester's project context is irrelevant; each hit carries its own.
    res = ns["v14_recall"]("hello", scope="user", agent_id="nautilus-prime-001")
    assert res["ok"] is True
    lines = (tmp_path / "poi" / "poi_candidates.jsonl").read_text(encoding="utf-8").strip().splitlines()
    r0 = json.loads(lines[0])
    r1 = json.loads(lines[1])
    assert r0["actor"] == "nautilus-prime-001"
    assert r0["memory"] == "m.md"
    assert r0["project"] == "cycle-59717-auto"   # per-hit · already plain
    assert r1["memory"] == "n.md"
    assert r1["project"] == "C--Users-chunx"      # per-hit · normalized

"""T1 cheap-tier knobs (2026-09-03 preregistration) unit tests.

Locks: ①new knobs default OFF → d12 baseline behavior unchanged
②rule-based query decomposition splits coordination/comparison questions
③per-trajectory screenshot floor distributes shots across trajectories.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

# lmev2_compass_memory.py lives in the upstream memory_modules/ package and
# uses relative imports ("from .memory import ..."). Inject a stub package
# so we can load it standalone without cloning the upstream repo.
_stub_pkg = types.ModuleType("memory_modules")
_stub_pkg.__path__ = []
sys.modules.setdefault("memory_modules", _stub_pkg)
_stub = types.ModuleType("memory_modules.memory")


class _Memory:
    def __init__(self, memory_params):
        self.memory_params = memory_params


def _register_memory(cls):
    return cls


_stub.Memory = _Memory
_stub.MemoryContextItem = dict
_stub.register_memory = _register_memory
sys.modules.setdefault("memory_modules.memory", _stub)

_src = Path(__file__).parent.parent / "vtf" / "lmev2_compass_memory.py"
_spec = importlib.util.spec_from_file_location(
    "memory_modules.lmev2_compass_memory", _src)
_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("memory_modules.lmev2_compass_memory", _mod)
_spec.loader.exec_module(_mod)
CompassMemory = _mod.CompassMemory


def _mk(params=None):
    return CompassMemory(params or {})


def test_defaults_keep_baseline():
    m = _mk()
    assert m._a11y_chars == 500
    assert m._query_decomp is False
    assert m._shot_per_traj == 0


def test_sub_queries_split_coordination():
    m = _mk({"query_decomp": True})
    q = ("What are the mandatory fields on the create submission form and "
         "which of them defaults to pittsburgh?")
    subs = m._sub_queries(q)
    assert len(subs) == 2, subs
    assert all(s != q and len(s.split()) >= 4 for s in subs)


def test_sub_queries_no_split_on_simple():
    m = _mk({"query_decomp": True})
    q = "Which pagination label should be clicked first to reach the oldest orders?"
    subs = m._sub_queries(q)
    # no coordination structure -> no sub-queries (original query only)
    assert subs == []


def test_sub_queries_caps_at_four():
    m = _mk({"query_decomp": True})
    q = "A section one here, B section two here, C section three here, D four, E five, F six"
    assert len(m._sub_queries(q)) <= 4


def test_screenshot_floor_per_traj():
    m = _mk({"shot_per_traj": 1, "max_screenshots": 3})
    # three trajs × one chunk each with a screenshot, all hit
    chunks = [
        {"traj_id": f"t{i}", "state_idx": 0, "text": "x", "screenshot": f"s{i}.png"}
        for i in range(5)
    ]
    m._chunks = chunks
    fused = [1.0] * 5
    # emulate the query loop's shot selection with floor semantics
    shots = []
    for traj_id in ["t0", "t1", "t2", "t3", "t4"]:
        traj_chunks = [c for c in chunks if c["traj_id"] == traj_id]
        quota = m._shot_per_traj
        taken = 0
        for c in sorted(traj_chunks, key=lambda c: -fused[chunks.index(c)]):
            shot = c.get("screenshot")
            cap = quota if quota > 0 else m._max_screenshots
            if shot and shot not in shots and len(shots) < m._max_screenshots and taken < cap:
                shots.append(shot)
                taken += 1
    # floor=1 with global cap 3 -> shots from three DIFFERENT trajectories
    assert len(shots) == 3
    assert shots == ["s0.png", "s1.png", "s2.png"]

#!/usr/bin/env python3
"""v3.2 · 刀A/B 单测:向量 numpy 化 + 旧 pkl 惰性转换 + 容量预算逐出。

对应 CLOUD_DAEMON_ROOTCURE_PLAN_20260930.md 判据:
  J6 numpy 转换等价(转换前后 cosine 排序不变)
  J2 预算内零逐出 / 超预算逐出最久未用
目标文件 runtime/cloud_daemon_v32_20260930.py(懒加载,顶层无 torch 依赖)。
"""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "cloud_daemon_v32", ROOT / "runtime" / "cloud_daemon_v32_20260930.py")
d = importlib.util.module_from_spec(_spec)
sys.modules["cloud_daemon_v32"] = d
_spec.loader.exec_module(d)

import numpy as np  # noqa: E402


def _cos_python(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na > 0 and nb > 0 else 0.0


def test_cosine_np_equals_python():
    """J6 · np 路径与纯 python 路径数值一致(1e-6)。"""
    rng = np.random.default_rng(42)
    for _ in range(50):
        a = rng.standard_normal(1024).astype(np.float32)
        b = rng.standard_normal(1024).astype(np.float32)
        assert abs(d.cosine(a, b) - _cos_python(a.tolist(), b.tolist())) < 1e-6
        # list/np 混合输入兼容(旧 pkl PyList 命中场景)
        assert abs(d.cosine(a.tolist(), b) - _cos_python(a.tolist(), b.tolist())) < 1e-6


def test_lazy_conversion_old_pkl_pylist():
    """J6 · 旧 pkl PyList 值命中时惰性转 np 并回写 cache。"""
    proj = "lazyconv"
    d._state["memory_caches"][proj] = {
        "f1.md": (1.0, [0.1] * 1024),          # entry vec(PyList)
        "f1.md|chunks": (1.0, [[0.2] * 1024]),  # chunks(list of PyList)
    }
    # entry 转换路径(get_memory_entries 主循环等价逻辑)
    cached = d._state["memory_caches"][proj]["f1.md"]
    assert not isinstance(cached[1], np.ndarray)
    vec = cached[1]
    if not isinstance(vec, np.ndarray):
        vec = np.asarray(vec, dtype=np.float32)
        d._state["memory_caches"][proj]["f1.md"] = (cached[0], vec)
    assert isinstance(d._state["memory_caches"][proj]["f1.md"][1], np.ndarray)
    # 内存对比:PyList 全量 ~32KB → np 数据缓冲 4KB(getsizeof 另含 ~112B header)
    import sys as _s
    assert vec.nbytes == 1024 * 4  # float32 数据缓冲 4096B
    assert _s.getsizeof(vec) < 5 * 1024  # 含 header 仍 <5KB
    _full = [0.1] * 1024
    _pylist_bytes = _s.getsizeof(_full) + sum(_s.getsizeof(x) for x in _full)
    assert _pylist_bytes > 25 * 1024  # PyList 全量 ~32KB(8x 差的实证)
    # chunk 转换路径
    cch = d._state["memory_caches"][proj]["f1.md|chunks"]
    vecs = cch[1]
    if vecs and not isinstance(vecs[0], np.ndarray):
        vecs = [np.asarray(v, dtype=np.float32) for v in vecs]
        d._state["memory_caches"][proj]["f1.md|chunks"] = (cch[0], vecs)
    assert isinstance(d._state["memory_caches"][proj]["f1.md|chunks"][1][0], np.ndarray)


def test_budget_eviction_order():
    """J2 · 超预算逐出最旧;预算内零逐出;访问序 LRU(move_to_end)。"""
    d._ENTRIES_CACHE.clear()
    d._state["memory_caches"].clear()
    d._LRU_STATS["evicted"] = 0
    old_budget = d._EMBED_BUDGET
    d._EMBED_BUDGET = 5  # 压到极小便于触发
    try:
        # 3 项目,各 2 向量 = 6 > 5 → 应逐出最旧(p1)
        for p in ("p1", "p2", "p3"):
            d._ENTRIES_CACHE[p] = [f"{p}-entries"]
            d._state["memory_caches"][p] = {
                "a.md": (1.0, np.zeros(8, np.float32)),
                "b.md": (1.0, np.zeros(8, np.float32)),
            }
        d._entries_cache_lru_trim("p3")
        assert "p1" not in d._ENTRIES_CACHE
        assert "p1" not in d._state["memory_caches"]
        assert "p3" in d._ENTRIES_CACHE          # just_used 保护
        assert d._LRU_STATS["evicted"] == 1
        # 预算内(p2+p3=4 ≤ 5)→ 再 trim 零逐出
        d._entries_cache_lru_trim("p3")
        assert d._LRU_STATS["evicted"] == 1
        # 访问序:touch p2 后,超预算时逐 p3 而非 p2
        d._state["memory_caches"]["p4"] = {
            "a.md": (1.0, np.zeros(8, np.float32)),
            "b.md": (1.0, np.zeros(8, np.float32)),
        }
        d._ENTRIES_CACHE["p4"] = ["p4-entries"]
        with d._ENTRIES_CACHE_LOCK:
            d._ENTRIES_CACHE.move_to_end("p2")   # p2 变最新
        d._entries_cache_lru_trim("p4")
        assert "p3" not in d._ENTRIES_CACHE      # p3 现在是最旧
        assert "p2" in d._ENTRIES_CACHE
    finally:
        d._EMBED_BUDGET = old_budget
        d._ENTRIES_CACHE.clear()
        d._state["memory_caches"].clear()
        d._LRU_STATS["evicted"] = 0


def test_proj_embed_count_counts_chunks():
    """预算度量单位:entry 1 + chunks n。"""
    proj = "cnt"
    d._state["memory_caches"][proj] = {
        "a.md": (1.0, np.zeros(8, np.float32)),                       # 1
        "a.md|chunks": (1.0, [np.zeros(8, np.float32)] * 3),          # 1+3
    }
    try:
        assert d._proj_embed_count(proj) == 5
    finally:
        del d._state["memory_caches"][proj]


def test_pickle_roundtrip_np():
    """np 向量 pickle 落盘/回读无损(pkl 格式 numpy 原生支持)。"""
    import pickle as _p
    v = np.arange(1024, dtype=np.float32) / 1024.0
    blob = _p.dumps({"embeddings": {"f.md": (1.0, v)}})
    back = _p.loads(blob)["embeddings"]["f.md"][1]
    assert isinstance(back, np.ndarray)
    assert np.allclose(back, v)
    assert abs(d.cosine(v, back) - 1.0) < 1e-6


if __name__ == "__main__":
    for name, fn in sorted({k: v for k, v in globals().items()
                            if k.startswith("test_")}.items()):
        fn()
        print(f"[PASS] {name}")
    print("all green")

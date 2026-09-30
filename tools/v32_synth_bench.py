#!/usr/bin/env python3
"""v3.2 合成语料压测 · ROOTCURE_PLAN J1/J2 仿真读数(部署前离线验证纪律)。

仿云端真实规模(9/30 实测:75 项目 / cache 1469MB / ~600 向量每项目):
  75 项目 × 100 md × (1 entry + 5 chunks) = 45000 向量
  pkl 用旧 PyList 格式写入(模拟云端现状)→ 走 v3.2 惰性转换路径载入。

判读:
  J1 驻留内存:np.nbytes vs PyList 实测口径(getsizeof 差分),期望 ≥6x 降幅
  J2 预算制:budget=300000(默认)→ 零逐出;budget 压小 → 有序逐出且保 just_used
"""
from __future__ import annotations

import importlib.util
import pickle
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "cloud_daemon_v32", ROOT / "runtime" / "cloud_daemon_v32_20260930.py")
d = importlib.util.module_from_spec(_spec)
sys.modules["cloud_daemon_v32"] = d
_spec.loader.exec_module(d)

import numpy as np

N_PROJ, N_MD, N_CHUNK = 75, 100, 5
TOTAL_VECS = N_PROJ * N_MD * (1 + N_CHUNK)


def _pylist_vec_bytes() -> int:
    """实测口径:一个 1024-float PyList 的全量内存(指针数组+float 对象)。"""
    import sys as _s
    v = [0.1] * 1024
    return _s.getsizeof(v) + sum(_s.getsizeof(x) for x in v)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="v32_synth_"))
    try:
        # ── 构造:75 项目 × 100 md,cache 预填旧 PyList pkl ──
        rng = np.random.default_rng(7)
        py_kb = _pylist_vec_bytes() / 1024
        print(f"[synth] {N_PROJ} proj × {N_MD} md × (1+{N_CHUNK}) = {TOTAL_VECS} vecs "
              f"· PyList 实测 {py_kb:.1f}KB/vec")
        t0 = time.time()
        for pi in range(N_PROJ):
            proj_dir = tmp / f"proj_{pi:02d}" / "memory"
            proj_dir.mkdir(parents=True)
            cache = {}
            for mi in range(N_MD):
                f = proj_dir / f"m{mi:03d}.md"
                f.write_text(f"---\nname: m{mi}\n---\nsynth body {pi}-{mi}\n" * 3,
                             encoding="utf-8")
                mtime = f.stat().st_mtime
                fp = str(f)
                cache[fp] = (mtime, (rng.standard_normal(1024) * 1e-3).tolist())
                cache[fp + "|chunks"] = (
                    mtime, [(rng.standard_normal(1024) * 1e-3).tolist() for _ in range(N_CHUNK)])
            pkl = tmp / f"pkl_{pi:02d}.pkl"
            pickle.dump({"embeddings": cache}, open(pkl, "wb"))
            # 对齐 daemon 的 pkl 命名规则:把 pkl 放进 daemon CACHE_DIR 需要 sha
            # 仿真直接注入 memory_caches(等价于 v3.1 pkl 回读后的状态,值仍 PyList)
            key = str(proj_dir)
            d._state["memory_caches"][key] = cache
            d._ENTRIES_CACHE[key] = [f"entry-{mi}" for mi in range(N_MD)]
        print(f"[build] {time.time()-t0:.1f}s · PyList 状态注入完成(模拟云端现状)")

        # ── J1 · 惰性转换后驻留内存 ──
        t1 = time.time()
        np_bytes = py_eq = 0
        for key, cache in d._state["memory_caches"].items():
            for k2, (mt, v) in cache.items():
                if isinstance(v, list):
                    vecs = v if k2.endswith("|chunks") else [v]
                    conv = [np.asarray(x, dtype=np.float32) for x in vecs]
                    cache[k2] = (mt, conv[0] if not k2.endswith("|chunks") else conv)
                    np_bytes += sum(x.nbytes for x in conv)
                    py_eq += len(conv)
                else:
                    np_bytes += v.nbytes
                    py_eq += 1
        mb_np = np_bytes / 1024 / 1024
        mb_py = py_eq * py_kb / 1024
        print(f"[J1] 惰性转换 {time.time()-t1:.1f}s · np 驻留 {mb_np:.1f}MB "
              f"vs PyList 等效 {mb_py:.1f}MB · 降幅 {mb_py/mb_np:.1f}x "
              f"({'PASS' if mb_py/mb_np >= 6 and mb_np < 400 else 'CHECK'})")

        # ── J2 · 预算制(默认预算 → 零逐出)──
        d._LRU_STATS["evicted"] = 0
        d._EMBED_BUDGET = 300000
        last_key = key
        d._entries_cache_lru_trim(last_key)
        e0 = d._LRU_STATS["evicted"]
        print(f"[J2] budget=300000(默认)· 总向量 {d._proj_embed_count and ''}"
              f"{sum(d._proj_embed_count(k) for k in d._ENTRIES_CACHE)} "
              f"→ evicted={e0} {'PASS(预算内零逐出)' if e0 == 0 else 'FAIL'}")

        # ── J2' · 压小预算 → 有序逐出 ──
        d._EMBED_BUDGET = 40000
        d._entries_cache_lru_trim(last_key)
        e1 = d._LRU_STATS["evicted"] - e0
        remain = len(d._ENTRIES_CACHE)
        print(f"[J2'] budget=40000 → evicted={e1} · 剩余 {remain} 项目 · "
              f"just_used 保留 {'PASS' if last_key in d._ENTRIES_CACHE else 'FAIL'}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        d._state["memory_caches"].clear()
        d._ENTRIES_CACHE.clear()
        d._LRU_STATS["evicted"] = 0


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""云端 daemon 内存根治 patch(1729 最后通牒·四刀·2026-09-30)。

对 runtime/cloud_daemon_20260930.py(云端 9/22 版原样拷贝)做增量修改,
不整文件替换(云端无 token 鉴权,换本地版会全 401):

  刀1 idle-unload:BGE 空闲 30min 自动卸载(~1.4GB),wrapper 打 last_embed
  刀2 entries+memory_caches LRU:超过 N 项目(默认 8)逐出最旧,治"75 项目全驻"
  刀3 chunk cap env 化:COMPASS_CHUNK_PER_ENTRY_CAP 默认 24(部署配 8)
  刀4 pkl warmup 只载最近 N 项目(按 pkl mtime),治启动峰值
"""
import re, sys

SRC = "runtime/cloud_daemon_20260930.py"
s = open(SRC, encoding="utf-8").read()
orig_len = len(s)

def must(old, new, tag):
    global s
    assert old in s, f"PATCH MISS: {tag}"
    assert s.count(old) == 1, f"PATCH AMBIGUOUS: {tag}"
    s = s.replace(old, new)
    print(f"OK {tag}")

# 刀1a · wrapper 打 last_embed
must(
    """    class _BGEWrapper:
        def encode(self, text, **kwargs):
            return model.encode(text).tolist()
    _state["embedder"] = _BGEWrapper()""",
    """    class _BGEWrapper:
        def encode(self, text, **kwargs):
            _state["last_embed"] = time.time()  # 2026-09-30 idle-unload 时间戳
            return model.encode(text).tolist()
    _state["embedder"] = _BGEWrapper()
    _state["last_embed"] = time.time()""",
    "1a wrapper last_embed")

# 刀1b · idle-unloader 线程(插在 _get_embedder alias 前)
must(
    """def _get_embedder():
    \"\"\"Thin alias for the embedder singleton accessor.""",
    """# v3.1 · 2026-09-30 · 内存根治刀1:空闲自动卸载 BGE+reranker(默认 30min)
_IDLE_UNLOAD_SEC = int(os.environ.get("COMPASS_IDLE_UNLOAD_SEC", "1800"))


def _idle_unloader():
    while True:
        time.sleep(60)
        try:
            if _state.get("embedder") is not None:
                idle = time.time() - _state.get("last_embed", _DAEMON_START_TS)
                if idle > _IDLE_UNLOAD_SEC:
                    _state["embedder"] = None
                    _state.pop("last_embed", None)
                    global _RERANKER_SINGLETON
                    _RERANKER_SINGLETON = None
                    import gc
                    gc.collect()
                    log(f"idle-unload: BGE+reranker freed after {idle:.0f}s idle "
                        f"(saved ~1.4GB; next recall lazy-reloads ~30s)")
        except Exception as e:
            log(f"idle-unload error: {e}")


_idle_thread = threading.Thread(target=_idle_unloader, daemon=True,
                                name="idle-unloader")
_idle_thread.start()


def _get_embedder():
    \"\"\"Thin alias for the embedder singleton accessor.""",
    "1b idle-unloader")

# 刀3 · chunk cap env 化
must(
    "_CHUNK_PER_ENTRY_CAP = 24",
    "_CHUNK_PER_ENTRY_CAP = int(os.environ.get(\"COMPASS_CHUNK_PER_ENTRY_CAP\", \"24\"))",
    "3 chunk cap env")

# 刀2 · entries LRU(插在 get_memory_entries 尾部写入处)
must(
    """    if _INOTIFY_USE:
        with _ENTRIES_CACHE_LOCK:
            _ENTRIES_CACHE[proj_key] = entries""",
    """    if _INOTIFY_USE:
        with _ENTRIES_CACHE_LOCK:
            _ENTRIES_CACHE[proj_key] = entries
            _entries_cache_lru_trim(proj_key)""",
    "2a lru call")
must(
    """def _inotify_maybe_log_stats():""",
    """# v3.1 · 2026-09-30 · 内存根治刀2:entries+memory_caches 按项目 LRU 淘汰。
# 云端 75 项目全量驻留(entries 含 chunk_embs)是"启动即 9GB"的主因之一。
_ENTRIES_CACHE_MAX_PROJ = int(os.environ.get("COMPASS_ENTRIES_CACHE_MAX_PROJ", "8"))
_LRU_STATS = {"evicted": 0}


def _entries_cache_lru_trim(just_used: str) -> None:
    \"\"\"保留最近使用的 N 个项目,逐出最旧(entries + memory_caches 同步)。
    被逐项目下次 recall 重新 warmup(pkl 仍在盘上,只丢内存驻留)。\"\"\"
    while len(_ENTRIES_CACHE) > _ENTRIES_CACHE_MAX_PROJ:
        oldest = next(iter(_ENTRIES_CACHE))
        if oldest == just_used:
            break
        _ENTRIES_CACHE.pop(oldest, None)
        _state["memory_caches"].pop(oldest, None)
        _LRU_STATS["evicted"] += 1
        log(f"entries-cache LRU evict {oldest} "
            f"(total evicted={_LRU_STATS['evicted']})")


def _inotify_maybe_log_stats():""",
    "2b lru func")

# 刀4 · pkl warmup 只载最近 N 项目(按 pkl mtime)
must(
    """    loaded = 0
    skipped = 0
    failed = 0
    for _name, mem_dir in _list_user_project_dirs():""",
    """    loaded = 0
    skipped = 0
    failed = 0
    # v3.1 · 2026-09-30 · 内存根治刀4:warmup 只载最近 N 个项目的 pkl(按 mtime),
    # 治启动峰值(全量 1.5GB pkl 载入即数 GB 驻留)。其余项目首次 recall 时 lazy 载。
    _warm = []
    for _n, _md in _list_user_project_dirs():
        _ph = CACHE_DIR / f"{_hashlib_w.sha256(str(_md).encode()).hexdigest()[:12]}.pkl"
        if _ph.exists():
            try:
                _warm.append((_ph.stat().st_mtime, _md))
            except OSError:
                continue
    _warm.sort(reverse=True)
    for _name, mem_dir in (_md for _, _md in _warm[:_ENTRIES_CACHE_MAX_PROJ]):""",
    "4 warmup topN")

open(SRC, "w", encoding="utf-8", newline=chr(10)).write(s)
print(f"written {orig_len} -> {len(s)} bytes")
compile(s, SRC, "exec")
print("compile OK")

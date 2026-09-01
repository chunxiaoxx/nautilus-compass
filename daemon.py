#!/usr/bin/env python3
"""V5 Memory Plugin · BGE Daemon · keep model loaded · TCP IPC.

启动: bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
停止: 杀 PID (写在 .cache/daemon.pid)

Protocol (JSON over TCP localhost:9876):
  request:  {"action":"recall|drift|both", "query":"...", "project":"<encoded_cwd>", "top_k":5}
  response: {"ok":true, "recall":[{score,path,age,desc}...], "drift":{score,alignment,deviation,top_neg}}

设计:
  · Lazy load: 第一次 recall 时 load BGE (~30s) · 之后 keep
  · Memory cache: pickled by mtime · file 变只重 embed 该 file
  · Anchors cache: similarly
  · 多客户端并发 OK · single threaded GIL 但 BGE encode 快 (~50ms/句)
"""
import hashlib
import json
import os

# v2.0.2 · P6 · BLAS internal thread limit · CRITICAL: must set BEFORE importing
# any numpy/torch/sentence-transformers downstream. Each BGE encode call would
# otherwise spawn 4-8 BLAS/OMP threads internally. With ThreadPoolExecutor(8)
# worker threads concurrently encoding, 8×4=32 internal threads thrash on a
# 4-core CPU. 2026-05-22 observed: 206% CPU sustained · 24 CLOSE_WAIT after
# 19min · ingest timeout under V5/V7/Kairos concurrent load. Limiting BLAS
# to 1 thread per encode (8 workers × 1 internal = 8 threads on 4 cores · OK).
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import pickle
import socket
import sys
import threading
import time
from collections import deque as _deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# v3.0.2 · Stage1a /status endpoint (ported from cloud /opt fork 2026-08-25 to
# end the repo-vs-/opt daemon divergence; psutil optional so local Windows
# runs without it still work).
try:
    import psutil  # noqa: F401 · /status process metrics
except ImportError:
    psutil = None

# P6 (companion) · torch single-thread per encode · applied after import
try:
    import torch as _torch_for_threadcap
    _torch_for_threadcap.set_num_threads(1)
    _torch_for_threadcap.set_num_interop_threads(1)
except Exception:
    pass

# v2.0.0 · P4 fix · bounded handler pool prevents unbounded thread spawn
# under V5/V7 retry storms (root cause of 288-thread leak observed
# 2026-05-22). 8 workers matches the 4-core CPU's effective concurrency
# for BGE-m3 inference; further requests queue at the OS socket backlog.
DAEMON_MAX_HANDLER_THREADS = int(os.environ.get("COMPASS_DAEMON_POOL", "8"))
_HANDLER_POOL = ThreadPoolExecutor(
    max_workers=DAEMON_MAX_HANDLER_THREADS,
    thread_name_prefix="bge-handler",
)

# v2.0.7 · P7 · in-flight conn guard · caps queued+running at pool×4 = 32
# When V5/V7 retry-storms, ThreadPoolExecutor.submit() silently queues
# unbounded → conns wait → V5 timeouts → half-closes → daemon-side fd
# stuck in CLOSE-WAIT until handler eventually drains. Observed 2026-05-23:
# 2191 CLOSE-WAIT after 12h with P5+P6 alone. BoundedSemaphore reject-fast
# pattern keeps inflight under control + lets accept loop free fd promptly.
DAEMON_INFLIGHT_LIMIT = DAEMON_MAX_HANDLER_THREADS * 4
_INFLIGHT_SEM = threading.BoundedSemaphore(DAEMON_INFLIGHT_LIMIT)


# v2.0.7 · P9 · server-side recall result cache · 真 reduce CPU
# 2026-05-24 P8 (BatchCoordinator) failed because P6 OMP_NUM_THREADS=1
# makes batch encode have no parallelism benefit. Real CPU root cause:
# every recall query does BGE encode (50-100ms CPU bound) regardless of
# whether query was seen before. Cache final recall result keyed by
# (action, query, project, top_k, scope) · hits skip both encode + scoring.
# Expected: 60-80% cache hit rate (V5/V7/Kairos repeat same anchors) ·
# CPU drops proportionally.
import hashlib as _hashlib_p9
from collections import OrderedDict as _OrderedDict_p9
RECALL_CACHE_MAX = int(os.environ.get("COMPASS_RECALL_CACHE_MAX", "10000"))
RECALL_CACHE_TTL = int(os.environ.get("COMPASS_RECALL_CACHE_TTL", "3600"))
_RECALL_CACHE = _OrderedDict_p9()   # key → (timestamp, result)
_RECALL_CACHE_LOCK = threading.Lock()
_RECALL_CACHE_STATS = {"hit": 0, "miss": 0, "expire": 0, "evict": 0}
_RECALL_CACHE_LAST_LOG = 0.0  # P9-instr: throttled stats log timestamp
_RECALL_CACHE_LOG_INTERVAL = 60.0

# v2.1.0 · Phase 2 · BM25 + vec RRF fusion · opt-in via env
_BM25_RRF_USE = os.environ.get("COMPASS_USE_BM25_RRF", "0") == "1"
_BM25_RRF_K = int(os.environ.get("COMPASS_BM25_RRF_K", "60"))
_BM25_RRF_TOP_K = int(os.environ.get("COMPASS_BM25_RRF_TOP_K", "30"))

# v2.3.0 · production cross-encoder reranker · opt-in via COMPASS_PROD_RERANK=1
# benchmark: bge-m3 + bge-reranker-v2-m3 → P@5 0.86→0.92, MRR 0.685→0.855
# (RESULTS.md:54-56). Local cross-encoder (non-LLM) → does NOT break the
# black-box hot-path constraint. Default OFF: behavior unchanged until enabled.
_PROD_RERANK_USE = os.environ.get("COMPASS_PROD_RERANK", "0") == "1"
_RERANKER_MODEL = os.environ.get(
    "ZMM_RERANKER_MODEL",
    # local ModelScope path preferred · else HF repo id (mirrors EMBEDDER_MODEL).
    # 2026-06-07: without the HF fallback, HF-cache-only hosts (e.g. fresh GPU
    # server) hit "reranker failed · Path .../modelscope/... not found" and
    # silently fell back to dense order. The exists()-guard fixes that.
    str(Path.home() / ".cache/modelscope/hub/models/BAAI/bge-reranker-v2-m3")
    if (Path.home() / ".cache/modelscope/hub/models/BAAI/bge-reranker-v2-m3").exists()
    else "BAAI/bge-reranker-v2-m3",
)
# how many top candidates to feed the cross-encoder before truncating to top_k.
# benchmark used full haystack (50); production keeps it bounded for latency.
_RERANK_CANDIDATES = int(os.environ.get("COMPASS_RERANK_CANDIDATES", "30"))
_RERANKER_SINGLETON = None  # lazy in-process singleton (loaded on first use)
_RERANKER_LOCK = threading.Lock()

# v2.3.0 · production lifecycle forget-filter · opt-in via COMPASS_PROD_LIFECYCLE=1
# Activates the dormant LLM-WIKI2 Ebbinghaus forgetting (README:104) in recall:
# drops entries whose forget_at has passed. Pure schema arithmetic (no LLM).
# Default OFF: no memory is ever hidden until explicitly enabled.
_PROD_LIFECYCLE_USE = os.environ.get("COMPASS_PROD_LIFECYCLE", "1") == "1"  # v3.0.5 default ON(池瘦身):只影响带 forget_at 的条目,无该字段 fail-safe 保留

# Phase 1 Task 4 · production tier-aware re-rank · opt-in via COMPASS_PROD_TIER_WEIGHT=1
# Among near-equal cosine hits, prefers the more-consolidated (higher-tier)
# capsule via a tiny additive bonus (recall.apply_tier_weight · ranking-only).
# Skipped when cross-encoder rerank is active (rerank order must win · the dense
# scores are non-monotonic there, so a score-sort would corrupt rerank order).
# Default OFF: daemon ranking is byte-identical until explicitly enabled.
_PROD_TIER_WEIGHT_USE = os.environ.get("COMPASS_PROD_TIER_WEIGHT", "0") == "1"

# v2.3.0 · opt-in gemini query rewrite before recall · COMPASS_PROD_QUERY_REWRITE=1
# (also needs COMPASS_USE_GEMINI_FLASH). LLM contact isolated in query_rewrite.py;
# any failure falls back to the original query. Default OFF: daemon recall is
# byte-identical, zero LLM (black-box hot path preserved).
_PROD_QUERY_REWRITE_USE = os.environ.get("COMPASS_PROD_QUERY_REWRITE", "0") == "1"


def _tokenize_for_bm25(text: str) -> list:
    """v2.1.0 · Whitespace + lowercase + CJK char tokenizer for BM25."""
    if not text:
        return []
    tokens = text.lower().split()
    cjk_chars = [c for c in text if "一" <= c <= "鿿"]
    return tokens + cjk_chars


# v3.2 · utterance-routing production port (COMPASS_CHUNK_RECALL=1, default off).
# LongMemEval-S head-to-head finding: the answer to detail queries usually
# lives in ONE turn/paragraph; whole-entry embedding dilutes it. Chunk-level
# retrieval lifted ssu 0.20→1.00 (M) / ssu P@1 +41pt (S) vs session-level.
# Production port: per-entry paragraph-window chunks, chunk-best score fused
# with the entry-level dense rank via RRF — classifier-free, safe for all
# query shapes (eval showed no harm on aggregate-type queries).
_CHUNK_RECALL_USE = os.environ.get("COMPASS_CHUNK_RECALL", "0") == "1"
_CHUNK_MAX_CHARS = int(os.environ.get("COMPASS_CHUNK_MAX_CHARS", "500"))
_CHUNK_PER_ENTRY_CAP = 24


def _entry_chunks(body: str, max_chars=_CHUNK_MAX_CHARS) -> list:
    """Sliding window of paragraph pairs (para i + i+1), truncated to
    max_chars — mirrors the eval-side user-turn window=2 that lifted ssu
    0.20→1.00. Greedy packing was tried and rejected: it merges unrelated
    paragraphs and re-dilutes the very signal chunking recovers."""
    if not body:
        return []
    paras = [p.strip() for p in body.split("\n\n") if p.strip()]
    out = []
    for i in range(len(paras)):
        chunk = paras[i]
        if i + 1 < len(paras) and len(chunk) + len(paras[i + 1]) + 1 <= max_chars:
            chunk = chunk + "\n" + paras[i + 1]
        elif i + 1 < len(paras):
            chunk = (chunk + "\n" + paras[i + 1])[:max_chars]
        out.append(chunk[:max_chars])
    return out[:_CHUNK_PER_ENTRY_CAP]


def _build_bm25_retriever(entries):
    """v2.1.0 · BM25 keyword retriever · feeds rrf_fusion as 2nd stream."""
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        return None
    if not entries:
        return None
    corpus = [_tokenize_for_bm25(e.get("embed_text", "")) for e in entries]
    if not any(corpus):
        return None
    return BM25Okapi(corpus)


def _bm25_score_to_ranked(bm25, entries, query, top_k=30):
    """v2.1.0 · BM25 query → ranked list compatible with rrf_fusion."""
    if bm25 is None or not entries:
        return []
    tokens = _tokenize_for_bm25(query)
    if not tokens:
        return []
    scores = bm25.get_scores(tokens)
    paired = sorted(zip(scores, entries), key=lambda x: x[0], reverse=True)
    return [(float(score), entry) for score, entry in paired[:top_k] if score > 0]


def _rrf_fusion(ranked_lists, k=60, top_k=10):
    """v2.1.0 · Reciprocal Rank Fusion · combine vec + BM25 rank lists.
    Each list = [(score, entry), ...] · output = [(fused_score, entry), ...] top_k."""
    fused_scores = {}
    entry_by_path = {}
    for ranked in ranked_lists:
        if not ranked:
            continue
        for rank, (score, entry) in enumerate(ranked):
            path = entry.get("path")
            if not path:
                continue
            entry_by_path[path] = entry
            fused_scores[path] = fused_scores.get(path, 0.0) + 1.0 / (k + rank + 1)
    sorted_paths = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    return [(score, entry_by_path[path]) for path, score in sorted_paths[:top_k]]


def _get_reranker():
    """v2.3.0 · lazy in-process singleton CrossEncoder (bge-reranker-v2-m3).

    Loaded only on first reranked recall (when COMPASS_PROD_RERANK=1). ~2GB
    model + tens-of-seconds load → pay only when the flag is on. Thread-safe
    double-checked init. Raises if load fails (caller falls back to dense)."""
    global _RERANKER_SINGLETON
    if _RERANKER_SINGLETON is not None:
        return _RERANKER_SINGLETON
    with _RERANKER_LOCK:
        if _RERANKER_SINGLETON is not None:
            return _RERANKER_SINGLETON
        from sentence_transformers import CrossEncoder  # lazy import
        try:
            import torch
            device = os.environ.get(
                "ZMM_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
        except Exception:
            device = os.environ.get("ZMM_DEVICE", "cpu")
        t0 = time.time()
        _RERANKER_SINGLETON = CrossEncoder(_RERANKER_MODEL, device=device)
        log(f"reranker loaded · {_RERANKER_MODEL} on {device} · {time.time()-t0:.1f}s")
        return _RERANKER_SINGLETON


def _rerank_top(query, top, top_k):
    """v2.3.0 · production reranker hook · reorder `top` by cross-encoder.

    `top` = [(dense_score, entry), ...] already in dense/fused order.
    · flag off → return top[:top_k] unchanged (default behavior preserved).
    · flag on  → cross-encoder rerank up to _RERANK_CANDIDATES then take top_k.
    Any model-load / predict failure is swallowed → fall back to dense order
    (recall must never crash on a reranker fault). Original dense_score kept in
    the returned tuples (downstream surfaces the dense score, not rerank score).
    """
    if not _PROD_RERANK_USE or not top:
        return top[:top_k]
    candidates = top[:_RERANK_CANDIDATES]
    try:
        reranker = _get_reranker()
        pairs = [(query, (e.get("embed_text") or e.get("description") or ""))
                 for _s, e in candidates]
        scores = reranker.predict(pairs)
        reordered = sorted(zip(candidates, scores), key=lambda x: -float(x[1]))
        # 2026-06-20 · rerank burst 后释放 reserved 缓存 → 降 nvidia-smi 稳态占用,
        # 让共置的 gate B GPU eval 不被间歇 OOM(soul 报的根因)。可 env 关。
        if os.environ.get("COMPASS_EMPTY_CACHE", "1") == "1":
            try:
                import torch
                torch.cuda.empty_cache()
            except Exception:
                pass
        return [item for item, _rscore in reordered][:top_k]
    except Exception as e:
        log(f"reranker failed · fallback to dense order: {e}")
        return top[:top_k]


def _apply_lifecycle_filter(entries):
    """v2.3.0 · production lifecycle forget-filter (opt-in COMPASS_PROD_LIFECYCLE).

    Drops entries whose forget_at has passed (LLM-WIKI2 Ebbinghaus Rule C),
    reusing recall.promote_lifecycle_tier()'s archived flag. Pure arithmetic, no
    LLM. Flag off → passthrough. A malformed / unparseable forget_at is never
    treated as forgotten (fail-safe: a memory is only hidden when the daemon is
    certain its forget time has passed)."""
    if not _PROD_LIFECYCLE_USE:
        return entries
    try:
        from recall import promote_lifecycle_tier
    except Exception as e:
        log(f"lifecycle filter import failed · passthrough: {e}")
        return entries
    kept = []
    for e in entries:
        try:
            if promote_lifecycle_tier(e).get("archived"):
                continue
        except Exception:
            pass  # fail-safe: keep on any error
        kept.append(e)
    return kept


def _apply_tier_weight_prod(top, top_k):
    """Phase 1 Task 4 · production tier-aware re-rank (opt-in COMPASS_PROD_TIER_WEIGHT).

    Reuses recall.apply_tier_weight (small additive tier bonus · ranking-only ·
    output scores unchanged). Skipped when:
      · flag off (default) → passthrough top[:top_k]
      · cross-encoder rerank active → rerank order must win (its tuples keep the
        non-monotonic dense score, so a score-sort here would corrupt that order)
    Any failure → fall back to the incoming order (recall must never crash)."""
    if not _PROD_TIER_WEIGHT_USE or _PROD_RERANK_USE or not top:
        return top[:top_k]
    try:
        from recall import apply_tier_weight
        return apply_tier_weight(top)[:top_k]
    except Exception as e:
        log(f"tier weight failed · passthrough: {e}")
        return top[:top_k]

# v2.0.9 · inotify-based cache invalidation · Layer 2 cure for 23k-file dir scan
_INOTIFY_USE = os.environ.get("COMPASS_USE_INOTIFY", "1") == "1"
if not _INOTIFY_USE:
    # 2026-08-28(workbuddy 反馈 P1·2.2): 关闭 inotify = 新写入不被 recall 索引,
    # 曾完全静默。启动时大声说一遍。
    print("⚠️ COMPASS_USE_INOTIFY=0 · new-file discovery DISABLED — fresh writes "
          "won't appear in recall until a manual rescan", file=sys.stderr)
_ENTRIES_CACHE = {}  # proj_key -> list of entries (with embeddings) · last scan
_ENTRIES_CACHE_LOCK = threading.Lock()
_DIR_DIRTY = set()   # proj_keys flagged for re-scan by inotify watcher
_DIR_DIRTY_LOCK = threading.Lock()
_INOTIFY_STATS = {"events": 0, "rescans_avoided": 0, "rescans_done": 0, "watch_count": 0, "errors": 0}
_INOTIFY_LAST_LOG = 0.0

# ── Stage1a /status state (ported from cloud /opt fork · 2026-08-25) ──
_DAEMON_START_TS = 0.0
_RECALL_TS_BUFFER = _deque(maxlen=10000)   # (ts, latency_ms)
_OVERLOAD_TS_BUFFER = _deque(maxlen=1000)


def _sliding_5min_stats():
    now = time.time()
    cutoff = now - 300
    recent = [(t, lat) for t, lat in _RECALL_TS_BUFFER if t >= cutoff]
    overload = sum(1 for t in _OVERLOAD_TS_BUFFER if t >= cutoff)
    count = len(recent)
    if count > 0:
        latencies = sorted(lat for _, lat in recent)
        p95 = latencies[min(int(count * 0.95), count - 1)]
        avg = round(sum(latencies) / count, 2)
    else:
        p95 = 0
        avg = 0
    return {"count_5min": count, "p95_ms": p95, "avg_ms": avg, "overload_5min": overload}


def _compute_memory_stats():
    try:
        pkls = list(CACHE_DIR.glob("*.pkl"))
        return {"pkl_count": len(pkls),
                "pkl_total_mb": sum(p.stat().st_size for p in pkls) // (1024 * 1024)}
    except Exception:
        return {"pkl_count": 0, "pkl_total_mb": 0}


def _status_payload() -> dict:
    from datetime import datetime, timezone
    try:
        proc = psutil.Process()
        cpu_pct = proc.cpu_percent(interval=0.1)
        rss_mb = proc.memory_info().rss // (1024 * 1024)
    except Exception:
        cpu_pct, rss_mb = 0.0, 0
    try:
        load_avg = list(os.getloadavg())
    except Exception:
        load_avg = [0.0, 0.0, 0.0]
    return {
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "uptime_s": int(time.time() - _DAEMON_START_TS) if _DAEMON_START_TS else 0,
        "pid": os.getpid(),
        "cpu_pct": cpu_pct,
        "rss_mb": rss_mb,
        "load_avg": load_avg,
        "recall": {"p9_cache": dict(_RECALL_CACHE_STATS), "sliding_5min": _sliding_5min_stats(),
                   "inotify": {"watches": _INOTIFY_STATS["watch_count"],
                               "events": _INOTIFY_STATS["events"],
                               "avoid_rate": round(
                                   (_INOTIFY_STATS["rescans_avoided"] /
                                    max(_INOTIFY_STATS["rescans_avoided"] + _INOTIFY_STATS["rescans_done"], 1)) * 100, 1)}},
        "memory": _compute_memory_stats(),
    }


def _p9_cache_key(action, query, project, top_k, scope, agent_type=""):
    blob = f"{action}|{scope}|{project}|{top_k}|{agent_type}|{query}"
    return _hashlib_p9.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _p9_cache_get(key):
    with _RECALL_CACHE_LOCK:
        entry = _RECALL_CACHE.get(key)
        if entry is None:
            _RECALL_CACHE_STATS["miss"] += 1
            _result = None
        else:
            ts, result = entry
            if time.time() - ts > RECALL_CACHE_TTL:
                del _RECALL_CACHE[key]
                _RECALL_CACHE_STATS["expire"] += 1
                _RECALL_CACHE_STATS["miss"] += 1
                _result = None
            else:
                _RECALL_CACHE.move_to_end(key)
                _RECALL_CACHE_STATS["hit"] += 1
                _result = result
    _p9_maybe_log_stats()
    return _result


def _p9_cache_put(key, result):
    with _RECALL_CACHE_LOCK:
        if len(_RECALL_CACHE) >= RECALL_CACHE_MAX:
            _RECALL_CACHE.popitem(last=False)
            _RECALL_CACHE_STATS["evict"] += 1
        _RECALL_CACHE[key] = (time.time(), result)


def _p9_maybe_log_stats():
    # P9-instr: throttled — call from get path on every request
    global _RECALL_CACHE_LAST_LOG
    now = time.time()
    if now - _RECALL_CACHE_LAST_LOG < _RECALL_CACHE_LOG_INTERVAL:
        return
    _RECALL_CACHE_LAST_LOG = now
    s = _RECALL_CACHE_STATS
    total = s['hit'] + s['miss']
    if total == 0:
        return
    hit_rate = s['hit'] / total * 100
    log(f"P9 cache · {total} ops · hit_rate={hit_rate:.1f}% · size={len(_RECALL_CACHE)} · hits={s['hit']} misses={s['miss']} expires={s['expire']} evicts={s['evict']}")

try:
    sys.stdout.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
    sys.stderr.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
except Exception:
    pass

HOST = "127.0.0.1"
PORT = 9876
_PLUGIN_USER = Path.home() / ".claude" / "plugins" / "nautilus-compass"
# CI / pip-install fallback · use the script's own dir when user-level
# plugin path doesn't exist (eg. installed via pip · or fresh git clone)
PLUGIN_DIR = _PLUGIN_USER if _PLUGIN_USER.exists() else Path(__file__).resolve().parent
CACHE_DIR = PLUGIN_DIR / ".cache"
ANCHORS_PATH = PLUGIN_DIR / "anchors.json"
PID_FILE = CACHE_DIR / "daemon.pid"
LOG_FILE = CACHE_DIR / "daemon.log"
EMBEDDER_MODEL = os.environ.get(
    "ZMM_EMBEDDER_MODEL",
    # 默认 bge-m3 (1024 d · 100+ 语) · 本地路径优先 · 没 ModelScope 则 HF repo id
    # 实测 (2026-04-29 LongMemEval-S subset 4): MRR 0.760 · Drift AUC 0.923
    str(Path.home() / ".cache/modelscope/hub/models/BAAI/bge-m3")
    if (Path.home() / ".cache/modelscope/hub/models/BAAI/bge-m3").exists()
    else "BAAI/bge-m3",
)
# 选型对比 (2026-04-29 LongMemEval-S subset 4):
#   bge-m3 (默认)     (1024 d · 2.27GB · 100+ 语):  MRR 0.760 · AUC 0.923 ✅ · ⚠️ Win 本地慢/OOM 风险 → WSL2
#   intfloat/multilingual-e5-small (384 d · 471MB):  MRR 0.762 · AUC 0.850 · 需 query:/passage: prefix
#   bge-small-zh-v1.5 (512 d · 92MB · 中文 only):  MRR 0.414 (英文崩) · AUC 0.793 · 中文场景仍可用
# 切换需 rm -f .cache/anchors.pkl + .cache/*.pkl (dim 不匹配)
# 切小模型: ZMM_EMBEDDER_MODEL=intfloat/multilingual-e5-small
# 切中文: ZMM_EMBEDDER_MODEL=BAAI/bge-small-zh-v1.5
EMBED_MAX_CHARS = 1500
TOP_K = 5
# 校准值 = 2026-04-29 跑 tests/eval_calibrate.py 实测 (bge-m3 + 28 项目 memory)
# 历史 (bge-small-zh-v1.5): 0.565 / -0.04 / 0.606
# 注: COSINE_MIN 是 query↔memory 阈值 · 比 memory↔memory p25 (0.484) 系统性低 · 用 0.35
COSINE_MIN = float(os.environ.get("ZMM_COSINE_MIN", "0.35"))
DRIFT_ALERT_THRESHOLD = float(os.environ.get("ZMM_DRIFT_THRESHOLD", "-0.032"))  # m3+hard 后 best Youden J
NEG_ANCHOR_HIT_THRESHOLD = float(os.environ.get("ZMM_NEG_HIT_THRESHOLD", "0.538"))

# ─── v2 shadow drift detector (2026-05-27 · study-validated · SHADOW ONLY · 不 enforce · R1 护栏不变) ───
# 研究 compass-value-study 证:生产 should_alert(neg_cos≥0.538 OR)在工具调用流 29% alert / ~10% precision
# (90% 误报)。v2 = rule_alert(危险命令正则) OR drift_score < V2_THRESH · 全量 alert ~0.4% · 仅记 log 供比对,
# 不改实际 should_alert(R1-R5 护栏不变)。清理在途重构后可据真实流量比对决定是否 enforce。
ZMM_DRIFT_V2_THRESH = float(os.environ.get("ZMM_DRIFT_V2_THRESH", "-0.07"))
import re as _re_v2
_V2_RULES = [
    _re_v2.compile(r"\brm\s+-[a-z]*r[a-z]*\b"),                                   # 0 rm -r* 递归删除
    _re_v2.compile(r"git\s+push\b.*(--force\b|\s-f\b)"),                          # 1 force push
    _re_v2.compile(r"git\s+reset\s+--hard"),                                      # 2
    _re_v2.compile(r"git\s+clean\s+-[a-z]*[fdx]"),                                # 3
    _re_v2.compile(r"taskkill\b.*/IM\b", _re_v2.I),                               # 4 无差别杀
    _re_v2.compile(r"\b(killall|pkill)\b"),                                       # 5
    _re_v2.compile(r"\b(DROP\s+(DATABASE|TABLE)|TRUNCATE\s+TABLE?)\b", _re_v2.I), # 6
    _re_v2.compile(r"DELETE\s+FROM\b(?!.*\bWHERE\b)", _re_v2.I | _re_v2.S),       # 7 DELETE 无 WHERE
    _re_v2.compile(r"chmod\s+(-R\s+)?777\b"),                                     # 8
    _re_v2.compile(r"\bsk-[A-Za-z0-9]{16,}"),                                     # 9 硬编码 key
    _re_v2.compile(r"(api[_-]?key|password|secret|token)\s*[=:]\s*[\"'][^\"'\s]{12,}[\"']", _re_v2.I),  # 10
    # 2026-08-28(workbuddy 实测反馈): 纯中文意图不触发 rule_hit。保守补高频两条,
    # 模糊语义(如"删除一些文件")故意不加——误报会滥用 R1 drift 自停。
    _re_v2.compile(r"删库|清空(全部|整个|生产)?(数据库|数据表)"),                   # 11 中文删库
    _re_v2.compile(r"(强制|强行|强)推(送|上去)"),                                   # 12 中文强推
]
_V2_SAFE_RM = _re_v2.compile(
    r"(node_modules|/dist\b|\bdist\b|/build\b|\.cache|__pycache__|\.tmp\b|/tmp/|\.swc\b|\.tgz|\.tar|"
    r"\.zip|\.log\b|\.lock\b|package-lock|\.npmrc|hf_stage|\.next\b|\.turbo|coverage|\.pytest_cache|\.mypy_cache)",
    _re_v2.I)
_V2_SAFE_KILL = _re_v2.compile(r"(killall|pkill)\b[^\n;|&]*?-f\s+\S*(/|\.py|\.js|\.sh|\.cjs)\S*", _re_v2.I)
_V2_META = _re_v2.compile(r"^(Edit|Write|Read|MultiEdit):.*(rule_drift|dangerous-commands|_V2_RULES|_RULES)", _re_v2.I)


def _shadow_rule_alert(query: str) -> bool:
    """SHADOW · rule-based 危险动作检测(faithful to compass-value-study/lib/rule_drift.py)。"""
    q = query or ""
    if _V2_META.search(q):
        return False
    for i, rx in enumerate(_V2_RULES):
        if rx.search(q):
            if i == 0 and _V2_SAFE_RM.search(q):    # rm -r* 删构建/临时 · 低危
                continue
            if i == 5 and _V2_SAFE_KILL.search(q):  # pkill -f 具体脚本 · 非无差别
                continue
            return True
    return False


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    line = f"[{time.strftime('%H:%M:%S')}] {msg}\n"
    try:
        # v3.0.9 · size-rotate · daemon.log append-only 曾无上限(12.6MB+)
        try:
            if LOG_FILE.exists() and LOG_FILE.stat().st_size > 20 * 1024 * 1024:
                LOG_FILE.replace(LOG_FILE.with_suffix(LOG_FILE.suffix + ".1"))
        except Exception:
            pass
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    print(line.rstrip(), file=sys.stderr)


# ── Singleton state ─────────────────────────────
_state = {
    "embedder": None,
    "anchor_cache": None,
    # v0.7.2 · multi-profile cache · keyed by abs anchors path
    # {path_str: {mtime, pos_anchors, pos_embs, pos_weights, neg_anchors, neg_embs, neg_weights, n_pos, n_neg, raw}}
    "anchor_caches": {},
    "memory_caches": {},   # {project_dir: {file_path: (mtime, embedding)}}
    "lock": threading.Lock(),
}


class _APIEmbedder:
    """API-based embedder (Gemini / OpenAI compatible) · 250ms vs 30s BGE.

    借鉴禅心 4-27 project_intl_memory_actual_state.md · gemini-embedding 250ms 实测.
    """

    def __init__(self, api_key: str, model: str = "gemini-embedding-001"):
        self.api_key = api_key
        self.model = model
        # Gemini API endpoint
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"

    def encode(self, text: str, **kwargs):
        import urllib.request
        payload = {
            "model": f"models/{self.model}",
            "content": {"parts": [{"text": text[:2000]}]},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.url, data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["embedding"]["values"]


def get_embedder():
    if _state["embedder"] is not None:
        return _state["embedder"]
    # 2026-04-28 · 用户强制不用 gemini · 永远只 BGE local (隐私 + 不依赖外部 API)
    # 旧: 优先 Gemini API (250ms) · 没 key 才 BGE
    # 新: 永远 BGE · 不读 GEMINI_API_KEY · 完全本地
    log("loading BGE model · ~30s · 强制本地 · 不用 gemini ...")
    t0 = time.time()
    from sentence_transformers import SentenceTransformer
    # v0.7.2 · cuda autodetect · ZMM_DEVICE env override
    try:
        import torch
        device = os.environ.get("ZMM_DEVICE",
                                "cuda" if torch.cuda.is_available() else "cpu")
    except Exception:
        device = "cpu"
    log(f"BGE device: {device}")
    model = SentenceTransformer(EMBEDDER_MODEL, device=device)
    # 2026-06-20 · GPU 显存瘦身:bge-m3 默认 max_seq_len=8192,memory 条目短,
    # 8192 的激活 buffer 是 T4 上 ~13GB 占用的大头(权重才 2.3GB)。封到 512
    # 砍激活 buffer(可 env 覆盖)。释放显存给共置的 gate B eval(soul 收敛路径)。
    try:
        _max_seq = int(os.environ.get("COMPASS_BGE_MAX_SEQ", "512"))
        model.max_seq_length = _max_seq
        log(f"BGE max_seq_length capped → {_max_seq} (GPU 瘦身)")
    except Exception as _e:
        log(f"BGE max_seq cap skipped: {_e}")
    # 包一个 wrapper · encode 返 list 兼容 _APIEmbedder
    class _BGEWrapper:
        def encode(self, text, **kwargs):
            return model.encode(text).tolist()
    _state["embedder"] = _BGEWrapper()
    log(f"BGE loaded · {time.time()-t0:.1f}s")
    return _state["embedder"]


def _get_embedder():
    """Thin alias for the embedder singleton accessor.

    Exists so the score path (and tests) have a single, monkeypatch-able seam
    that returns the loaded embedder without binding to get_embedder's name.
    """
    return get_embedder()


def cosine(a, b):
    import math
    if not a or not b: return 0.0
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na>0 and nb>0 else 0.0


def _handle_score(req: dict) -> dict:
    """score action · cosine(query, candidate) for each candidate (bge-m3).

    request:  {"action":"score","query":"<str>","candidates":["<text>", ...]}
    response: {"ok":true,"scores":[<float cosine>, ...]}  # order aligns candidates
              {"ok":false,"error":"..."}                   # empty / embedder fault

    Serves the serving-side semantic recall: rank a caller-supplied candidate
    set against a query using the already-loaded embedder (no haystack scan).
    """
    candidates = req.get("candidates") or []
    if not candidates:
        return {"ok": False, "error": "no candidates"}
    query = req.get("query") or ""
    try:
        embedder = _get_embedder()
        q_vec = embedder.encode(query)
        if hasattr(q_vec, "tolist"):
            q_vec = q_vec.tolist()
        scores = []
        for c in candidates:
            c_vec = embedder.encode(c)
            if hasattr(c_vec, "tolist"):
                c_vec = c_vec.tolist()
            scores.append(cosine(q_vec, c_vec))
        return {"ok": True, "scores": scores}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def parse_memory_file(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    fm = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 4)
        if end > 0:
            for line in text[4:end].split("\n"):
                if ":" in line:
                    k, _, v = line.partition(":")
                    fm[k.strip()] = v.strip()
            body = text[end+4:].strip()
    age_s = time.time() - path.stat().st_mtime
    if age_s < 86400: age_str = f"{age_s/3600:.1f}h"
    elif age_s < 30*86400: age_str = f"{int(age_s/86400)}d"
    else: age_str = f"{int(age_s/86400/30)}mo"
    return {
        "path": path.name, "fullpath": str(path),
        "name": fm.get("name", path.stem),
        "description": fm.get("description","")[:120],
        # v2.3.1 · recall 直交付正文摘录(此前只回 path+常空的 description,消费方须二跳读文件)
        "body": body[:500],
        "type": fm.get("type","?"),
        "age_seconds": age_s, "age_str": age_str,
        "embed_text": (fm.get("description","") + "\n" + body)[:EMBED_MAX_CHARS],
        "mtime": path.stat().st_mtime,
        # v2.3.0 · lifecycle · surface forget_at for production forget-filter
        "forget_at": fm.get("forget_at", ""),
    }


# v3.0.1 · atomic pkl writes + periodic flush · 2026-08-24 cloud incident:
# corrupt half-written 74MB pkl ("Ran out of input" on every warmup) → full
# project re-embed on each restart → slow recall → caller retry storm → 32
# in-flight cap = overloaded livelock. Non-atomic writes could truncate the
# file at any kill; embed progress mid-scan was never persisted at all.
_PKL_FLUSH_EVERY = int(os.environ.get("COMPASS_PKL_FLUSH_EVERY", "50"))

# v3.0.3 · per-project embed/flush lock · 2026-08-25 cloud incident: concurrent
# get_memory_entries calls raced (setdefault → two divergent cache dicts; the
# later flush overwrote the richer pkl with a sparse one → entries lost →
# perpetual re-embed at 347% CPU; plus same-tmp collisions between periodic
# flushes → os.replace ENOENT ×33). Serializing per project fixes both; projects
# still parallelize against each other.
_MEM_LOCKS = {}
_MEM_LOCKS_GUARD = threading.Lock()


def _mem_lock(proj_key: str) -> threading.Lock:
    with _MEM_LOCKS_GUARD:
        lk = _MEM_LOCKS.get(proj_key)
        if lk is None:
            lk = _MEM_LOCKS[proj_key] = threading.Lock()
        return lk


def _pkl_write_atomic(path, obj) -> None:
    """v3.0.1 · write pkl via tmp + os.replace so a kill never leaves a
    truncated (permanently corrupt) cache file behind."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    with open(tmp, "wb") as f:
        pickle.dump(obj, f)
    os.replace(tmp, path)


def _flush_memory_pkl(proj_key: str, cache: dict) -> None:
    """v3.0.1 · persist one project's embedding cache (atomic).
    v3.0.9 · fail 重试一次(历史 34 条 flush fail 全有消化价值)。"""
    import hashlib
    proj_hash = hashlib.sha256(proj_key.encode()).hexdigest()[:12]
    for _attempt in (1, 2):
        try:
            _pkl_write_atomic(CACHE_DIR / f"{proj_hash}.pkl", {"embeddings": cache})
            return
        except Exception as _e:
            if _attempt == 2:
                log(f"pkl flush fail {proj_hash}: {_e}")
            else:
                time.sleep(0.2)


def get_memory_entries(mem_dir: Path):
    proj_key = str(mem_dir)
    # v2.0.9 · inotify fast path · skip O(N) glob+stat+parse if dir not dirty
    if _INOTIFY_USE:
        with _DIR_DIRTY_LOCK:
            is_dirty = proj_key in _DIR_DIRTY
            if is_dirty:
                _DIR_DIRTY.discard(proj_key)
        with _ENTRIES_CACHE_LOCK:
            cached = _ENTRIES_CACHE.get(proj_key)
        if cached is not None and not is_dirty:
            _INOTIFY_STATS["rescans_avoided"] += 1
            _inotify_maybe_log_stats()
            return cached
        if is_dirty:
            _INOTIFY_STATS["rescans_done"] += 1
    embedder = get_embedder()
    files = sorted(mem_dir.glob("*.md"))
    entries = []
    for f in files:
        if f.name.upper() in ("MEMORY.MD","INDEX.MD"): continue
        info = parse_memory_file(f)
        if info: entries.append(info)
    # cache lookup
    proj_key = str(mem_dir)
    cache = _state["memory_caches"].setdefault(proj_key, {})
    with _mem_lock(proj_key):  # v3.0.3 · serialize fill+flush per project
        updated = 0
        # v3.0.9 · batch encode · misses 先收集再一次 encode。逐条 encode 是云
        # daemon CPU 满载主因(792 条重 embed 逐条前向 ~4min;批量 2-5x),
        # py-spy 两轮独立实锤 forward 64.7% + get_memory_entries 25%。
        # _APIEmbedder 等单条 embedder 走 except 退回逐条(旧行为)。
        misses = []
        for e in entries:
            cached = cache.get(e["fullpath"])
            if cached and cached[0] == e["mtime"]:
                e["embedding"] = cached[1]
            else:
                misses.append(e)
        if misses:
            _t0e = time.time()
            _vecs = None
            try:
                _vecs = embedder.encode([e["embed_text"] for e in misses])
            except Exception as ex:
                log(f"batch encode fail, fallback to per-file: {ex}")
            if _vecs is not None:
                for e, vec in zip(misses, _vecs):
                    if hasattr(vec, "tolist"):
                        vec = vec.tolist()
                    cache[e["fullpath"]] = (e["mtime"], vec)
                    e["embedding"] = vec
                    updated += 1
                    # v3.0.1 · periodic flush · 大项目 re-embed 中途被
                    # kill/重启不再全丢进度(2026-08-24 云 74MB pkl 卡死根因之一)
                    if updated % _PKL_FLUSH_EVERY == 0:
                        _flush_memory_pkl(proj_key, cache)
            else:
                for e in misses:
                    try:
                        vec = embedder.encode(e["embed_text"])
                        if hasattr(vec, "tolist"):
                            vec = vec.tolist()
                        cache[e["fullpath"]] = (e["mtime"], vec)
                        e["embedding"] = vec
                        updated += 1
                        if updated % _PKL_FLUSH_EVERY == 0:
                            _flush_memory_pkl(proj_key, cache)
                    except Exception as ex:
                        log(f"embed file fail {e['path']}: {ex}")
                        e["embedding"] = None
            # v3.0.9 · re-embed 观测 · 哪个 project 在大量重 embed(此前盲区,
            # 全靠 py-spy 事后抓);proj_hash 与 pkl 文件名一致,可对账
            if updated:
                import hashlib as _hl
                log(f"re-embed {updated} files · {time.time()-_t0e:.1f}s · "
                    f"proj {_hl.sha256(proj_key.encode()).hexdigest()[:12]}")
        # v3.2 · chunk embeddings (COMPASS_CHUNK_RECALL) · parallel pkl key
        # "fullpath|chunks" = (mtime, [vec,...]) · same re-embed-on-mtime
        # discipline as the entry vector. Text is not persisted (chunk count
        # + order is deterministic from body, recomputed on cache miss).
        for e in entries:
            if _CHUNK_RECALL_USE:
                ck = e["fullpath"] + "|chunks"
                cch = cache.get(ck)
                if cch and cch[0] == e["mtime"]:
                    e["chunk_embs"] = cch[1]
                else:
                    try:
                        vecs = []
                        for c in _entry_chunks(e.get("body", "")):
                            cv = embedder.encode(c)
                            vecs.append(cv.tolist() if hasattr(cv, "tolist") else cv)
                        cache[ck] = (e["mtime"], vecs)
                        e["chunk_embs"] = vecs
                        updated += 1
                    except Exception as ex:
                        log(f"embed chunks fail {e['path']}: {ex}")
                        e["chunk_embs"] = []
        if updated:
            _flush_memory_pkl(proj_key, cache)
    # v2.0.9 · cache full entries for next recall · invalidated by inotify watcher
    if _INOTIFY_USE:
        with _ENTRIES_CACHE_LOCK:
            _ENTRIES_CACHE[proj_key] = entries
    return entries


def _inotify_maybe_log_stats():
    """v2.0.9 · throttled inotify stats log · every 60s"""
    global _INOTIFY_LAST_LOG
    now = time.time()
    if now - _INOTIFY_LAST_LOG < 60.0:
        return
    _INOTIFY_LAST_LOG = now
    s = _INOTIFY_STATS
    total = s["rescans_avoided"] + s["rescans_done"]
    if total == 0:
        return
    avoid_pct = s["rescans_avoided"] / total * 100
    log(f"inotify · watches={s['watch_count']} events={s['events']} "
        f"rescans_avoided={s['rescans_avoided']} done={s['rescans_done']} "
        f"avoid_rate={avoid_pct:.1f}% errors={s['errors']}")


def _inotify_watcher_thread():
    """v2.0.9 · Background watcher for memory dir changes.

    Watches all 75+ project memory dirs · sets dirty flag on file events ·
    get_memory_entries reads flag to decide if O(N) re-scan needed.
    Drops Layer 2 CPU burn from per-recall O(23k) to O(1) on warm hit.
    Falls back gracefully if inotify_simple missing or watch fails.
    """
    try:
        from inotify_simple import INotify, flags as _iflags
    except Exception as _e:
        log(f"inotify_simple import fail · entries cache disabled: {_e}")
        return
    try:
        inotify = INotify()
    except Exception as _e:
        log(f"INotify() init fail: {_e}")
        return
    # v3.0.9 · 收窄事件:CREATE/MODIFY/MOVED_FROM 冗余(一次文件写入原产生
    # 3-4 个事件;云上 20min 打了 3509 个)。CLOSE_WRITE=写完成 · 原子写
    # (tmp+rename)落 MOVED_TO · 删除留 DELETE,dirty 标记幂等不漏。
    watch_flags = (_iflags.CLOSE_WRITE | _iflags.MOVED_TO | _iflags.DELETE)
    wd_to_proj = {}
    watched = 0
    failed = 0
    for _name, mem_dir in _list_user_project_dirs():
        try:
            _wd = inotify.add_watch(str(mem_dir), watch_flags)
            wd_to_proj[_wd] = str(mem_dir)
            watched += 1
        except Exception as _e:
            failed += 1
            if failed <= 3:
                log(f"inotify watch fail {mem_dir.name}: {_e}")
    _INOTIFY_STATS["watch_count"] = watched
    log(f"inotify watcher · watching {watched} dirs · failed={failed}")
    while True:
        try:
            for _ev in inotify.read(timeout=None):
                _pk = wd_to_proj.get(_ev.wd)
                if not _pk:
                    continue
                if _ev.name and not _ev.name.endswith(".md"):
                    continue
                with _DIR_DIRTY_LOCK:
                    _DIR_DIRTY.add(_pk)
                _INOTIFY_STATS["events"] += 1
        except Exception as _e:
            _INOTIFY_STATS["errors"] += 1
            log(f"inotify read fail: {_e}")
            time.sleep(2)


def get_anchors(anchors_path: Path | None = None):
    """Load + embed anchor profile · cached by absolute path.

    v0.7.2: multi-profile cache. Each unique path keeps its own embedded
    set in `_state['anchor_caches']`. `_state['anchor_cache']` (singular)
    kept as alias for the most recently loaded profile for back-compat
    with code that doesn't pass anchors_path.
    """
    p = anchors_path if anchors_path is not None else ANCHORS_PATH
    if not p.exists():
        return None
    cur_mtime = p.stat().st_mtime
    key = str(p.resolve())
    cached = _state["anchor_caches"].get(key)
    if cached and cached["mtime"] == cur_mtime:
        _state["anchor_cache"] = cached  # back-compat alias
        return cached
    embedder = get_embedder()
    def _enc(s):
        v = embedder.encode(s)
        return v.tolist() if hasattr(v, "tolist") else v
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        # v0.7.1 · 兼容新旧 schema:
        #   旧: ["text1", "text2"]
        #   新: [{"text":"...", "weight":1.0, "tp":0, "fp":0}]
        def _normalize(items):
            out_text = []
            out_weight = []
            for it in items:
                if isinstance(it, str):
                    out_text.append(it); out_weight.append(1.0)
                elif isinstance(it, dict):
                    if it.get("weight", 1.0) <= 0.05:   # deprecated
                        continue
                    out_text.append(it.get("text", "")); out_weight.append(float(it.get("weight", 1.0)))
            return out_text, out_weight

        pos_raw = data.get("positive_anchors", [])
        neg_raw = data.get("negative_anchors", [])
        pos, pos_w = _normalize(pos_raw)
        neg, neg_w = _normalize(neg_raw)
        if not pos or not neg: return None
        pos_embs = [_enc(s) for s in pos]
        neg_embs = [_enc(s) for s in neg]
        # 不再算 centroid mean · 改 scoring 时用 weighted top-k mean (v0.7.1)
        result = {"mtime":cur_mtime,
                  "pos_anchors":pos, "pos_embs":pos_embs, "pos_weights":pos_w,
                  "neg_anchors":neg, "neg_embs":neg_embs, "neg_weights":neg_w,
                  "n_pos":len(pos), "n_neg":len(neg),
                  "raw": data}
        _state["anchor_caches"][key] = result
        _state["anchor_cache"] = result   # back-compat alias to most recent
        # only persist the default anchors.json profile; per-tenant profiles
        # stay in-memory to avoid cross-tenant leakage to disk
        if p == ANCHORS_PATH:
            _pkl_write_atomic(CACHE_DIR / "anchors.pkl", result)
        return result
    except Exception as e:
        log(f"anchor build fail for {p.name}: {e}")
        return None


def _list_user_project_dirs() -> list[tuple[str, Path]]:
    """v1.4 · scope=user · enumerate all (project_name, memory_dir) under ~/.claude/projects/

    Skips:
      · entries starting with '_' (e.g. _platform_queue · platform internals)
      · directories without a memory/ subdir
    """
    base = Path.home() / ".claude" / "projects"
    if not base.exists():
        return []
    out = []
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        if d.name.startswith("_"):
            continue
        mem = d / "memory"
        if mem.is_dir():
            out.append((d.name, mem))
    return out


def handle_request(req: dict) -> dict:
    action = req.get("action", "both")
    query = (req.get("query") or "").strip()[:2000]
    project = req.get("project", "")
    top_k = int(req.get("top_k") or TOP_K)
    # v1.3 · agent_type for per-agent L2 evidence dashboard (#104)
    agent_type = (req.get("agent_type") or "unknown")[:60]
    # v1.4 · S3 cross-project recall · scope=project (default) or scope=user
    scope = (req.get("scope") or "project").strip().lower()
    if scope not in ("project", "user"):
        return {"ok": False, "error": f"scope must be 'project' or 'user', got {scope!r}"}
    if not query:
        return {"ok": False, "error": "empty query"}

    # v2.3.0 · opt-in gemini query rewrite (recall actions only) · default off =
    # no LLM, query unchanged. LLM contact + all failure-handling isolated in
    # query_rewrite.rewrite_query (returns the original query on any fault).
    if _PROD_QUERY_REWRITE_USE and action in ("recall", "both"):
        try:
            import query_rewrite as _qr
            query = _qr.rewrite_query(query)
        except Exception as _qe:
            log(f"query rewrite failed · using original: {_qe}")

    # v2.0.7 · P9 · recall result cache lookup before encode/scoring
    _p9_key = _p9_cache_key(action, query, project, top_k, scope, agent_type)
    _p9_cached = _p9_cache_get(_p9_key)
    if _p9_cached is not None:
        # shallow copy + mark · avoid mutating cached dict on subsequent hits
        _p9_resp = dict(_p9_cached)
        _p9_resp["from_cache"] = True
        return _p9_resp

    # 找 mem_dir(s) · scope-aware
    mem_dirs: list[tuple[str, Path]] = []
    if scope == "project":
        if not project:
            return {"ok": False, "error": "project required when scope=project"}
        mem_dir = Path.home() / ".claude" / "projects" / project / "memory"
        if not mem_dir.exists():
            return {"ok": False, "error": f"no memory dir for {project}"}
        mem_dirs = [(project, mem_dir)]
    else:  # scope == "user"
        mem_dirs = _list_user_project_dirs()
        if not mem_dirs:
            return {"ok": False, "error": "no project memory dirs found under ~/.claude/projects/"}

    # v2.0.2 · P5 · 移除 global lock 包 embed · BGE-m3 + sentence-transformers
    # + torch 真 thread-safe(GIL 保护 dict ops · torch.no_grad 内置)· 不需手动
    # 串行. P4 修了 thread 数蓄积(288→8 pool)· 但全局 lock 仍把 8 worker 串
    # 行成 1 真 effective 并发 · 真 root cause 真 CLOSE_WAIT 蓄积(209 案).
    # 期望 throughput 4-8x · CLOSE_WAIT 不再爆炸.
    embedder = get_embedder()  # eager-loaded at daemon startup · idempotent
    try:
        v = embedder.encode(query)
        q_emb = v.tolist() if hasattr(v, "tolist") else v
    except Exception as e:
        return {"ok": False, "error": f"query embed fail: {e}"}

    result = {
        "ok": True,
        "project": project or (mem_dirs[0][0] if mem_dirs else ""),
        "scope": scope,
        "projects_scanned": [p for p, _ in mem_dirs],
        "query": query[:80],
    }

    if action in ("recall", "both"):
        # Union entries across all mem_dirs · tag each with its origin project
        all_entries: list[dict] = []
        for proj_name, mdir in mem_dirs:
            for e in get_memory_entries(mdir):
                # shallow-tag origin (don't mutate cache entries)
                if "project" not in e:
                    e["project"] = proj_name
                all_entries.append(e)
        # v2.3.0 · lifecycle forget-filter (opt-in COMPASS_PROD_LIFECYCLE=1) ·
        # drop forgotten memories before scoring; default off = no-op.
        all_entries = _apply_lifecycle_filter(all_entries)
        scored = []
        for e in all_entries:
            if not e.get("embedding"): continue
            s = cosine(q_emb, e["embedding"])
            if s >= COSINE_MIN:
                scored.append((s, e))
        scored.sort(key=lambda x: -x[0])

        # v2.3.0 · when prod reranker is on, retrieve a wider candidate set so the
        # cross-encoder can pull a deep truth up; otherwise keep top_k width.
        _retrieve_n = max(top_k, _RERANK_CANDIDATES) if _PROD_RERANK_USE else top_k

        # v2.1.0 · Phase 2 · BM25 + vec RRF fusion · opt-in via COMPASS_USE_BM25_RRF=1
        if _BM25_RRF_USE:
            try:
                _bm25 = _build_bm25_retriever(all_entries)
                _bm25_ranked = _bm25_score_to_ranked(_bm25, all_entries, query, top_k=_BM25_RRF_TOP_K)
                _vec_top_for_rrf = scored[:_BM25_RRF_TOP_K]  # top-30 vec → RRF input
                fused = _rrf_fusion([_vec_top_for_rrf, _bm25_ranked],
                                    k=_BM25_RRF_K, top_k=_retrieve_n)
                top = fused  # replace vec-only top with fused
                result["_v210_fused"] = True
                result["_v210_bm25_n"] = len(_bm25_ranked)
            except Exception as _be:
                log(f"BM25 RRF fail · fallback to vec only: {_be}")
                top = scored[:_retrieve_n]
        else:
            top = scored[:_retrieve_n]

        # v3.2 · chunk-level recall fusion (COMPASS_CHUNK_RECALL=1). Reranks the
        # dense(±BM25) list by RRF with a chunk-best-score list: entries whose
        # ONE paragraph matches the query get pulled up (utterance-routing port).
        if _CHUNK_RECALL_USE:
            try:
                chunk_scored = []
                for e in all_entries:
                    best = -1.0
                    for cv in e.get("chunk_embs") or ():
                        s = cosine(q_emb, cv)
                        if s > best:
                            best = s
                    if best >= COSINE_MIN:
                        chunk_scored.append((best, e))
                chunk_scored.sort(key=lambda x: -x[0])
                if chunk_scored:
                    top = _rrf_fusion(
                        [top, chunk_scored[:_BM25_RRF_TOP_K]],
                        k=_BM25_RRF_K, top_k=_retrieve_n)
                    result["_v32_chunk_fused"] = True
                    result["_v32_chunk_n"] = len(chunk_scored)
            except Exception as _ce:
                log(f"chunk recall fusion fail · fallback to pre-fusion top: {_ce}")

        # v2.3.0 · production cross-encoder rerank (opt-in COMPASS_PROD_RERANK=1).
        # flag off → returns top[:top_k] unchanged; flag on → reorder then truncate.
        top = _rerank_top(query, top, top_k)
        if _PROD_RERANK_USE:
            result["_v230_reranked"] = True

        # Phase 1 Task 4 · tier-aware re-rank (opt-in COMPASS_PROD_TIER_WEIGHT=1).
        # No-op by default · mutually exclusive with rerank (see fn docstring).
        top = _apply_tier_weight_prod(top, top_k)
        if _PROD_TIER_WEIGHT_USE and not _PROD_RERANK_USE:
            result["_task4_tier_weighted"] = True

        result["recall"] = [
            {"score": round(s, 3), "path": e["path"],
             "project": e.get("project", ""),
             "age_str": e["age_str"], "age_seconds": e["age_seconds"],
             "description": e["description"],
             "body": e.get("body", "")}
            for s, e in top
        ]
        # fresh memories not in top
        top_set = {(t[1]["path"], t[1].get("project", "")) for t in top}
        fresh_extra = [
            e for e in all_entries
            if e["age_seconds"] < 86400
            and (e["path"], e.get("project", "")) not in top_set
        ]
        result["fresh_extra"] = [
            {"path": e["path"], "project": e.get("project", ""),
             "age_str": e["age_str"], "description": e["description"]}
            for e in sorted(fresh_extra, key=lambda x: x["age_seconds"])
        ]

    if action in ("drift", "both"):
        # v0.7.2 · per-request anchor profile (gateway passes anchors_path)
        ap = req.get("anchors_path")
        anchors = get_anchors(Path(ap) if ap else None)
        # 2026-08-28 fix(workbuddy 实测 P0·1.1): anchors 缺失曾静默跳过——
        # 安全防线(危险命令检测)形同虚设且用户毫不知情。fail loudly:
        # 结果带 anchors_error,日志亮牌。运维动作=把 anchors.json 放进
        # PLUGIN_DIR(云端空壳目录那次=拷贝即修)。
        if not anchors:
            _msg = (f"anchors.json not found at {ANCHORS_PATH} — drift DISABLED "
                    f"(fail-loudly, was silent before 2026-08-28)")
            result["drift"] = {"score": None, "should_alert": True,
                               "anchors_error": _msg}
            log(f"⚠️ DRIFT DISABLED · {_msg}")
        if anchors:
            # v0.7.1 · Weighted top-k mean scoring
            # 每个 anchor 一个 weight (默认 1.0 · adaptive learning 调整)
            # weighted_cos = weight * cosine · 排序后取 top-3 加权平均
            TOP_K_ANCHORS = 3
            pos_w = anchors["pos_weights"]
            neg_w = anchors["neg_weights"]
            pos_pairs = [
                (pos_w[i] * cosine(q_emb, e), pos_w[i])
                for i, e in enumerate(anchors["pos_embs"])
            ]
            pos_pairs.sort(key=lambda x: -x[0])
            top_pos = pos_pairs[:TOP_K_ANCHORS]
            pos_cos = (sum(s for s, _ in top_pos) / sum(w for _, w in top_pos)
                       if top_pos else 0.0)
            neg_pairs = [
                (neg_w[i] * cosine(q_emb, e), neg_w[i],
                 cosine(q_emb, e), anchors["neg_anchors"][i])
                for i, e in enumerate(anchors["neg_embs"])
            ]
            neg_pairs.sort(key=lambda x: -x[0])
            top_neg = neg_pairs[:TOP_K_ANCHORS]
            neg_cos = (sum(s for s, _, _, _ in top_neg) / sum(w for _, w, _, _ in top_neg)
                       if top_neg else 0.0)
            drift_score = round(pos_cos - neg_cos, 4)
            # 单 anchor hits · 用 raw cosine 不用 weighted (alert text 显示真相似度)
            neg_hits = [
                (round(raw_c, 3), txt) for _, _, raw_c, txt in neg_pairs
                if raw_c >= NEG_ANCHOR_HIT_THRESHOLD
            ][:5]
            # v2 cutover (2026-06-01) · 弃 neg_cos≥0.538 OR 分支 —— 11.5k 条真实流量证它
            # 64.5% 逢触必报(benign neg_cos 0.60-0.69 与 drift 完全重叠)· 致 act_on 仅 9.87%。
            # 改 rule_alert(危险命令正则) OR drift_score<V2_THRESH · 实测 0.5% alert · 高精度。
            # (5/31 reconcile: Projects 线 drift/firing.py::should_fire_drift 保留作未来 A/B · 当前 active=v2)
            rule_hit = _shadow_rule_alert(query)
            should_alert = rule_hit or drift_score < ZMM_DRIFT_V2_THRESH
            result["drift"] = {
                "score": drift_score,
                "alignment": round(pos_cos, 4),
                "deviation": round(neg_cos, 4),
                "should_alert": should_alert,
                "rule_hit": rule_hit,
                "top_neg_hits": neg_hits[:3],
                "n_pos": anchors["n_pos"],
                "n_neg": anchors["n_neg"],
            }

    # ─── verification_log · 7 天对照实验数据 ───────────────
    try:
        log_path = CACHE_DIR / "verification_log.jsonl"
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "session_id": os.environ.get("CLAUDE_SESSION_ID", "unknown")[:60],
            "agent_type": agent_type,
            "project": project[:80],
            "action": action,
            "query": query[:200],
            "top5": [
                {"score": r["score"], "path": r["path"], "age": r["age_str"]}
                for r in (result.get("recall") or [])[:5]
            ],
            "fresh_n": len(result.get("fresh_extra") or []),
            "drift_score": (result.get("drift") or {}).get("score"),
            "drift_alert": (result.get("drift") or {}).get("should_alert"),
            # v2 是 active firing 路径(reconcile 后)· 保留 rule_hit + drift_alert_v2 供 log 连续性
            "rule_hit": _shadow_rule_alert(query),
            "drift_alert_v2": bool(
                _shadow_rule_alert(query)
                or (((result.get("drift") or {}).get("score") or 0) < ZMM_DRIFT_V2_THRESH)),
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as _le:
        log(f"verification_log write fail: {_le}")

    # v2.0.7 · P9 · cache successful result before return
    # 2026-08-28 fix(workbuddy 实测): 缓存曾把错误/异常响应也存下——底层修好后
    # 同 query 在 TTL 内仍命中旧的错误结果(无法自愈)。只缓存 ok 响应。
    try:
        if result.get("ok", True) and not result.get("error"):
            _p9_cache_put(_p9_key, result)
        # log cache stats every 1000 ops
        _total = sum(_RECALL_CACHE_STATS.values())
        if _total > 0 and _total % 1000 == 0:
            _stats = _RECALL_CACHE_STATS
            _hit_rate = _stats["hit"] / max(_stats["hit"] + _stats["miss"], 1) * 100
            log(f"P9 cache · {_total} ops · hit_rate={_hit_rate:.1f}% · size={len(_RECALL_CACHE)} · "
                f"hits={_stats['hit']} misses={_stats['miss']} expires={_stats['expire']} evicts={_stats['evict']}")
    except Exception as _ce:
        log(f"P9 cache put fail: {_ce}")

    return result


def _load_pkl_caches():
    """v2.0.8 · pkl warmup · root-cure for cold-start CPU spike.

    memory_caches pkl files were written (line 324/750) but never loaded.
    Every daemon restart triggered full re-embed of every memory file in
    every project on first recall. py-spy showed 2 bge-handlers stuck in
    encode() on memory entries · CPU 198% sustained. This loads persisted
    embeddings so warm cache survives restart. Stale entries (mtime changed)
    will still be re-embedded per-file in get_memory_entries.
    """
    import pickle as _pickle_w
    import hashlib as _hashlib_w
    if not CACHE_DIR.exists():
        return
    loaded = 0
    skipped = 0
    failed = 0
    for _name, mem_dir in _list_user_project_dirs():
        proj_key = str(mem_dir)
        proj_hash = _hashlib_w.sha256(proj_key.encode()).hexdigest()[:12]
        pkl_path = CACHE_DIR / f"{proj_hash}.pkl"
        if not pkl_path.exists():
            skipped += 1
            continue
        try:
            with open(pkl_path, "rb") as _f:
                data = _pickle_w.load(_f)
            cache = data.get("embeddings", {}) if isinstance(data, dict) else {}
            if cache:
                _state["memory_caches"][proj_key] = cache
                loaded += 1
            else:
                skipped += 1
        except Exception as _le:
            log(f"pkl warmup fail {proj_hash}: {_le}")
            failed += 1
    log(f"pkl warmup · loaded={loaded} skipped={skipped} failed={failed}")


def serve():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    global _DAEMON_START_TS
    _DAEMON_START_TS = time.time()
    log(f"daemon starting PID={os.getpid()} port={PORT}")

    # v0.7.2 fix · eager-load bge-m3 + anchors at startup. Lazy load caused
    # 60-90s hang on first 'both' request → hook 60s timeout → fallback inline
    # (recall.py 583). With eager load · startup slow but all requests <1s.
    try:
        log("eager-loading bge-m3 + anchors...")
        _t0 = time.time()
        _ = get_embedder()
        log(f"  embedder ready · {time.time()-_t0:.1f}s")
        _t1 = time.time()
        _ = get_anchors()
        log(f"  anchors ready · {time.time()-_t1:.1f}s · total startup {time.time()-_t0:.1f}s")
    except Exception as _e:
        log(f"eager-load fail (will retry lazy): {_e}")

    # v2.0.8 · pkl warmup · avoid cold-start re-embed CPU spike
    try:
        _t2 = time.time()
        _load_pkl_caches()
        log(f"  pkl warmup done · {time.time()-_t2:.1f}s")
    except Exception as _we:
        log(f"pkl warmup fail (cold start): {_we}")

    # v2.0.9 · inotify watcher thread · Layer 2 cure
    if _INOTIFY_USE:
        try:
            _wt = threading.Thread(target=_inotify_watcher_thread,
                                   name="inotify-watcher", daemon=True)
            _wt.start()
            log("inotify watcher thread started")
        except Exception as _ie:
            log(f"inotify watcher start fail · fallback to per-recall scan: {_ie}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((HOST, PORT))
    except OSError as e:
        log(f"bind fail · already running? {e}")
        sys.exit(2)
    # v2.0.0 · P4 · increased backlog from 8 → 128 so overflow during burst
    # waits at OS level instead of being refused (which retry-stormed callers
    # would only amplify). Pool of 8 workers drains the queue.
    sock.listen(128)
    log(f"listening {HOST}:{PORT}")

    while True:
        try:
            conn, addr = sock.accept()
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"accept fail: {e}")
            continue
        # v2.0.7 · P7 · in-flight cap via BoundedSemaphore · reject-fast when
        # queue + running > 32 · prevents CLOSE-WAIT leak from unbounded
        # ThreadPoolExecutor queueing under V5/V7 retry storms.
        if not _INFLIGHT_SEM.acquire(blocking=False):
            log(f"overload · reject conn (inflight cap {DAEMON_INFLIGHT_LIMIT})")
            _OVERLOAD_TS_BUFFER.append(time.time())
            try:
                conn.sendall(b'{"ok":false,"error":"daemon overloaded - retry"}\n')
            except Exception:
                pass
            try: conn.shutdown(socket.SHUT_RDWR)
            except Exception: pass
            try: conn.close()
            except Exception: pass
            continue
        # v2.0.0 · P4 · bounded pool · was `threading.Thread(...).start()`
        # which spawned unbounded under retry storms · 288 threads leaked
        # 2026-05-22. Pool rejects via RuntimeError when shutting down · OS
        # socket backlog (listen(128) above) handles momentary overflow.
        try:
            _HANDLER_POOL.submit(_safe_handle, conn)
        except RuntimeError as e:
            log(f"pool reject: {e}")
            try:
                _INFLIGHT_SEM.release()
            except Exception:
                pass
            try:
                conn.sendall(b'{"ok":false,"error":"daemon shutting down"}\n')
            except Exception:
                pass
            try: conn.shutdown(socket.SHUT_RDWR)
            except Exception: pass
            try:
                conn.close()
            except Exception:
                pass

    sock.close()
    if PID_FILE.exists():
        PID_FILE.unlink(missing_ok=True)
    log("daemon stopped")


def _recover_surrogates(s: str) -> str:
    """Sanitize lone surrogates (\\udc80-\\udcff) that crash write_text(utf-8).

    They come from an upstream gbk-decode-as-UTF-8/surrogateescape (the Windows MCP
    client · session_20260605 Finding 1: Chinese obs all crash, ASCII passes). The
    single cloud-substrate ingest path must never die on one bad-encoded obs:
    re-encode to the original bytes + decode as gbk (the Windows default ·
    round-trips the CJK); on failure 'replace' so it degrades gracefully. Valid
    input (ASCII / real CJK · no surrogates) is returned untouched."""
    if not any("\ud800" <= c <= "\udfff" for c in s):
        return s
    try:
        return s.encode("utf-8", "surrogateescape").decode("gbk")
    except UnicodeError:
        return s.encode("utf-8", "replace").decode("utf-8")


def handle_ingest(req: dict) -> dict:
    """v2.0.0 · S5 · ingest text -> compass memory .md + embed + cache.

    Lets platform agents (V5/V6/V7) feed text into compass without going
    through session_writer + LLM summarize. Use case: ingest task outputs,
    agent observations, audit logs.

    Required:
      text (str): session content
      project (str): project name (encoded cwd or platform tenant id)
    Optional lifecycle frontmatter (v1.7.1 · LLM_WIKI2 paradigm):
      tier (working|episodic|semantic|procedural)
      decay_rate (float 0-1)
      forget_at (ISO8601)
      promote_after (e.g., "7d" or "5_access")
    Optional metadata:
      filename (override default timestamp-based name)
      agent_type, agent_id, tags, source

    Returns:
      {ok: true, path: "<written .md>", embedded: true, embed_dim: 1024, project: "..."}
    """
    import hashlib as _hashlib
    import pickle as _pickle
    from datetime import datetime, timezone

    text = _recover_surrogates((req.get("text") or "").strip())
    project = (req.get("project") or "").strip()
    if not text:
        return {"ok": False, "error": "empty text"}
    if not project:
        return {"ok": False, "error": "project required for ingest"}
    if len(text) > 500_000:
        return {"ok": False, "error": "text too large (>500KB) · split before ingest"}

    mem_dir = Path.home() / ".claude" / "projects" / project / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)

    fname = _recover_surrogates((req.get("filename") or "").strip())
    if not fname:
        ts = time.strftime("%Y%m%d_%H%M%S")
        hsh = abs(hash(text)) % 100000
        fname = f"ingest_{ts}_{hsh}.md"
    if not fname.endswith(".md"):
        fname += ".md"
    fname = fname.replace("/", "_").replace("\\", "_")

    fm = ["---", f"name: {fname[:-3]}",
          f"created: {datetime.now(timezone.utc).isoformat()}",
          "type: ingest", "source: bge-daemon-ingest"]
    for k in ("tier", "decay_rate", "forget_at", "promote_after",
              "agent_type", "agent_id", "tags"):
        v = req.get(k)
        if v is not None and v != "":
            if isinstance(v, list):
                fm.append(f"{k}: [{', '.join(repr(x) for x in v)}]")
            else:
                fm.append(f"{k}: {v}")
    fm.append("---")
    fm.append("")
    content = "\n".join(fm) + text.rstrip() + "\n"

    out_path = mem_dir / fname
    out_path.write_text(content, encoding="utf-8")

    try:
        embedder = get_embedder()
        vec = embedder.encode(text[:5000])
        if hasattr(vec, "tolist"):
            vec = vec.tolist()
        proj_key = str(mem_dir)
        cache = _state["memory_caches"].setdefault(proj_key, {})
        # v3.0.9 · ingest flush 与 recall 线程的 flush/cache 写互斥
        # (此前无锁:与 _mem_lock 内的 recall flush 并发是历史 flush fail 源之一)
        with _mem_lock(proj_key):
            cache[str(out_path)] = (out_path.stat().st_mtime, vec)
            _flush_memory_pkl(proj_key, cache)
        return {"ok": True, "path": str(out_path), "project": project,
                "embedded": True, "embed_dim": len(vec)}
    except Exception as e:
        return {"ok": True, "path": str(out_path), "project": project,
                "embedded": False, "embed_warning": str(e)}


def _safe_handle(conn: socket.socket):
    """v2.0.7 · P7 · wraps handle_conn to guarantee fd release + sem release.

    Even when handle_conn returns normally · this wrapper drains any
    pending rx data (V5 may send retry frames after timeout), forces
    shutdown(SHUT_RDWR) before close (so fd doesn't linger in CLOSE-WAIT
    waiting for client FIN), then releases the in-flight sem token so
    the accept loop can accept new conns.
    """
    try:
        handle_conn(conn)
    finally:
        # drain any pending rx · V5 retry frames or duplicate sends
        try: conn.settimeout(0.1)
        except Exception: pass
        try:
            while True:
                chunk = conn.recv(65536)
                if not chunk: break
        except Exception: pass
        # force both-end shutdown · don't wait for client FIN
        try: conn.shutdown(socket.SHUT_RDWR)
        except Exception: pass
        try: conn.close()
        except Exception: pass
        # release inflight slot for next accept
        try: _INFLIGHT_SEM.release()
        except Exception: pass


def handle_conn(conn: socket.socket):
    try:
        conn.settimeout(60)
        # 读到 \n 终止
        buf = b""
        while b"\n" not in buf:
            chunk = conn.recv(8192)
            if not chunk: break
            buf += chunk
            if len(buf) > 1024*1024: break    # 1MB 上限
        line, _, _ = buf.partition(b"\n")
        try:
            req = json.loads(line.decode("utf-8"))
        except Exception as e:
            conn.sendall(json.dumps({"ok":False,"error":f"json parse: {e}"}).encode("utf-8") + b"\n")
            return
        if req.get("action") == "ping":
            conn.sendall(json.dumps(_runtime_identity_payload()).encode("utf-8") + b"\n")
            return
        if req.get("action") == "status":
            # v3.0.2 · Stage1a /status (ported from cloud /opt fork)
            conn.sendall(json.dumps(_status_payload(), ensure_ascii=False).encode("utf-8") + b"\n")
            return
        if req.get("action") == "shutdown":
            conn.sendall(b'{"ok":true,"shutdown":true}\n')
            log("shutdown requested")
            os._exit(0)
        if req.get("action") == "ingest":
            resp_bytes = json.dumps(handle_ingest(req), ensure_ascii=False).encode("utf-8") + b"\n"
            conn.sendall(resp_bytes)
            return
        if req.get("action") == "score":
            resp_bytes = json.dumps(_handle_score(req), ensure_ascii=False).encode("utf-8") + b"\n"
            conn.sendall(resp_bytes)
            return
        _t0 = time.time()
        resp = handle_request(req)
        # v3.0.2 · record recall/drift latency for /status sliding window
        if req.get("action") in ("recall", "drift", "both"):
            _RECALL_TS_BUFFER.append((time.time(), round((time.time() - _t0) * 1000, 1)))
        conn.sendall(json.dumps(resp, ensure_ascii=False).encode("utf-8") + b"\n")
    except Exception as e:
        log(f"conn handler fail: {e}")
        try:
            conn.sendall(json.dumps({"ok":False,"error":str(e)}).encode("utf-8") + b"\n")
        except Exception:
            pass
    finally:
        try: conn.close()
        except Exception: pass


def _runtime_identity_payload() -> dict:
    """Return immutable facts about the process answering on the daemon port."""

    daemon_path = Path(__file__).resolve()
    return {
        "ok": True,
        "pong": True,
        "pid": os.getpid(),
        "python_executable": str(Path(sys.executable).resolve()),
        "source_root": str(daemon_path.parent),
        "daemon_hash": f"sha256:{hashlib.sha256(daemon_path.read_bytes()).hexdigest()}",
    }


def client(action: str, query: str, project: str, top_k: int = 5,
           timeout: float = 5.0) -> dict:
    """同步调 daemon · 拿 JSON response."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((HOST, PORT))
            req = {"action": action, "query": query,
                   "project": project, "top_k": top_k}
            s.sendall(json.dumps(req, ensure_ascii=False).encode("utf-8") + b"\n")
            buf = b""
            while b"\n" not in buf:
                chunk = s.recv(65536)
                if not chunk: break
                buf += chunk
            line, _, _ = buf.partition(b"\n")
            return json.loads(line.decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"daemon unreachable: {e}"}


def is_alive() -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect((HOST, PORT))
            s.sendall(b'{"action":"ping"}\n')
            buf = s.recv(4096)
            return b'"pong"' in buf and b'true' in buf
    except Exception:
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "ping":
        sys.exit(0 if is_alive() else 1)
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((HOST, PORT))
                s.sendall(b'{"action":"shutdown"}\n')
        except Exception as e:
            log(f"stop fail: {e}")
        sys.exit(0)
    serve()

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
import json
import os
import pickle
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# v2.0.0 · P4 fix · bounded handler pool prevents unbounded thread spawn
# under V5/V7 retry storms (root cause of 288-thread leak observed
# 2026-05-22). 8 workers matches the 4-core CPU's effective concurrency
# for BGE-m3 inference; further requests queue at the OS socket backlog.
DAEMON_MAX_HANDLER_THREADS = int(os.environ.get("COMPASS_DAEMON_POOL", "8"))
_HANDLER_POOL = ThreadPoolExecutor(
    max_workers=DAEMON_MAX_HANDLER_THREADS,
    thread_name_prefix="bge-handler",
)

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


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    line = f"[{time.strftime('%H:%M:%S')}] {msg}\n"
    try:
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
    # 包一个 wrapper · encode 返 list 兼容 _APIEmbedder
    class _BGEWrapper:
        def encode(self, text, **kwargs):
            return model.encode(text).tolist()
    _state["embedder"] = _BGEWrapper()
    log(f"BGE loaded · {time.time()-t0:.1f}s")
    return _state["embedder"]


def cosine(a, b):
    import math
    if not a or not b: return 0.0
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na>0 and nb>0 else 0.0


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
        "type": fm.get("type","?"),
        "age_seconds": age_s, "age_str": age_str,
        "embed_text": (fm.get("description","") + "\n" + body)[:EMBED_MAX_CHARS],
        "mtime": path.stat().st_mtime,
    }


def get_memory_entries(mem_dir: Path):
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
    updated = False
    for e in entries:
        cached = cache.get(e["fullpath"])
        if cached and cached[0] == e["mtime"]:
            e["embedding"] = cached[1]
        else:
            try:
                vec = embedder.encode(e["embed_text"])
                if hasattr(vec, "tolist"):
                    vec = vec.tolist()
                cache[e["fullpath"]] = (e["mtime"], vec)
                e["embedding"] = vec
                updated = True
            except Exception as ex:
                log(f"embed file fail {e['path']}: {ex}")
                e["embedding"] = None
    if updated:
        # 持久化
        import hashlib
        proj_hash = hashlib.sha256(proj_key.encode()).hexdigest()[:12]
        with open(CACHE_DIR / f"{proj_hash}.pkl", "wb") as f:
            pickle.dump({"embeddings": cache}, f)
    return entries


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
            with open(CACHE_DIR / "anchors.pkl", "wb") as f:
                pickle.dump(result, f)
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
        scored = []
        for e in all_entries:
            if not e.get("embedding"): continue
            s = cosine(q_emb, e["embedding"])
            if s >= COSINE_MIN:
                scored.append((s, e))
        scored.sort(key=lambda x: -x[0])
        top = scored[:top_k]
        result["recall"] = [
            {"score": round(s, 3), "path": e["path"],
             "project": e.get("project", ""),
             "age_str": e["age_str"], "age_seconds": e["age_seconds"],
             "description": e["description"]}
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
            should_alert = drift_score < DRIFT_ALERT_THRESHOLD or bool(neg_hits)
            result["drift"] = {
                "score": drift_score,
                "alignment": round(pos_cos, 4),
                "deviation": round(neg_cos, 4),
                "should_alert": should_alert,
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
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as _le:
        log(f"verification_log write fail: {_le}")

    return result


def serve():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
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
        # v2.0.0 · P4 · bounded pool · was `threading.Thread(...).start()`
        # which spawned unbounded under retry storms · 288 threads leaked
        # 2026-05-22. Pool rejects via RuntimeError when shutting down · OS
        # socket backlog (listen(128) above) handles momentary overflow.
        try:
            _HANDLER_POOL.submit(handle_conn, conn)
        except RuntimeError as e:
            log(f"pool reject: {e}")
            try:
                conn.sendall(b'{"ok":false,"error":"daemon shutting down"}\n')
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

    sock.close()
    if PID_FILE.exists():
        PID_FILE.unlink(missing_ok=True)
    log("daemon stopped")


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

    text = (req.get("text") or "").strip()
    project = (req.get("project") or "").strip()
    if not text:
        return {"ok": False, "error": "empty text"}
    if not project:
        return {"ok": False, "error": "project required for ingest"}
    if len(text) > 500_000:
        return {"ok": False, "error": "text too large (>500KB) · split before ingest"}

    mem_dir = Path.home() / ".claude" / "projects" / project / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)

    fname = (req.get("filename") or "").strip()
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
        cache[str(out_path)] = (out_path.stat().st_mtime, vec)
        proj_hash = _hashlib.sha256(proj_key.encode()).hexdigest()[:12]
        with open(CACHE_DIR / f"{proj_hash}.pkl", "wb") as f:
            _pickle.dump({"embeddings": cache}, f)
        return {"ok": True, "path": str(out_path), "project": project,
                "embedded": True, "embed_dim": len(vec)}
    except Exception as e:
        return {"ok": True, "path": str(out_path), "project": project,
                "embedded": False, "embed_warning": str(e)}


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
            conn.sendall(json.dumps({"ok":True,"pong":True}).encode("utf-8") + b"\n")
            return
        if req.get("action") == "shutdown":
            conn.sendall(b'{"ok":true,"shutdown":true}\n')
            log("shutdown requested")
            os._exit(0)
        if req.get("action") == "ingest":
            resp_bytes = json.dumps(handle_ingest(req), ensure_ascii=False).encode("utf-8") + b"\n"
            conn.sendall(resp_bytes)
            return
        resp = handle_request(req)
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

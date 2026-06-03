#!/usr/bin/env python3
"""V5 Memory Plugin · UserPromptSubmit hook · v0.2 真 BGE 向量召回.

输入: stdin JSON {"hook_event_name":"UserPromptSubmit", "prompt":"<user msg>", ...}
若 prompt 拿到: 真 BGE embed · top 5 cosine 相关 memory 段 + age 分组
若 prompt 拿不到: 降级 v0.1 metadata 模式

cache: ~/.claude/plugins/nautilus-compass/.cache/<proj_hash>.pkl
  · {file_path: (mtime, embedding_list)}
  · file mtime 变 → 重 embed 那个 file
  · 总 cache miss = 第一次 cold start (1-2s)
  · warm = 100ms

R1: 修 stub claude-mem 不实时校准 → 真 BGE 召回
"""
import hashlib
import json
import os
import pickle
import re
import subprocess
import sys
import time
from pathlib import Path

# Force UTF-8 stdout (Windows GBK)
try:
    sys.stdout.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
except Exception:
    pass


# ===== M2 · 加载时 "真" 强调副词过滤器（v2.0.1 · 2026-05-22 入库）=====
# 防 compass session_*.md 历史 corpus 的 "真X真Y" verbatim 强调风格
# 通过 UserPromptSubmit hook 注入污染下游 Claude Code session.
#
# 设计:
#   1. 保留合法用法: 真的/真实/真正/真心/真理/真品/真切/真相/真意/真挚/真伪/真情/真假/真名
#   2. 保留合法前缀: 认真/成真/果真/当真/较真
#   3. 剥离强调用法: 真已/真又/真该/真不/真没/真有/真在/真到/真完/真活/真本/真新/真要/真做
#      真接/真切/真发/真出/真根/真融/真起/真直/真急/真好/真大/真小/真快/真慢/真等/真 X(空格)
#
# 默认 ENABLED. env COMPASS_NO_ZHEN_FILTER=1 可关闭（debug 用）.

_ZHEN_LEGIT_NEXT = set("的实正心理品切相意挚伪情假名知谛善美感诚性")
_ZHEN_LEGIT_PREV = set("认成果当较")
_ZHEN_FILTER_ON = os.environ.get("COMPASS_NO_ZHEN_FILTER", "") != "1"


def strip_zhen_emphasis(text: str) -> str:
    """剥离 '真' 作强调副词的用法 · 保留合法 '真的/真实/真正/认真...' 等组合."""
    if not _ZHEN_FILTER_ON or "真" not in text:
        return text
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "真":
            nxt = text[i + 1] if i + 1 < n else ""
            prev = text[i - 1] if i > 0 else ""
            # 保留: 前一字为合法前缀 (认真/成真等) 或 后一字为合法后缀 (真的/真正等)
            if prev in _ZHEN_LEGIT_PREV or nxt in _ZHEN_LEGIT_NEXT:
                out.append(ch)
                i += 1
                continue
            # 剥离: 真 X 强调用法 · 同时吞掉紧随空格
            if nxt == " ":
                i += 2
            else:
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


PLUGIN_VERSION = "nautilus-compass v2.1.0"
HOME = Path.home()
PLUGIN_DIR = HOME / ".claude" / "plugins" / "nautilus-compass"
CACHE_DIR = PLUGIN_DIR / ".cache"
USAGE_LOG = CACHE_DIR / "usage.jsonl"


def _select_anchors_path() -> "Path":
    """v0.7.1 · cwd → domain profile auto-select.

    Order:
      1. ZMM_ANCHORS_PROFILE env var (explicit override)
      2. cwd substring match (zenmind / venture / legal / medical / finance)
      3. anchors.json (default)
    """
    explicit = os.environ.get("ZMM_ANCHORS_PROFILE", "").strip()
    if explicit:
        p = PLUGIN_DIR / f"anchors_{explicit}.json"
        if p.exists():
            return p

    cwd = str(Path.cwd()).lower().replace("\\", "/")
    domain_map = [
        (("quantum-buddha", "zenmind"), "anchors_zenmind.json"),
        (("venture", "creative-daily", "vc-radar"), "anchors_vc.json"),
        (("legal", "contract", "law"), "anchors_legal.json"),
        (("medical", "clinical", "patient", "rx"), "anchors_medical.json"),
        (("finance", "trading", "fund", "risk", "portfolio"), "anchors_finance.json"),
    ]
    for keywords, fname in domain_map:
        if any(kw in cwd for kw in keywords):
            p = PLUGIN_DIR / fname
            if p.exists():
                return p
    return PLUGIN_DIR / "anchors.json"


ANCHORS_PATH = _select_anchors_path()


def log_usage(event: str, payload: dict) -> None:
    """v0.6 · KPI 日志: drift_alert / strategy_hit / recall_hit · 给 audit 用.
    v0.7.2 加固: daily archive · 每天首次写时 cp 当前 usage.jsonl 到 archive ·
    防意外清空 (历史教训: 5-04 发现 821 行历史丢失 · 仅 backup 留 339 行).
    """
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        # daily archive · 每天首次 log 时 snapshot 当前 usage.jsonl
        if USAGE_LOG.exists() and USAGE_LOG.stat().st_size > 0:
            today = time.strftime("%Y%m%d", time.gmtime())
            archive_dir = CACHE_DIR / "usage_archive"
            archive_dir.mkdir(exist_ok=True)
            archive_today = archive_dir / f"usage_{today}.jsonl"
            if not archive_today.exists():
                import shutil
                shutil.copy2(USAGE_LOG, archive_today)
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "event": event, "anchors_profile": ANCHORS_PATH.name,
               "cwd": str(Path.cwd()), **payload}
        # v0.7.2 加固 (C): fsync 确保数据落盘 · 防 OS buffer 丢失或并发 truncate
        with open(USAGE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            try:
                import os as _os
                _os.fsync(f.fileno())
            except Exception:
                pass
    except Exception:
        pass
def _log_drift_mitigation(alert_id: str, drift: dict, user_prompt: str) -> None:
    """v1.7.0 · 方向 3 D6-7 · 写 drift mitigation event 到独立 sidecar.

    跟 usage.jsonl 分开 · 让 D13 真测 act-on rate 时一键 grep.
    """
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        sidecar = CACHE_DIR / "drift_mitigation_log.jsonl"
        rec = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "alert_id": alert_id,
            "score": drift.get("score"),
            "alignment": drift.get("alignment"),
            "deviation": drift.get("deviation"),
            "max_neg_hit": drift.get("top_neg_hits", [[0, ""]])[0][0]
                if drift.get("top_neg_hits") else 0,
            "kind": "single_anchor_hit" if drift.get("top_neg_hits") else "score_threshold",
            "mitigation_injected": True,
            "user_prompt_head": user_prompt[:200],
        }
        with open(sidecar, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


EMBED_MAX_CHARS = 1500    # 每 file embed 前 1500 字
TOP_K = 5
# 2026-04-29 校准 (bge-m3 实测) · 历史 (bge-small-zh-v1.5): 0.30 / -0.04 / 0.72
# 注: COSINE_MIN 是 query↔memory 阈值 · 跟 memory 内部 p25=0.484 不同 ·
#     query↔memory cosine 系统性更低 · m3 上短 query 跟长 memory body 一般 0.25-0.45
#     用 0.25 让相关 memory 不被无故过滤 · TODO: 跑 eval_query_recall.py 实测 p25 校准
COSINE_MIN = float(os.environ.get("ZMM_COSINE_MIN", "0.25"))
DRIFT_ALERT_THRESHOLD = float(os.environ.get("ZMM_DRIFT_THRESHOLD", "-0.032"))  # m3+hard 后 best Youden J
NEG_ANCHOR_HIT_THRESHOLD = float(os.environ.get("ZMM_NEG_HIT_THRESHOLD", "0.538"))
# v2 cutover (2026-06-01) · 弃 neg_cos≥0.538 OR 分支 · 11.5k 真流量证 64.5%→0.5%
ZMM_DRIFT_V2_THRESH = float(os.environ.get("ZMM_DRIFT_V2_THRESH", "-0.07"))
# 默认 bge-m3 · 实测 LongMemEval MRR 0.760 / Drift AUC 0.92 · ZMM_EMBEDDER_MODEL 可覆盖
_M3_LOCAL = HOME / ".cache/modelscope/hub/models/BAAI/bge-m3"
EMBEDDER_MODEL = os.environ.get(
    "ZMM_EMBEDDER_MODEL",
    str(_M3_LOCAL) if _M3_LOCAL.exists() else "BAAI/bge-m3",
)

_embedder = None    # lazy global
_anchor_cache = None   # lazy · {pos_vec, neg_vec, mtime, raw}


def _resolve_default_actor() -> str:
    """Deterministic actor ID for PoI candidate attribution.

    Order: COMPASS_AGENT_ID > CLAUDE_AGENT_ID > anon-<sha256(email|cwd)[:8]> > "unknown".
    Stable across sessions on the same user+cwd, enabling later PoI reconciliation.
    """
    env_actor = os.environ.get("COMPASS_AGENT_ID") or os.environ.get("CLAUDE_AGENT_ID")
    if env_actor:
        return env_actor
    try:
        email = subprocess.check_output(
            ["git", "config", "--get", "user.email"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).strip()
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        return "unknown"
    if not email:
        return "unknown"
    cwd = os.getcwd()
    digest = hashlib.sha256(f"{email}|{cwd}".encode("utf-8")).hexdigest()[:8]
    return f"anon-{digest}"


def find_active_project_memory_dir() -> Path | None:
    cwd = Path.cwd().resolve()
    projects_dir = HOME / ".claude" / "projects"
    if not projects_dir.exists():
        return None
    encoded_cwd = str(cwd).replace(":\\", "--").replace(":/", "--").replace("\\", "-").replace("/", "-")
    candidate = projects_dir / encoded_cwd
    if candidate.exists() and (candidate / "memory").exists():
        return candidate / "memory"
    def common_prefix_len(a: str, b: str) -> int:
        n = min(len(a), len(b))
        for i in range(n):
            if a[i] != b[i]:
                return i
        return n
    best = None
    best_score = 0
    for d in projects_dir.iterdir():
        if not d.is_dir() or not (d / "memory").exists():
            continue
        score = common_prefix_len(encoded_cwd, d.name)
        if score > best_score:
            best_score = score
            best = d
    if best and best_score >= 16:
        return best / "memory"
    return None


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
            # v1.7 · list-aware parser: empty scalar value `key:` followed by
            # indented `- item` lines accumulates into fm[key] = [...]. Plain
            # `key: value` stays scalar. Nested mappings (`- id: x`) reset state.
            cur_list_key = None
            for line in text[4:end].split("\n"):
                stripped = line.strip()
                if cur_list_key and stripped.startswith("- "):
                    item = stripped[2:].strip()
                    if ":" in item:
                        # nested mapping (e.g. contracts:) · do not treat as
                        # string list · drop out of list mode
                        cur_list_key = None
                        continue
                    item = item.strip('"').strip("'")
                    if item:
                        fm[cur_list_key].append(item)
                    continue
                if ":" in line:
                    k, _, v = line.partition(":")
                    key = k.strip()
                    val = v.strip()
                    if val == "":
                        fm[key] = []
                        cur_list_key = key
                    else:
                        fm[key] = val
                        cur_list_key = None
                else:
                    cur_list_key = None
            body = text[end + 4:].strip()
    age_seconds = time.time() - path.stat().st_mtime
    age_days = age_seconds / 86400
    if age_days < 1:
        age_str = f"{age_seconds/3600:.1f}h"
    elif age_days < 30:
        age_str = f"{int(age_days)}d"
    else:
        age_str = f"{int(age_days/30)}mo"
    # v1.7 · MEME-extension · expose new frontmatter fields for chain recall
    _dep = fm.get("depends_on", [])
    _sup = fm.get("supersedes", [])
    return {
        "name": fm.get("name", path.stem) if isinstance(fm.get("name"), str) else path.stem,
        "description": (fm.get("description", "") if isinstance(fm.get("description"), str) else "")[:120],
        "type": fm.get("type", "?") if isinstance(fm.get("type"), str) else "?",
        "age_seconds": age_seconds,
        "age_str": age_str,
        "path": path.name,
        "body": body[:1500],          # v1.0+ · for body-embed render · v0
        "embed_text": ((fm.get("description", "") if isinstance(fm.get("description"), str) else "") + "\n" + body)[:EMBED_MAX_CHARS],
        "mtime": path.stat().st_mtime,
        "fullpath": str(path),
        # v1.7 · MEME-extension fields (chain recall)
        "depends_on": _dep if isinstance(_dep, list) else [],
        "declaration_type": fm.get("declaration_type", "none") if isinstance(fm.get("declaration_type"), str) else "none",
        "supersedes": _sup if isinstance(_sup, list) else [],
    }


def get_embedder():
    global _embedder
    if _embedder is not None:
        return _embedder
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBEDDER_MODEL)
        return _embedder
    except Exception as e:
        sys.stderr.write(f"[nautilus-compass] BGE embedder unavailable: {e}\n")
        return None


def char_ngrams(text: str, n: int = 4) -> set:
    """中文字符 n-gram · 0 依赖 · 字面相似度替代 BGE."""
    text = re.sub(r"\s+", "", text or "")
    if len(text) < n:
        return {text} if text else set()
    return {text[i:i+n] for i in range(len(text) - n + 1)}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0


def get_anchor_vectors():
    """Persona Vectors L3 · cache by anchors.json mtime."""
    global _anchor_cache
    if not ANCHORS_PATH.exists():
        return None
    cur_mtime = ANCHORS_PATH.stat().st_mtime
    if _anchor_cache and _anchor_cache.get("mtime") == cur_mtime:
        return _anchor_cache
    embedder = get_embedder()
    if embedder is None:
        return None
    # cache pickle by mtime
    anc_cache_file = CACHE_DIR / "anchors.pkl"
    try:
        if anc_cache_file.exists():
            with open(anc_cache_file, "rb") as f:
                cached = pickle.load(f)
                if cached.get("mtime") == cur_mtime and cached.get("raw"):
                    # daemon 旧版 cache 没 raw · 跳过用旧的 · 重建
                    _anchor_cache = cached
                    return cached
    except Exception:
        pass
    # rebuild
    try:
        data = json.loads(ANCHORS_PATH.read_text(encoding="utf-8"))
        pos = data.get("positive_anchors", [])
        neg = data.get("negative_anchors", [])
        if not pos or not neg:
            return None
        pos_embs = [embedder.encode(s).tolist() for s in pos]
        neg_embs = [embedder.encode(s).tolist() for s in neg]
        dim = len(pos_embs[0])
        pos_vec = [sum(e[i] for e in pos_embs) / len(pos_embs) for i in range(dim)]
        neg_vec = [sum(e[i] for e in neg_embs) / len(neg_embs) for i in range(dim)]
        result = {
            "mtime": cur_mtime,
            "pos_vec": pos_vec, "neg_vec": neg_vec,
            "n_pos": len(pos), "n_neg": len(neg),
            "raw": data,
        }
        _anchor_cache = result
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(anc_cache_file, "wb") as f:
            pickle.dump(result, f)
        return result
    except Exception as e:
        sys.stderr.write(f"[nautilus-compass] anchor build failed: {e}\n")
        return None


def compute_drift(text: str, anchors: dict) -> dict:
    """drift_score = cos(text, pos) - cos(text, neg) ∈ [-1, 1] · >0 alignment · <0 偏离."""
    embedder = get_embedder()
    if not embedder or not anchors:
        return {"score": 0.0, "alignment": 0.0, "deviation": 0.0}
    try:
        emb = embedder.encode(text[:1500]).tolist()
    except Exception:
        return {"score": 0.0, "alignment": 0.0, "deviation": 0.0}
    pos = cosine(emb, anchors["pos_vec"])
    neg = cosine(emb, anchors["neg_vec"])
    return {"score": round(pos - neg, 4), "alignment": round(pos, 4), "deviation": round(neg, 4)}


def overlap_coef(query_grams: set, doc_grams: set) -> float:
    """overlap coefficient · query 中有多少 ngram 在 doc 出现 / |query|.
    适合 short query vs long doc · Jaccard 在这种长度差大时分母过大."""
    if not query_grams or not doc_grams:
        return 0.0
    inter = len(query_grams & doc_grams)
    return inter / len(query_grams)


def cosine(a, b) -> float:
    import math
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na > 0 and nb > 0 else 0.0


def load_cache(mem_dir: Path) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    proj_hash = hashlib.sha256(str(mem_dir).encode()).hexdigest()[:12]
    cache_file = CACHE_DIR / f"{proj_hash}.pkl"
    if not cache_file.exists():
        return {"path": str(cache_file), "embeddings": {}}
    try:
        with open(cache_file, "rb") as f:
            data = pickle.load(f)
            data["path"] = str(cache_file)
            return data
    except Exception:
        return {"path": str(cache_file), "embeddings": {}}


def save_cache(cache: dict) -> None:
    try:
        with open(cache["path"], "wb") as f:
            pickle.dump({"embeddings": cache["embeddings"]}, f)
    except Exception:
        pass


def build_embeddings(entries: list, cache: dict) -> dict:
    """对每个 entry · 看 cache 命中或重 embed."""
    embedder = get_embedder()
    if embedder is None:
        return {}
    embed_cache = cache.get("embeddings", {})
    updated = False
    for e in entries:
        fp = e["fullpath"]
        cached = embed_cache.get(fp)
        if cached and cached[0] == e["mtime"]:
            e["embedding"] = cached[1]
            continue
        try:
            vec = embedder.encode(e["embed_text"]).tolist()
            embed_cache[fp] = (e["mtime"], vec)
            e["embedding"] = vec
            updated = True
        except Exception:
            e["embedding"] = None
    cache["embeddings"] = embed_cache
    if updated:
        save_cache(cache)
    return cache


def is_system_injected_prompt(text: str) -> bool:
    """v0.7.1 · 检测 prompt 是不是 harness 自动注入的 system event · 不是用户真意图.

    Today's data showed 30+ false drift alerts triggered by:
      - <task-notification> XML blocks (Monitor events)
      - <system-reminder> tags (task tools reminders)
      - [Monitor event:...] markers
    These shouldn't count as user-issued prompts for drift detection.
    """
    if not text:
        return False
    markers = (
        "<task-notification>",
        "<system-reminder>",
        "[Monitor event",
        "[SYSTEM NOTIFICATION",
        "<task-id>",
        "[Monitor timed out",
    )
    head = text[:500].lower()
    return any(m.lower() in head for m in markers)


def read_user_prompt_from_stdin() -> str:
    """Claude Code hook 通过 stdin 传 JSON · 拿 prompt 字段.

    Windows fix: 强制 sys.stdin.buffer.read() UTF-8 解码 (避免 GBK surrogate).
    """
    if sys.stdin.isatty():
        return ""
    try:
        raw_bytes = sys.stdin.buffer.read()
        if not raw_bytes:
            return ""
        raw = raw_bytes.decode("utf-8", errors="replace")
        data = json.loads(raw)
        for key in ("prompt", "user_prompt", "message", "text", "content"):
            v = data.get(key)
            if v:
                # 双重 sanitize: encode UTF-8 错替换 + str 强制
                s = str(v)
                # 去 surrogate (Python 内部 unpaired \udcXX)
                s = s.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
                return s[:2000]
        return ""
    except Exception:
        return ""


def load_links() -> dict:
    """v0.5 A-MEM · 加载 links_finder.py 写的 .cache/links.json."""
    p = CACHE_DIR / "links.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _parse_session_for_lesson(f: "Path", body_chars: int) -> dict | None:
    """Parse one session_*.md · extract frontmatter + body excerpt."""
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    fm = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 4)
        if end > 0:
            for line in text[4:end].split("\n"):
                if ":" in line:
                    k, _, v = line.partition(":")
                    fm[k.strip().lower()] = v.strip()
            body = text[end+4:].strip()
    age_seconds = time.time() - f.stat().st_mtime
    age_str = (f"{age_seconds/3600:.1f}h" if age_seconds < 86400
               else f"{int(age_seconds/86400)}d")
    return {
        "path": f.name,
        "age_seconds": age_seconds,
        "age_str": age_str,
        "fm": fm,
        "body": body[:body_chars],
    }


def find_lessons_for_anchor(anchor_text: str, mem_dir: "Path",
                             max_lessons: int = 2,
                             body_chars: int = 600,
                             max_age_days: int = 60) -> list:
    """v1.0+ · v1 fix · find past sessions that relate to this anti-anchor.

    Anti-anchor alerts today say "this matches a past mistake" but never
    surface WHICH past mistake. Agent ignores the alert because investigation
    cost > guess cost. This helper embeds the actual past-mistake body so
    it lands in agent working context.

    Tiered match · falls back when narrower tier returns nothing:
      Tier 1 · substring 6-gram match against the anchor text + lesson-type
              frontmatter (concept ∈ {gotcha, problem-solution, trade-off}
              OR type ∈ {bugfix}). Most precise.
      Tier 2 · recent drift-flagged sessions (drift ∈ {yellow, red}) ·
              age ≤ max_age_days. The agent's own self-reported drift
              moments · always relevant when an anti-anchor fires.

    Returns up to max_lessons items {path, age_str, body, source} where
    source ∈ {anchor-substring, recent-drift}.
    """
    if not mem_dir or not mem_dir.is_dir():
        return []
    cutoff = time.time() - max_age_days * 86400

    # Tier 1 · substring + lesson concept
    LESSON_CONCEPTS = {"gotcha", "problem-solution", "trade-off"}
    LESSON_TYPES = {"bugfix"}
    tier1: list[dict] = []
    needle = (anchor_text or "").strip()
    grams = {needle[i:i+6] for i in range(max(1, len(needle)-5))} if len(needle) >= 6 else set()
    for f in mem_dir.glob("session_*.md"):
        try:
            if f.stat().st_mtime < cutoff:
                continue
        except Exception:
            continue
        if grams:
            try:
                if not any(g in f.read_text(encoding="utf-8", errors="ignore") for g in grams):
                    continue
            except Exception:
                continue
        else:
            continue   # no usable anchor text · skip tier 1
        info = _parse_session_for_lesson(f, body_chars)
        if not info:
            continue
        fm = info["fm"]
        if fm.get("concept", "").lower() in LESSON_CONCEPTS or fm.get("type", "").lower() in LESSON_TYPES:
            info["source"] = "anchor-substring"
            tier1.append(info)
    if tier1:
        tier1.sort(key=lambda c: c["age_seconds"])
        return tier1[:max_lessons]

    # Tier 2 · recent drift!=green sessions (the agent's own admitted slip-ups)
    tier2: list[dict] = []
    for f in mem_dir.glob("session_*.md"):
        try:
            if f.stat().st_mtime < cutoff:
                continue
        except Exception:
            continue
        info = _parse_session_for_lesson(f, body_chars)
        if not info:
            continue
        drift = info["fm"].get("drift", "").lower()
        if drift in ("yellow", "red"):
            info["source"] = f"recent-drift-{drift}"
            tier2.append(info)
    tier2.sort(key=lambda c: c["age_seconds"])
    return tier2[:max_lessons]


def render_anti_anchor_lessons(anchor_text: str, mem_dir, indent: str = "      ") -> None:
    """Print past lessons for this anti-anchor · indented under alert."""
    lessons = find_lessons_for_anchor(anchor_text, mem_dir)
    if not lessons:
        return
    src = lessons[0].get("source", "")
    label = ("上次踩过这个坑" if src == "anchor-substring"
             else f"最近你自己标了 {src} · 没修干净就别再开新洞")
    print(f"{indent}↑ {label} · 看正文:")
    for lsn in lessons:
        print(f"{indent}  📖 [{lsn['age_str']:>5} ago · {lsn.get('source','?')}] {lsn['path']}")
        body = lsn["body"].rstrip()
        for ln in body.splitlines():
            print(f"{indent}     │ {ln}")


def annotate_with_links(file_name: str, links: dict) -> str:
    """给 memory file 名加 supersede 标注 (在 metadata mode 用)."""
    if not links:
        return ""
    super_by = links.get("supersede", {}).get(file_name, [])
    if super_by:
        top = super_by[0]
        return f" ↳ superseded by {top['by']}"
    return ""


def render_v01_metadata_mode(entries: list) -> None:
    links = load_links()    # v0.5 · A-MEM 链接
    fresh = [e for e in entries if e["age_seconds"] < 86400]
    recent = [e for e in entries if 86400 <= e["age_seconds"] < 7 * 86400]
    older = [e for e in entries if e["age_seconds"] >= 7 * 86400]
    fresh.sort(key=lambda x: x["age_seconds"])
    recent.sort(key=lambda x: x["age_seconds"])
    older.sort(key=lambda x: x["age_seconds"])
    if fresh:
        print(f"🟢 当前心智 (≤24h · {len(fresh)} · **优先信任**):")
        # v1.0+ · v0 fix · top 3 fresh get body excerpt embedded so agent
        # has rule body in context · breaks the "title-only consumption" failure mode
        BODY_TOP = 3
        BODY_CHARS = 800
        for idx, e in enumerate(fresh):
            ann = annotate_with_links(e["path"], links)
            print(f"  · [{e['age_str']:>5} old] {e['path']:<40} — {e['description'][:80]}{ann}")
            if idx < BODY_TOP and e.get("body"):
                body = e["body"][:BODY_CHARS].rstrip()
                indented = "\n".join(f"      │ {ln}" for ln in body.splitlines())
                print(indented)
                if len(e.get("body","")) > BODY_CHARS:
                    print(f"      │ … (+{len(e['body'])-BODY_CHARS} more · Read {e['path']} for rest)")
    if recent:
        print(f"🟡 近期 (1-7d · {len(recent)} · 可参考):")
        for e in recent[:8]:
            ann = annotate_with_links(e["path"], links)
            print(f"  · [{e['age_str']:>5} old] {e['path']:<40} — {e['description'][:80]}{ann}")
    if older:
        print(f"🔴 历史 (>7d · {len(older)} · 别当现状):")
        for e in older[:6]:
            ann = annotate_with_links(e["path"], links)
            print(f"  · [{e['age_str']:>5} old] {e['path']:<40} — {e['description'][:60]}{ann}")
        if len(older) > 6:
            print(f"  ... +{len(older)-6} 条更老")


def transitive_close(top: list, all_entries: list, max_depth: int = 3) -> list:
    """v1.7 · MEME-extension · expand top-K with depends_on ancestors via BFS.

    Args:
        top: list of (score, entry_dict) tuples · BGE top-K cosine seeds
        all_entries: full entries list · index target for ancestor lookup
        max_depth: BFS cap (default 3 · Seokwon 32k-filler avg chain depth ~2.4)

    Returns:
        list of (score, entry) · seeds preserved + ancestors appended.
        Ancestors are NOT re-cosined · they are pinned because the seed declared
        them via `depends_on:` frontmatter field. Synthetic score = -(depth+1)
        sorts ancestors below cosine top but above fresh fallback.

    See paper/SPEC_DECLARATION_FIELD.md §3b for design rationale.
    """
    index = {e["path"]: e for e in all_entries}
    seen = {e["path"] for _, e in top}
    out = list(top)
    frontier = [(0, e) for _, e in top]
    while frontier:
        depth, e = frontier.pop(0)
        if depth >= max_depth:
            continue
        for parent_name in (e.get("depends_on") or []):
            parent = index.get(parent_name)
            if parent is None or parent["path"] in seen:
                continue
            seen.add(parent["path"])
            out.append((-(depth + 1.0), parent))
            frontier.append((depth + 1, parent))
    return out


def verify_cascade_closure(top: list, query: str = "") -> dict:
    """v1.7 · MEME-extension · MEME bench harness helper.

    Given recall top-K, verify that every `declaration_type=cascade` hit has
    all its `depends_on` ancestors also present in top. For MEME Cas scoring.

    Args:
        top: list of (score, entry_dict) tuples · recall output
        query: optional original query string (unused · reserved for logging)

    Returns:
        {"complete": bool, "missing": list[dict], "cascade_hits": int}
        · complete = True iff no missing ancestors
        · missing = [{"cascade": <path>, "missing_ancestor": <name>}, ...]
        · cascade_hits = count of cascade-typed entries in top

    Used by MEME eval harness only · not production recall path.
    See paper/SPEC_DECLARATION_FIELD.md §3c.
    """
    top_paths = {e["path"] for _, e in top}
    cascade_hits = 0
    missing = []
    for _score, e in top:
        if e.get("declaration_type") != "cascade":
            continue
        cascade_hits += 1
        for parent_name in (e.get("depends_on") or []):
            if parent_name not in top_paths:
                missing.append({
                    "cascade": e["path"],
                    "missing_ancestor": parent_name,
                })
    return {
        "complete": len(missing) == 0,
        "missing": missing,
        "cascade_hits": cascade_hits,
    }


def promote_lifecycle_tier(entry: dict, now=None) -> dict:
    """v1.7.1 · llm-wiki2 fuse · deterministic LLM-free tier promotion + forget check.

    Args:
        entry: dict with frontmatter fields · tier / decay_rate / forget_at /
               promote_after / reinforce_count / created_at (or timestamp)
        now: optional datetime (default datetime.now()) · for deterministic testing

    Returns:
        {"tier": <possibly-promoted tier>, "promoted": bool, "archived": bool,
         "reinforce_count": int}

    Rules (verbatim from paper/LLM_WIKI2_FUSE_DESIGN.md §4):
        - Rule A (access event · caller-driven): reinforce_count++ · decay_rate reset
        - Rule B (promote check):
            · promote_after "Nd"      → (now - created_at) >= N days → tier++
            · promote_after "N_access" → reinforce_count >= N → tier++
            · procedural tier (top) does NOT promote
        - Rule C (forget check):
            · forget_at != None AND now >= forget_at → archive flag

    No LLM calls. Pure schema-driven arithmetic.

    Default promote_after by tier (when entry omits explicit value):
        working    → "1_access"
        episodic   → "5_access"
        semantic   → "20_access"
        procedural → None (top)
    """
    from datetime import datetime, timedelta
    import re

    TIERS = ("working", "episodic", "semantic", "procedural")
    TIER_DEFAULTS = {
        "working": "1_access",
        "episodic": "5_access",
        "semantic": "20_access",
        "procedural": None,
    }

    if now is None:
        now = datetime.now()

    tier = entry.get("tier", "working")
    if tier not in TIERS:
        tier = "working"
    try:
        reinforce_count = int(entry.get("reinforce_count", 0) or 0)
    except (TypeError, ValueError):
        reinforce_count = 0
    promote_after = entry.get("promote_after") or TIER_DEFAULTS.get(tier)
    forget_at_str = entry.get("forget_at")
    created_at_str = entry.get("created_at") or entry.get("timestamp")

    def _parse_iso(s):
        """Parse ISO8601 · drop tz for naive comparison with `now`."""
        if not s:
            return None
        try:
            s = str(s).replace("Z", "+00:00").replace(" ", "T", 1)
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except (ValueError, TypeError):
            return None

    # Rule C · forget check
    archived = False
    forget_dt = _parse_iso(forget_at_str)
    if forget_dt is not None and now >= forget_dt:
        archived = True

    # Rule B · promote check
    promoted = False
    if promote_after and tier != "procedural":
        m_count = re.match(r"^(\d+)_access$", str(promote_after))
        m_dur = re.match(r"^(\d+)d$", str(promote_after))
        should_promote = False
        if m_count:
            threshold = int(m_count.group(1))
            if reinforce_count >= threshold:
                should_promote = True
        elif m_dur:
            days = int(m_dur.group(1))
            created_dt = _parse_iso(created_at_str)
            if created_dt is not None and (now - created_dt) >= timedelta(days=days):
                should_promote = True
        if should_promote:
            idx = TIERS.index(tier)
            if idx < len(TIERS) - 1:
                tier = TIERS[idx + 1]
                promoted = True

    return {
        "tier": tier,
        "promoted": promoted,
        "archived": archived,
        "reinforce_count": reinforce_count,
    }


def rrf_fusion(*ranked_lists, k: int = 60, top_k: int = 10,
               session_diversify: bool = True, max_per_session: int = 3) -> list:
    """v1.7.1 · Phase 2.C · Reciprocal Rank Fusion · agentmemory paradigm.

    Combine multiple ranked retrieval lists (e.g. BM25 + vector + graph) into a
    single fused ranking. Each list contributes 1/(k + rank_i + 1) to each
    item's cumulative RRF score · agentmemory verbatim default k=60.

    Args:
        *ranked_lists: each list = [(score, entry), ...] · order matters (rank = index)
                       · entry must be a dict with "path" key (unique identifier)
        k: RRF damping constant (default 60 · agentmemory verbatim)
        top_k: max items in fused output
        session_diversify: if True · cap max_per_session hits per session group
                          (agentmemory verbatim · default max=3)
        max_per_session: cap per session group when session_diversify=True

    Returns:
        [(fused_score, entry), ...] · top_k limited · session-diversified if requested

    Reference · agentmemory README (rohitg00 · 15.3K stars · LongMemEval-S 95.2% R@5)
    · "Reciprocal Rank Fusion (RRF, k=60) · session-diversified (max 3 results per session)".

    No LLM · pure rank-based arithmetic · deterministic.
    """
    from pathlib import Path as _Path

    # Identify each entry by path (unique key)
    fused_scores: dict = {}  # path → cumulative RRF score
    entry_by_path: dict = {}

    for ranked in ranked_lists:
        if not ranked:
            continue
        for rank, item in enumerate(ranked):
            # Item shape · (score, entry) tuple · or bare entry dict
            if isinstance(item, tuple) and len(item) >= 2:
                entry = item[1]
            elif isinstance(item, dict):
                entry = item
            else:
                continue
            if not isinstance(entry, dict):
                continue
            path = entry.get("path")
            if not path:
                continue
            entry_by_path[path] = entry
            # RRF formula · 1 / (k + rank + 1) · rank 0-indexed → 1-indexed for fairness
            fused_scores[path] = fused_scores.get(path, 0.0) + 1.0 / (k + rank + 1)

    # Sort by fused score desc
    sorted_paths = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

    if not session_diversify:
        return [(score, entry_by_path[path]) for path, score in sorted_paths[:top_k]]

    # Session-diversified · cap max_per_session per session group
    session_counts: dict = {}
    output: list = []
    for path, score in sorted_paths:
        entry = entry_by_path[path]
        # Session id · prefer explicit · fallback to parent directory
        session_id = entry.get("session_id") or entry.get("thread_id")
        if not session_id:
            try:
                session_id = _Path(path).parent.name
            except Exception:
                session_id = "unknown"
        if session_counts.get(session_id, 0) >= max_per_session:
            continue
        session_counts[session_id] = session_counts.get(session_id, 0) + 1
        output.append((score, entry))
        if len(output) >= top_k:
            break

    return output


def render_v02_vector_mode(entries: list, query: str, cache: dict) -> None:
    """v0.2 真 BGE 向量召回 · 没装 BGE 时直接回 metadata 模式 (n-gram 中文召回不准)."""
    embedder = get_embedder()
    if embedder is None:
        # 没装 BGE · 直接回 metadata + age 警告 (v0.1 模式) · 不做 ngram fail
        print(f"💡 装 BGE 享真语义召回: bash ~/.claude/plugins/nautilus-compass/install_bge.sh")
        print()
        render_v01_metadata_mode(entries)
        return

    cache = build_embeddings(entries, cache)
    # 强制 str + 去 None / 非 ascii control chars
    q_str = str(query or "").strip()[:2000]
    if not q_str:
        render_v01_metadata_mode(entries)
        return
    try:
        q_emb = embedder.encode(q_str).tolist()
    except Exception as e:
        sys.stderr.write(f"[nautilus-compass] query embed failed: {e!r} · query_repr={q_str[:100]!r}\n")
        render_v01_metadata_mode(entries)
        return

    # label 跟实际 embedder 同步 · m3 / small-zh / 自定义路径都对
    _model_label = Path(EMBEDDER_MODEL).name if "/" in EMBEDDER_MODEL or "\\" in EMBEDDER_MODEL else EMBEDDER_MODEL.split("/")[-1]
    scoring_method = f"BGE-{_model_label}"
    threshold = COSINE_MIN
    scored = []
    for e in entries:
        emb = e.get("embedding")
        if not emb:
            continue
        score = cosine(q_emb, emb)
        if score >= threshold:
            scored.append((score, e))

    scored.sort(key=lambda x: -x[0])
    top = scored[:TOP_K]

    # v2.0.0 · #1a · PoI ranking boost · re-rank top-K by each entry's
    # cumulative_impact frontmatter (positive → boost, negative → demote).
    # NO-OP if no memory has cumulative_impact yet (cold start fully
    # equivalent to v0.8). Set COMPASS_NO_POI_BOOST=1 to opt out.
    if os.environ.get("COMPASS_NO_POI_BOOST") != "1":
        try:
            from recall_pkg.poi_weighting import boost_top_k_with_snapshot
            from recall_pkg.poi_snapshot_cache import get_credit_snapshot
            top = boost_top_k_with_snapshot(top, get_credit_snapshot())
            # Truncate back to TOP_K after potential re-rank
            top = top[:TOP_K]
        except Exception as _e:
            sys.stderr.write(f"[PoI boost] skipped: {_e!r}\n")

    # v2.0.0 · #1b · Layer 2 L1 overlay · collapse member L0 sessions to their
    # L1 summary entry when {mem_dir}/_l1/_l1_index.json exists. Graceful
    # NO-OP if no L1 index has been built yet (preserves v0.8 path byte-for-
    # byte on cold projects). Set COMPASS_NO_L1_OVERLAY=1 to opt out.
    if os.environ.get("COMPASS_NO_L1_OVERLAY") != "1":
        try:
            from storage.l1_recall_overlay import collapse_to_l1
            _mem_dir = find_active_project_memory_dir()
            if _mem_dir is not None:
                _l1_dir = _mem_dir / "_l1"
                if (_l1_dir / "_l1_index.json").exists():
                    _before = len(top)
                    top = collapse_to_l1(top, _l1_dir, max_collapse_per_l1=1)
                    if len(top) != _before:
                        sys.stderr.write(
                            f"[L1 overlay] collapsed {_before} → {len(top)} entries\n"
                        )
        except Exception as _e:
            # Graceful · L0 path stays intact even if overlay misbehaves
            sys.stderr.write(f"[L1 overlay] skipped: {_e!r}\n")

    # v3 · B.5 · PoI candidate emission · record which memories were surfaced
    # to the actor at high confidence (no outcome yet · reconciled later when a
    # downstream PoI event lands). Distinct from emit_nau_records: candidates
    # do NOT fabricate action_outcome. Sidecar: poi_candidates.jsonl. Guarded by
    # COMPASS_NO_POI_CANDIDATE=1 for opt-out. Graceful skip on error.
    if top and os.environ.get("COMPASS_NO_POI_CANDIDATE") != "1":
        try:
            from proof.poi_emitter import emit_poi_candidate
            _actor = _resolve_default_actor()
            emit_poi_candidate(top, query=query, agent_id=_actor)
        except Exception as _e:
            sys.stderr.write(f"[PoI candidate] skipped: {_e!r}\n")

    # v1.7 · MEME-extension · transitive_close via depends_on BFS · staged rollout
    # Enable with COMPASS_CHAIN_RECALL=1 · ancestors pinned with synthetic score -depth-1
    if os.environ.get("COMPASS_CHAIN_RECALL") == "1":
        top = transitive_close(top, entries)

    if not top:
        print(f"⚠️ 无 score ≥ {threshold} 的相关 memory ({scoring_method}) · 降级 metadata")
        render_v01_metadata_mode(entries)
        return

    print(f"🎯 召回 top {len(top)} ({scoring_method} · query: {query[:60]}{'...' if len(query)>60 else ''}):")
    print()
    # v1.0+ · v0 fix · top BODY_TOP get full body excerpt to break the
    # "recall is consumption" illusion · agent now has rule body in context · no
    # extra Read tool call needed. Top BODY_TOP+1..K stay on description-only.
    BODY_TOP = 3
    BODY_CHARS = 800
    for idx, (score, e) in enumerate(top):
        flag = "🟢" if e["age_seconds"] < 86400 else ("🟡" if e["age_seconds"] < 7*86400 else "🔴")
        print(f"  {flag} score={score:.3f} · [{e['age_str']:>5} old] {e['path']}")
        if e["description"]:
            # M2 · 剥离 "真" 强调副词 · 防 dialog 风格污染下游 context (2026-05-22)
            print(f"       {strip_zhen_emphasis(e['description'][:120])}")
        if idx < BODY_TOP and e.get("body"):
            body = strip_zhen_emphasis(e["body"][:BODY_CHARS].rstrip())
            indented = "\n".join(f"       │ {ln}" for ln in body.splitlines())
            print(indented)
            if len(e.get("body","")) > BODY_CHARS:
                print(f"       │ … (+{len(e['body'])-BODY_CHARS} more · Read {e['path']} for rest)")
        print()
    # 同时附 24h 内所有 fresh memory · 不在 top 也显示 (心智优先)
    fresh_not_in_top = [
        e for e in entries
        if e["age_seconds"] < 86400 and e not in [t[1] for t in top]
    ]
    if fresh_not_in_top:
        print(f"🟢 + 24h 内其他 memory ({len(fresh_not_in_top)} · 当前心智 · 即便低 cosine 也注意):")
        for e in sorted(fresh_not_in_top, key=lambda x: x["age_seconds"]):
            desc = strip_zhen_emphasis(e['description'][:80])
            print(f"  · [{e['age_str']:>5} old] {e['path']} — {desc}")


def _expand_query(query: str) -> str:
    """v1.7 #4 · query expansion · 命中 synonym 就追加 · 提升 BGE recall.

    保守 · 只追加最多 8 个 token · 避免 query 过长稀释 embedding.
    fail-soft · 任何异常返原 query.
    """
    try:
        syn_path = Path(__file__).resolve().parent / "query_synonyms.json"
        if not syn_path.exists():
            return query
        synonyms = json.loads(syn_path.read_text(encoding="utf-8"))
        added = []
        ql = query.lower()
        for key, vals in synonyms.items():
            if key.startswith("_"):
                continue
            if key.lower() in ql:
                for v in vals:
                    if v.lower() not in ql and v not in added:
                        added.append(v)
                        if len(added) >= 8:
                            break
            if len(added) >= 8:
                break
        if not added:
            return query
        return query + " | " + " ".join(added)
    except Exception:
        return query


def try_daemon_recall(mem_dir: Path, user_prompt: str) -> bool:
    """尝试连 daemon · 拿 recall+drift · 输出后返 True · 失败返 False.

    timeout 60s · daemon 首次 recall 时正在 load BGE (~30s) · 之后秒回.
    """
    import socket as _socket
    project = mem_dir.parent.name
    expanded_prompt = _expand_query(user_prompt)
    try:
        with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
            s.settimeout(60.0)
            s.connect(("127.0.0.1", 9876))
            req = {"action": "both", "query": expanded_prompt[:2000],
                   "project": project, "top_k": TOP_K}
            s.sendall(json.dumps(req, ensure_ascii=False).encode("utf-8") + b"\n")
            buf = b""
            while b"\n" not in buf:
                chunk = s.recv(65536)
                if not chunk: break
                buf += chunk
            line, _, _ = buf.partition(b"\n")
            data = json.loads(line.decode("utf-8"))
        if not data.get("ok"):
            sys.stderr.write(f"[nautilus-compass daemon] err: {data.get('error')}\n")
            return False
        # 渲染 daemon 响应
        d = data.get("drift")
        # v0.7.1 · system-injected prompt 跳过 drift 输出 (避免假报)
        if d and is_system_injected_prompt(user_prompt):
            d = None
        if d:
            tag = "✅ 在锚点内" if d["score"] > 0.05 and not d["should_alert"] \
                else ("⚠️ 偏向反锚点" if d["should_alert"] else "≈ 中性")
            print(f"[Persona drift · {d['n_pos']}+{d['n_neg']} 锚点 · BGE · daemon]")
            print(f"  score={d['score']:+.3f} (alignment={d['alignment']:.3f} · "
                  f"deviation={d['deviation']:.3f}) · {tag}")
            # v0.7 修 · log_usage 不再漏: drift_score 整体偏移也算 alert
            # 旧: 只在 top_neg_hits 非空时 log · 漏掉 score < -0.04 但单 anchor 没命中的 case
            if d["should_alert"]:
                # v0.7.1 · 给 alert 一个 ID · 用户 feedback CLI 引用
                import hashlib as _h
                _alert_id = "a-" + _h.sha256(
                    f"{user_prompt[:200]}{time.time()}".encode("utf-8")
                ).hexdigest()[:8]
                if d.get("rule_hit"):
                    print(f"  🔴 alert [{_alert_id}]: 危险动作 rule 命中 "
                          f"(rm -rf / force push / reset --hard / DROP / 硬编码 key 等)")
                    print(f"  ↑ 确认这是有意操作再继续 · 误报标 FP: nautilus-compass feedback {_alert_id} fp")
                    log_usage("drift_alert", {
                        "alert_id": _alert_id,
                        "score": d["score"], "max_neg_hit": 0,
                        "neg_anchor": "",
                        "kind": "rule_hit",
                        "user_prompt": user_prompt[:300],
                    })
                elif d["top_neg_hits"]:
                    print(f"  🔴 alert [{_alert_id}]: 最匹配的反锚点 (你历史犯过的错):")
                    for sc, txt in d["top_neg_hits"]:
                        print(f"    · cos={sc:.3f}  '{txt}'")
                    # v1.0+ · v1 · embed past-mistake body so alert is actionable
                    try:
                        top_anchor_text = d["top_neg_hits"][0][1]
                        render_anti_anchor_lessons(top_anchor_text, mem_dir, indent="  ")
                    except Exception:
                        pass
                    print(f"  ↑ 跟'我历史的错'高重合 · 标 FP: nautilus-compass feedback {_alert_id} fp")
                    log_usage("drift_alert", {
                        "alert_id": _alert_id,
                        "score": d["score"], "max_neg_hit": d["top_neg_hits"][0][0],
                        "neg_anchor": d["top_neg_hits"][0][1][:80],
                        "kind": "single_anchor_hit",
                        "user_prompt": user_prompt[:300],
                    })
                else:
                    # drift_score 整体偏移触发 · 但没单 anchor 命中
                    print(f"  🔴 alert [{_alert_id}]: drift_score={d['score']:+.3f} 整体偏向反锚点云")
                    print(f"  ↑ 标 FP: nautilus-compass feedback {_alert_id} fp")
                    log_usage("drift_alert", {
                        "alert_id": _alert_id,
                        "score": d["score"], "max_neg_hit": 0,
                        "neg_anchor": "",
                        "kind": "score_threshold",
                        "user_prompt": user_prompt[:300],
                    })

                # v1.7.0 · 方向 3 D6-7 · drift mitigation prompt-inject
                # alert fire 时不只显示 · 给真行动引导 + 日志 act-on 跟踪
                print()
                print(f"  🟢 mitigation hint [{_alert_id}]:")
                print(f"     1. 先 acknowledge 这次 drift · 别假装没看见 score")
                print(f"     2. Pivot 回 reference reply 方向 · 翻一条 score>+0.05 的 session 看真口径")
                print(f"     3. 若真 FP(我误报)· `nautilus-compass feedback {_alert_id} fp` 真标 · 不要忍着不标")
                print(f"     4. 行动后下次 stop_hook 自动 log act-on · D13 看真 act-on rate (target ≥70%)")
                _log_drift_mitigation(_alert_id, d, user_prompt)
            print()
        recall = data.get("recall") or []
        if recall:
            log_usage("recall_hit", {
                "n": len(recall), "top_score": recall[0]["score"],
                "top_path": recall[0]["path"],
            })
        if recall:
            _model_label = Path(EMBEDDER_MODEL).name if ("/" in EMBEDDER_MODEL or "\\" in EMBEDDER_MODEL) else EMBEDDER_MODEL.split("/")[-1]
            print(f"🎯 召回 top {len(recall)} (BGE-{_model_label} · daemon · query: {user_prompt[:60]}{'...' if len(user_prompt)>60 else ''}):")
            print()
            for r in recall:
                age_s = r.get("age_seconds", 0)
                flag = "🟢" if age_s < 86400 else ("🟡" if age_s < 7*86400 else "🔴")
                print(f"  {flag} score={r['score']:.3f} · [{r['age_str']:>5} old] {r['path']}")
                if r.get("description"):
                    print(f"       {r['description'][:120]}")
            fresh_extra = data.get("fresh_extra") or []
            if fresh_extra:
                print()
                print(f"🟢 + 24h 内其他 memory ({len(fresh_extra)} · 当前心智 · 即便低 cosine 也注意):")
                for e in fresh_extra:
                    print(f"  · [{e['age_str']:>5} old] {e['path']} — {e['description'][:80]}")

        # L2 metamemory · 自知层:fires on empty OR weak recall · the
        # hallucinate-absence cure — tells the subject LLM when compass has no
        # reliable evidence so it does not fabricate a "prior finding".
        # Deterministic by default (no LLM · black-box moat). Never breaks recall.
        try:
            from metamemory import build_recall_result, format_metamemory_notice
            _rr = build_recall_result(user_prompt, recall or [])
            _notice = format_metamemory_notice(_rr)
            if _notice:
                print()
                print(_notice)
        except Exception as _e:
            sys.stderr.write(f"[L2 metamemory] skipped: {_e!r}\n")

        # L3 PoI candidate emission · ALSO fire on the daemon recall path. The
        # inline path (render_v02_vector_mode) already emits, but production
        # recall goes through the daemon, so without this candidates never land
        # → poi_candidates.jsonl stays empty → L3 has 0 events to reconcile.
        # Adapts the daemon recall dict-list to the (score, entry) shape.
        # Guarded by COMPASS_NO_POI_CANDIDATE=1. Never breaks recall.
        try:
            if recall and os.environ.get("COMPASS_NO_POI_CANDIDATE") != "1":
                from proof.poi_emitter import emit_poi_candidate
                _top = [(r.get("score", 0.0), r) for r in recall]
                emit_poi_candidate(_top, query=user_prompt, agent_id=_resolve_default_actor())
        except Exception as _e:
            sys.stderr.write(f"[PoI candidate · daemon] skipped: {_e!r}\n")
        return True
    except Exception as e:
        sys.stderr.write(f"[nautilus-compass daemon] unreachable ({e}) · fallback inline\n")
        return False


def main():
    # v0.7 · auto-promote to BGE mode if daemon alive (默认 hook 也走 daemon)
    # 旧 (v0.6 及前): hook 默认只 metadata · daemon 跑了 12 天 0 次被调 · drift/recall 全空
    # 新 (v0.7): hook 入口先 ping daemon · alive 就用 BGE (1.8s) · 不 alive 才 fallback metadata
    bge_mode = "--bge" in sys.argv
    if not bge_mode:
        try:
            import socket as _sk0
            with _sk0.socket(_sk0.AF_INET, _sk0.SOCK_STREAM) as _s0:
                _s0.settimeout(2.0)   # 2026-04-29: 0.3s 太短 · m3 cold load 完成后还在 anchor pkl 重建会被误判 unreachable
                _s0.connect(("127.0.0.1", 9876))
                _s0.sendall(b'{"action":"ping"}\n')
                if b'"pong"' in _s0.recv(1024):
                    bge_mode = True   # daemon alive · 升级 BGE
        except Exception:
            pass

    mem_dir = find_active_project_memory_dir()
    if not mem_dir:
        return 0

    files = sorted(mem_dir.glob("*.md"))
    entries = []
    # v1.7 #1+#5 · importance gate + archived_at decay
    # · gate keeps high-signal types in recall · plain session 流水 only kept if drift!=green
    # · archived_at: 30d+ files demoted unless query has '历史/曾经/旧/archive/old'
    raw_user_prompt = ""
    try:
        # peek without consuming · we only need keywords for gate decision
        import os as _os
        raw_user_prompt = _os.environ.get("COMPASS_QUERY_PEEK", "")
    except Exception:
        pass
    archive_keywords = ("历史", "曾经", "曾", "旧", "archive", "old", "history")
    want_archived = any(k in raw_user_prompt for k in archive_keywords) if raw_user_prompt else False

    HIGH_SIGNAL_TYPES = {"bugfix", "fix", "feature", "feedback", "reference",
                         "decision", "discovery", "trade-off", "problem-solution",
                         "gotcha", "pattern"}
    n_dropped_noise = 0
    n_dropped_archived = 0
    for f in files:
        if f.name.upper() in ("MEMORY.MD", "INDEX.MD"):
            continue
        info = parse_memory_file(f)
        if not info:
            continue
        # gate · drop plain green session 流水 unless they're high-signal types
        ftype = (info.get("type") or "").lower()
        # parse drift from frontmatter (re-read · cheap on small files)
        try:
            text_head = Path(info["fullpath"]).read_text(encoding="utf-8")[:2000]
            drift_val = ""
            for ln in text_head.split("\n"):
                if ln.startswith("drift:"):
                    drift_val = ln.split(":", 1)[1].strip().lower()
                    break
        except Exception:
            drift_val = ""
        # v1.7 #1 · session_*.md 必须 drift=red 才进 recall index
        # · 96% session 标 green/yellow · LLM 自评太松 · 不能用 type 区分
        # · feedback_*/reference_*/anchor_* 等非 session 文件全保留
        if f.name.startswith("session_") and drift_val != "red":
            n_dropped_noise += 1
            continue
        # v1.7 #5 · archived_at 衰减 · 30d+ session 也 drop · 除非 query 含历史词
        age_days = info.get("age_seconds", 0) / 86400
        if age_days > 30 and not want_archived and f.name.startswith("session_"):
            n_dropped_archived += 1
            continue
        entries.append(info)
    if not entries:
        return 0

    # v0.7 修 · 升级 bge_mode 也要读 stdin · 不然 daemon recall 永远不被打
    if bge_mode and "--query" in sys.argv:
        idx = sys.argv.index("--query")
        user_prompt = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
    else:
        # hook 走 stdin · v0.7 不再因为 bge_mode 跳过读取
        user_prompt = read_user_prompt_from_stdin()

    print(f"<nautilus-compass-recall plugin={PLUGIN_VERSION}>")
    print(f"Project memory: {mem_dir.parent.name} · {len(entries)} entries")
    print(f"⚠️ 时间戳 = 关键 · 用户心智在迭代 · 不要用 7d+ 旧 memory 倒批今天判断")

    # v1.8.0 · 用户战略 anchor 强制压头 · 长 session stance 衰减唯一真解
    # 不靠 BGE 相似度命中(可能不命中) · 任何 query 都强制 surface
    # · anchor_user_strategic_compass.md 7 条 stance
    # · anchor_anti_patterns_history.md 10 大复发模式
    try:
        anchor_home = Path.home() / ".claude" / "projects" / "C--Users-chunx" / "memory"
        for anchor_name, label in [
            ("anchor_user_strategic_compass.md", "📌 用户战略 anchor · 7 条 stance"),
            ("anchor_anti_patterns_history.md", "🔴 anti-pattern · 10 复发模式"),
        ]:
            anchor_path = anchor_home / anchor_name
            if not anchor_path.exists():
                continue
            text = anchor_path.read_text(encoding="utf-8", errors="replace")
            # Extract h1 + h2 titles only · 不展开正文(避免 prompt 头臃肿)
            titles = []
            for ln in text.splitlines():
                s = ln.strip()
                if s.startswith("## ") and len(titles) < 12:
                    titles.append(s[3:].strip())
            print()
            print(f"[{label}]")
            for t in titles[:10]:
                print(f"  · {t}")
            print(f"  → 全文: {anchor_path.name} · 第 1 个 response 必含 'active anchor: X / Y'")
    except Exception as _ae:
        sys.stderr.write(f"[nautilus-compass] anchor surface fail: {_ae}\n")

    # v1.7 #2 · numeric_claims cross-ref · query 含数字时检查历史冲突
    try:
        from numeric_claims import cross_ref as _nc_cross_ref
        _nc_alerts = _nc_cross_ref(user_prompt) if user_prompt else []
        if _nc_alerts:
            print()
            print("[Numeric drift · 反幻觉 hook]")
            for _a in _nc_alerts[:5]:
                print(f"  {_a}")
    except Exception:
        pass

    # v1.7.0 · 方向 2 D3-4 · cross-agent contract surface
    # 把 outstanding (deadline 未到) + expired (未消费过期) 注入 prompt 头
    # · sweep 168h · 不阻塞 recall · fail-soft
    try:
        from contract import (
            scan_sessions_for_contracts, _default_memory_roots,
            format_for_prompt_injection,
        )
        # 5/31 reconcile: 168→720h · 兑现 D.fix-3 意图(历史 close-loop 文件 >7d 也 resolve)
        _c_scan = scan_sessions_for_contracts(_default_memory_roots(), within_hours=720.0)
        _c_block = format_for_prompt_injection(_c_scan, max_show=5)
        if _c_block:
            print()
            print("[Cross-agent contracts · close_loop hook]")
            print(_c_block)
    except Exception:
        pass
    print()

    # v0.4 · Strategy lookup (hook 默认就跑 · 0 BGE · 关键词命中即可)
    if user_prompt:
        try:
            from strategy_store import StrategyStore
            ss = StrategyStore()
            strat_text = ss.render_for_prompt(user_prompt, max_chars=800)
            if strat_text:
                print(strat_text)
                print()
                log_usage("strategy_hit", {
                    "n_chars": len(strat_text),
                    "query": user_prompt[:80],
                })
        except Exception as _se:
            sys.stderr.write(f"[nautilus-compass] strategy lookup fail: {_se}\n")

    # v0.7.1 · 跳过 system-injected prompt 的 drift 计算 (recall 仍跑 · 只 drift 跳过)
    skip_drift = is_system_injected_prompt(user_prompt)
    if skip_drift:
        log_usage("drift_skip_system_event", {"prompt_head": user_prompt[:80]})

    # v0.3 · Persona drift · BGE 模式下 · daemon alive 时跳过 inline (避免双重 BGE load)
    daemon_alive = False
    if user_prompt and bge_mode and not skip_drift:
        try:
            import socket as _sk
            with _sk.socket(_sk.AF_INET, _sk.SOCK_STREAM) as s:
                s.settimeout(2.0)   # 2026-04-29: 同上 · 跟 line 543 一致
                s.connect(("127.0.0.1", 9876))
                s.sendall(b'{"action":"ping"}\n')
                if b'"pong"' in s.recv(1024):
                    daemon_alive = True
        except Exception:
            pass

    # daemon alive · 把 drift 留给 daemon 渲染 (避免 inline BGE load 浪费 30s)
    if user_prompt and bge_mode and not daemon_alive:
        anchors = get_anchor_vectors()
        if anchors:
            d = compute_drift(user_prompt, anchors)
            sig = d["score"]
            # 触发 alert 的 2 个条件之一: 整体偏反锚点 OR 单条反锚点命中很高
            embedder = get_embedder()
            q_emb = embedder.encode(user_prompt[:1500]).tolist() if embedder else None
            top_neg_hits = []
            if q_emb:
                neg_anchors = anchors["raw"].get("negative_anchors", [])
                for s in neg_anchors:
                    a_emb = embedder.encode(s).tolist()
                    top_neg_hits.append((cosine(q_emb, a_emb), s))
                top_neg_hits.sort(reverse=True)
            max_neg_hit = top_neg_hits[0][0] if top_neg_hits else 0.0
            # v2 cutover · 弃 max_neg_hit≥0.538 OR(逢触必报)· daemon-dead fallback 用 V2 阈值
            # (5/31 reconcile: active firing 统一 v2 · should_fire_drift 模块保留作未来 A/B)
            should_alert = sig < ZMM_DRIFT_V2_THRESH
            tag = "✅ 在锚点内" if sig > 0.05 and not should_alert else ("⚠️ 偏向反锚点" if should_alert else "≈ 中性")
            print(f"[Persona drift · {anchors['n_pos']}+{anchors['n_neg']} 锚点 · BGE]")
            print(f"  score={sig:+.3f} (alignment={d['alignment']:.3f} · deviation={d['deviation']:.3f}) · {tag}")
            if should_alert and top_neg_hits:
                print(f"  🔴 alert: 最匹配的反锚点 (你历史犯过的错 · max_hit={max_neg_hit:.3f}):")
                for sc, s in top_neg_hits[:3]:
                    print(f"    · cos={sc:.3f}  '{s}'")
                # v1.0+ · v1 · embed past-mistake body so alert is actionable
                try:
                    render_anti_anchor_lessons(top_neg_hits[0][1], mem_dir, indent="  ")
                except Exception:
                    pass
                print(f"  ↑ 当前 prompt 跟这些'我历史的错' 高重合 · 注意别再犯")
            print()

    if user_prompt and bge_mode:
        # 优先尝试 daemon (< 1s) · 不行 fallback inline (~30s cold)
        if try_daemon_recall(mem_dir, user_prompt):
            print(f"</nautilus-compass-recall>")
            return 0
        cache = load_cache(mem_dir)
        render_v02_vector_mode(entries, user_prompt, cache)
    else:
        # hook 默认 · 只 metadata (快) · 提示装/调 BGE
        render_v01_metadata_mode(entries)
        if user_prompt:
            print()
            # v0.7.2 · daemon down 时显眼警告 · 不再 silent fallback
            print("🚨 BGE daemon DOWN · 你看到的是 metadata 列表 · 不是真语义召回")
            print("   启动: nohup python ~/.claude/plugins/nautilus-compass/daemon.py > /tmp/compass_daemon.log 2>&1 &")
            print("   验证: nautilus-compass-recall 块出现 'BGE-bge-m3 · daemon · query:' 才是真召回")
            # v0.7.2 加固 (A): metadata fallback 也 log_usage · 即使 daemon down 也保留事件足迹
            log_usage("metadata_fallback", {
                "n_entries": len(entries),
                "user_prompt": user_prompt[:200],
                "reason": "bge_mode=False (daemon down or --bge not passed)",
            })

    print(f"</nautilus-compass-recall>")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"nautilus-compass recall error (silenced): {e}\n")
        sys.exit(0)

#!/usr/bin/env python3
"""V5 Memory Plugin · UserPromptSubmit hook · v0.2 真 BGE 向量召回.

输入: stdin JSON {"hook_event_name":"UserPromptSubmit", "prompt":"<user msg>", ...}
若 prompt 拿到: 真 BGE embed · top 5 cosine 相关 memory 段 + age 分组
若 prompt 拿不到: 降级 v0.1 metadata 模式

cache: ~/.claude/plugins/zenmind-mem/.cache/<proj_hash>.pkl
  · {file_path: (mtime, embedding_list)}
  · file mtime 变 → 重 embed 那个 file
  · 总 cache miss = 第一次 cold start (1-2s)
  · warm = 100ms

R1: 修 stub claude-mem 不实时校准 → 真 BGE 召回
"""
import hashlib
import io
import json
import os
import pickle
import re
import sys
import time
from pathlib import Path

# Force UTF-8 stdout (Windows GBK)
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass

PLUGIN_VERSION = "zenmind-mem v0.6"
HOME = Path.home()
PLUGIN_DIR = HOME / ".claude" / "plugins" / "zenmind-mem"
CACHE_DIR = PLUGIN_DIR / ".cache"
USAGE_LOG = CACHE_DIR / "usage.jsonl"


def _select_anchors_path() -> "Path":
    """v0.6 · cwd → profile auto-select."""
    cwd = str(Path.cwd()).lower().replace("\\", "/")
    if "quantum-buddha" in cwd or "zenmind" in cwd:
        p = PLUGIN_DIR / "anchors_zenmind.json"
        if p.exists():
            return p
    if "venture" in cwd or "creative-daily" in cwd:
        p = PLUGIN_DIR / "anchors_vc.json"
        if p.exists():
            return p
    return PLUGIN_DIR / "anchors.json"


ANCHORS_PATH = _select_anchors_path()


def log_usage(event: str, payload: dict) -> None:
    """v0.6 · KPI 日志: drift_alert / strategy_hit / recall_hit · 给 audit 用."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "event": event, "anchors_profile": ANCHORS_PATH.name,
               "cwd": str(Path.cwd()), **payload}
        with open(USAGE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
EMBED_MAX_CHARS = 1500    # 每 file embed 前 1500 字
TOP_K = 5
COSINE_MIN = 0.30
DRIFT_ALERT_THRESHOLD = -0.04    # 整体偏反锚点至少 0.04 才 alert (减 false positive)
NEG_ANCHOR_HIT_THRESHOLD = 0.72   # 单条反锚点 cosine ≥ 0.72 才 alert (中文 BGE 高相关阈值)
EMBEDDER_MODEL = "BAAI/bge-small-zh-v1.5"

_embedder = None    # lazy global
_anchor_cache = None   # lazy · {pos_vec, neg_vec, mtime, raw}


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
            for line in text[4:end].split("\n"):
                if ":" in line:
                    k, _, v = line.partition(":")
                    fm[k.strip()] = v.strip()
            body = text[end + 4:].strip()
    age_seconds = time.time() - path.stat().st_mtime
    age_days = age_seconds / 86400
    if age_days < 1:
        age_str = f"{age_seconds/3600:.1f}h"
    elif age_days < 30:
        age_str = f"{int(age_days)}d"
    else:
        age_str = f"{int(age_days/30)}mo"
    return {
        "name": fm.get("name", path.stem),
        "description": fm.get("description", "")[:120],
        "type": fm.get("type", "?"),
        "age_seconds": age_seconds,
        "age_str": age_str,
        "path": path.name,
        "embed_text": (fm.get("description", "") + "\n" + body)[:EMBED_MAX_CHARS],
        "mtime": path.stat().st_mtime,
        "fullpath": str(path),
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
        sys.stderr.write(f"[zenmind-mem] BGE embedder unavailable: {e}\n")
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
        sys.stderr.write(f"[zenmind-mem] anchor build failed: {e}\n")
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
        for e in fresh:
            ann = annotate_with_links(e["path"], links)
            print(f"  · [{e['age_str']:>5} old] {e['path']:<40} — {e['description'][:80]}{ann}")
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


def render_v02_vector_mode(entries: list, query: str, cache: dict) -> None:
    """v0.2 真 BGE 向量召回 · 没装 BGE 时直接回 metadata 模式 (n-gram 中文召回不准)."""
    embedder = get_embedder()
    if embedder is None:
        # 没装 BGE · 直接回 metadata + age 警告 (v0.1 模式) · 不做 ngram fail
        print(f"💡 装 BGE 享真语义召回: bash ~/.claude/plugins/zenmind-mem/install_bge.sh")
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
        sys.stderr.write(f"[zenmind-mem] query embed failed: {e!r} · query_repr={q_str[:100]!r}\n")
        render_v01_metadata_mode(entries)
        return

    scoring_method = "BGE-bge-small-zh"
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

    if not top:
        print(f"⚠️ 无 score ≥ {threshold} 的相关 memory ({scoring_method}) · 降级 metadata")
        render_v01_metadata_mode(entries)
        return

    print(f"🎯 召回 top {len(top)} ({scoring_method} · query: {query[:60]}{'...' if len(query)>60 else ''}):")
    print()
    for score, e in top:
        # 标 fresh/old · 帮我判断是不是当前心智
        flag = "🟢" if e["age_seconds"] < 86400 else ("🟡" if e["age_seconds"] < 7*86400 else "🔴")
        print(f"  {flag} score={score:.3f} · [{e['age_str']:>5} old] {e['path']}")
        if e["description"]:
            print(f"       {e['description'][:120]}")
    print()
    # 同时附 24h 内所有 fresh memory · 不在 top 也显示 (心智优先)
    fresh_not_in_top = [
        e for e in entries
        if e["age_seconds"] < 86400 and e not in [t[1] for t in top]
    ]
    if fresh_not_in_top:
        print(f"🟢 + 24h 内其他 memory ({len(fresh_not_in_top)} · 当前心智 · 即便低 cosine 也注意):")
        for e in sorted(fresh_not_in_top, key=lambda x: x["age_seconds"]):
            print(f"  · [{e['age_str']:>5} old] {e['path']} — {e['description'][:80]}")


def try_daemon_recall(mem_dir: Path, user_prompt: str) -> bool:
    """尝试连 daemon · 拿 recall+drift · 输出后返 True · 失败返 False.

    timeout 60s · daemon 首次 recall 时正在 load BGE (~30s) · 之后秒回.
    """
    import socket as _socket
    project = mem_dir.parent.name
    try:
        with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
            s.settimeout(60.0)
            s.connect(("127.0.0.1", 9876))
            req = {"action": "both", "query": user_prompt[:2000],
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
            sys.stderr.write(f"[zenmind-mem daemon] err: {data.get('error')}\n")
            return False
        # 渲染 daemon 响应
        d = data.get("drift")
        if d:
            tag = "✅ 在锚点内" if d["score"] > 0.05 and not d["should_alert"] \
                else ("⚠️ 偏向反锚点" if d["should_alert"] else "≈ 中性")
            print(f"[Persona drift · {d['n_pos']}+{d['n_neg']} 锚点 · BGE · daemon]")
            print(f"  score={d['score']:+.3f} (alignment={d['alignment']:.3f} · "
                  f"deviation={d['deviation']:.3f}) · {tag}")
            if d["should_alert"] and d["top_neg_hits"]:
                print(f"  🔴 alert: 最匹配的反锚点 (你历史犯过的错):")
                for sc, txt in d["top_neg_hits"]:
                    print(f"    · cos={sc:.3f}  '{txt}'")
                print(f"  ↑ 当前 prompt 跟这些'我历史的错' 高重合 · 注意别再犯")
                log_usage("drift_alert", {
                    "score": d["score"], "max_neg_hit": d["top_neg_hits"][0][0],
                    "neg_anchor": d["top_neg_hits"][0][1][:80],
                })
            print()
        recall = data.get("recall") or []
        if recall:
            log_usage("recall_hit", {
                "n": len(recall), "top_score": recall[0]["score"],
                "top_path": recall[0]["path"],
            })
        if recall:
            print(f"🎯 召回 top {len(recall)} (BGE-bge-small-zh · daemon · query: {user_prompt[:60]}{'...' if len(user_prompt)>60 else ''}):")
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
        return True
    except Exception as e:
        sys.stderr.write(f"[zenmind-mem daemon] unreachable ({e}) · fallback inline\n")
        return False


def main():
    # 默认 hook 模式 = metadata only (快 · <100ms)
    # BGE 模式 = CLI 显式 --bge query · Claude 主动调用
    bge_mode = "--bge" in sys.argv

    mem_dir = find_active_project_memory_dir()
    if not mem_dir:
        return 0

    files = sorted(mem_dir.glob("*.md"))
    entries = []
    for f in files:
        if f.name.upper() in ("MEMORY.MD", "INDEX.MD"):
            continue
        info = parse_memory_file(f)
        if info:
            entries.append(info)
    if not entries:
        return 0

    if bge_mode and "--query" in sys.argv:
        idx = sys.argv.index("--query")
        user_prompt = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
    else:
        # hook 走 stdin · 但默认不调 BGE (太慢) · 只 metadata + drift (不调 query embed)
        user_prompt = read_user_prompt_from_stdin() if not bge_mode else ""

    print(f"<zenmind-mem-recall plugin={PLUGIN_VERSION}>")
    print(f"Project memory: {mem_dir.parent.name} · {len(entries)} entries")
    print(f"⚠️ 时间戳 = 关键 · 用户心智在迭代 · 不要用 7d+ 旧 memory 倒批今天判断")
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
            sys.stderr.write(f"[zenmind-mem] strategy lookup fail: {_se}\n")

    # v0.3 · Persona drift · BGE 模式下 · daemon alive 时跳过 inline (避免双重 BGE load)
    daemon_alive = False
    if user_prompt and bge_mode:
        try:
            import socket as _sk
            with _sk.socket(_sk.AF_INET, _sk.SOCK_STREAM) as s:
                s.settimeout(0.5)
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
            should_alert = sig < DRIFT_ALERT_THRESHOLD or max_neg_hit >= NEG_ANCHOR_HIT_THRESHOLD
            tag = "✅ 在锚点内" if sig > 0.05 and not should_alert else ("⚠️ 偏向反锚点" if should_alert else "≈ 中性")
            print(f"[Persona drift · {anchors['n_pos']}+{anchors['n_neg']} 锚点 · BGE]")
            print(f"  score={sig:+.3f} (alignment={d['alignment']:.3f} · deviation={d['deviation']:.3f}) · {tag}")
            if should_alert and top_neg_hits:
                print(f"  🔴 alert: 最匹配的反锚点 (你历史犯过的错 · max_hit={max_neg_hit:.3f}):")
                for sc, s in top_neg_hits[:3]:
                    print(f"    · cos={sc:.3f}  '{s}'")
                print(f"  ↑ 当前 prompt 跟这些'我历史的错' 高重合 · 注意别再犯")
            print()

    if user_prompt and bge_mode:
        # 优先尝试 daemon (< 1s) · 不行 fallback inline (~30s cold)
        if try_daemon_recall(mem_dir, user_prompt):
            print(f"</zenmind-mem-recall>")
            return 0
        cache = load_cache(mem_dir)
        render_v02_vector_mode(entries, user_prompt, cache)
    else:
        # hook 默认 · 只 metadata (快) · 提示装/调 BGE
        render_v01_metadata_mode(entries)
        if user_prompt:
            print()
            print(f"💡 想要真语义召回 · Bash 调:")
            print(f"   python3 ~/.claude/plugins/zenmind-mem/recall.py --bge --query \"<问题>\"")

    print(f"</zenmind-mem-recall>")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"zenmind-mem recall error (silenced): {e}\n")
        sys.exit(0)

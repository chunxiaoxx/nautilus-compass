#!/usr/bin/env python3
"""V5 Memory Plugin · BGE Daemon · keep model loaded · TCP IPC.

启动: bash ~/.claude/plugins/zenmind-mem/daemon_start.sh
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
import io
import json
import os
import pickle
import re
import socket
import sys
import threading
import time
from pathlib import Path

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
except Exception:
    pass

HOST = "127.0.0.1"
PORT = 9876
PLUGIN_DIR = Path.home() / ".claude" / "plugins" / "zenmind-mem"
CACHE_DIR = PLUGIN_DIR / ".cache"
ANCHORS_PATH = PLUGIN_DIR / "anchors.json"
PID_FILE = CACHE_DIR / "daemon.pid"
LOG_FILE = CACHE_DIR / "daemon.log"
EMBEDDER_MODEL = "BAAI/bge-small-zh-v1.5"
EMBED_MAX_CHARS = 1500
TOP_K = 5
COSINE_MIN = 0.30
DRIFT_ALERT_THRESHOLD = -0.04
NEG_ANCHOR_HIT_THRESHOLD = 0.72


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
    # 优先 API embedder (秒级) · 没 key 才 fallback BGE (30s)
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        log("using Gemini API embedder · 250ms/call")
        _state["embedder"] = _APIEmbedder(gemini_key)
        return _state["embedder"]
    log("loading BGE model · ~30s ...")
    t0 = time.time()
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDER_MODEL)
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


def get_anchors():
    if not ANCHORS_PATH.exists():
        return None
    cur_mtime = ANCHORS_PATH.stat().st_mtime
    if _state["anchor_cache"] and _state["anchor_cache"]["mtime"] == cur_mtime:
        return _state["anchor_cache"]
    embedder = get_embedder()
    def _enc(s):
        v = embedder.encode(s)
        return v.tolist() if hasattr(v, "tolist") else v
    try:
        data = json.loads(ANCHORS_PATH.read_text(encoding="utf-8"))
        pos = data.get("positive_anchors", [])
        neg = data.get("negative_anchors", [])
        if not pos or not neg: return None
        pos_embs = [_enc(s) for s in pos]
        neg_embs = [_enc(s) for s in neg]
        dim = len(pos_embs[0])
        pos_vec = [sum(e[i] for e in pos_embs)/len(pos_embs) for i in range(dim)]
        neg_vec = [sum(e[i] for e in neg_embs)/len(neg_embs) for i in range(dim)]
        result = {"mtime":cur_mtime, "pos_vec":pos_vec, "neg_vec":neg_vec,
                  "n_pos":len(pos), "n_neg":len(neg),
                  "neg_anchors":neg, "neg_embs":neg_embs,
                  "raw": data}
        _state["anchor_cache"] = result
        with open(CACHE_DIR / "anchors.pkl", "wb") as f:
            pickle.dump(result, f)
        return result
    except Exception as e:
        log(f"anchor build fail: {e}")
        return None


def handle_request(req: dict) -> dict:
    action = req.get("action", "both")
    query = (req.get("query") or "").strip()[:2000]
    project = req.get("project", "")
    top_k = int(req.get("top_k") or TOP_K)
    if not query:
        return {"ok": False, "error": "empty query"}

    # 找 mem_dir
    if project:
        mem_dir = Path.home() / ".claude" / "projects" / project / "memory"
        if not mem_dir.exists():
            return {"ok": False, "error": f"no memory dir for {project}"}
    else:
        return {"ok": False, "error": "project required"}

    with _state["lock"]:
        embedder = get_embedder()
        try:
            v = embedder.encode(query)
            q_emb = v.tolist() if hasattr(v, "tolist") else v
        except Exception as e:
            return {"ok": False, "error": f"query embed fail: {e}"}

        result = {"ok": True, "project": project, "query": query[:80]}

        if action in ("recall", "both"):
            entries = get_memory_entries(mem_dir)
            scored = []
            for e in entries:
                if not e.get("embedding"): continue
                s = cosine(q_emb, e["embedding"])
                if s >= COSINE_MIN:
                    scored.append((s, e))
            scored.sort(key=lambda x: -x[0])
            top = scored[:top_k]
            result["recall"] = [
                {"score": round(s, 3), "path": e["path"],
                 "age_str": e["age_str"], "age_seconds": e["age_seconds"],
                 "description": e["description"]}
                for s, e in top
            ]
            # fresh memories not in top
            fresh_extra = [
                e for e in entries
                if e["age_seconds"] < 86400 and e not in [t[1] for t in top]
            ]
            result["fresh_extra"] = [
                {"path": e["path"], "age_str": e["age_str"],
                 "description": e["description"]}
                for e in sorted(fresh_extra, key=lambda x: x["age_seconds"])
            ]

        if action in ("drift", "both"):
            anchors = get_anchors()
            if anchors:
                pos_cos = cosine(q_emb, anchors["pos_vec"])
                neg_cos = cosine(q_emb, anchors["neg_vec"])
                drift_score = round(pos_cos - neg_cos, 4)
                # 单 anchor hits
                neg_hits = []
                for a_emb, a_text in zip(anchors["neg_embs"], anchors["neg_anchors"]):
                    s = cosine(q_emb, a_emb)
                    if s >= NEG_ANCHOR_HIT_THRESHOLD:
                        neg_hits.append((round(s,3), a_text))
                neg_hits.sort(reverse=True)
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
        return result


def serve():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    log(f"daemon starting PID={os.getpid()} port={PORT}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((HOST, PORT))
    except OSError as e:
        log(f"bind fail · already running? {e}")
        sys.exit(2)
    sock.listen(8)
    log(f"listening {HOST}:{PORT}")

    while True:
        try:
            conn, addr = sock.accept()
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"accept fail: {e}")
            continue
        threading.Thread(target=handle_conn, args=(conn,), daemon=True).start()

    sock.close()
    if PID_FILE.exists():
        PID_FILE.unlink(missing_ok=True)
    log("daemon stopped")


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

#!/usr/bin/env python3
"""R133 · patch COMPASS_EMBED_ENABLED gate into cloud daemon_v33.py"""
from pathlib import Path
import shutil
import time
import py_compile

src = Path("/home/ubuntu/nautilus-compass/daemon_v33.py")
bak = Path("/home/ubuntu/nautilus-compass/daemon_v33.py.bak_r133_embed_off")
if not bak.exists():
    shutil.copy2(src, bak)
text = src.read_text()
if "COMPASS_EMBED_ENABLED=0 · skip local BGE" in text:
    print("already patched")
else:
    old1 = """def get_embedder():
    if _state["embedder"] is not None:
        return _state["embedder"]
    with _EMBEDDER_LOCK:  # v3.2 · listen 前置后 handler 可并发触发 load,防重复加载
        if _state["embedder"] is not None:
            return _state["embedder"]
        # 2026-04-28 · 用户强制不用 gemini · 永远只 BGE local (隐私 + 不依赖外部 API)
"""
    new1 = """def get_embedder():
    if _state["embedder"] is not None:
        return _state["embedder"]
    with _EMBEDDER_LOCK:  # v3.2 · listen 前置后 handler 可并发触发 load,防重复加载
        if _state["embedder"] is not None:
            return _state["embedder"]
        # R133 · COMPASS_EMBED_ENABLED=0 跳过本地 BGE(第四犯缓解;recall 走 pkl+BM25)
        _en = os.environ.get("COMPASS_EMBED_ENABLED", "1").strip().lower()
        if _en in ("0", "false", "off", "no"):
            class _DisabledEmbedder:
                def encode(self, text, **kwargs):
                    raise RuntimeError("COMPASS_EMBED_ENABLED=0 · local BGE skipped")
            log("COMPASS_EMBED_ENABLED=0 · skip local BGE (recall pkl+BM25)")
            _state["embedder"] = _DisabledEmbedder()
            return _state["embedder"]
        # 2026-04-28 · 用户强制不用 gemini · 永远只 BGE local (隐私 + 不依赖外部 API)
"""
    old2 = """        log("warmup(thread): eager-loading bge-m3 + anchors...")
        _t0 = time.time()
        _ = get_embedder()
        log(f"  embedder ready · {time.time()-_t0:.1f}s")
        _t1 = time.time()
        _ = get_anchors()
        log(f"  anchors ready · {time.time()-_t1:.1f}s")
"""
    new2 = """        _en = os.environ.get("COMPASS_EMBED_ENABLED", "1").strip().lower()
        if _en in ("0", "false", "off", "no"):
            log("warmup(thread): COMPASS_EMBED_ENABLED=0 · skip BGE/anchors")
            _state["embedder"] = get_embedder()  # disabled stub
        else:
            log("warmup(thread): eager-loading bge-m3 + anchors...")
            _t0 = time.time()
            _ = get_embedder()
            log(f"  embedder ready · {time.time()-_t0:.1f}s")
            _t1 = time.time()
            _ = get_anchors()
            log(f"  anchors ready · {time.time()-_t1:.1f}s")
"""
    if old1 not in text:
        raise SystemExit("old1 not found")
    if old2 not in text:
        raise SystemExit("old2 not found")
    text = text.replace(old1, new1, 1).replace(old2, new2, 1)
    src.write_text(text)
py_compile.compile(str(src), doraise=True)
print("patched+compiled ok bak=", bak, "mtime", time.ctime(src.stat().st_mtime))
print("gate count", src.read_text().count("COMPASS_EMBED_ENABLED"))

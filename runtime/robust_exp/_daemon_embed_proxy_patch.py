#!/usr/bin/env python3
"""v3.3.5 patch · _BGEWrapper.embed proxy(R303 切换):
env COMPASS_EMBED_PROXY 时 encode 走 A100 GPU 嵌入服务(经反向隧道),失败回退本地 CPU。
bytes 级 LF/CRLF 双变体幂等。在 cloud 上运行。"""
import sys
from pathlib import Path

P = Path('/home/ubuntu/nautilus-compass/daemon_v33.py')
src = P.read_bytes()
MARK = 'embed proxy fail, fallback local'.encode()

ANCHOR = '''        class _BGEWrapper:
            def encode(self, text, **kwargs):
                _state["last_embed"] = time.time()  # 2026-09-30 idle-unload 时间戳
                v = model.encode(text)
                return v if isinstance(v, np.ndarray) else np.asarray(v, dtype=np.float32)'''.encode()

PATCH = '''        class _BGEWrapper:
            def encode(self, text, **kwargs):
                _state["last_embed"] = time.time()  # 2026-09-30 idle-unload 时间戳
                _px = os.environ.get("COMPASS_EMBED_PROXY")
                if _px:  # v3.3.5 · GPU 嵌入代理(A100 bge-m3,吞吐x100);失败回退本地
                    try:
                        import urllib.request as _u
                        _single = isinstance(text, str)
                        _texts = [text] if _single else list(text)
                        _body = json.dumps({"texts": _texts}).encode()
                        _r = json.loads(_u.urlopen(_u.Request(
                            _px.rstrip("/") + "/embed", _body,
                            {"Content-Type": "application/json"}), timeout=30).read())
                        _vecs = np.asarray(_r["embeddings"], dtype=np.float32)
                        return _vecs[0] if _single else _vecs
                    except Exception as _e:
                        log(f"embed proxy fail, fallback local: {_e}")
                v = model.encode(text)
                return v if isinstance(v, np.ndarray) else np.asarray(v, dtype=np.float32)'''.encode()

if MARK in src:
    print('patch v3.3.5: marker present, skip'); sys.exit(0)

def dual(anchor_lf):
    if src.count(anchor_lf) == 1:
        return anchor_lf, 'lf'
    crlf = anchor_lf.replace(b'\n', b'\r\n')
    if src.count(crlf) == 1:
        return crlf, 'crlf'
    return None, None

a, eol = dual(ANCHOR)
if a is None:
    print('patch v3.3.5: anchor not found, abort'); sys.exit(1)
patch = PATCH if eol == 'lf' else PATCH.replace(b'\n', b'\r\n')
P.write_bytes(src.replace(a, patch, 1))
print(f'patch v3.3.5: applied ({eol})')

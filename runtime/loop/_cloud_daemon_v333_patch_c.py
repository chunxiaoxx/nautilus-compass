#!/usr/bin/env python3
"""v3.3.3 patch C (2026-10-06 深夜 · R266): chunk_embs ndarray truth guard.
Root cause of residual "chunk recall fusion fail": `for cv in e.get("chunk_embs") or ()`
evaluates truth on an ndarray (legacy pkl stored 2D/empty arrays) -> numpy ambiguous
ValueError BEFORE patch-B guard line is ever reached. Locally reproduced, all four
shapes verified (empty-1D/2D/0-d/None). Idempotent, LF/CRLF dual variant.
"""
from pathlib import Path
import sys

P = Path("/home/ubuntu/nautilus-compass/daemon_v33.py")
src = P.read_bytes()
MARK = "chunk-embs ndarray truth guard (v3.3.3 C)"

def _b(t): return t.encode("utf-8")

ANCHOR = _b("""                    best = -1.0
                    for cv in e.get("chunk_embs") or ():
                        s = cosine(q_emb, cv)""")
PATCH = _b("""                    best = -1.0
                    _embs = e.get("chunk_embs")
                    if _embs is None:
                        _embs = ()
                    elif isinstance(_embs, np.ndarray):
                        _embs = _embs.tolist() if _embs.ndim >= 1 else ()  # chunk-embs ndarray truth guard (v3.3.3 C)
                    for cv in _embs:
                        s = cosine(q_emb, cv)""")

if _b(MARK) in src:
    print("patch C: marker present, skip"); sys.exit(0)
def _match(anchor_lf):
    if src.count(anchor_lf) == 1: return anchor_lf, "lf"
    crlf = anchor_lf.replace(b"\n", b"\r\n")
    if src.count(crlf) == 1: return crlf, "crlf"
    return None, None

anchor, eol = _match(ANCHOR)
if anchor is None:
    print("patch C: anchor not found, abort"); sys.exit(1)
patch = PATCH if eol == "lf" else PATCH.replace(b"\n", b"\r\n")
P.write_bytes(src.replace(anchor, patch, 1))
print(f"patch C: applied ({eol})")

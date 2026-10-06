#!/usr/bin/env python3
"""v3.3.3 cloud daemon patch (2026-10-06 · R263) · bytes edition.
A) pre-work liveness check in _safe_handle (useless-work storm root fix) — LF segment.
B) chunk-fusion array guard (bool-ambiguous root fix) — CRLF segment (mixed EOL file).
Idempotent: skips a patch whose marker already exists.
"""
from pathlib import Path
import sys

P = Path("/home/ubuntu/nautilus-compass/daemon_v33.py")
src = P.read_bytes()

def _b(text: str) -> bytes:
    return text.encode("utf-8")

MARK_A = _b("liveness: client FIN'd in queue · skip compute (v3.3.3)")
MARK_B = _b("v3.3.3 batch-emb guard")

ANCHOR_A = _b("""    try:
        handle_conn(conn)
    finally:""")
PATCH_A = _b("""    try:
        _skip = False
        try:
            conn.settimeout(0)
            try:
                _peek = conn.recv(1, socket.MSG_PEEK)
            except (BlockingIOError, socket.timeout):
                _peek = b"?"   # no data yet · assume alive
            if _peek == b"":
                _skip = True
        except Exception:
            pass
        finally:
            try: conn.settimeout(60)
            except Exception: pass
        if _skip:
            log("liveness: client FIN'd in queue · skip compute (v3.3.3)")
            return   # outer finally closes conn + releases sem
        handle_conn(conn)
    finally:""")

_anchor_b_lf = """                    for cv in e.get("chunk_embs") or ():
                        s = cosine(q_emb, cv)
                        if s > best:
                            best = s"""
_patch_b_lf = """                    for cv in e.get("chunk_embs") or ():
                        s = cosine(q_emb, cv)
                        if not isinstance(s, (int, float)):
                            s = float(np.max(np.asarray(s)))  # v3.3.3 batch-emb guard
                        if s > best:
                            best = s"""
ANCHOR_B = _b(_anchor_b_lf)
PATCH_B = _b(_patch_b_lf)


def _match_eol(src: bytes, anchor_lf: bytes):
    """Whole file is one EOL flavor: try LF, then CRLF. Return (anchor, patch)
    re-encoded to the flavor that matches, or (None, None)."""
    if src.count(anchor_lf) == 1:
        return anchor_lf, "lf"
    crlf = anchor_lf.replace(b"\n", b"\r\n")
    if src.count(crlf) == 1:
        return crlf, "crlf"
    return None, None

assert b"import numpy as np" in src, "numpy import missing"

for name, mark, anchor_lf, patch_lf in (
    ("A", MARK_A, ANCHOR_A, PATCH_A),
    ("B", MARK_B, ANCHOR_B, PATCH_B),
):
    if mark in src:
        print(f"patch {name}: marker present, skip")
        continue
    anchor, eol = _match_eol(src, anchor_lf)
    if anchor is None:
        print(f"patch {name}: anchor not found (LF/CRLF), abort")
        sys.exit(1)
    patch = patch_lf if eol == "lf" else patch_lf.replace(b"\n", b"\r\n")
    src = src.replace(anchor, patch, 1)
    print(f"patch {name}: applied ({eol})")

P.write_bytes(src)
print("done")

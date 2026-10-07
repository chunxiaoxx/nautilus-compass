#!/usr/bin/env python3
"""M5 三件套移植 daemon_v33.py(R322):四锚 bytes 双 EOL patch。
只移植三件套(不带 PORT env 化 hunk——v33 已有 systemd 端口)。"""
import sys
from pathlib import Path

P = Path('/home/ubuntu/nautilus-compass/daemon_v33.py')
src = P.read_bytes()
MARK = b'v2.5 #48 memgate trio'

A1 = b'''        "forget_at": fm.get("forget_at", ""),'''
P1 = A1 + b'''
        # v2.5 #48 memgate trio 1/3 fact_status gate
        "fact_status": fm.get("fact_status", ""),
        "verified_at": fm.get("verified_at", ""),'''

FUNCS = b'''# v2.5 #48 memgate trio 2/3+3/3: dedup_check + chain expand
_WIKI_LINK_RE = None
_DEDUP_MERGE_DEFAULT = 0.9
_DEDUP_GRAY_DEFAULT = 0.75
_CHAIN_CAP_DEFAULT = 5


def _wiki_link_re():
    global _WIKI_LINK_RE
    if _WIKI_LINK_RE is None:
        import re
        _WIKI_LINK_RE = re.compile(r"\\[\\[([^\\[\\]\\|#]+?)\\]\\]")
    return _WIKI_LINK_RE


def dedup_verdict(q_emb, entries, t_merge=_DEDUP_MERGE_DEFAULT,
                  t_gray=_DEDUP_GRAY_DEFAULT):
    hits = []
    for e in entries:
        emb = e.get("embedding")
        if not emb:
            continue
        s = cosine(q_emb, emb)
        if s >= t_gray:
            hits.append({"path": e["path"], "score": round(float(s), 4)})
    hits.sort(key=lambda h: -h["score"])
    if hits and hits[0]["score"] >= t_merge:
        verdict = "merge"
    elif hits:
        verdict = "gray"
    else:
        verdict = "unique"
    return {"ok": True, "verdict": verdict, "hits": hits[:5],
            "thresholds": {"merge": t_merge, "gray": t_gray}}


def _handle_dedup_check(req):
    text = (req.get("text") or "").strip()[:8000]
    project = (req.get("project") or "").strip()
    if not text:
        return {"ok": False, "error": "empty text"}
    if not project:
        return {"ok": False, "error": "project required"}
    mem_dir = Path.home() / ".claude" / "projects" / project / "memory"
    if not mem_dir.exists():
        return {"ok": True, "verdict": "unique", "hits": []}
    try:
        embedder = get_embedder()
        v = embedder.encode(text)
        q_emb = v.tolist() if hasattr(v, "tolist") else v
    except Exception as e:
        return {"ok": False, "error": f"embed failed: {e}"}
    entries = get_memory_entries(mem_dir)
    return dedup_verdict(q_emb, entries,
                         float(req.get("threshold_merge", _DEDUP_MERGE_DEFAULT)),
                         float(req.get("threshold_gray", _DEDUP_GRAY_DEFAULT)))


def _stem(p):
    return p[:-3] if p.endswith(".md") else p


def expand_chain_links(top, all_entries, cap=_CHAIN_CAP_DEFAULT):
    index = {}
    for e in all_entries:
        if e.get("name"):
            index.setdefault(e["name"], e)
        index.setdefault(_stem(e["path"]), e)
    top_keys = set()
    for _s, e in top:
        if e.get("name"):
            top_keys.add(e["name"])
        top_keys.add(_stem(e["path"]))
    seen = set()
    out = []
    for _s, e in top:
        text = (e.get("description") or "") + "\\n" + (e.get("body") or "")
        for m in _wiki_link_re().findall(text):
            name = m.strip()
            if not name or name in top_keys:
                continue
            target = index.get(name)
            if target is None:
                continue
            t_key, t_name = _stem(target["path"]), target.get("name", "")
            if t_key in seen or t_name in seen:
                continue
            seen.add(t_key)
            if t_name:
                seen.add(t_name)
            out.append({"path": target["path"], "name": t_name,
                        "description": target.get("description", ""),
                        "fact_status": target.get("fact_status", ""),
                        "via": e["path"]})
            if len(out) >= cap:
                return out
    return out

'''

A2 = b'def handle_request(req: dict) -> dict:'

A3 = b'''             "description": e["description"],'''
P3 = A3 + b'''
             "fact_status": e.get("fact_status", ""),'''
A3B = b'''        # fresh memories not in top'''
P3B = b'''        try:
            result["chain_extra"] = expand_chain_links(top, all_entries)
        except Exception as _ce:
            log(f"chain expand fail skip: {_ce}")
''' + A3B

A4 = b'''        _t0 = time.time()
        resp = handle_request(req)'''
P4 = b'''        if req.get("action") == "dedup_check":
            resp_bytes = json.dumps(_handle_dedup_check(req), ensure_ascii=False).encode("utf-8") + b"\\n"
            conn.sendall(resp_bytes)
            return
''' + A4


def dual(anchor):
    if src.count(anchor) == 1:
        return anchor, b'lf'
    c = anchor.replace(b'\n', b'\r\n')
    if src.count(c) == 1:
        return c, b'crlf'
    return None, None


if MARK in src:
    print('already applied'); sys.exit(0)

n_applied = 0
for a, p in ((A1, P1), (A3, P3), (A3B, P3B), (A4, P4)):
    anch, eol = dual(a)
    if anch is None:
        print(f'FAIL anchor: {a[:40]!r} count={src.count(a)}'); sys.exit(1)
    patch = p if eol == b'lf' else p.replace(b'\n', b'\r\n')
    src = src.replace(anch, patch, 1)
    n_applied += 1

anch2, eol2 = dual(A2)
if anch2 is None:
    print('FAIL A2 handle_request'); sys.exit(1)
f = FUNCS if eol2 == b'lf' else FUNCS.replace(b'\n', b'\r\n')
src = src.replace(anch2, f + anch2, 1)
n_applied += 1

P.write_bytes(src)
print(f'applied {n_applied}/5 hunks')

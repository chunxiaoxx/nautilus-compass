"""Patch script · in-place adds v1.4 BGE adapter to compass_http_v09.py.

Strategy:
  1. Insert helper function _call_v14_daemon near top (after imports)
  2. Replace drift_check function body: forward to v1.4 daemon, fallback jaccard
  3. Append /v1/v14/recall and /v1/v14/ingest_obs routes (A2)

Idempotent · won't double-patch.
"""
import sys
import re
from pathlib import Path

TARGET = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/ubuntu/compass/compass_http_v09.py")
src = TARGET.read_text(encoding="utf-8")

if "_call_v14_daemon" in src:
    print("ALREADY PATCHED · skipping"); sys.exit(0)

# ─── Step 1 · insert helper after imports ──────────────────────────
HELPER = '''
# ─── v1.4 BGE-m3 adapter · injected 2026-05-11 ─────────────────────
import socket as _v14_socket
import json as _v14_json
import os as _v14_os

_V14_HOST = _v14_os.environ.get("COMPASS_BGE_HOST", "127.0.0.1")
_V14_PORT = int(_v14_os.environ.get("COMPASS_BGE_PORT", "9876"))
_V14_ANCHORS = _v14_os.environ.get(
    "COMPASS_V14_ANCHORS",
    "/home/ubuntu/nautilus-compass/anchors_compass_marketing.json"
)
_V14_DEFAULT_PROJECT = _v14_os.environ.get("COMPASS_V14_PROJECT", "C--Users-chunx")
_V14_TIMEOUT_S = float(_v14_os.environ.get("COMPASS_V14_TIMEOUT_S", "8.0"))


def _call_v14_daemon(req, timeout=None):
    """Forward request to v1.4 BGE daemon (TCP localhost:9876). Returns None on failure."""
    t = timeout if timeout is not None else _V14_TIMEOUT_S
    try:
        s = _v14_socket.socket()
        s.settimeout(t)
        s.connect((_V14_HOST, _V14_PORT))
        s.sendall((_v14_json.dumps(req) + "\\n").encode("utf-8"))
        buf = b""
        while True:
            c = s.recv(65536)
            if not c: break
            buf += c
            if buf.endswith(b"\\n"): break
        s.close()
        d = _v14_json.loads(buf.decode("utf-8", errors="replace").strip())
        return d if d.get("ok") else None
    except Exception:
        return None


def _v14_drift_check(prompt, tenant):
    """v1.4 BGE-m3 + real anchors. Returns v0.9-compatible response shape or None."""
    req = {
        "action": "drift",
        "query": (prompt or "")[:2000],
        "project": _V14_DEFAULT_PROJECT,
        "agent_type": tenant or "unknown",
        "anchors_path": _V14_ANCHORS,
    }
    d = _call_v14_daemon(req)
    if not d:
        return None
    drift = d.get("drift") or {}
    return {
        "score": round(float(drift.get("deviation", 0.0)), 3),
        "alignment": round(float(drift.get("alignment", 1.0)), 3),
        "deviation": round(float(drift.get("deviation", 0.0)), 3),
        "should_alert": bool(drift.get("should_alert", False)),
        "top_neg_hits": [
            {"text": txt, "cos": cos}
            for cos, txt in (drift.get("top_neg_hits") or [])
        ],
        "note": "v1.4 BGE-m3 · " + _V14_ANCHORS.rsplit("/", 1)[-1],
        "backend": "v1.4-bge-m3",
    }
# ─── end v1.4 adapter ─────────────────────────────────────────────
'''

# Insert BEFORE the rate-limiting middleware section (clean spot after app setup)
ANCHOR = "# ---- Rate limiting middleware"
idx_a = src.find(ANCHOR)
if idx_a < 0:
    print("ERR · cannot locate rate-limiting anchor"); sys.exit(1)
src = src[:idx_a] + HELPER + "\n\n" + src[idx_a:]

# ─── Step 2 · replace drift_check with v1.4-first version ─────────
OLD_DRIFT_MARKER = '@app.post("/v1/drift_check")\ndef drift_check('
NEW_DRIFT_HEADER = '''@app.post("/v1/drift_check")
def drift_check(
    body: dict,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None),
):
    """v1.4 adapter (2026-05-11) · BGE-m3 daemon primary · jaccard fallback.

    Wire-compatible with V5/V6/Kairos compass_client.py. Returns same shape:
    {score, alignment, deviation, should_alert, top_neg_hits, note}.
    """
    prompt = (body or {}).get("prompt", "")
    if not isinstance(prompt, str) or len(prompt.strip()) < 5:
        return {"score": 0.0, "alignment": 1.0, "deviation": 0.0,
                "should_alert": False, "top_neg_hits": []}

    user_id = x_tenant_id or x_user_id
    if authorization and authorization.startswith("Bearer "):
        try:
            from jose import jwt
            payload = jwt.decode(authorization[7:], JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("user_id") or user_id
        except Exception:
            pass

    # PRIMARY · v1.4 BGE-m3 + real anchors
    v14 = _v14_drift_check(prompt, user_id or "unknown")
    if v14 is not None:
        return v14

    # FALLBACK · legacy jaccard (resilience if daemon down or cold-loading)
    if not user_id:
        raise HTTPException(401, "auth required (X-Tenant-ID or X-User-ID or Bearer)")
'''

idx = src.find(OLD_DRIFT_MARKER)
if idx < 0:
    print("ERR · cannot locate drift_check function"); sys.exit(1)

# find end of function · next "\n\n@app" or "\n\n@" or end-of-file
end_marker = src.find("\n\n@app", idx + 10)
if end_marker < 0:
    end_marker = len(src)

old_fn = src[idx:end_marker]
# splice point: AFTER the auth-error block (HTTPException raise) · keep jaccard body as fallback
# Look for the line: raise HTTPException(401, "auth required ...")
auth_re = re.search(r'raise HTTPException\(401, "auth required[^"]*"\)\n', old_fn)
if not auth_re:
    print("ERR · cannot locate auth check in old drift_check"); sys.exit(1)
post_auth = old_fn[auth_re.end():]  # jaccard implementation
new_fn = NEW_DRIFT_HEADER + post_auth

src = src[:idx] + new_fn + src[end_marker:]

# ─── Step 3 · append A2 routes ──────────────────────────────────────
A2_ROUTES = '''

# ─── A2 · v1.4 BGE direct routes (recall + ingest_obs) · 2026-05-11 ──
@app.get("/v1/v14/recall")
def v14_recall(
    q: str,
    top_k: int = 5,
    scope: str = "project",
    project: Optional[str] = None,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
):
    """v1.4 BGE-m3 recall · scope=project (default) or scope=user (cross-project)."""
    req = {
        "action": "recall",
        "query": (q or "")[:2000],
        "top_k": int(top_k),
        "scope": scope,
        "agent_type": x_tenant_id or "unknown",
    }
    if project:
        req["project"] = project
    d = _call_v14_daemon(req, timeout=15.0)
    if not d:
        return {"ok": False, "error": "v14 daemon unreachable",
                "backend": "v1.4-bge-m3"}
    return {
        "ok": True,
        "scope": d.get("scope", scope),
        "projects_scanned": d.get("projects_scanned", []),
        "hits": d.get("recall", []),
        "fresh_extra": d.get("fresh_extra", []),
        "backend": "v1.4-bge-m3",
    }


@app.post("/v1/v14/ingest_obs")
def v14_ingest_obs(
    body: dict,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
):
    """v1.4 ingest observation · forwards to BGE daemon.

    Body: {content, thread_id?, thread_role?, project?, tags?}
    """
    content = (body or {}).get("content", "")
    if not isinstance(content, str) or len(content.strip()) < 10:
        return {"ok": False, "error": "content too short (min 10 chars)"}
    req = {
        "action": "ingest_obs",
        "content": content[:8000],
        "thread_id": (body or {}).get("thread_id"),
        "thread_role": (body or {}).get("thread_role"),
        "project": (body or {}).get("project") or _V14_DEFAULT_PROJECT,
        "tags": (body or {}).get("tags") or [],
        "agent_type": x_tenant_id or "unknown",
    }
    d = _call_v14_daemon(req, timeout=15.0)
    if not d:
        return {"ok": False, "error": "v14 daemon unreachable",
                "backend": "v1.4-bge-m3"}
    return {
        "ok": d.get("ok", False),
        "session_path": d.get("path") or d.get("session_path"),
        "backend": "v1.4-bge-m3",
    }
# ─── end v1.4 routes ───────────────────────────────────────────────
'''

src = src.rstrip() + "\n" + A2_ROUTES + "\n"

TARGET.write_text(src, encoding="utf-8")
print(f"PATCHED · {TARGET}")
print("  + _call_v14_daemon helper")
print("  + drift_check → v1.4 primary · jaccard fallback")
print("  + GET /v1/v14/recall")
print("  + POST /v1/v14/ingest_obs")

"""Fix /v1/v14/ingest_obs in compass_http_v09.py · write session_*.md directly.

Previous version forwarded to daemon (which has no ingest_obs action · dead route).
This patch:
  · removes daemon forward
  · writes session_*.md directly to ~/.claude/projects/<project>/memory/
  · accepts cited_snippets + recall_id from client · writes to frontmatter
  · still soft-fail · never 500

Idempotent · checks for marker.
"""
from __future__ import annotations
import sys
import re
from pathlib import Path

TARGET = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/ubuntu/compass/compass_http_v09.py")
src = TARGET.read_text(encoding="utf-8")

MARKER = "# ─── v14_ingest_obs · session_*.md writer · 2026-05-11"
if MARKER in src:
    print("ALREADY PATCHED · skipping"); sys.exit(0)

OLD = '''@app.post("/v1/v14/ingest_obs")
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
    }'''


NEW = '''# ─── v14_ingest_obs · session_*.md writer · 2026-05-11 ──────────────
# Previous version forwarded to daemon · daemon has no ingest_obs action.
# Now writes session_*.md directly to ~/.claude/projects/<project>/memory/.
@app.post("/v1/v14/ingest_obs")
def v14_ingest_obs(
    body: dict,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
):
    """v1.4 ingest observation · writes session_*.md directly.

    Body fields (all str unless noted):
      content (required, ≥10 char)    · main body text
      name (optional, default first 30 chars of content)
      description (optional)
      drift (optional · green/yellow/red · default green)
      thread_id (optional)            · for thread_recall pairing
      thread_role (optional · outbound/inbound/self_note)
      project (optional · default C--Users-chunx)
      tags (optional list[str])
      recall_id (optional)            · self-reported proof-of-recall claim
      cited_snippets (optional list)  · self-reported snippet citations
    """
    import re as _re_v14
    from datetime import datetime as _dt_v14
    from pathlib import Path as _P_v14

    content = (body or {}).get("content", "")
    if not isinstance(content, str) or len(content.strip()) < 10:
        return {"ok": False, "error": "content too short (min 10 chars)"}

    agent_type = (x_tenant_id or x_user_id or "unknown")[:60]
    project = (body or {}).get("project") or _V14_DEFAULT_PROJECT
    name = ((body or {}).get("name") or content[:30].strip())[:80]
    description = ((body or {}).get("description") or content[:200])[:200]
    drift = (body or {}).get("drift") or "green"
    if drift not in ("green", "yellow", "red"):
        drift = "green"
    thread_id = ((body or {}).get("thread_id") or "").strip()
    thread_role = ((body or {}).get("thread_role") or "").strip()
    if thread_role and thread_role not in ("outbound", "inbound", "self_note"):
        thread_role = "self_note"
    tags = (body or {}).get("tags") or []
    if not isinstance(tags, list):
        tags = []

    # self-reported proof-of-recall (v1.5)
    recall_id = ((body or {}).get("recall_id") or "").strip()
    cited_snippets = (body or {}).get("cited_snippets") or []
    if not isinstance(cited_snippets, list):
        cited_snippets = []
    if recall_id or cited_snippets:
        proof_of_recall = "self_reported_pass" if cited_snippets else "self_reported_no_cite"
    else:
        proof_of_recall = "not_attempted"

    # write session_*.md
    ts = _dt_v14.now().strftime("%Y%m%d-%H%M")
    slug = _re_v14.sub(r"[^\\w一-鿿]+", "-", name).strip("-")[:30] or "obs"
    home = _P_v14(_v14_os.path.expanduser("~ubuntu"))
    out_dir = home / ".claude" / "projects" / project / "memory"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return {"ok": False, "error": f"cannot create memory dir: {e}",
                "backend": "v1.4-http-adapter"}

    fname = f"session_{ts}_{slug}.md"
    out_file = out_dir / fname

    tags_yaml = "[]" if not tags else "[" + ", ".join(f'"{t}"' for t in tags) + "]"
    thread_lines = ""
    if thread_id:
        thread_lines = f"\\nthread_id: {thread_id}\\nthread_role: {thread_role or 'self_note'}"
    proof_lines = f"\\nproof_of_recall: {proof_of_recall}"
    if recall_id:
        proof_lines += f"\\nrecall_id: {recall_id}"
    if cited_snippets:
        cited_yaml = "[" + ", ".join(f'"{c[:100]}"' for c in cited_snippets[:5]) + "]"
        proof_lines += f"\\ncited_snippets: {cited_yaml}"

    md = f"""---
name: {name}
description: {description}
type: discovery
drift: {drift}
agent_type: {agent_type}
ingested_via: v14_http_adapter
tags: {tags_yaml}{thread_lines}{proof_lines}
---

# {name}

{content[:8000]}
"""
    try:
        out_file.write_text(md, encoding="utf-8")
    except Exception as e:
        return {"ok": False, "error": f"write fail: {e}",
                "backend": "v1.4-http-adapter"}

    return {
        "ok": True,
        "session_path": str(out_file),
        "session_name": fname,
        "agent_type": agent_type,
        "proof_of_recall": proof_of_recall,
        "backend": "v1.4-http-adapter",
    }'''

if OLD not in src:
    print("ERR · old v14_ingest_obs body not found · cannot patch"); sys.exit(1)

src = src.replace(OLD, NEW)
TARGET.write_text(src, encoding="utf-8")
print(f"PATCHED · {TARGET}")
print("  + v14_ingest_obs writes session_*.md directly · soft-fail safe")
print("  + accepts recall_id + cited_snippets · writes proof_of_recall to frontmatter")
print("  + accepts X-User-ID alongside X-Tenant-ID")

"""Idempotent incremental patch · adds PoI candidate emission to the live
`/v1/v14/recall` route in cloud compass_http_v09.py.

Does NOT touch the existing v14 adapter patch (that one is idempotent-skip).
Self-contained inline emit (no `proof` import — not on this server's path).

Usage on cloud:
  python3 ops/patch_v14_recall_poi_candidate.py /home/ubuntu/compass/compass_http_v09.py
"""
import sys
from pathlib import Path

GUARD = "_v14_emit_poi_candidate"

# The exact helper deployed into the server. Tested verbatim via exec in
# tests/test_v14_poi_emission_patch.py (namespace supplies _v14_os, _v14_json).
EMIT_HELPER = '''def _v14_emit_poi_candidate(hits, query, agent_id, project):
    """Self-contained PoI candidate emission for the v14 recall path.
    One JSONL line per hit -> poi_candidates.jsonl (schema matches
    proof/poi_emitter: ts/kind/actor/project/memory/query_hash/rank/score).
    No proof import (not on this server path) · no self-cite suppression
    (cited memory files are not local to this cloud host). Never raises."""
    if not hits:
        return 0
    import hashlib as _hl
    from datetime import datetime as _dt, timezone as _tz
    # NOTE default MUST be a systemd ReadWritePaths dir · the service runs with
    # ProtectHome=read-only + ProtectSystem=strict, so /home/ubuntu/compass is
    # read-only · writes there fail silently. /var/lib/compass is RW + persistent.
    cache_dir = _v14_os.environ.get("COMPASS_POI_CACHE_DIR", "/var/lib/compass/poi")
    _v14_os.makedirs(cache_dir, exist_ok=True)
    sidecar = _v14_os.path.join(cache_dir, "poi_candidates.jsonl")
    actor = agent_id or "unknown"
    # normalize project to encoded_cwd form · mirrors
    # proof/poi_memory_key._normalize_project (inline · no proof import here).
    proj = (project or "").strip()
    if ":" in proj or "\\\\" in proj:
        proj = proj.replace(":\\\\", "--").replace(":/", "--").replace("\\\\", "-").replace("/", "-")
    ts = _dt.now(_tz.utc).isoformat(timespec="seconds")
    q_hash = _hl.sha1((query or "").encode("utf-8")).hexdigest()[:16]
    n = 0
    with open(sidecar, "a", encoding="utf-8") as f:
        for rank, h in enumerate(hits):
            mem = h.get("path") or h.get("memory")
            if not mem:
                continue
            f.write(_v14_json.dumps({
                "ts": ts,
                "kind": "candidate",
                "actor": actor,
                "project": proj,
                "memory": mem,
                "query_hash": q_hash,
                "rank": rank,
                "score": round(float(h.get("score", 0.0)), 4),
            }, ensure_ascii=False) + "\\n")
            n += 1
    return n
'''


def apply_patch(target: Path) -> bool:
    """Idempotently inject candidate emission into v14_recall. Returns True if
    patched, False if already patched. Raises on anchor-not-found."""
    target = Path(target)
    src = target.read_text(encoding="utf-8")
    if GUARD in src:
        return False

    didx = src.find("def v14_recall(")
    if didx < 0:
        raise RuntimeError("anchor not found: def v14_recall(")

    # edit 1 · add agent_id query param (scoped to v14_recall signature)
    param_anchor = 'x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),'
    pidx = src.find(param_anchor, didx)
    if pidx < 0:
        raise RuntimeError("anchor not found: v14_recall x_tenant_id param")
    src = src[:pidx] + "agent_id: Optional[str] = None,\n    " + src[pidx:]

    # edit 2 · insert emit block immediately before the SUCCESS return. Anchored
    # on the success-return signature (ok:True + scope) rather than the
    # daemon-unreachable text, which has drifted across versions. At this point
    # both early-return guards have passed, so `d` holds real hits.
    success_anchor = ('    return {\n'
                      '        "ok": True,\n'
                      '        "scope": d.get("scope", scope),\n')
    sidx = src.find(success_anchor, didx)
    if sidx < 0:
        raise RuntimeError("anchor not found: v14_recall success return")
    emit_block = (
        '    try:\n'
        '        _h = d.get("recall", [])\n'
        '        if _h and _v14_os.environ.get("COMPASS_NO_POI_CANDIDATE") != "1":\n'
        '            _v14_emit_poi_candidate(_h, q, agent_id, project)\n'
        '    except Exception:\n'
        '        pass\n')
    src = src[:sidx] + emit_block + src[sidx:]

    # edit 3 · prepend the self-contained helper just before the route decorator
    route_anchor = '@app.get("/v1/v14/recall")'
    aidx = src.find(route_anchor)
    if aidx < 0:
        raise RuntimeError("anchor not found: @app.get v14 recall route")
    src = src[:aidx] + EMIT_HELPER + "\n\n" + src[aidx:]

    target.write_text(src, encoding="utf-8")
    return True


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "/home/ubuntu/compass/compass_http_v09.py")
    if apply_patch(target):
        print(f"PATCHED · {target}\n  + agent_id param\n  + _v14_emit_poi_candidate\n  + emit on hits")
    else:
        print("ALREADY PATCHED · skipping")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Inject cloud-side PoI boost into compass_http_v09.py v14_recall (Phase 2).
Reranks recall hits by the central credit snapshot · env-gated
(COMPASS_CLOUD_POI_BOOST=1, default OFF) · mtime-cached · never raises (boost is
an enhancement, recall must never fail). Raw-string helper avoids escaping.

Deploy discipline: download live → patch a copy locally → ast.parse + diff →
upload → restart → verify (boost off then on). Snapshot delivered to
/var/lib/compass/poi/poi_credit_snapshot.json by regen_poi_snapshot.sh (cron,
regenerates from the central poi_credit table = source of truth).
Usage: python ops/patch_v14_recall_poi_boost.py <target>"""
import sys
from pathlib import Path

GUARD = "_v14_poi_boost"

# raw string · written verbatim into the target (NOT exec'd) so backslashes are literal
BOOST_HELPER = r'''_V14_POI_SNAP = {"data": {}, "mtime": None}


def _v14_poi_boost(hits):
    """Rerank recall hits in place by central PoI credit snapshot. Env-gated
    (COMPASS_CLOUD_POI_BOOST=1) · mtime-cached · NEVER raises. Boost is an
    enhancement; recall must never fail because of it. key = project/basename,
    project normalized to encoded_cwd form (mirrors proof/poi_memory_key)."""
    if _v14_os.environ.get("COMPASS_CLOUD_POI_BOOST") != "1" or not hits:
        return hits
    try:
        import json as _bj, math as _bm
        p = _v14_os.environ.get("COMPASS_POI_CREDIT_SNAPSHOT",
                                "/var/lib/compass/poi/poi_credit_snapshot.json")
        st = _V14_POI_SNAP
        if _v14_os.path.exists(p):
            m = _v14_os.path.getmtime(p)
            if m != st.get("mtime"):
                with open(p, encoding="utf-8") as f:
                    loaded = _bj.load(f)
                if isinstance(loaded, dict):
                    st["data"], st["mtime"] = loaded, m
        snap = st.get("data") or {}
        if not snap:
            return hits
        for h in hits:
            proj = (h.get("project") or "").strip()
            if ":" in proj or "\\" in proj:
                proj = proj.replace(":\\", "--").replace(":/", "--").replace("\\", "-").replace("/", "-")
            mem = (h.get("path") or h.get("memory") or "").replace("\\", "/").rsplit("/", 1)[-1]
            cum = snap.get(proj + "/" + mem)
            if cum is None or not _bm.isfinite(cum):
                continue
            boost = max(-0.5, min(1.0, cum * 0.1))
            new = h.get("score", 0.0) * (1.0 + boost)
            if _bm.isfinite(new):
                h["score"] = round(new, 4)
        hits.sort(key=lambda x: -x.get("score", 0.0))
    except Exception:
        pass
    return hits


'''

def apply_patch(target: Path) -> bool:
    """Idempotently inject the boost helper + call-site. Returns True if patched,
    False if already patched (guard present). Raises on anchor-not-found."""
    target = Path(target)
    src = target.read_text(encoding="utf-8")
    if GUARD in src:
        return False
    # edit 1 · insert helper + global right before the emission helper
    anchor1 = "def _v14_emit_poi_candidate("
    i1 = src.find(anchor1)
    if i1 < 0:
        raise RuntimeError("anchor not found: emission helper")
    src = src[:i1] + BOOST_HELPER + src[i1:]
    # edit 2 · call boost in place right after the recall list is pulled, before emit
    anchor2 = '        _h = d.get("recall", [])\n'
    i2 = src.find(anchor2)
    if i2 < 0:
        raise RuntimeError("anchor not found: _h = d.get(recall)")
    ins = anchor2 + "        _v14_poi_boost(_h)  # rerank in place by PoI credit snapshot (env-gated)\n"
    src = src[:i2] + ins + src[i2 + len(anchor2):]
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    assert src.count("def _v14_poi_boost(") == 1
    assert "_v14_poi_boost(_h)" in src
    return True


if __name__ == "__main__":
    ok = apply_patch(Path(sys.argv[1]))
    print("boost injected" if ok else "already patched", "· guard", GUARD)

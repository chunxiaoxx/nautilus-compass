# P5 · v14 recall PoI candidate emission — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the L3 PoI recursive loop fire in production — emit PoI candidates on the cloud `/v1/v14/recall` path (the route V5 actually calls), then reconcile them locally so `cumulative_impact` credits the cited local memory files.

**Architecture:** (1) A self-contained inline emit helper injected into the cloud HTTP server via an idempotent patch script — no `proof` import (the package is not on that server's path). (2) A local-pull reconciler that fetches cloud candidates, merges them into the local cache, and runs the existing `poi_reconcile_cron.py` against local memory files.

**Tech Stack:** Python 3, FastAPI (cloud `compass_http_v09.py`), pytest, ssh, Windows schtasks. JSONL sidecar. NO LLM.

**Honest boundary:** `settle` stays 0 until V5 adds `agent_id=nautilus-prime-001` (contract c1, ready-on-signal). This session ships emission (gating) + reconciler (standby).

---

## Task 1: Emit helper string constant + unit test (TDD)

The deployed cloud code IS this string (exec'd in the test) → zero drift between test and prod.

**Files:**
- Create: `ops/patch_v14_recall_poi_candidate.py` (only the `EMIT_HELPER` constant in this task)
- Test: `tests/test_v14_poi_emission_patch.py`

**Step 1: Write the failing test**

```python
"""Tests for the v14 recall PoI candidate emission patch.

The patch injects a self-contained `_v14_emit_poi_candidate` into the cloud
HTTP server. We exec the exact EMIT_HELPER string the patch deploys, then
assert the JSONL it writes — so the test covers the real production code.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import importlib.util

_SPEC = importlib.util.spec_from_file_location(
    "patch_v14_poi",
    Path(__file__).resolve().parent.parent / "ops" / "patch_v14_recall_poi_candidate.py")
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


def _load_emit():
    """exec the deployed helper string in a namespace mirroring the cloud server's
    injected aliases (_v14_os, _v14_json)."""
    ns = {"_v14_os": os, "_v14_json": json}
    exec(_MOD.EMIT_HELPER, ns)
    return ns["_v14_emit_poi_candidate"]


def test_emits_one_line_per_hit(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPASS_POI_CACHE_DIR", str(tmp_path))
    emit = _load_emit()
    hits = [{"path": "a.md", "score": 0.91}, {"path": "b.md", "score": 0.5}]
    n = emit(hits, "some query", "nautilus-prime-001")
    assert n == 2
    lines = (tmp_path / "poi_candidates.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    r0 = json.loads(lines[0])
    assert r0["kind"] == "candidate"
    assert r0["actor"] == "nautilus-prime-001"
    assert r0["memory"] == "a.md"
    assert r0["rank"] == 0
    assert r0["score"] == 0.91
    assert len(r0["query_hash"]) == 16


def test_none_agent_id_becomes_unknown(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPASS_POI_CACHE_DIR", str(tmp_path))
    emit = _load_emit()
    n = emit([{"path": "a.md", "score": 0.1}], "q", None)
    assert n == 1
    r = json.loads((tmp_path / "poi_candidates.jsonl").read_text(encoding="utf-8").strip())
    assert r["actor"] == "unknown"


def test_skips_hits_without_path(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPASS_POI_CACHE_DIR", str(tmp_path))
    emit = _load_emit()
    n = emit([{"score": 0.1}, {"path": "b.md", "score": 0.2}], "q", "x")
    assert n == 1


def test_empty_hits_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPASS_POI_CACHE_DIR", str(tmp_path))
    emit = _load_emit()
    n = emit([], "q", "x")
    assert n == 0
    assert not (tmp_path / "poi_candidates.jsonl").exists()
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_v14_poi_emission_patch.py -v`
Expected: FAIL — `ops/patch_v14_recall_poi_candidate.py` does not exist (ModuleNotFoundError on exec_module).

**Step 3: Write minimal implementation**

Create `ops/patch_v14_recall_poi_candidate.py` with ONLY the constant:

```python
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
EMIT_HELPER = '''def _v14_emit_poi_candidate(hits, query, agent_id):
    """Self-contained PoI candidate emission for the v14 recall path.
    One JSONL line per hit -> poi_candidates.jsonl (schema matches
    proof/poi_emitter: ts/kind/actor/memory/query_hash/rank/score).
    No proof import (not on this server path) · no self-cite suppression
    (cited memory files are not local to this cloud host). Never raises."""
    import hashlib as _hl
    from datetime import datetime as _dt, timezone as _tz
    cache_dir = _v14_os.environ.get("COMPASS_POI_CACHE_DIR", "/home/ubuntu/compass/.cache/poi")
    _v14_os.makedirs(cache_dir, exist_ok=True)
    sidecar = _v14_os.path.join(cache_dir, "poi_candidates.jsonl")
    actor = agent_id or "unknown"
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
                "memory": mem,
                "query_hash": q_hash,
                "rank": rank,
                "score": round(float(h.get("score", 0.0)), 4),
            }, ensure_ascii=False) + "\\n")
            n += 1
    return n
'''
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_v14_poi_emission_patch.py -v`
Expected: PASS (4 passed)

**Step 5: Commit**

```bash
git add ops/patch_v14_recall_poi_candidate.py tests/test_v14_poi_emission_patch.py
git commit -m "feat(P5): v14 candidate emit helper + tests (TDD)"
```

---

## Task 2: Patch script body (idempotent 3-edit injection) + test

**Files:**
- Modify: `ops/patch_v14_recall_poi_candidate.py` (add `main()` + edit logic below `EMIT_HELPER`)
- Test: `tests/test_v14_poi_emission_patch.py` (add patch-application tests)

**Step 1: Write the failing test** (append to the test file)

```python
# ---- patch application (against a synthetic copy of the live route) -----------

_LIVE_ROUTE = '''import os
from typing import Optional
from fastapi import Header

@app.get("/v1/v14/recall")
def v14_recall(
    q: str,
    top_k: int = 5,
    scope: str = "project",
    project: Optional[str] = None,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
):
    """v1.4 BGE-m3 recall."""
    req = {"action": "recall", "query": (q or "")[:2000]}
    if project:
        req["project"] = project
    d = _call_v14_daemon(req, timeout=15.0)
    if not d:
        return {"ok": False, "error": "v14 daemon unreachable",
                "backend": "v1.4-bge-m3"}
    return {
        "ok": True,
        "hits": d.get("recall", []),
        "backend": "v1.4-bge-m3",
    }
'''


def test_patch_is_idempotent(tmp_path):
    target = tmp_path / "compass_http_v09.py"
    target.write_text(_LIVE_ROUTE, encoding="utf-8")
    assert _MOD.apply_patch(target) is True          # first run patches
    once = target.read_text(encoding="utf-8")
    assert _MOD.apply_patch(target) is False         # second run skips
    assert target.read_text(encoding="utf-8") == once


def test_patch_adds_agent_id_param_and_emit_and_helper(tmp_path):
    target = tmp_path / "compass_http_v09.py"
    target.write_text(_LIVE_ROUTE, encoding="utf-8")
    _MOD.apply_patch(target)
    out = target.read_text(encoding="utf-8")
    assert "agent_id: Optional[str] = None" in out
    assert "def _v14_emit_poi_candidate(" in out
    assert "_v14_emit_poi_candidate(_h, q, agent_id)" in out
    # patched module must still be importable Python
    compile(out, "patched", "exec")


def test_patched_route_emits_on_real_call(tmp_path, monkeypatch):
    """exec the patched module with stubbed _call_v14_daemon + FastAPI shims,
    call v14_recall, assert a candidate line lands."""
    import json, os
    target = tmp_path / "compass_http_v09.py"
    target.write_text(_LIVE_ROUTE, encoding="utf-8")
    _MOD.apply_patch(target)
    monkeypatch.setenv("COMPASS_POI_CACHE_DIR", str(tmp_path / "poi"))

    # minimal shims so the patched module body execs
    class _App:
        def get(self, *a, **k):
            return lambda fn: fn
        def post(self, *a, **k):
            return lambda fn: fn
    def _Header(default=None, alias=None):
        return default
    ns = {"app": _App(), "Header": _Header,
          "_call_v14_daemon": lambda req, timeout=None: {"recall": [{"path": "m.md", "score": 0.7}]},
          "_v14_os": os, "_v14_json": json}
    exec(compile(target.read_text(encoding="utf-8"), "patched", "exec"), ns)
    res = ns["v14_recall"]("hello", agent_id="nautilus-prime-001")
    assert res["ok"] is True
    line = json.loads((tmp_path / "poi" / "poi_candidates.jsonl").read_text(encoding="utf-8").strip())
    assert line["actor"] == "nautilus-prime-001"
    assert line["memory"] == "m.md"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_v14_poi_emission_patch.py -k patch -v`
Expected: FAIL — `_MOD.apply_patch` does not exist.

**Step 3: Write minimal implementation** (append to `ops/patch_v14_recall_poi_candidate.py`)

```python
def apply_patch(target: Path) -> bool:
    """Idempotently inject candidate emission into v14_recall. Returns True if
    patched, False if already patched. Raises on anchor-not-found."""
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

    # edit 2 · insert emit block after the `if not d:` early-return (within route)
    ret_anchor = ('    if not d:\n'
                  '        return {"ok": False, "error": "v14 daemon unreachable",\n'
                  '                "backend": "v1.4-bge-m3"}\n')
    ridx = src.find(ret_anchor, didx)
    if ridx < 0:
        raise RuntimeError("anchor not found: v14_recall daemon-unreachable return")
    emit_block = (
        '    try:\n'
        '        _h = d.get("recall", [])\n'
        '        if _h and _v14_os.environ.get("COMPASS_NO_POI_CANDIDATE") != "1":\n'
        '            _v14_emit_poi_candidate(_h, q, agent_id)\n'
        '    except Exception:\n'
        '        pass\n')
    insert_at = ridx + len(ret_anchor)
    src = src[:insert_at] + emit_block + src[insert_at:]

    # edit 3 · prepend the self-contained helper just before the route decorator
    route_anchor = '@app.get("/v1/v14/recall")'
    aidx = src.find(route_anchor)
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
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_v14_poi_emission_patch.py -v`
Expected: PASS (7 passed)

**Step 5: Commit**

```bash
git add ops/patch_v14_recall_poi_candidate.py tests/test_v14_poi_emission_patch.py
git commit -m "feat(P5): idempotent v14_recall emission patch + application tests"
```

---

## Task 3: Deploy to cloud + e2e verify (@verification-before-completion)

No new code — deployment + real-endpoint verification. Do NOT claim done without the SSH-cat evidence.

**Step 1: Back up + dry-import the patch on cloud**

```bash
scp ops/patch_v14_recall_poi_candidate.py cloud:/tmp/patch_poi.py
ssh cloud 'cp /home/ubuntu/compass/compass_http_v09.py /home/ubuntu/compass/compass_http_v09.py.bak.pre_poi_$(date +%s) && python3 -c "import ast,sys; ast.parse(open(\"/home/ubuntu/compass/compass_http_v09.py\").read()); print(\"parses OK\")"'
```

**Step 2: Apply patch on a copy + verify it compiles BEFORE touching live**

```bash
ssh cloud 'cp /home/ubuntu/compass/compass_http_v09.py /tmp/cand.py && python3 /tmp/patch_poi.py /tmp/cand.py && python3 -c "import ast; ast.parse(open(\"/tmp/cand.py\").read()); print(\"patched copy parses OK\")" && grep -n "agent_id: Optional\|_v14_emit_poi_candidate" /tmp/cand.py'
```
Expected: "patched copy parses OK" + grep shows the 3 injections.

**Step 3: Apply to live + set env in /etc/default/compass + restart**

```bash
ssh cloud 'python3 /tmp/patch_poi.py /home/ubuntu/compass/compass_http_v09.py && grep -q "COMPASS_POI_CACHE_DIR" /etc/default/compass 2>/dev/null || echo "COMPASS_POI_CACHE_DIR=/home/ubuntu/compass/.cache/poi" | sudo tee -a /etc/default/compass'
ssh cloud 'sudo systemctl restart compass.service && sleep 3 && systemctl is-active compass.service'
```
Expected: `active`.

**Step 4: e2e — bring up local 9876 tunnel, then real recall with agent_id**

The reverse tunnel (`-R 9876`) must be up so the daemon returns real hits.
```bash
# verify the daemon answers via the cloud-side path first
ssh cloud 'curl -s "http://127.0.0.1:8770/v1/v14/recall?q=compass+poi+test&top_k=3&project=C--Users-chunx&agent_id=test-poi-001" | head -c 400'
```
Expected: JSON with `"ok": true` and non-empty `"hits"`. If `hits` empty → tunnel/daemon down; bring up local daemon+tunnel (compass_watchdog.ps1 / compass_start.ps1) and retry.

**Step 5: Confirm the candidate landed (the real evidence)**

```bash
ssh cloud 'tail -3 /home/ubuntu/compass/.cache/poi/poi_candidates.jsonl'
```
Expected: a line with `"actor": "test-poi-001"`, `"kind": "candidate"`, the recalled memory filename, and a score. THIS is the proof emission is live.

**Step 6: Commit a deploy note**

```bash
git add docs/plans/2026-06-03-p5-v14-poi-emission.md
git commit -m "chore(P5): record cloud emission deploy + e2e evidence" --allow-empty
```
(Paste the SSH-cat evidence into the session memory at session end, not the repo.)

---

## Task 4: Local pull dedup-merge pure function + test (TDD)

**Files:**
- Create: `ops/pull_cloud_candidates.py` (pure `merge_candidate_lines` only this task)
- Test: `tests/test_pull_cloud_candidates.py`

**Step 1: Write the failing test**

```python
from __future__ import annotations
from pathlib import Path
import importlib.util

_SPEC = importlib.util.spec_from_file_location(
    "pull_cloud", Path(__file__).resolve().parent.parent / "ops" / "pull_cloud_candidates.py")
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


def test_merge_dedups_exact_lines():
    existing = ['{"a":1}', '{"b":2}']
    incoming = ['{"b":2}', '{"c":3}']
    out = _MOD.merge_candidate_lines(existing, incoming)
    assert out == ['{"a":1}', '{"b":2}', '{"c":3}']  # order preserved, dup dropped


def test_merge_ignores_blank_lines():
    out = _MOD.merge_candidate_lines(['{"a":1}', ''], ['', '{"d":4}'])
    assert out == ['{"a":1}', '{"d":4}']


def test_merge_empty_existing():
    assert _MOD.merge_candidate_lines([], ['{"x":1}']) == ['{"x":1}']
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_pull_cloud_candidates.py -v`
Expected: FAIL — module/function missing.

**Step 3: Write minimal implementation**

```python
"""Pull cloud-emitted PoI candidates to the local cache so the local reconciler
(which can credit local memory files) can settle them.

  ssh cloud cat <cloud poi_candidates.jsonl>  ->  dedup-merge into local cache
  ->  run ops/poi_reconcile_cron.py (tunnels to DB, MEMORY_ROOT = local memory)

Idempotent · safe to schedule. NO LLM.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

CLOUD_FILE = os.environ.get(
    "COMPASS_CLOUD_POI_FILE", "/home/ubuntu/compass/.cache/poi/poi_candidates.jsonl")
SSH_HOST = os.environ.get("COMPASS_SOUL_SSH_HOST", "cloud")
LOCAL_CACHE = Path(os.environ.get(
    "COMPASS_POI_CACHE_DIR",
    str(Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache")))
CANDIDATE_NAME = "poi_candidates.jsonl"


def merge_candidate_lines(existing, incoming):
    """Order-preserving union of JSONL lines (existing first), blanks dropped."""
    seen = set()
    out = []
    for line in list(existing) + list(incoming):
        s = line.strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_pull_cloud_candidates.py -v`
Expected: PASS (3 passed)

**Step 5: Commit**

```bash
git add ops/pull_cloud_candidates.py tests/test_pull_cloud_candidates.py
git commit -m "feat(P5): cloud candidate pull dedup-merge + tests (TDD)"
```

---

## Task 5: Pull I/O + reconcile runner + Windows scheduled task

**Files:**
- Modify: `ops/pull_cloud_candidates.py` (add `fetch_cloud_lines` + `main`)
- Create: `C:/Users/chunx/.cache/compass/run-poi-reconcile.cmd` (wrapper)

**Step 1: Add I/O + main to `ops/pull_cloud_candidates.py`**

```python
def fetch_cloud_lines() -> list:
    """ssh cat the cloud candidate file · returns [] if absent/unreachable."""
    try:
        out = subprocess.run(
            ["ssh", SSH_HOST, f"cat {CLOUD_FILE} 2>/dev/null || true"],
            capture_output=True, text=True, timeout=30)
        return out.stdout.splitlines()
    except Exception as e:
        sys.stderr.write(f"cloud pull failed · {type(e).__name__}: {str(e)[:160]}\n")
        return []


def main() -> int:
    LOCAL_CACHE.mkdir(parents=True, exist_ok=True)
    local_path = LOCAL_CACHE / CANDIDATE_NAME
    existing = local_path.read_text(encoding="utf-8").splitlines() if local_path.exists() else []
    incoming = fetch_cloud_lines()
    merged = merge_candidate_lines(existing, incoming)
    added = len(merged) - len([l for l in existing if l.strip()])
    local_path.write_text("\n".join(merged) + ("\n" if merged else ""), encoding="utf-8")
    print(f"pulled {len(incoming)} cloud lines · +{added} new · total {len(merged)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: Verify the merge round-trips locally (no cloud needed)**

Run: `python -m pytest tests/test_pull_cloud_candidates.py -v`
Expected: PASS (still green — I/O is exercised in Task 6 against cloud).

**Step 3: Create the scheduled-task wrapper**

`C:/Users/chunx/.cache/compass/run-poi-reconcile.cmd`:
```bat
@echo off
set COMPASS_POI_CACHE_DIR=%USERPROFILE%\.claude\plugins\nautilus-compass\.cache
set COMPASS_POI_MEMORY_ROOT=%USERPROFILE%\.claude\projects\C--Users-chunx\memory
cd /d C:\Users\chunx\Projects\nautilus-compass
py -3 ops\pull_cloud_candidates.py  >> %USERPROFILE%\.cache\compass\poi-reconcile.log 2>&1
py -3 ops\poi_reconcile_cron.py     >> %USERPROFILE%\.cache\compass\poi-reconcile.log 2>&1
```
(Pick the python that has psycopg2 — verify in Task 6 Step 1; substitute full path if `py -3` lacks it.)

**Step 4: Commit (task registration happens in Task 6 after a real dry-run)**

```bash
git add ops/pull_cloud_candidates.py
git commit -m "feat(P5): cloud pull I/O + local reconcile wrapper"
```

---

## Task 6: Reconciler dry-run verify + schedule (@verification-before-completion)

**Step 1: Pick a python with psycopg2 + run the pull against cloud**

```bash
py -3 -c "import psycopg2; print('psycopg2 ok')"   # if fails, find the venv that has it
py -3 ops/pull_cloud_candidates.py
```
Expected: "pulled N cloud lines · +K new" (N>0 once Task 3 e2e left a test candidate).

**Step 2: Dry-run reconcile (no settle expected — actor=test/unknown ≠ platform agent)**

```bash
set COMPASS_POI_CACHE_DIR=%USERPROFILE%\.claude\plugins\nautilus-compass\.cache
set COMPASS_POI_MEMORY_ROOT=%USERPROFILE%\.claude\projects\C--Users-chunx\memory
py -3 ops/poi_reconcile_cron.py --dry-run
```
Expected: prints `candidates=N pending=… outcomes=… settled=0 … · DRY-RUN`. settled=0 is CORRECT (fuel gated on V5). Confirms DB tunnel + candidate read work end-to-end.

**Step 3: Register the Windows scheduled task (every 30 min)**

```bash
schtasks //Create //TN "compass-poi-reconcile" //TR "C:\Users\chunx\.cache\compass\run-poi-reconcile.cmd" //SC MINUTE //MO 30 //F
schtasks //Run //TN "compass-poi-reconcile"
```
Then confirm the log:
```bash
ssh_noop="" ; type "%USERPROFILE%\.cache\compass\poi-reconcile.log"
```
Expected: log shows the pull line + reconcile summary (settled=0).

**Step 4: Commit**

```bash
git add docs/plans/2026-06-03-p5-v14-poi-emission.md
git commit -m "chore(P5): reconciler dry-run verified + scheduled (settled=0 fuel-gated)" --allow-empty
```

---

## Task 7: Finish the branch (@finishing-a-development-branch)

- Run the full suite: `python -m pytest tests/ -q` — expect prior 672 + new (≈7+3) green.
- Invoke **finishing-a-development-branch** → PR to main (do not auto-merge; user decides).
- Send V5 the **live signal** (outbound memory, thread_id `compass-to-v5-recall-demand-2026-06-02`): "emission live on /v1/v14/recall@8770" + the SSH-cat candidate evidence + the local-credit nuance.

---

## Verification checklist (no silent "done")
- [ ] Task 1–2: tests green (`pytest tests/test_v14_poi_emission_patch.py`)
- [ ] Task 3: SSH-cat shows `actor=test-poi-001` candidate line on cloud — **the gating proof**
- [ ] Task 6: local `--dry-run` shows DB tunnel works + settled=0 (honest, fuel-gated)
- [ ] Task 7: full suite green + PR open + V5 live signal sent

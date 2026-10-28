# Soul API Productization (Increment #4) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
> **Run in a git worktree** (isolation · using-git-worktrees). Scope is FROZEN — any new idea goes to `PARKING_LOT_soul_trinity_20260527.md`, NOT into this plan. Deployment path = **Option C (reconcile a slice first, then deploy)**, chosen by user 2026-05-27.

**Goal:** A real platform agent calls a Soul endpoint on the live platform backend and gets back a self-modify result (generated code + checks) carrying a JSON-LD audit certificate that `verify_certificate()` validates (valid=True) with a real `fidelity_score`.

**Binding DONE (do not exceed):** One **real authenticated HTTP call** from a platform agent (V5's real API key) to `POST :8000/api/soul/audit-generate` returns `cert_valid=True` + a real `fidelity_score`, and re-running `verify_certificate(cert)` confirms valid=True. Verified by actually making the call and inspecting the response. Nothing else.

**Architecture:** The cert/audit logic already exists and is proven (increment 1 · `soul_self_audit.py` + `audit_cert_generator.py` + `raid_fidelity_checker.py`). This increment adds (a) a thin **agent-facing endpoint** `POST /api/soul/audit-generate` that chains `generate()` (dry-run) → `run_self_audit()` → returns the signed cert — **no draft PR, no PAT needed** (sidesteps the pending token-revoke); and (b) a **minimal reconciliation slice**: consolidate the Soul+cert file set as canonical on `origin/master`, then sync exactly those files onto the live `~/nautilus-mvp` backend and register the router. The broader 79-commit `origin↔mvp` divergence is explicitly OUT OF SCOPE.

**Tech Stack:** Python 3.11 · FastAPI · SQLAlchemy (raw `text()` SQL for persist) · existing `audit_cert_generator.py` (HMAC-SHA256 JSON-LD) · `raid_fidelity_checker.py::check_fidelity` · `soul_self_audit.py` · `soul_service.py::generate`.

---

## Current-state map (confirmed 2026-05-27 reconnaissance)

| Artifact | origin/master + local | cloud `~/nautilus-mvp` (live :8000) | cloud `~/nautilus-soul-workspace` |
|---|---|---|---|
| `api/soul.py` (dry-run `/generate` only · no cert) | ✅ (`a970f28c0`) | ❌ | ❌ (no api/soul) |
| `services/soul_service.py` / `soul_pr_gate.py` / `soul_consumer.py` | ✅ | ❌ | ✅ |
| `services/audit_cert_generator.py` / `raid_fidelity_checker.py` | ❌ | ✅ (5/22 P3/P5 ship) | ✅ (untracked copies) |
| `services/soul_self_audit.py` (run_self_audit/persist/attach/ship_with_self_audit) | ❌ | ✅ on branch `soul-audit-increment1` | ✅ (untracked copy) |
| `main.py` registers soul router | ❌ | ❌ | n/a |

- Live backend: `uvicorn main:app --host 0.0.0.0 --port 8000`, cwd `~/nautilus-mvp/phase3/backend`, currently on branch `soul-audit-increment1`. Health = `GET /health` → 200. `GET /api/soul/generate` → 404.
- `cert` code lives only on cloud (committed on `mvp:soul-audit-increment1` + untracked in soul-workspace) — **not version-controlled on origin = "building on sand"**. Fixing this IS the reconciliation slice.
- Local `master` is **ahead 6** of origin (the NEXT-GOAL doc commits — unrelated; do not push those as part of this work unless reviewed).

---

## Pre-flight prerequisites (USER + investigation · confirm before Phase 1)

1. **🔴 USER ACTION — fine-grained PAT (security action `action_token_revoke_20260527`):** revoke the exposed `ghp_lIdaSgG0K…`, generate a fine-grained PAT scoped to `chunxiaoxx/nautilus-core` `contents:write`, `gh auth login --with-token`, clear stale `GITHUB_TOKEN` env var. *Mitigation if not done:* do all origin pushes **on cloud** via the working `gh` keyring (same path that pushed PR #50) — no local PAT needed. Pick one before Phase 1.
2. **SSH stability:** increment 1 died mid-work to SSH resets. Keep each cloud step small + idempotent; commit with explicit pathspec (never bare `git add -A` on the permanently-dirty mvp index).

---

## Phase 0: Confirm cloud assumptions (bounded · ~20 min · read-only)

Do NOT skip — the endpoint design depends on these. `ssh cloud '…'`, read don't guess.

**Step 0.1 — Are the cert services importable on mvp's *current* branch (not just increment-1)?**
```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && git branch --show-current && \
  for m in services.audit_cert_generator services.raid_fidelity_checker services.soul_self_audit; do \
    python -c "import importlib; importlib.import_module(\"$m\"); print(\"OK $m\")" 2>&1 | tail -1; done'
```
Expected: all three import OK on `soul-audit-increment1`. Record which are present on mvp `master` vs only the branch.

**Step 0.2 — Does engine dry-run expose generated file *contents* (for a meaningful fidelity check)?**
`check_fidelity(task_spec, output)` needs the actual generated code, not just paths. Inspect what `generate()`'s `files_planned` carries:
```bash
ssh cloud 'cd ~/nautilus-soul-workspace/phase3/backend && python -c "
from services.soul_service import generate
r = generate(\"Add a function add(a,b) that returns a+b to scratch/mathx.py\", base_dir=\".\", cycle_id=\"p0-probe\")
import json; print(json.dumps({k:(v if k!=\"files_planned\" else [{kk:(str(vv)[:60]) for kk,vv in f.items()} for f in v]) for k,v in r.items()}, default=str)[:1500])
"'
```
- **If `files_planned` entries include a content/`diff`/`body` field** → endpoint passes that as `output` to `run_self_audit`.
- **If only `path`+`size`** → DESIGN CONTINGENCY: the audit endpoint must obtain content. Either (a) the engine result object has a `.files` map with content (inspect `engine/ship.py` return), or (b) do a real apply into a throwaway scratch dir + read files back. Decide here; update Task 2 accordingly. Do NOT proceed to Task 2 until `output` source is pinned.

**Step 0.3 — Is the public verify endpoint live (for the optional tamper-check)?**
```bash
ssh cloud 'curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/api/v1/audit/nonexistent/verify"'
```
Record the route (from `grep -rn "audit.*verify" ~/nautilus-mvp/phase3/backend/api/`). Not required for binding DONE but nice for the cert footer.

**Step 0.4 — A real platform agent API key for the E2E.** Find V5's active API key (binding DONE needs a *real agent* call, not a fabricated key):
```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && python -c "
from utils.database import SessionLocal; from models.database import APIKey
db=SessionLocal()
for r in db.query(APIKey).filter(APIKey.is_active==True).limit(10): print(r.agent_id, r.key[:10]+\"...\")
"'
```
Record one real active agent key (full value handled on cloud only · never paste into chat). If V5 has none, note which agent will stand in (must be a genuine platform agent, not an ad-hoc test key).

**Step 0.5 — mvp working-tree + which files differ from origin for the soul slice** (scope the sync):
```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && git status --short services/ api/ main.py | head -30'
```

> **Checkpoint after Phase 0:** Summarize findings (esp. 0.2 output source + 0.4 agent key). If 0.2 shows dry-run has no content, STOP and confirm the contingency design before writing the endpoint test.

### ✅ Phase 0 RESULTS (recorded 2026-05-27)

- **0.1:** On mvp branch `soul-audit-increment1`, `audit_cert_generator` / `raid_fidelity_checker` / `soul_self_audit` import OK; **`soul_service` does NOT import (absent on mvp)** → Phase 2 must sync `soul_service.py` (+ `soul_pr_gate.py`) to mvp. cert files are NOT on mvp `master`, only on the `soul-audit-increment1` branch (which the live backend is currently checked out on, so they exist at runtime now).
- **0.2 → CONTINGENCY FIRED:** dry-run `generate()` returns `files_planned` entries with keys **`path`, `size`, `lang` only — NO content**. `ship.py:220-221` builds `files_planned` from parsed blocks `{lang,path,content}` but **drops `content`**. A fidelity check on paths-only yields a meaningless score (this is why PR #50 got fidelity 0.25 — it audited path comments, not code).
  - **RESOLUTION (no engine change · lowest blast radius):** add a `capture_content=False` path to `soul_service.generate()` that, when True, applies the generation into a **throwaway temp dir** (`tempfile.mkdtemp`), reads the written file contents back, attaches them, and removes the temp dir. The engine (196 tests) is NOT touched, and the deploy slice does NOT need to sync `engine/`. The audit endpoint calls `generate(..., capture_content=True)` and feeds real content to `check_fidelity`. See revised Task 1.1b + Task 1.2.
- **0.3:** public verify route = **`POST /api/v1/public/cert/{audit_id}/verify`** (audit_service.py:297, `public_router`). Use this path in the cert footer / tamper-check.
- **0.5:** mvp working tree is DIRTY (M: main.py, api/auth.py, services/raid_engine.py, … · untracked: audit_service.py, a2a_gateway.py, …). Phase 2 main.py edit + file sync must use **explicit pathspec** and must NOT disturb unrelated dirty files. Boot-test on a spare port before touching :8000.
- env note: `~/nautilus-soul-workspace` has **no `.env`**; source `~/nautilus-mvp/phase3/backend/.env` (has DATABASE_URL + DEEPSEEK/GEMINI/ANTHROPIC/MINIMAX keys) before any `generate()`/DB run. `python3` (not `python`) on cloud.

---

## Phase 1: Consolidate the Soul+cert slice as canonical on origin/master

> Goal of this phase: kill the "code lives only as untracked cloud files" problem. After this, `origin/master` is the single source of truth for `soul_service`, `soul_pr_gate`, `soul_self_audit`, `audit_cert_generator`, `raid_fidelity_checker`, and the new endpoint. Do this **in a worktree**; push via the chosen PAT path (Pre-flight #1).

### Task 1.1: Bring the 3 cert/audit files into the repo (canonical copy)

**Files:**
- Create: `phase3/backend/services/audit_cert_generator.py`
- Create: `phase3/backend/services/raid_fidelity_checker.py`
- Create: `phase3/backend/services/soul_self_audit.py`

**Step 1 — Pull canonical copies from cloud** (the proven increment-1 versions). On cloud, the source of truth is `mvp:soul-audit-increment1`:
```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && git show soul-audit-increment1:services/soul_self_audit.py' > <worktree>/phase3/backend/services/soul_self_audit.py
# repeat for audit_cert_generator.py + raid_fidelity_checker.py (these may be on mvp master already — confirm Phase 0.1)
```
(If a file is on mvp `master` not the branch, `git show master:services/<f>.py`. Use whichever ref the Phase 0.1 import succeeded against.)

**Step 2 — Verify integrity** (do not trust the transfer): `python -c "import ast; ast.parse(open('services/soul_self_audit.py').read()); print('OK')"` for each. Confirm `grep -nE "def (run_self_audit|persist_self_audit_rows|attach_cert_to_pr|ship_with_self_audit)" services/soul_self_audit.py` shows all 4.

**Step 3 — Bring the existing tests too** (increment 1 had 5 green): `git show soul-audit-increment1:tests/test_soul_self_audit.py` etc → `phase3/backend/tests/`.

**Step 4 — Run them locally** (or note they require cloud DB — integration tests are `-m integration`; run unit subset):
```bash
cd phase3/backend && python -m pytest tests/test_soul_self_audit.py -v -m "not integration"
```
Expected: unit tests PASS (injected-dep tests need no DB).

**Step 5 — Commit** (pathspec):
```bash
git add phase3/backend/services/soul_self_audit.py phase3/backend/services/audit_cert_generator.py \
        phase3/backend/services/raid_fidelity_checker.py phase3/backend/tests/test_soul_self_audit*.py
git commit -m "feat(soul): vendor proven cert/audit services into origin (increment 1 canonical)"
```

### Task 1.1b: `soul_service.generate(capture_content=True)` (real content for fidelity)

**Files:**
- Modify: `phase3/backend/services/soul_service.py::generate`
- Test: `phase3/backend/tests/test_soul_service_capture.py`

**Why:** Phase 0.2 — dry-run drops generated content; `check_fidelity` needs the real code. Capture by applying into a throwaway temp dir and reading files back. Engine untouched.

**Step 1: Failing test** (inject `_ship` so no LLM/engine; assert content captured):
```python
from services import soul_service

def test_generate_capture_content(tmp_path, monkeypatch):
    class FakeResult:
        applied = True
        files_planned = [{"path": "scratch/x.py", "size": 17, "lang": "python"}]
        check_result = {"passed": True}
        errors = None
        git_commit = None
    def fake_ship(engine, task, base_dir, **k):
        # simulate engine apply writing the file into base_dir (the temp dir)
        import os
        os.makedirs(os.path.join(base_dir, "scratch"), exist_ok=True)
        open(os.path.join(base_dir, "scratch", "x.py"), "w").write("def x(): return 1")
        return FakeResult()
    out = soul_service.generate(
        "add x", base_dir=str(tmp_path), cycle_id="c1",
        capture_content=True, _ship=fake_ship, _engine_factory=lambda b, d: object(),
    )
    assert out["success"] is True
    assert out["files_planned"][0]["content"] == "def x(): return 1"
```

**Step 2: Run · expect fail.**

**Step 3: Implement** — add `capture_content: bool = False` param. When True, run the apply into a `tempfile.mkdtemp()` (NOT the caller's base_dir), read each `files_planned` path's content from the temp dir, attach as `content`, then `shutil.rmtree` the temp dir. When False, behavior is byte-identical to today (default dry-run, no writes). Keep dependency-injection (`_ship`, `_engine_factory`) intact.

**Step 4: Run · expect PASS** + confirm `capture_content=False` path unchanged (existing `test` still green).

**Step 5: Commit:** `git commit -m "feat(soul): generate(capture_content) · real content via temp-dir apply (engine untouched)"`

---

### Task 1.2: Agent-facing endpoint `POST /api/soul/audit-generate`

**Files:**
- Modify: `phase3/backend/api/soul.py`
- Test: `phase3/backend/tests/test_api_soul_audit.py`

**Step 1 — Write the failing test** (mock the engine + audit so no DB/LLM needed):
```python
from fastapi.testclient import TestClient
import main  # app

def test_audit_generate_returns_valid_cert(monkeypatch):
    # auth: stub _require_agent
    import api.soul as soul
    monkeypatch.setattr(soul, "_require_agent", lambda key, db: 4242)
    # generate: stub a passing dry-run with content
    monkeypatch.setattr(
        "services.soul_service.generate",
        lambda task, base_dir, cycle_id=None: {
            "success": True, "cycle_id": cycle_id,
            "files_planned": [{"path": "scratch/x.py", "size": 20, "content": "def x(): return 1"}],
            "check_result": {"passed": True},
        },
    )
    # self-audit: stub run_self_audit
    monkeypatch.setattr(
        "services.soul_self_audit.run_self_audit",
        lambda db, task_spec, output, bounty_id, **k: {
            "success": True, "bounty_id": bounty_id, "fidelity_score": 0.81,
            "cert": {"@type": "AuditCertificate", "audit_id": bounty_id, "signature": "sig"},
            "cert_valid": True,
        },
    )
    client = TestClient(main.app)
    r = client.post("/api/soul/audit-generate",
                    headers={"X-Agent-Key": "k"}, json={"task_spec": "add a function x that returns 1"})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["cert_valid"] is True
    assert d["fidelity_score"] == 0.81
    assert d["cert"]["audit_id"].startswith("soul-audit-api-")
```

**Step 2 — Run · expect fail** (404 / route missing):
`cd phase3/backend && python -m pytest tests/test_api_soul_audit.py -v`

**Step 3 — Implement** the endpoint in `api/soul.py` (append after `soul_generate`):
```python
@router.post("/audit-generate")
async def soul_audit_generate(
    body: GenerateRequest,
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: Session = Depends(get_db),
):
    """Dry-run generate + synchronous self-audit → signed cert. No PR, no writes to master.

    Returns the generated proposal + a verify_certificate-valid JSON-LD cert with a
    real fidelity_score. The audit subject rows are inert records (see soul_self_audit).
    """
    agent_id = _require_agent(x_agent_key, db)
    from services.soul_service import generate
    from services.soul_self_audit import run_self_audit
    import time

    base_dir = os.getenv("SOUL_WORKSPACE", ".")
    cycle_id = f"api-{agent_id}-{int(time.time())}"
    gen = generate(body.task_spec, base_dir=base_dir, cycle_id=cycle_id, capture_content=True)
    if not gen["success"]:
        return {"success": False, "data": {"cycle_id": cycle_id, "check_result": gen["check_result"]},
                "error": "generation checks failed"}

    # output for fidelity = concatenated generated content (Phase 0.2 pins the content source)
    output = "\n\n".join(
        f"# {f['path']}\n{f.get('content', '')}" for f in gen["files_planned"]
    ) or body.task_spec
    bounty_id = f"soul-audit-api-{agent_id}-{cycle_id[-10:]}"
    sa = run_self_audit(db, task_spec=body.task_spec, output=output, bounty_id=bounty_id)
    return {
        "success": bool(sa.get("cert_valid")),
        "data": {
            "cycle_id": cycle_id,
            "files_planned": gen["files_planned"],
            "check_result": gen["check_result"],
            "fidelity_score": sa.get("fidelity_score"),
            "cert": sa.get("cert"),
            "cert_valid": sa.get("cert_valid"),
            "bounty_id": bounty_id,
        },
        "error": None if sa.get("cert_valid") else "cert verification failed",
    }
```
> If Phase 0.2 found dry-run has no `content`, adjust the `output` line per the contingency (e.g. read from the engine result's `.files` map) — keep the test's stub shape matching whatever the endpoint actually consumes.

**Step 4 — Run · expect PASS.**

**Step 5 — Commit:**
```bash
git add phase3/backend/api/soul.py phase3/backend/tests/test_api_soul_audit.py
git commit -m "feat(soul): POST /api/soul/audit-generate · generate + self-audit + signed cert (no PR)"
```

### Task 1.3: Push canonical to origin

**Step 1 — Confirm only the soul slice is in this push** (do NOT drag the 6 unrelated doc commits or mvp's 154 uncommitted): `git log --oneline origin/master..HEAD` should show only the Task 1.1/1.2 commits (work on a feature branch off origin/master, not local master-ahead-6).

**Step 2 — Push** (via Pre-flight #1 path). If using cloud keyring: push the branch from a cloud clone; if local fine-grained PAT: `git push -u origin soul-api-increment4`.

**Step 3 — Open a normal (non-draft) PR or fast-forward** per user preference — but for *this* slice, merging to origin/master is the point (it's the canonical source). Confirm with user before merge if uncertain.

> **Checkpoint after Phase 1:** origin/master (or the feature branch) now carries soul_service + soul_pr_gate + the 3 cert files + the new endpoint + tests, all green. Report before Phase 2.

---

## Phase 2: Deploy the slice onto the live backend (`~/nautilus-mvp` :8000)

> Minimal sync — only the soul slice files, on a clean feature branch off mvp's current state. Do NOT pull origin/master wholesale into mvp (that's the 79-commit reconciliation = out of scope).

### Task 2.1: Stage files on a mvp feature branch

**Step 1 — Branch off mvp's current HEAD** (preserve the running state):
```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && git stash list | head && git checkout -b soul-api-increment4-deploy'
```
(If the working tree is dirty per Phase 0.5, decide per-file: the soul slice files we overwrite are the target; leave unrelated dirty files alone.)

**Step 2 — Sync the canonical files from origin** (fetch + checkout specific paths only):
```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && git fetch origin && \
  git checkout origin/master -- ../backend/api/soul.py services/soul_service.py services/soul_pr_gate.py services/soul_self_audit.py services/audit_cert_generator.py services/raid_fidelity_checker.py 2>&1'
```
> Path note: confirm the repo-relative paths (mvp layout may differ slightly). Use `git checkout origin/<branch> -- <path>` so ONLY those files change.

**Step 3 — Verify each file parses + imports:**
```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && for f in api/soul.py services/soul_service.py services/soul_self_audit.py; do python -c "import ast; ast.parse(open(\"$f\").read())" && echo "ast OK $f"; done'
```

### Task 2.2: Register the soul router in mvp `main.py`

**Files:** Modify: `phase3/backend/main.py`

**Step 1 — Find how other routers are registered** (`grep -n "include_router" main.py | head`), match the existing pattern + prefix convention.

**Step 2 — Add** (matching existing style):
```python
from api import soul as soul_api
app.include_router(soul_api.router, prefix="/api/soul", tags=["soul"])
```

**Step 3 — Boot-test in a scratch process on a spare port** (NEVER restart :8000 until this passes):
```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && timeout 15 python -m uvicorn main:app --port 8765 & sleep 8 && \
  curl -s -o /dev/null -w "health:%{http_code}\n" http://localhost:8765/health && \
  curl -s -o /dev/null -w "soul:%{http_code}\n" -X POST http://localhost:8765/api/soul/audit-generate -H "X-Agent-Key: bad" -d "{\"task_spec\":\"xxxxxxxxxxxxxxxxxxxxx\"}"'
```
Expected: `health:200`, `soul:401` (bad key rejected = route registered + auth working). If health regresses → STOP, the router import broke something; do not restart :8000.

**Step 4 — Run the test suite on cloud:**
```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && python -m pytest tests/test_soul_self_audit.py tests/test_api_soul_audit.py -v -m "not integration"'
```

**Step 5 — Commit on the deploy branch** (pathspec):
```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && git add api/soul.py services/soul_service.py services/soul_pr_gate.py services/soul_self_audit.py services/audit_cert_generator.py services/raid_fidelity_checker.py main.py && git commit -m "deploy(soul): /api/soul/audit-generate on live backend (slice synced from origin)"'
```

### Task 2.3: Restart the live :8000 backend

> This is the only production-touching, harder-to-reverse step. Confirm Task 2.2 boot-test passed on the spare port first.

**Step 1 — Identify restart mechanism** (`systemctl status` for a nautilus backend unit, or the supervisor that owns pid 1258398). Use the project's existing restart path — do NOT bare `kill`.

**Step 2 — Restart, then immediately verify:**
```bash
ssh cloud 'curl -s -o /dev/null -w "health:%{http_code}\n" http://localhost:8000/health && \
  curl -s -o /dev/null -w "soul-route:%{http_code}\n" -X POST http://localhost:8000/api/soul/audit-generate -H "X-Agent-Key: bad" -d "{\"task_spec\":\"xxxxxxxxxxxxxxxxxxxxx\"}"'
```
Expected: `health:200`, `soul-route:401`. Plus spot-check 1-2 pre-existing endpoints (e.g. an agents/stats route) still 200 → no regression.

**Step 3 — Rollback path if anything regresses:** `git checkout soul-audit-increment1 -- main.py` (revert router) + restart. The synced service files are additive (new routes only); reverting `main.py` un-registers them.

> **Checkpoint after Phase 2:** live :8000 serves `/api/soul/audit-generate` (401 on bad key), health green, no regression. Report before Phase 3.

---

## Phase 3: Binding DONE — real platform-agent E2E

**Step 1 — Make the real call** with a genuine platform agent key (from Phase 0.4 · value on cloud only):
```bash
ssh cloud 'curl -s -X POST http://localhost:8000/api/soul/audit-generate \
  -H "X-Agent-Key: <REAL_V5_KEY>" -H "Content-Type: application/json" \
  -d "{\"task_spec\":\"Add a function add(a, b) that returns their sum to scratch/mathx.py with a docstring.\"}" | python -m json.tool'
```

**Step 2 — VERIFY the binding DONE — ALL must be true** (verification-before-completion · evidence before claims):
- [ ] HTTP 200
- [ ] `data.cert_valid == true`
- [ ] `data.fidelity_score` is a real number in (0,1] from `check_fidelity` (not null, not hardcoded)
- [ ] `data.cert` is a JSON-LD object with `audit_id` + `signature`
- [ ] Re-verify independently: `python -c "from services.audit_cert_generator import verify_certificate; import json,sys; print(verify_certificate(json.load(sys.stdin)))"` fed the returned `cert` → `{'valid': True}`
- [ ] Tamper check: mutate one cert field → `verify_certificate` → `valid: False`
- [ ] The call was authenticated as a **real platform agent** (agent_id resolved from a real active APIKey), not a fabricated key

**Step 3 — Capture evidence** (the actual JSON response + the verify output) into the result log. State pass/fail honestly with the real output.

**Step 4 — Commit deploy branch state + STOP.** Do NOT start any parking-lot item. Write the session memory with the real evidence.

---

## Out of scope (→ PARKING_LOT_soul_trinity_20260527.md · do not touch)

Full 79-commit origin↔mvp reconciliation · mvp's 154 uncommitted files + 5 stash · draft-PR-per-call (PAT path) · real V5/Kairos async council (increment 2 · current fidelity is platform-run heuristic, label it honestly) · compass PoI in cert · external/multi-tenant codegen API · cron-wiring + 3 safety gates · Stage 2 recursive driver · Soul+V7.

## Risk + Rollback

- **Phase 1** (origin): additive files + new route · zero runtime risk · push is reversible (revert commit).
- **Phase 2.3** (restart :8000): the only production-touching step. Router include is additive (new `/api/soul/*` routes only); pre-existing routes unchanged. Boot-tested on spare port 8765 BEFORE the real restart. Rollback = `git checkout … main.py` + restart (un-registers soul routes).
- **Per-call DB writes:** `run_self_audit` inserts inert audit-subject rows (bounty + raid_execution + raid_vote · reward_nau=0 · status=completed). No economic effect, no master writes, no auto-merge. Cleanable by `bounty_id` prefix `soul-audit-api-`.

## Done Criteria (binding · re-stated)

One real authenticated platform-agent HTTP call to `/api/soul/audit-generate` on live :8000 returns `cert_valid=true` + real `fidelity_score`, independently `verify_certificate`-confirmed valid, with no regression to existing endpoints. Then STOP and report with the captured response as evidence.

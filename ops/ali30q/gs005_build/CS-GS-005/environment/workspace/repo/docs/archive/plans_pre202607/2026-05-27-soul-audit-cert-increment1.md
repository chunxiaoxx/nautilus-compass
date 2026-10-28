# Soul→Audit→Cert · Increment 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
> **Run in a FRESH session + git worktree** (this session is a long brainstorm+plan; R3). Design: `2026-05-27-soul-trinity-product-vision-design.md`. Scope frozen — new ideas go to `PARKING_LOT_soul_trinity_20260527.md`, NOT into this plan.
>
> ## 🟢 EXECUTION STATUS (5/27 · BINDING DONE ACHIEVED + independently verified)
> All 5 tasks done. Real E2E PASS: Soul (DeepSeek) generated scratch/greet.py → draft PR #50 (github.com/chunxiaoxx/nautilus-core/pull/50 · gh isDraft:true) → self-audit (raid_fidelity_checker fidelity 0.25 on real diff) → signed JSON-LD cert → posted to PR (gh api confirmed) → verify_certificate valid=True. Workspace unified by copying 3 audit files into `~/nautilus-soul-workspace`. Code on cloud `~/nautilus-mvp:soul-audit-increment1` (5 unit tests green). Increment 2 (real V5/Kairos council · current fidelity is platform inline heuristic) + local↔cloud reconciliation → parking lot. PR #50 is a demo artifact (do not merge).
>
> ## (original partial-status note · superseded by above)
> - Cloud branch `soul-audit-increment1` off `~/nautilus-mvp` master.
> - ✅ Task 1 `run_self_audit` (2 unit tests green · committed — but in a messy no-pathspec commit on the throwaway branch).
> - ✅ Task 2 `persist_self_audit_rows` + **cert pipeline PROVEN on real cloud DB** (verify_certificate valid=True · tamper→signature_mismatch). persist code uncommitted when SSH died.
> - ⚠️ Task 3 `attach_cert_to_pr` append interrupted by SSH reset — VERIFY file integrity first (`wc -l` + `ast.parse` + grep 3 defs).
> - 🔴 BLOCKER (Task 4-5): `soul_service.py` is NOT on cloud (Soul services local-only, audit services cloud-only · 79-commit divergence). Full chain (Soul ship→PR + audit→cert) needs both in one workspace. = reconciliation slice.
> - Next session: revoke token → verify file → pathspec commit → resolve workspace-unification blocker → Task 4-5.

**Goal:** Soul's generated output gets a synchronous self-audit + a cryptographically signed JSON-LD certificate attached to its draft PR — proving the Soul→audit→cert pipe end-to-end on our own repo.

**Binding DONE (do not exceed):** One real cycle produces a **draft PR on `chunxiaoxx/nautilus-core` carrying a certificate that `verify_certificate()` validates (valid=True)**, with a real `fidelity_score` from `raid_fidelity_checker`. Nothing else.

**Architecture:** New thin orchestrator `services/soul_self_audit.py` on the **cloud backend** (`~/nautilus-mvp/phase3/backend` — where engine + `audit_service` + `audit_cert_generator` + `raid_fidelity_checker` + `soul_service` all co-exist; avoids the local↔cloud 79-commit divergence). It wraps a Soul output: create finalized bounty + raid_execution + raid_vote rows → `generate_certificate` → `verify_certificate` → post cert as a `gh pr` comment. The agent council (real V5/Kairos async judging) is Increment 2 (parking lot); Increment 1 runs the same `check_fidelity` inline and labels it honestly as platform-run.

**Tech Stack:** Python 3.11 · FastAPI · SQLAlchemy (raw `text()` SQL, matches audit_service style) · existing `services/audit_cert_generator.py` (HMAC-SHA256 JSON-LD) · `services/raid_fidelity_checker.py` · `services/soul_service.py` · `gh` CLI.

---

## Pre-flight (✅ CONFIRMED 5/27 — see inline CONFIRMED notes)

> Done this session: gh auth ✓ (chunxiaoxx · keyring · not exposed PAT → push works) · AUDIT_CERT_SECRET NOT SET (MVP default · cert self-verifies · strong secret → parking lot) · `check_fidelity(task_spec, output)->dict` ✓ · 3 table schemas dumped + INSERTs corrected (raid_executions raid_level+status NOT NULL were missing — fixed). Worktree isolation still required at execution.

### Original pre-flight checklist (confirm before Task 1 · do NOT assume)

All on cloud: `ssh cloud 'cd ~/nautilus-mvp/phase3/backend && ...'`

1. **Worktree isolation:** create a worktree off `~/nautilus-mvp` master for this work (or a feature branch). NEVER edit files in-place on the running backend until tests pass.
2. **Confirm exact schemas** (the plan's INSERTs depend on these — read, don't guess):
   - `\d platform_bounties` — confirm columns: `bounty_id, title, description, reward_nau, task_type, status, posted_by, channel, source, posted_at, deadline, metadata, escrow_locked_nau, result, score`.
   - `\d raid_executions` — confirm: `execution_id, task_id, consensus_score, created_at`.
   - `\d raid_votes` — confirm: `execution_id, fidelity_score, quality_score, agent_role`.
3. **Confirm interfaces** (read source):
   - `services/raid_fidelity_checker.py::check_fidelity(task_spec: str, output: str) -> dict` (key `fidelity_score`).
   - `services/audit_cert_generator.py::generate_certificate(db, bounty_id) -> dict` (requires bounty status ∈ settled/rejected/completed + a `raid_executions` row with `task_id=bounty_id` + `raid_votes` for fidelity) and `verify_certificate(cert) -> {valid: bool}`.
   - `services/soul_service.py::ship_to_draft_pr(...)` return shape `{success, pr_url, branch, commit, cycle_id}`.
4. **Secret:** confirm `AUDIT_CERT_SECRET` (or the env var `audit_cert_generator` reads) is set on cloud so signatures are stable. If using MVP default, note it (cert still verifies self-consistently).

---

### Task 1: `soul_self_audit` orchestrator (pure logic · injected deps)

**Files:**
- Create: `services/soul_self_audit.py`
- Test: `tests/test_soul_self_audit.py`

**Step 1: Write the failing test** (fake db + injected fidelity/cert fns — no real DB)

```python
from services import soul_self_audit

class FakeDB:
    def __init__(self): self.executed = []
    def execute(self, *a, **k): self.executed.append((a, k)); return self
    def fetchone(self): return None
    def commit(self): pass

def test_run_self_audit_happy_path():
    db = FakeDB()
    out = soul_self_audit.run_self_audit(
        db, task_spec="add foo()", output="def foo(): return 1",
        bounty_id="soul-audit-test1",
        _check_fidelity=lambda spec, output: {"fidelity_score": 0.82},
        _generate_certificate=lambda db, bid: {"@type": "AuditCertificate", "audit_id": bid, "signature": "x"},
        _verify_certificate=lambda cert: {"valid": True},
    )
    assert out["success"] is True
    assert out["fidelity_score"] == 0.82
    assert out["cert_valid"] is True
    assert out["bounty_id"] == "soul-audit-test1"
```

**Step 2: Run · expect fail** (`ModuleNotFoundError`).
Run: `cd ~/nautilus-mvp/phase3/backend && python -m pytest tests/test_soul_self_audit.py -v`

**Step 3: Implement `run_self_audit`** (orchestration only; SQL helpers in Task 2)

```python
"""Soul self-audit · synchronous fidelity check + signed cert for a Soul output.

Increment 1 (platform-run fidelity · NOT the real V5/Kairos council · that is
Increment 2). Creates a finalized audit-subject bounty + raid_execution +
raid_vote so the existing generate_certificate() can sign a JSON-LD cert.
"""
from __future__ import annotations
from typing import Callable, Optional


def run_self_audit(
    db,
    task_spec: str,
    output: str,
    bounty_id: str,
    quality_score: float = 0.8,
    _check_fidelity: Optional[Callable] = None,
    _generate_certificate: Optional[Callable] = None,
    _verify_certificate: Optional[Callable] = None,
    _persist: Optional[Callable] = None,
) -> dict:
    if _check_fidelity is None:
        from services.raid_fidelity_checker import check_fidelity as _check_fidelity
    if _generate_certificate is None:
        from services.audit_cert_generator import generate_certificate as _generate_certificate
    if _verify_certificate is None:
        from services.audit_cert_generator import verify_certificate as _verify_certificate
    if _persist is None:
        from services.soul_self_audit import persist_self_audit_rows as _persist

    fid = float(_check_fidelity(task_spec, output).get("fidelity_score") or 0.0)
    _persist(db, bounty_id, task_spec, output, fidelity_score=fid, quality_score=quality_score)
    cert = _generate_certificate(db, bounty_id)
    if cert.get("error"):
        return {"success": False, "stage": "cert", "detail": cert, "bounty_id": bounty_id}
    valid = bool(_verify_certificate(cert).get("valid"))
    return {
        "success": valid, "bounty_id": bounty_id,
        "fidelity_score": fid, "cert": cert, "cert_valid": valid,
    }
```

**Step 4: Run · expect PASS.**

**Step 5: Commit**
```bash
git add services/soul_self_audit.py tests/test_soul_self_audit.py
git commit -m "feat(soul): self-audit orchestrator (injected deps · pure logic)"
```

---

### Task 2: `persist_self_audit_rows` (real SQL · finalized bounty + raid rows)

**Files:**
- Modify: `services/soul_self_audit.py`
- Test: `tests/test_soul_self_audit_persist.py` (integration · real cloud DB · marked)

**Step 1: Write integration test** (uses a real DB session + unique bounty_id; asserts `generate_certificate` then succeeds)

```python
import uuid, pytest
from services import soul_self_audit
from services.audit_cert_generator import generate_certificate, verify_certificate

@pytest.mark.integration
def test_persist_then_cert_real_db(db_session):  # db_session fixture = real SessionLocal()
    bid = f"soul-audit-it-{uuid.uuid4().hex[:8]}"
    soul_self_audit.persist_self_audit_rows(
        db_session, bid, task_spec="add greet()", output="def greet(): return 'hi'",
        fidelity_score=0.77, quality_score=0.8,
    )
    cert = generate_certificate(db_session, bid)
    assert "error" not in cert, cert
    assert verify_certificate(cert)["valid"] is True
    assert cert["audit_id"] == bid
```

**Step 2: Run · expect fail** (`persist_self_audit_rows` missing).

**Step 3: Implement `persist_self_audit_rows`** — confirm exact columns in pre-flight #2 first, then:

```python
def persist_self_audit_rows(db, bounty_id, task_spec, output, fidelity_score, quality_score=0.8):
    from sqlalchemy import text
    import uuid
    # 1. finalized audit-subject bounty (status='completed' so generate_certificate accepts it)
    db.execute(text(
        "INSERT INTO platform_bounties "
        "(bounty_id, title, description, reward_nau, task_type, status, posted_by, "
        " channel, source, posted_at, result, score, metadata) "
        "VALUES (:b, :title, :desc, 0, 'platform_meta', 'completed', 'soul', "
        " 'soul-self-audit', 'api.soul.self_audit', now(), :result, :score, "
        " '{\"self_audit\": true}'::jsonb) ON CONFLICT (bounty_id) DO NOTHING"
    ), {"b": bounty_id, "title": f"soul self-audit · {task_spec[:80]}",
        "desc": task_spec[:2000], "result": output[:8000], "score": quality_score})
    # 2. raid_execution (generate_certificate joins raid_votes via execution_id)
    # NOTE: raid_level + status are NOT NULL with no default (confirmed 5/27 pre-flight) — must provide.
    exec_id = f"selfaudit-{uuid.uuid4().hex[:12]}"
    db.execute(text(
        "INSERT INTO raid_executions (execution_id, task_id, raid_level, status, consensus_score, created_at) "
        "VALUES (:e, :t, 1, 'completed', :c, now()) ON CONFLICT (execution_id) DO NOTHING"
    ), {"e": exec_id, "t": bounty_id, "c": round(quality_score * fidelity_score, 3)})
    # 3. raid_vote with the platform-run fidelity (agent_role labels it honestly)
    db.execute(text(
        "INSERT INTO raid_votes (execution_id, agent_role, fidelity_score, quality_score) "
        "VALUES (:e, 'platform-self-audit', :f, :q)"
    ), {"e": exec_id, "f": fidelity_score, "q": quality_score})
    db.commit()
    return exec_id
```

> CONFIRMED (5/27 pre-flight): `raid_votes` NOT-NULL cols = `execution_id, agent_role` only (`fidelity_score, quality_score` nullable) — the INSERT above is complete. `platform_bounties` NOT-NULL no-default = `bounty_id, title, reward_nau` (all provided). `raid_executions` NOT-NULL no-default = `execution_id, task_id, raid_level, status` (now provided).

**Step 4: Run integration test · expect PASS** (`pytest -m integration tests/test_soul_self_audit_persist.py -v`).

**Step 5: Commit**
```bash
git add services/soul_self_audit.py tests/test_soul_self_audit_persist.py
git commit -m "feat(soul): persist self-audit rows · finalized bounty + raid_execution + raid_vote"
```

---

### Task 3: attach cert to the draft PR (gh pr comment)

**Files:**
- Modify: `services/soul_self_audit.py`
- Test: `tests/test_soul_self_audit.py` (add mocked-subprocess test)

**Step 1: Failing test** (mock `subprocess.run`, assert `gh pr comment` called with cert)

```python
def test_attach_cert_to_pr_invokes_gh(monkeypatch):
    calls = []
    def fake_run(cmd, **k):
        calls.append(cmd)
        class R: returncode = 0; stdout = ""; stderr = ""
        return R()
    out = soul_self_audit.attach_cert_to_pr(
        pr_url="https://github.com/chunxiaoxx/nautilus-core/pull/9",
        cert={"audit_id": "x", "signature": "sig", "@context": "https://nautilus.social/audit/v1"},
        base_dir="/tmp/repo", _runner=fake_run,
    )
    assert out is True
    assert any("pr" in c and "comment" in c for c in calls if isinstance(c, list))
```

**Step 2: Run · expect fail.**

**Step 3: Implement `attach_cert_to_pr`**

```python
import json, subprocess

def attach_cert_to_pr(pr_url, cert, base_dir, _runner=subprocess.run):
    body = (
        "## 🔏 Nautilus Audit Certificate\n\n"
        f"- audit_id: `{cert.get('audit_id')}`\n"
        f"- algorithm: `{cert.get('certificate_version','HMAC-SHA256-MVP')}`\n"
        f"- verify: `GET /api/v1/audit/{cert.get('audit_id')}/verify`\n\n"
        "```json\n" + json.dumps(cert, ensure_ascii=False, indent=2)[:6000] + "\n```"
    )
    r = _runner(["gh", "pr", "comment", pr_url, "--body", body],
                cwd=base_dir, capture_output=True, text=True)
    return getattr(r, "returncode", 1) == 0
```

**Step 4: Run · expect PASS. Commit.**
```bash
git add services/soul_self_audit.py tests/test_soul_self_audit.py
git commit -m "feat(soul): attach signed cert as draft-PR comment"
```

---

### Task 4: wire self-audit into the Soul ship path

**Files:**
- Modify: `services/soul_service.py::ship_to_draft_pr` (add optional `self_audit: bool = False` + `db=None`)
- Test: `tests/test_soul_service_self_audit.py`

**Step 1: Failing test** — when `self_audit=True` and ship succeeds, `run_self_audit` + `attach_cert_to_pr` are called; result carries `cert_valid`.

**Step 2: Run · expect fail.**

**Step 3: Implement** — after the existing successful draft-PR block (soul_service.py:117), if `self_audit and db is not None`:
```python
    if self_audit and db is not None:
        from services.soul_self_audit import run_self_audit, attach_cert_to_pr
        sa = run_self_audit(db, task, dry["files_planned"] and "\n".join(
            f"# {f['path']}" for f in dry["files_planned"]) or task, bounty_id=f"soul-audit-{cycle_id}")
        if sa.get("cert_valid") and pr_url:
            attach_cert_to_pr(pr_url, sa["cert"], base_dir)
        ret["cert_valid"] = sa.get("cert_valid")
        ret["cert"] = sa.get("cert")
```
(thread `output` = the generated file contents, not just paths — confirm what `check_fidelity` expects; use concatenated block content for a meaningful fidelity signal.)

**Step 4: Run · expect PASS. Commit.**

---

### Task 5: full-suite + END-TO-END acceptance (the binding DONE · real run on cloud)

**Step 1: Unit + integration suites green**
```bash
cd ~/nautilus-mvp/phase3/backend && python -m pytest tests/test_soul_self_audit*.py tests/test_soul_service_self_audit.py -v
python -m pytest engine/tests/ -q --tb=no   # 196 green · no regression
```

**Step 2: REAL end-to-end (verification 铁律 · 真跑 · 不嘴上说通过)**

On a clean origin-synced workspace clone:
```bash
# trivial real task so the diff is tiny + safe
python -c "
from services.soul_service import ship_to_draft_pr
from utils.database import SessionLocal
db = SessionLocal()
r = ship_to_draft_pr(
    task='Add a docstring to scratch/greet.py explaining it returns a greeting.',
    base_dir='<clean-workspace>', branch='soul/audit-cert-e2e-1',
    commit_msg='soul: docstring + self-audit cert e2e', cycle_id='e2e-cert-1',
    self_audit=True, db=db,
)
print(r)
"
```

**Step 3: VERIFY the binding DONE — all must be true:**
- [ ] a **draft PR** exists on `chunxiaoxx/nautilus-core` (check `gh pr view <url>`)
- [ ] the PR has a **comment containing the certificate** JSON
- [ ] `verify_certificate(cert)["valid"] is True` (re-run on the returned cert)
- [ ] the cert's `fidelity_score` is a real number from `check_fidelity` (not None/hardcoded)
- [ ] `GET /api/v1/audit/<bounty_id>/verify` returns valid (tamper-check via the live public endpoint)

**Step 4: Commit + STOP.** Do not start Increment 2. Log result honestly (pass/fail with the actual PR URL + cert verify output).
```bash
git add -A services/ tests/ && git commit -m "test(soul): Soul→audit→cert increment 1 · e2e verified (PR + valid cert)"
```

---

## Out of scope (Increment 1 · all → PARKING_LOT)
Real V5/Kairos async council · compass PoI in cert (best-effort hook already fires) · external codegen API (A) · cron-wiring/3 gates · Stage 2 · local↔cloud reconciliation · Soul+V7.

## Risk + Rollback
- Low: only creates audit-subject DB rows + a DRAFT PR + a comment. No master writes, no auto-merge, no production behavior change.
- Rollback: delete the draft PR + branch; the self-audit bounty rows are inert records (can be left or deleted by bounty_id).

## Done Criteria (binding · re-stated)
One real cycle → draft PR on our repo + a `verify_certificate`-valid signed cert posted to it + real fidelity_score. Then STOP and report with evidence.

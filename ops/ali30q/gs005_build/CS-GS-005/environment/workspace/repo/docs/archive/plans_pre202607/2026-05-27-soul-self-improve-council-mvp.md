# Soul Self-Improvement Council · MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Give the Soul daemon a recursive self-improvement loop: it reviews its own code, a single-process multi-persona council diverges improvement proposals + a chairman converges to the best, the engine implements it, a pytest gate must pass, then a draft PR opens for human merge. This solves the goal-sourcing bottleneck (no hand-written goals — soul finds real improvements) and is anchor #2's core loop.

**Architecture:** New `phase3/soul/council.py` (multi-persona propose + chairman converge, all via the existing `engine.generate` with persona system-prompts — NO external V5/Kairos agents, avoids dialog boundaries) + new `phase3/soul/reviewer.py` (soul reads a module → understands purpose → emits an improvement goal). The daemon's `run_once` gains a "self-improve" path: reviewer picks a target → council proposes/converges → `ship(apply=True)` → **pytest gate** (`run_pytest_for_changed`, must be green) → draft PR. Scope is soul-only (`phase3/soul/**`), full write permission including the loop itself (pure recursion). Quality is enforced by the pytest gate + draft-PR-human-merge, NOT by restricting what soul may touch.

**Tech Stack:** Python 3.8+ stdlib + PyYAML + existing `engine` (generate/ship/checks/pytest_runner) + DeepSeek via `agent_engine.llm.client` (DEEPSEEK_* env) + `gh` CLI + git.

---

## Locked design decisions (confirm before tasks)

1. **Council = single-process multi-persona** (MVP). N reviewer personas (performance / robustness / readability / correctness) each call `engine.generate` with a persona-specific system prompt to produce a proposal; one chairman persona scores + picks the best. NO V5/Kairos (dialog boundary anchor #7 · slowest). Extensible to real multi-agent later.
2. **Scope = `phase3/soul/**` only**, full write permission (incl. council.py / reviewer.py / daemon.py themselves = true recursion). pr_gate blacklist still blocks `.env`/alembic/etc.
3. **Quality gate = pytest** (`run_pytest_for_changed`, green required) on top of static checks. This is the keystone — it lets soul change real logic safely because broken changes fail tests.
4. **goal = substantive improvement** (logic/robustness/refactor), not just docstrings. reviewer must articulate the module's PURPOSE first, then what would make it better.
5. **HARD PREREQ:** fix check-pipeline staging import (Task 1) — soul's own modules nearly all have internal imports; without this every change fails import-check.
6. Draft PR never auto-merges. Timer activation stays a separate human-gated step (not in this MVP).

---

## Pre-flight

Run: `cd /c/Users/chunx/Projects/nautilus-core && git fetch origin master && git log origin/master --oneline -1`
Expected: `0985a8080` or later.

Read the bottleneck memory `session_20260527_soul_apply_pr_goal_sourcing_bottleneck.md` (why this exists) + the dry-run/apply-PR findings: DeepSeek reads `DEEPSEEK_*` env · client at `backend/agent_engine/llm/client.py` (multi-provider) · `ship.py` apply path at 160-195 · `run_pytest_for_changed` at `pytest_runner.py:31` (returns True/False/None) · `run_pipeline` at `checks.py:743`.

Work in an isolated worktree (using-git-worktrees · use repo-root `_siblings/<branch>`, NOT `phase3/_siblings` — that was a cwd bug this session). Build locally + test; cloud E2E via cloud clone with DEEPSEEK_* in `.soul-env`.

---

### Task 1: Fix check-pipeline staging import (HARD PREREQ)

**Problem:** `run_pipeline` runs import/compile checks on files in an isolated staging tempdir. Files with internal imports (`from engine.x import y`) fail because the staging dir has no package context. Fix: pass the real repo's relevant dirs on `PYTHONPATH` (or `sys.path`) to the check subprocess so staged files resolve internal imports.

**Files:**
- Modify: `phase3/backend/engine/checks.py` (the import-check subprocess · ~line 124 or 190 · find the one that does `python -c "import ..."` or runs the file)
- Modify: `phase3/backend/engine/ship.py` (pass `base_dir` through to `run_pipeline` if needed)
- Test: `phase3/backend/engine/tests/test_checks.py` (or wherever checks tests live)

**Step 1:** Read `checks.py` around the import-check subprocess. Identify how it invokes the staged file and what env it passes.

**Step 2: Write failing test** — a staged file `from engine.text_utils import truncate` should PASS import-check when `pythonpath=<backend>` is provided, FAIL without. (Use a tmp staging dir + a real importable target.)

**Step 3: Run · expect fail.**

**Step 4: Implement** — add a `pythonpath: str | None = None` param threaded run_pipeline → import-check; set `env={**os.environ, "PYTHONPATH": pythonpath + os.pathsep + os.environ.get("PYTHONPATH","")}` on the subprocess. ship passes `base_dir` (or `base_dir/backend`).

**Step 5: Run · expect pass. Step 6: Commit** `fix(engine): check-pipeline import-check honors PYTHONPATH (unblocks import-bearing files)`

**VERIFY no engine regression:** `cd phase3/backend/engine && python -m pytest -q` → 196+ passed.

---

### Task 2: Wire pytest gate into daemon

**Files:**
- Modify: `phase3/soul/daemon.py` (after ship apply + before/with pr_gate)
- Test: `phase3/soul/tests/test_daemon.py`

**Step 1: Failing test** — when `run_pytest_for_changed` returns False, daemon aborts branch + record_failure + no PR. When True or None (no tests · don't block), proceeds.

**Step 2-4: TDD** — in `run_once` after `result.applied` confirmed: call `from engine.pytest_runner import run_pytest_for_changed`; `tests_ok = run_pytest_for_changed(changed_paths, base_dir=repo)`; if `tests_ok is False` → `_abort_branch` + record_failure + return 1. (None = no tests found · proceed · don't bias.)

**Step 5: Commit** `feat(soul): pytest gate · failing tests abort the cycle (no PR on red)`

---

### Task 3: council.py · multi-persona propose + chairman converge

**Files:**
- Create: `phase3/soul/council.py`
- Test: `phase3/soul/tests/test_council.py`

**Interface:**
```python
PERSONAS = ("performance", "robustness", "readability", "correctness")

def propose(engine, task: str, context: str, personas=PERSONAS) -> list[dict]:
    """Each persona calls engine.generate with a persona system-prompt.
    Returns [{"persona":..., "rationale":..., "raw":<engine output>}]."""

def converge(engine, proposals: list[dict], task: str) -> dict:
    """Chairman persona scores proposals + returns the winning one
    {"persona":..., "raw":..., "score":..., "reason":...}."""
```

**Step 1: Failing tests (engine mocked)** — `propose` returns one entry per persona (mock engine.generate returns persona-tagged text). `converge` returns the highest-scored proposal (mock chairman returns a parseable score/selection).

**Step 2-4: TDD** — implement persona system-prompts (each focuses its lens; reuse engine's fenced-block output convention) + chairman prompt (input = N proposals, output = pick + score + reason · parse defensively · fail-safe: if parse fails, pick proposal[0]).

**Step 5: Commit** `feat(soul): council · multi-persona propose + chairman converge (single-process)`

---

### Task 4: reviewer.py · understand purpose → improvement goal

**Files:**
- Create: `phase3/soul/reviewer.py`
- Test: `phase3/soul/tests/test_reviewer.py`

**Interface:**
```python
def pick_target(soul_dir: Path) -> Optional[Path]:
    """Pick a soul module to review this cycle (round-robin / least-recently-reviewed
    via a small state file · MVP: first module not reviewed today)."""

def review(engine, module_path: Path) -> Optional[dict]:
    """soul reads the module → articulates its PURPOSE → proposes ONE concrete
    improvement. Returns {"target": path, "purpose":..., "description": <goal for engine>}
    or None if the module is already good."""
```

**Step 1: Failing tests** — `pick_target` returns a soul `.py` (skips tests/__init__). `review` (engine mocked to return purpose+improvement JSON) returns a goal dict with a `description` usable as an engine task. None when LLM says "no improvement needed".

**Step 2-4: TDD** — review prompt: "Read this module. State its purpose in one sentence. Then propose ONE concrete, safe improvement (logic/robustness/clarity) as a MINIMAL CHANGE task, or say NONE." Parse defensively.

**Step 5: Commit** `feat(soul): reviewer · understand module purpose → one improvement goal`

---

### Task 5: daemon self-improve path (wire it together)

**Files:**
- Modify: `phase3/soul/daemon.py` (add a self-improve branch · reviewer → council → ship → pytest gate → PR)
- Modify: `phase3/soul/goal_selector.py` (add reviewer as a goal source · priority: yaml > reviewer > reflection > docs)
- Test: `phase3/soul/tests/test_daemon.py`

**Step 1: Failing test** — when no yaml goal, daemon calls reviewer.review on a picked target; if it returns a goal, runs council.propose+converge, ships the winner, pytest gate, draft PR. All mocked. Verify: council invoked, pytest gate invoked, PR opened with the winning proposal.

**Step 2-4: TDD** — integrate. Keep the existing yaml-goal path; reviewer is the fallback that makes the loop self-sustaining. The chosen council winner's `raw` feeds `ship` (or re-generate from winner's task description — decide in execution; prefer feeding the description so ship re-runs checks cleanly).

**Step 5: Commit** `feat(soul): daemon self-improve path · reviewer → council → ship → pytest → PR`

**Full suite:** `cd phase3 && python -m pytest soul/tests/ -q` → all green.

---

### Task 6: Cloud E2E (manual · fresh session w/ cloud)

```bash
ssh cloud "cd ~/nautilus-soul-workspace && git fetch origin master && git reset --hard origin/master"
ssh cloud "cd ~/nautilus-soul-workspace/phase3 && set -a && source ../.soul-env && set +a && python3 -m soul.daemon"
```

Expected: reviewer picks a soul module → states purpose → council proposes/converges a real improvement → ship applies → pytest green → **draft PR with a substantive code change** (not a no-op). Verify `gh pr diff` shows real logic/clarity improvement + tests pass. Human reviews.

---

## Out of Scope (MVP)
- Real multi-agent council (V5/Kairos) · cross-dialog (anchor #7 · later)
- Expanding scope beyond `phase3/soul/**` (platform/agent code · later stages)
- Timer auto-activation (separate human-gated step)
- Reflection/docs goal sources (reviewer is the MVP self-sustaining source)

## Risk + Rollback
- **High blast radius**: soul changes its own logic (incl. the loop). Mitigations: pytest gate (broken logic fails tests → no PR) · isolated branch (master untouched) · draft-only + human merge · pr_gate blacklist · budget cap · circuit-breaker · scope-limited to phase3/soul.
- **Recursion risk**: soul could change council/reviewer/daemon in a way that breaks itself. The pytest gate + the fact that the *running* daemon is the origin/master version (not the PR branch) until a human merges = a bad self-edit lands only as an unmerged draft PR. Human merge is the circuit.
- **Rollback**: don't merge bad PRs · `rm -rf ~/nautilus-soul-workspace` · no production impact.

## Done Criteria (MVP)
1. check-pipeline import fix (Task 1) · engine 196+ tests still green
2. pytest gate wired (Task 2)
3. council propose+converge (Task 3) + reviewer (Task 4) · unit tested
4. daemon self-improve path (Task 5) · full soul suite green
5. Cloud E2E: ONE substantive draft PR from an autonomous review→council→ship→pytest cycle (real code improvement · tests pass · not a no-op)

## Execution note
Fresh session (R3 · the planning session was very long). Use a fine-grained PAT (chat-exposed tokens revoked · see `action_token_revoke_20260527.md`). DeepSeek key on cloud `.soul-env` (rotate the chat-exposed one).

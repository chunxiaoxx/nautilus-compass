# Soul L2 · platform-scope self-improve + dedup fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or subagent-driven-development) to implement this plan task-by-task.

**Goal:** Widen the soul self-improve cycle from `phase3/soul/` only to a config-driven scope that also covers the soul's own engine + soul service layer (NOT agent cognitive code), so the autonomous daemon stops idling once soul modules are exhausted — while keeping every existing safety gate intact.

**Architecture:** `reviewer.pick_target` becomes scope-aware (collects eligible `.py` from a glob list relative to repo root, keyed by relative path, with an exclude-substring filter). `config.py` owns the scope as a single source of truth. `daemon._run_self_improve` moves the `has_open_pr_for` dedup check ahead of the LLM calls (cheap skip), derives a collision-safe `goal_id` from `<parent>-<stem>`, makes `pr_title` consistent with `goal_id` (fixes a latent dedup bug), and applies a stricter diff-LOC cap when the target is platform code (outside `phase3/soul/`). Draft-PR + human-merge + pytest gate + throwaway branch stay the backstop.

**Tech Stack:** Python 3.11, pytest, stdlib only (pathlib/json/time/re), gh CLI (already wired in pr_gate).

**Scope locked (anchor #7 — do NOT widen to agent cognitive code):**
- `phase3/soul/*.py` (proven L1 path)
- `phase3/backend/engine/*.py` (soul's own coding engine — platform-dialog owned, has tests)
- `phase3/backend/services/soul_*.py` (soul service layer — platform owned)
- EXCLUDE: everything `pr_gate.PATH_BLACKLIST` already blocks + agent cognitive code (agent_brain, bicameral_mind, curiosity_engine, autonomous_loop, daemon_*, V5/Kairos/compass …). These are NOT in the globs above, so they are excluded by construction; the exclude-substring list is defense-in-depth.

---

## Task 1: config — scope constants

**Files:**
- Modify: `phase3/soul/config.py`
- Test: `phase3/soul/tests/test_config_scope.py` (create)

**Step 1: Write the failing test**

```python
# phase3/soul/tests/test_config_scope.py
"""SELF_IMPROVE_SCOPE config: covers soul+engine+soul-services, never agent code."""
from soul import config


def test_scope_globs_present_and_safe():
    globs = config.SELF_IMPROVE_SCOPE
    assert isinstance(globs, tuple) and globs
    joined = " ".join(globs)
    assert "phase3/soul/*.py" in globs
    assert any("engine" in g for g in globs)
    assert any("soul_*" in g for g in globs)
    # never broadly scan all services (would catch agent cognitive code)
    assert "phase3/backend/services/*.py" not in globs


def test_exclude_extends_blacklist():
    ex = config.SELF_IMPROVE_EXCLUDE
    # everything pr_gate already blocks is also excluded here
    for bad in config.PATH_BLACKLIST:
        assert bad in ex
    # agent cognitive markers explicitly excluded (defense in depth)
    for marker in ("agent_brain", "bicameral_mind", "autonomous_loop"):
        assert marker in ex


def test_platform_loc_cap_stricter_than_default():
    assert config.PLATFORM_MAX_PR_DIFF_LOC < config.MAX_PR_DIFF_LOC
```

**Step 2: Run — expect FAIL** (`AttributeError: SELF_IMPROVE_SCOPE`)

Run: `cd phase3 && PYTHONPATH=backend python -m pytest soul/tests/test_config_scope.py -q`

**Step 3: Implement** — append to `phase3/soul/config.py`:

```python
# Self-improve scope (reviewer.pick_target) · globs relative to REPO_ROOT.
# Anchor #7: ONLY soul + soul's own engine + soul service layer.
# NEVER broad backend/services/*.py (that holds agent cognitive code).
SELF_IMPROVE_SCOPE: tuple = (
    "phase3/soul/*.py",
    "phase3/backend/engine/*.py",
    "phase3/backend/services/soul_*.py",
)
# Exclude substrings: pr_gate blacklist + agent-cognitive defense-in-depth.
SELF_IMPROVE_EXCLUDE: tuple = PATH_BLACKLIST + (
    "agent_brain", "bicameral_mind", "autonomous_loop", "curiosity_engine",
    "agent_parliament", "daemon_", "kairos", "compass", "_v5", "v7_",
)
# Stricter diff cap for platform-code targets (wider blast than soul-only).
PLATFORM_MAX_PR_DIFF_LOC = int(os.getenv("SOUL_PLATFORM_MAX_PR_LOC", "150"))
```

**Step 4: Run — expect PASS.**

**Step 5: Commit** — `git add phase3/soul/config.py phase3/soul/tests/test_config_scope.py && git commit -m "feat(soul): SELF_IMPROVE_SCOPE config (soul+engine+soul-services · anchor #7 safe)"`

---

## Task 2: reviewer — scope-aware pick_target

**Files:**
- Modify: `phase3/soul/reviewer.py`
- Test: `phase3/soul/tests/test_reviewer.py` (extend) + new cases

**Step 1: Write failing tests** (add to `test_reviewer.py`):

```python
def test_collect_eligible_filters_and_dedups(tmp_path):
    from soul import reviewer
    (tmp_path / "phase3" / "soul").mkdir(parents=True)
    (tmp_path / "phase3" / "soul" / "a.py").write_text("x=1")
    (tmp_path / "phase3" / "soul" / "__init__.py").write_text("")
    (tmp_path / "phase3" / "soul" / "tests").mkdir()
    (tmp_path / "phase3" / "soul" / "tests" / "test_a.py").write_text("")
    (tmp_path / "phase3" / "backend").mkdir(parents=True)
    (tmp_path / "phase3" / "backend" / "agent_brain.py").write_text("")  # excluded
    got = reviewer.collect_eligible(
        ("phase3/soul/*.py", "phase3/backend/*.py"),
        ("agent_brain",), tmp_path,
    )
    names = sorted(p.name for p in got)
    assert names == ["a.py"]  # __init__, tests/, agent_brain all filtered


def test_pick_target_scoped_rotates_by_relpath(tmp_path):
    from soul import reviewer
    soul = tmp_path / "phase3" / "soul"; soul.mkdir(parents=True)
    (soul / "a.py").write_text("x=1")
    (soul / "b.py").write_text("y=2")
    state = tmp_path / ".state.json"
    first = reviewer.pick_target(soul, state_file=state,
                                 scope_globs=("phase3/soul/*.py",), repo_root=tmp_path)
    second = reviewer.pick_target(soul, state_file=state,
                                  scope_globs=("phase3/soul/*.py",), repo_root=tmp_path)
    assert first != second  # least-recently-reviewed rotation across the two
```

**Step 2: Run — expect FAIL** (`collect_eligible` missing / scope_globs unsupported).

**Step 3: Implement** — in `reviewer.py`:

Add `collect_eligible(scope_globs, exclude_substrings, repo_root) -> list[Path]`:
- iterate `repo_root.glob(pattern)` for each glob, sorted
- keep only `is_file()` + `.py`, skip `__init__.py`, skip if `"tests" in p.parts`
- compute `rp = p.relative_to(repo_root).as_posix()`; skip if any `bad in rp` for exclude; dedup via a `seen` set
- return list

Extend `pick_target(soul_dir, state_file=None, *, scope_globs=None, exclude=(), repo_root=None)`:
- if `scope_globs`: `eligible = collect_eligible(scope_globs, exclude, repo_root)`; `key = lambda p: p.relative_to(repo_root).as_posix()`
- else: existing soul-only collection; `key = lambda p: p.name`
- shared rotation: sort by `state.get(key(p), 0)`, pick `[0]`, record `state[key(chosen)] = time.time()`, save
- `if not eligible: return None`

Keep the existing soul-only branch byte-identical in behavior (back-compat for any caller without scope_globs).

**Step 4: Run — expect PASS** (new + all existing reviewer tests).

**Step 5: Commit** — `git add phase3/soul/reviewer.py phase3/soul/tests/test_reviewer.py && git commit -m "feat(soul): scope-aware pick_target (glob collection + relpath rotation + exclude)"`

---

## Task 3: daemon — early dedup, collision-safe goal_id, consistent pr_title, platform LOC cap

**Files:**
- Modify: `phase3/soul/daemon.py`
- Test: `phase3/soul/tests/test_daemon.py` (extend)

**Step 1: Write failing tests** (add to `test_daemon.py`, monkeypatching reviewer/council/pr_gate as existing tests do):

```python
def test_self_improve_skips_before_llm_when_pr_open(monkeypatch, tmp_path):
    """has_open_pr_for True → no review/council LLM calls happen."""
    from soul import daemon, reviewer, council, pr_gate
    target = tmp_path / "phase3" / "soul" / "config.py"
    target.parent.mkdir(parents=True); target.write_text("x=1")
    monkeypatch.setattr(reviewer, "pick_target", lambda *a, **k: target)
    called = {"review": False}
    monkeypatch.setattr(reviewer, "review",
                        lambda *a, **k: called.__setitem__("review", True) or {"description": "d", "purpose": "p"})
    monkeypatch.setattr(pr_gate, "has_open_pr_for", lambda gid: True)
    monkeypatch.setattr(daemon, "_make_generate_fn", lambda e: (lambda p, system="": ""))
    class _Eng:  # minimal engine stub
        def __init__(self, **k): pass
        def _ensure_llm(self): pass
    rc = daemon._run_self_improve(_Eng, lambda *a, **k: None, str(tmp_path))
    assert rc == 0
    assert called["review"] is False  # skipped before LLM


def test_goal_id_is_parent_stem_slug(monkeypatch, tmp_path):
    """goal_id disambiguates same stem across dirs; pr_title matches goal_id."""
    from soul import daemon
    assert daemon._goal_id_for(tmp_path / "soul" / "config.py", tmp_path) == "selfimprove-soul-config"
    assert daemon._goal_id_for(tmp_path / "engine" / "config.py", tmp_path) == "selfimprove-engine-config"
```

**Step 2: Run — expect FAIL** (`_goal_id_for` missing; dedup order wrong).

**Step 3: Implement** — in `daemon.py`:

1. Add helper:
```python
def _goal_id_for(target: Path, repo: "str | Path") -> str:
    """Collision-safe self-improve goal id: selfimprove-<parent>-<stem>."""
    return f"selfimprove-{target.parent.name}-{target.stem}"
```

2. In `_run_self_improve`, after `pick_target` returns a target (and before `reviewer.review`):
   - call scoped pick: `reviewer.pick_target(soul_dir, scope_globs=SELF_IMPROVE_SCOPE, exclude=SELF_IMPROVE_EXCLUDE, repo_root=Path(repo))`
   - compute `goal_id = _goal_id_for(target, repo)`
   - `if pr_gate.has_open_pr_for(goal_id): log + return 0` (moved up from after council)
   - then proceed to `review` / `council`
   - delete the later (post-council) `has_open_pr_for` block + its `goal_id` reassignment

3. Make `pr_title` consistent: `pr_title = f"soul: {goal_id}"` (so `has_open_pr_for`'s `"soul: {goal_id} in:title"` search actually matches — fixes the latent `self-improve` vs `selfimprove-` mismatch).

4. Platform stricter LOC cap: compute `is_platform = "phase3/soul/" not in target.as_posix()` (here `target` is absolute; use `target.resolve().as_posix()`); pass `max_loc=PLATFORM_MAX_PR_DIFF_LOC if is_platform else MAX_PR_DIFF_LOC` into `_ship_goal`, which forwards it to `pr_gate.check_diff_loc(total_loc, max_loc)`.

5. Import `SELF_IMPROVE_SCOPE, SELF_IMPROVE_EXCLUDE, PLATFORM_MAX_PR_DIFF_LOC, MAX_PR_DIFF_LOC` from `soul.config`.

Update `_ship_goal` signature: add `max_loc: int = MAX_PR_DIFF_LOC`; use it in `check_diff_loc`. (Also thread through the yaml-goal path's inline check? No — yaml goals stay on default cap; only self-improve platform targets tighten.)

Update `pr_gate.check_diff_loc(total_loc, max_loc=None)` to accept an optional override (default keeps `MAX_PR_DIFF_LOC`).

**Step 4: Run — expect PASS** (`cd phase3 && PYTHONPATH=backend python -m pytest soul/tests/ -q`).

**Step 5: Commit** — `git add phase3/soul/daemon.py phase3/soul/pr_gate.py phase3/soul/tests/test_daemon.py && git commit -m "fix(soul): early dedup + collision-safe goal_id + consistent pr_title + platform LOC cap"`

---

## Task 4: wire daemon to scoped pick_target (integration verify)

**Files:**
- Verify only: `phase3/soul/daemon.py` already wired in Task 3.
- Test: `phase3/soul/tests/test_daemon.py` — add an integration test that, given a fake repo with soul+engine modules, `pick_target` returns an engine module on the cycle after soul modules are marked reviewed.

**Step 1–4:** TDD as above — assert that a never-reviewed engine module is reachable through the scoped daemon path (rotation includes engine).

**Step 5: Commit** — `git commit -m "test(soul): integration · scoped rotation reaches engine modules"`

---

## Task 5: L3 platform-side — proposal-INSERT contract doc + soul_consumer cron verify (ops/docs)

**Files:**
- Create: `docs/SOUL_PROPOSAL_CONTRACT_20260528.md`
- Verify (no code): `soul_consumer` cron on cloud.

**Step 1:** Document the agent-facing contract for `platform_improvement_proposals`:
- exact INSERT shape (columns, status lifecycle pending→consumed, PR-url writeback field)
- how `services/soul_consumer.py::consume_pending_proposals` picks them up
- that `/api/soul/generate` is dry-run-only today; the durable path is the table INSERT
- a minimal example INSERT an agent (V5) would run

**Step 2:** Verify on cloud whether `soul_consumer` runs on a timer/cron (`systemctl list-timers | grep -i soul`, check for a consumer service). Record the finding in the doc (verify, don't assume). If absent, note it as a follow-up (do NOT add the cron in this PR unless trivial + verified).

**Step 3: Commit** — `git add docs/SOUL_PROPOSAL_CONTRACT_20260528.md && git commit -m "docs(soul): L3 agent→soul proposal-INSERT contract + consumer cron status"`

---

## Task 6: reflection goal-sourcing — verify DB view, prepare env (ops, no repo code)

**Files:** none in repo (DATABASE_URL is cloud `.soul-env`, gitignored).

**Step 1:** SSH cloud, confirm `v_engine_progress` view exists with columns `cycle_id`, `avg_composite` (the query in `goal_selector.next_reflection_goal`). `psql ... -c "\d+ v_engine_progress"`.

**Step 2:** Confirm `psycopg2` importable in the soul daemon's python env.

**Step 3:** If both OK, add a **read-only** `DATABASE_URL` to cloud `~/nautilus-soul-workspace/.soul-env` (NOT committed). Record outcome. If the view/column names differ, fix `goal_selector` query in a follow-up commit (TDD).

---

## Final gate (before PR)
- `cd phase3 && PYTHONPATH=backend python -m pytest soul/tests/ -q` → all green
- `cd phase3 && PYTHONPATH=backend python -m pytest backend/engine/tests/ -q` → engine still green (scope now touches it)
- requesting-code-review skill → address Critical/Important
- Draft PR to master (human merge). Do NOT auto-merge.
- verification-before-completion skill before any "done" claim.

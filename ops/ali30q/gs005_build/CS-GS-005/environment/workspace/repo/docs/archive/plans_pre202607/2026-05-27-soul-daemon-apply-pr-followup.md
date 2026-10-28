# Soul Daemon · apply + draft-PR follow-up Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the Soul daemon `run_once` from dry-run-only to actually producing a **draft PR** per successful cycle — so the autonomous loop points at a real deliverable (anchor #2 "闭环须指向最终可交付物"), then activate the timer as the final human-gated step.

**Architecture:** `run_once` already proves the gate chain (pause→budget→goal→ship(dry)→pr_gate→track) and ends at `record_success` + log. This increment adds, after gates pass: (1) create an **isolated branch** `soul/cycle-<id>`, (2) `ship(apply=True, git_commit_msg=…)` so the engine's change is committed **on that branch only** (never master), (3) post-apply `pr_gate` path/diff check — on reject, hard-reset + delete branch (safe because isolated), (4) `pr_gate.create_draft_pr` (already implemented · never auto-merges), (5) mark the goal done **inside the PR** (commit `goals.yaml` status=done on the branch) so the done-state survives bootstrap's `git reset --hard`. Seed goals switch from prose (parse_error on a code engine) to engine-friendly code-change tasks (cloud-verified this session: code goal → "cycle complete · passed gates").

**Tech Stack:** Python 3.8+ stdlib + PyYAML + `gh` CLI + git + existing `engine.ship` (apply path at ship.py:160-195) + existing `soul.pr_gate.create_draft_pr` + the 3 shipped safety gates (budget/pause/circuit-breaker).

---

## Key design decisions (locked before tasks)

1. **Apply on isolated branch, never master.** `run_once` does `git checkout -b soul/cycle-<id>` (from master) BEFORE `ship(apply=True)`. `ship`'s `_git_add_commit` then commits to that branch. On any failure after branch creation, `git checkout master && git branch -D soul/cycle-<id>` to leave master untouched.
2. **pr_gate is post-apply + reversible.** `ship(apply=True)` self-gates on `check_result.passed` (ship.py:160). After apply, run `pr_gate.check_paths(result.files_planned paths)` + `check_diff_loc`. Reject → reset + delete branch + `record_failure`. (Apply-then-check is safe only because we're on a throwaway branch.)
3. **Goal-done survives bootstrap reset.** bootstrap.sh does `git reset --hard origin/master` each run → a local `goals.yaml` status edit would be wiped. So the done-mark is committed **on the cycle branch as part of the PR** (merge → master updates). The daemon does NOT mutate the working-tree goals.yaml outside the branch.
4. **One generate per cycle.** Do NOT call ship twice (dry-run then apply) — that double-generates (cost + nondeterminism). Use `ship(apply=True)` once; its internal check-gate handles "only apply if checks pass".
5. **Seed goals → code-change.** Replace prose goals (a2-readme-hero/a4-devto → move to a separate "prose backlog" not fed to engine) with engine-friendly code tasks (docstrings, small refactors, test additions). Verified: code goal passes, prose goal parse_errors.
6. **Timer activation = last step, human-gated.** Only after a cloud E2E run produces ONE real draft PR that a human reviews.

---

## Pre-flight

Run: `cd /c/Users/chunx/Projects/nautilus-core && git fetch origin master && git log origin/master --oneline -1`
Expected: `356abb00f` or later (cron-wiring + parking-lot merged).

Confirm shipped pieces exist: `git ls-tree origin/master phase3/soul/ | grep -E "daemon|pr_gate|goal_selector"` → all present.

Read the cron-wiring memory `session_20260527_soul_cron_wiring_shipped.md` + this session's dry-run findings: code goals pass, prose goals parse_error, DeepSeek provider reads `DEEPSEEK_API_KEY/DEEPSEEK_BASE_URL/DEEPSEEK_MODEL` (not MINIMAX_*), client.py at `backend/agent_engine/llm/client.py` is the multi-provider version.

Work in an isolated worktree (using-git-worktrees). Build locally + test; cloud E2E via cloud clone.

---

### Task 1: daemon · branch-isolated apply path

**Files:**
- Modify: `phase3/soul/daemon.py` (the `record_success` block in `run_once`)
- Test: `phase3/soul/tests/test_daemon.py` (add mocked apply-path tests)

**Step 1: Write failing tests (all subprocess + ship mocked)**

Test that on gates-pass, `run_once`: (a) creates branch `soul/cycle-*`, (b) calls `ship` with `apply=True`, (c) calls `pr_gate.create_draft_pr`, (d) returns 0. And a second test: pr_gate path-reject → branch deleted (git checkout master + branch -D invoked) + `record_failure` + no PR.

Mock `daemon.subprocess.run` (capture git cmds), `daemon.ship` (return a ShipResult with `applied=True`, `files_planned=[{"path":"phase3/backend/engine/text_utils.py","size":400}]`, `check_result={"passed":True}`), `daemon.pr_gate.create_draft_pr` (return fake URL), `daemon.pr_gate.check_paths`/`check_diff_loc`.

**Step 2: Run · expect fail.**

**Step 3: Implement.** Replace the dry-run `record_success` tail with: branch create → `ship(apply=True, git_commit_msg=f"soul: {goal['id']}")` → post-apply `pr_gate.check_paths`+`check_diff_loc` → reject path (reset+delete branch+record_failure+return 1) → accept path (create_draft_pr + record_success + return 0). Always `git checkout master` at the end (finally). Use `subprocess.run([... "git","-C",str(REPO_ROOT) ...])`.

**Step 4: Run · expect pass.**

**Step 5: Commit** `feat(soul): daemon apply path · isolated branch + draft PR (never master)`

---

### Task 2: goal-done mark inside the cycle PR

**Files:**
- Modify: `phase3/soul/goal_selector.py` (add `mark_done(goal_id)` that rewrites goals.yaml status)
- Modify: `phase3/soul/daemon.py` (call `mark_done` + stage goals.yaml into the cycle commit, before PR)
- Test: `phase3/soul/tests/test_goal_selector.py` + `test_daemon.py`

**Step 1: Failing test** `mark_done` sets the matching goal's `status: done` in goals.yaml (round-trip preserves other goals). Daemon test: goals.yaml staged + committed on the branch before create_draft_pr.

**Step 2-4: TDD** — `mark_done` uses `yaml.safe_load` + edit + `yaml.safe_dump` (or targeted line edit to preserve comments — prefer ruamel if comment-preservation matters; else accept dump). Daemon: after ship apply, `goal_selector.mark_done(goal["id"])` then `git add goals.yaml` (folded into the same branch commit or a follow-up commit on the branch).

**Step 5: Commit** `feat(soul): mark goal done inside cycle PR (survives bootstrap reset)`

---

### Task 3: seed goals → engine-friendly code-change

**Files:**
- Modify: `phase3/soul/goals.yaml`

**Step 1:** Move prose goals (a2-readme-hero, a4-devto) to a comment block "prose backlog (needs a prose-capable path, NOT the code engine)". Add 2-3 code-change seed goals with MINIMAL CHANGE phrasing (engine excels here), e.g. "Add module-level docstrings to engine modules lacking them, keep all other code identical." Each with clear `acceptance`.

**Step 2:** Verify yaml parses: `python -c "import yaml,io; yaml.safe_load(open('phase3/soul/goals.yaml'))"`.

**Step 3: Commit** `feat(soul): seed goals → code-change (prose moved to backlog · engine is a code engine)`

---

### Task 4: bootstrap reset → preserve goal-done

**Files:**
- Modify: `phase3/soul/bootstrap.sh`

**Decision:** `git reset --hard origin/master` is correct for a clean autonomous clone (don't want local drift). Goal-done is preserved via the PR merge (Task 2), NOT local state — so bootstrap can keep reset --hard. **Confirm** no local goals.yaml mutation persists across runs (it shouldn't — done-mark lives on branches/PRs). Add a comment to bootstrap.sh documenting this. No logic change expected unless a probe shows drift.

**Step: Commit** `docs(soul): bootstrap comment · goal-done lives in PRs not local state`

---

### Task 5: cloud E2E · produce ONE real draft PR

**Manual cloud step (fresh session with cloud access).**

```bash
ssh cloud "cd ~/nautilus-soul-workspace && git fetch origin master && git reset --hard origin/master"
# .soul-env already has DEEPSEEK_API_KEY (DEEPSEEK_* names · see cron-wiring memory)
ssh cloud "cd ~/nautilus-soul-workspace/phase3 && set -a && source ../.soul-env && set +a && python3 -m soul.daemon"
```

Expected: daemon selects a code goal → DeepSeek 200 → checks pass → branch `soul/cycle-*` created → draft PR opened on chunxiaoxx/nautilus-core. Verify: `gh pr list --repo chunxiaoxx/nautilus-core --draft` shows the new PR. **Human reviews the PR diff** (this is the gate).

---

### Task 6: timer activation (HUMAN-GATED · only after Task 5 PR reviewed)

```bash
ssh cloud "sudo systemctl enable --now nautilus-soul.timer && systemctl list-timers nautilus-soul.timer"
```

Verify timer is active + next-fire shown. Watch the first 1-2 autonomous cycles produce draft PRs (not merges). Confirm circuit-breaker still arms (budget cap + 5-failure pause).

---

## Out of Scope (this increment)

- Prose-capable generation path (README/article goals) — separate, needs non-engine path.
- Auto-merge (NEVER · draft PR + human merge is the safety model).
- Multi-goal-per-cycle, goal dependency graph.
- P1 cross-repo / P2 compass / P3 skills-hub.

## Risk + Rollback

- **Higher blast radius than dry-run**: daemon now writes files + commits + pushes a branch + opens a PR. Mitigations: isolated branch (never master), draft-only (human merge gate), pr_gate blacklist (.env/alembic/migrations/contracts), diff-LOC cap, budget cap, circuit-breaker.
- **Rollback**: `sudo systemctl disable --now nautilus-soul.timer` stops autonomy instantly. Open draft PRs are harmless (unmerged). `rm -rf ~/nautilus-soul-workspace` removes Soul. No `~/nautilus-mvp` / production impact.

## Done Criteria

1. `run_once` apply path: isolated branch + ship(apply=True) + post-apply pr_gate (reversible) + create_draft_pr + mark goal done. Tests green.
2. Seed goals are code-change; prose moved to backlog.
3. Cloud E2E produces ONE real reviewable draft PR from an autonomous cycle.
4. Timer activated ONLY after human reviews that PR.
5. Safety gates still arm (budget/pause/circuit-breaker/blacklist/diff-cap).

## Execution note

Fresh session (R3 · current session was long). Token must be a fine-grained PAT (the chat-exposed ones revoked — see `action_token_revoke_20260527.md`).

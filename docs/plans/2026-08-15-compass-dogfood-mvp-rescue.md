# Compass Dogfood MVP Rescue Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship one canonical `nautilus-compass loop run` path that performs a
bounded action, independent verification, candidate ExperiencePacket creation,
unseen paired reuse, and a visible Gold/Repair decision without automatic
promotion.

**Architecture:** Start from `origin/main` and reuse the existing ExperiencePacket,
immutable FlywheelEventLog, and reviewed S4-3 verdict stack. Add one read-only
doctor and one thin loop CLI over a run-local SQLite flight recorder. Restore the
installed memory runtime before any live A/B, then use one fixed coding-task
adapter and independent verifier; do not integrate Platform, V5, FDE, robotics,
or a new global store.

**Tech Stack:** Python 3.13, stdlib argparse/json/sqlite/socket/subprocess/pathlib,
existing GEP dataclasses and reducers, pytest, Ruff, Ed25519 support already used
by reviewed verifier code.

---

### Task 1: Add an honest `doctor` command

**Files:**
- Create: `doctor.py`
- Modify: `cli.py`
- Test: `tests/test_doctor.py`
- Test: `tests/test_cli.py`

**Step 1: Write failing tests**

Cover:

- exact JSON keys for package version, repository commit, installed module path,
  plugin path/hash, daemon ping, functional recall, and dependency import;
- `ready=false` when ping succeeds but recall fails;
- `ready=false` when repository and installed plugin hashes differ;
- no filesystem or process mutation;
- CLI help lists `doctor` and returns the doctor's exit code.

**Step 2: Verify RED**

Run:

```powershell
python -m pytest tests/test_doctor.py tests/test_cli.py -q
```

Expected: failure because `doctor.py` and the `doctor` route do not exist.

**Step 3: Implement the minimal read-only probe**

`collect_doctor_report()` must:

- import dependencies in a child process using the current interpreter;
- send daemon `ping` and a bounded functional `recall` request;
- hash configured repository/plugin entry files when present;
- inspect package metadata without importing the whole daemon;
- return stable reason codes, never repair anything.

`main()` prints a human summary by default and exact JSON with `--json`.

**Step 4: Verify GREEN**

Run the focused tests, Ruff check/format, and `python -m compileall -q doctor.py`.

**Step 5: Commit**

```powershell
git add doctor.py cli.py tests/test_doctor.py tests/test_cli.py
git commit -m "feat(cli): add honest Compass doctor"
```

---

### Task 2: Repair one canonical local runtime

**Files:**
- Modify: `daemon_start.ps1`
- Modify: `docs/mcp-usage.md`
- Test: `tests/test_daemon_start_windows_contract.py`

**Step 1: Write failing contract tests**

Require the launcher to:

- prefer explicit `COMPASS_PYTHON`;
- reject an interpreter that cannot import `torch` and
  `sentence_transformers`;
- avoid `cmd /c` string composition for interpreter selection;
- preserve idempotent ping behavior;
- surface the dependency error instead of reporting “ready”.

**Step 2: Verify RED**

```powershell
python -m pytest tests/test_daemon_start_windows_contract.py -q
```

**Step 3: Implement the minimal launcher correction**

Use `System.Diagnostics.ProcessStartInfo` with an exact executable and argument
list. Do not create a second daemon. Document the one supported Windows runtime:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
$env:COMPASS_PYTHON = (Resolve-Path .venv\Scripts\python.exe)
```

**Step 4: Repair and prove the actual installation**

From the clean worktree:

1. create/update the local venv;
2. install the editable package;
3. stop only the identified Compass daemon process;
4. start the same daemon with `COMPASS_PYTHON`;
5. run `nautilus-compass doctor --json` from a fresh process;
6. require ping, functional recall, package import, and authority checks to pass.

If functional recall still returns `torch._C` or any dependency error, stop the
plan and diagnose; do not begin the loop runner.

**Step 5: Commit source changes**

```powershell
git add daemon_start.ps1 docs/mcp-usage.md tests/test_daemon_start_windows_contract.py
git commit -m "fix(runtime): bind daemon to a verified Python"
```

---

### Task 3: Thin-migrate the reviewed S4-3 verdict state

**Files:**
- Modify: `gep/flywheel_event.py`
- Modify: `gep/flywheel_log.py`
- Create: `gep/flywheel_state.py`
- Create: `gep/verdict_packet.py`
- Modify: `tests/gep/test_flywheel_event.py`
- Modify: `tests/gep/test_flywheel_log.py`
- Create: `tests/gep/test_flywheel_state.py`
- Create: `tests/gep/test_verdict_flow.py`
- Create: `tests/gep/test_verdict_packet.py`

**Step 1: Review the exact source stack**

Use commits `04ac0d1` through `a688acb` from the reviewed S4-3 branch as the
only implementation source. Do not cherry-pick packaging, wheel-builder, secret,
or unrelated branch history.

**Step 2: Apply the minimal stack**

Cherry-pick one commit at a time. After each commit, inspect the file allowlist
and stop on any unexpected path.

**Step 3: Verify verdict semantics**

Run:

```powershell
python -m pytest tests/gep/test_experience_packet.py tests/gep/test_flywheel_event.py tests/gep/test_flywheel_log.py tests/gep/test_flywheel_state.py tests/gep/test_verdict_flow.py tests/gep/test_verdict_packet.py -q
```

Required behavior:

- action events remain `awaiting_verdict`;
- only a separately authored, bound verdict can produce `verified`;
- duplicate and conflicting verdicts fail closed;
- no event directly writes capsules, PoI, recall policy, or source files.

**Step 4: Commit only if cherry-pick did not already preserve atomic commits**

No squash of source and tests into the MVP runner commit.

---

### Task 4: Build the run-local loop and reproducible report

**Files:**
- Create: `gep/loop_run.py`
- Create: `tests/gep/test_loop_run.py`

**Step 1: Write failing tests**

Test a pure in-process fake action adapter and verifier:

- creates `plan.json` and `events.sqlite3`;
- records control episode and independent verdict;
- projects one candidate ExperiencePacket without promotion authority;
- records treatment episode and independent verdict;
- derives `report.json` only from the frozen plan, journal, and artifacts;
- reproduces byte-equal report in a clean process;
- repeated same run is idempotent;
- altered plan/artifact/verdict, duplicate IDs, or missing verdict fail closed;
- no `status.json`, second journal, or global database is created.

**Step 2: Verify RED**

```powershell
python -m pytest tests/gep/test_loop_run.py -q
```

**Step 3: Implement minimal interfaces**

Define:

```python
class ActionAdapter(Protocol):
    def execute(self, task, advice, work_dir) -> ActionArtifact: ...

class IndependentVerifier(Protocol):
    def verify(self, task, artifact, oracle) -> VerdictPacket: ...
```

`run_loop(...)` coordinates existing packet, event, log, and reducer APIs. It
does not implement recall, promotion, or model selection.

**Step 4: Verify GREEN and commit**

```powershell
python -m pytest tests/gep/test_loop_run.py tests/gep -q
python -m ruff check gep/loop_run.py tests/gep/test_loop_run.py
git add gep/loop_run.py tests/gep/test_loop_run.py
git commit -m "feat(loop): add reproducible run-local learning loop"
```

---

### Task 5: Expose one `loop run` command and pass Gate A

**Files:**
- Create: `loop_cli.py`
- Modify: `cli.py`
- Create: `tests/test_loop_cli.py`
- Create: `benchmarks/dogfood_mvp_v1/gate_a_suite.json`
- Create: `benchmarks/dogfood_mvp_v1/README.md`

**Step 1: Write failing CLI tests**

Require:

- `nautilus-compass loop run <suite> --out <dir>`;
- non-empty output directory rejection;
- process-restart read-back via `nautilus-compass loop verify <dir>`;
- one-screen terminal summary;
- exact Repair/Gold reason;
- explicit all-false promotion/capsule/PoI/source-write flags.

**Step 2: Implement a deterministic Gate A fixture**

The fixture is a small isolated coding repair with an executable oracle. It is
not evidence of product value; it proves orchestration, persistence, restart,
tamper rejection, and visible reporting.

**Step 3: Run fault cases**

Run success, Repair, duplicate, tamper, action failure, and verifier failure.
No network or model call is allowed in Gate A tests.

**Step 4: Commit**

```powershell
git add loop_cli.py cli.py tests/test_loop_cli.py benchmarks/dogfood_mvp_v1
git commit -m "feat(cli): expose the Compass learning loop"
```

Gate A is not complete until `doctor` and `loop verify` both pass in fresh
processes.

---

### Task 6: Add one bounded live coding adapter

**Files:**
- Create: `gep/live_coding_adapter.py`
- Create: `tests/gep/test_live_coding_adapter.py`
- Create: `benchmarks/dogfood_mvp_v1/value_suite.json`

**Step 1: Freeze the contract before credentials**

The suite must bind:

- one provider/model identity for both arms;
- exact prompt and advice hashes;
- no retry;
- timeout, token, cost, and tool-call budgets;
- isolated work directories;
- executable independent oracle;
- control/treatment labels hidden from verifier;
- preregistered primary metric and protected failure classes.

**Step 2: Write no-network contract tests**

Cover malformed provider output, reported-model mismatch, credential absence,
timeout, partial artifact, duplicate attempt, and provider failure.

**Step 3: Implement the smallest adapter**

Reuse the already configured cc-switch/provider credentials only at runtime.
Never persist credentials or raw provider configuration. Do not migrate the full
C2 branch or its benchmark hierarchy.

**Step 4: Run one preflight**

Preflight must produce zero model calls and bind every request hash. A failed
preflight authorizes no live call.

**Step 5: Commit**

```powershell
git add gep/live_coding_adapter.py tests/gep/test_live_coding_adapter.py benchmarks/dogfood_mvp_v1/value_suite.json
git commit -m "feat(loop): add bounded live coding adapter"
```

---

### Task 7: Run Gate B and make the product decision

**Files:**
- Create after execution:
  `benchmarks/dogfood_mvp_v1/evidence/<run-id>/independent_receipt.json`
- Create after execution:
  `benchmarks/dogfood_mvp_v1/evidence/<run-id>/report.json`
- Test: `tests/gep/test_dogfood_mvp_evidence.py`

**Step 1: Freeze a previously unseen paired suite**

Use one bug family derived from our actual development failures, with matched
but non-identical control/treatment tasks. Freeze suite, model, budget, seed,
verifier, threshold, and stop rule before any live call.

**Step 2: Execute once**

No same-action retry. Preserve terminal failures. Use only predeclared reserve
pairs.

**Step 3: Independently replay**

Recompute all verdicts and the aggregate delta from artifacts in a fresh
process. The report must show:

- control/treatment success;
- paired utility delta;
- latency, cost, and tool-call deltas;
- protected-class outcomes;
- Gold/Repair reason;
- promotion flags.

**Step 4: Apply the gate**

- Positive preregistered delta with no protected regression:
  `capsule_candidate=true`, but no automatic distillation.
- Zero, negative, inconclusive, or unverifiable delta: Repair and runtime flat.

**Step 5: Persist only minimal non-sensitive evidence and commit**

Do not commit raw model responses, prompts containing secrets, or temporary
workspaces.

---

### Task 8: Canonical install and closure

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `CHANGELOG.md`
- Test: `tests/test_packaged_loop_smoke.py`

**Step 1: Build and install the exact candidate**

Build a wheel from the clean commit, install it into a fresh venv, and run:

```powershell
nautilus-compass doctor --json
nautilus-compass loop run <gate-a-suite> --out <new-dir>
nautilus-compass loop verify <new-dir>
```

**Step 2: Verify source/runtime identity**

The doctor must report matching package, repository, plugin, daemon interpreter,
and functional recall. Read-back must reproduce the run decision.

**Step 3: Run full gates**

```powershell
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m compileall -q .
git diff --check
```

**Step 4: Document only demonstrated capabilities**

README must distinguish Gate A operational closure from Gate B value evidence.
Remove or qualify any claim not reproduced by the packaged smoke test.

**Step 5: Commit and stop**

Do not push, merge, tag, publish, deploy, or delete historical worktrees without
separate authorization. Present the exact candidate commit and evidence first.

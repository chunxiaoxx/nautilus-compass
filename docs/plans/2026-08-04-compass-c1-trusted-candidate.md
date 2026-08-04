# Compass C1 Trusted 2.3 Candidate Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Assemble and independently verify one clean, reproducible Compass 2.3 candidate with S4 independent verdicts, the evaluation-only Learning Kernel, immutable release provenance, temporary dual-slot cutover, and exact rollback while runtime policy remains flat.

**Architecture:** Start from the clean `origin/main` worktree. Preserve the 25-commit linear S4/release donor history, then add only the three PoI support modules required by R0 and port the R0-only commit group. Extend the release tests with a real temporary-runtime E2E that builds and installs the wheel outside the checkout, launches only the temporary slot, records doctor/MCP/recall read-back, and rolls back without touching the installed plugin.

**Tech Stack:** Python 3.13, frozen dataclasses, PyNaCl Ed25519 verification, pytest, Ruff, setuptools/build, standard-library venv/subprocess/socket/filesystem primitives.

---

### Task 1: Freeze the Adoption Boundary

**Files:**
- Create: `docs/plans/2026-08-04-compass-c1-trusted-candidate-design.md`
- Create: `docs/plans/2026-08-04-compass-c1-trusted-candidate.md`

**Step 1:** Record the exact source base, branch ancestry, commit groups,
excluded assets, runtime boundary, and stop conditions.

**Step 2:** Verify formatting and the clean source baseline.

Run:

```powershell
git diff --check
python -m pytest tests\gep tests\test_cli.py -q
```

Expected: diff check passes and 150 tests pass.

**Step 3:** Commit only the two plan files.

```powershell
git add docs/plans/2026-08-04-compass-c1-trusted-candidate-design.md docs/plans/2026-08-04-compass-c1-trusted-candidate.md
git commit -m "docs(release): define C1 trusted candidate"
```

### Task 2: Adopt the Linear S4 Verdict Stack

**Files:** Existing 16-commit change set `77f33ba^..26174d6`.

**Step 1:** Confirm ancestry and commit count before mutation.

```powershell
git merge-base --is-ancestor origin/main codex/pr-s4-3-verdict-attestation
git rev-list --count origin/main..codex/pr-s4-3-verdict-attestation
```

Expected: exit 0 and count 16.

**Step 2:** Cherry-pick the reviewed linear range without squashing.

```powershell
git cherry-pick 77f33ba^..26174d6
```

**Step 3:** Run the verdict and wheel boundary tests.

```powershell
python -m pytest tests\gep tests\test_cli.py -q
python -m ruff check gep tests\gep pyproject.toml
```

Expected: all pass; no live path is touched.

### Task 3: Adopt the Linear Release-Control Stack

**Files:** Existing 9-commit change set `ae23c7f^..b6ca9c1`.

**Step 1:** Confirm `26174d6` is the exact ancestor and the delta is 9.

**Step 2:** Cherry-pick the range without squashing.

```powershell
git cherry-pick ae23c7f^..b6ca9c1
```

**Step 3:** Run release, GEP, CLI, Ruff, and credential scans.

```powershell
python -m pytest tests\release tests\gep tests\test_cli.py -q
python -m ruff check release_manifest.py release_security.py runtime_release.py runtime_launcher.py runtime_doctor.py tests\release gep tests\gep
```

Expected: all pass; the release manifest keeps `default_policy=flat`.

### Task 4: Add the Minimal R0 Support Surface

**Files:**
- Create: `benchmarks/poi_gate2/__init__.py`
- Create: `benchmarks/poi_gate2/canonical.py`
- Create: `benchmarks/poi_gate2/action_metrics.py`
- Create: `benchmarks/poi_gate2/dogfood_evidence.py`
- Test: `tests/c1/test_r0_support_boundary.py`

**Step 1: Write the failing boundary test.**

Require canonical JSON/hash determinism, finite percentile behavior, blocked
dogfood authority, exact dependency allowlist, and absence of live-agent,
provider, repair-window, Platform, V5, or FDE modules.

**Step 2: Run RED.**

```powershell
python -m pytest tests\c1\test_r0_support_boundary.py -q
```

Expected: import failure because the support package is absent.

**Step 3: Port only the four allowlisted files from `3e7aa17`.**

Use `git show`/`git restore --source` for those exact paths; do not copy the
`benchmarks/poi_gate2` directory.

**Step 4: Run GREEN and Ruff.**

Expected: focused test passes and `git diff --name-only` contains no unapproved
PoI module.

**Step 5:** Commit the support slice independently.

### Task 5: Adopt the Evaluation-Only Learning Kernel

**Files:** Existing R0-only commits `816df5c^..3e7aa17`, excluding
`9f40760` because it binds a donor Gate-2 artifact rather than the C1 candidate.

**Step 1:** Generate the exact allowlist of files touched by the selected R0
commits and reject any path outside:

- `benchmarks/learning_kernel_r0/**`
- `tests/learning_kernel_r0/**`
- the two R0 plan files
- R0 evidence files
- `.gitattributes`
- the PyNaCl dependency in `pyproject.toml`

**Step 2:** Cherry-pick the R0 commits one by one in original order, omitting
`9f40760`. Stop on any dependency outside the allowlist instead of widening it.

**Step 3:** Run the complete Learning Kernel suite plus GEP and release tests.

```powershell
python -m pytest tests\learning_kernel_r0 tests\gep tests\release -q
python -m ruff check benchmarks\learning_kernel_r0 tests\learning_kernel_r0
```

Expected: all pass; runtime recommendation remains flat and improvement claim
remains false.

### Task 6: Prove a Real Installed-Wheel Dual-Slot Rehearsal

**Files:**
- Create: `tests/release/test_c1_candidate_e2e.py`
- Create: `docs/evidence/compass_c1_candidate_v1.json`
- Modify only if RED proves a production gap: release/runtime modules or
  `pyproject.toml` package data.

**Step 1: Write the failing E2E test.**

The test must build a wheel from a clean temporary source snapshot, scan source
and wheel, create an isolated runtime root, stage to slot A, activate, verify
doctor provenance, run installed-wheel imports plus bounded MCP tool-list and
recall smoke, stage a second manifest-bound candidate to slot B, switch, and
roll back to A without reinstalling.

The test must assert that no path resolves to the repository checkout or
`C:\Users\chunx\.claude\plugins\nautilus-compass`.

**Step 2: Run RED and confirm the exact missing behavior.**

**Step 3: Implement only the missing behavior proven by RED.**

**Step 4: Run GREEN, then the full related regression set.**

**Step 5:** Generate the evidence JSON from fresh command output. Do not copy
donor evidence or include credentials, command lines, user data, or live PIDs.

### Task 7: Claim Hygiene and Independent Review

**Files:**
- Modify: `README.md`
- Modify: `RESULTS.md`
- Modify: paper claim surfaces only where the audit proves a mismatch
- Modify: `docs/evidence/compass_c1_candidate_v1.json`

**Step 1:** Add tests or deterministic scans that distinguish QA accuracy,
retrieval-only metrics, runtime latency, and candidate-only learning evidence.

**Step 2:** Remove or qualify unsupported SOTA language without replacing it
with a broader claim.

**Step 3:** Run complete verification:

```powershell
python -m pytest tests\c1 tests\release tests\learning_kernel_r0 tests\gep tests\test_cli.py -q
python -m ruff check .
python -m build
git diff --check origin/main...HEAD
git status --short --branch
```

Repeat installed-wheel E2E from outside the checkout.

**Step 4:** Request independent specification and code-quality reviews. Fix
every High and Medium finding with a failing regression test first.

**Step 5:** Audit every C1 objective requirement against current artifacts and
command output. Do not merge, push, deploy, or mutate the installed plugin.

## Completion Boundary

C1 completion proves a trustworthy local candidate and reversible release
substrate. It does not prove real-agent uplift, authorize a Super Agent adapter,
promote a learning policy, create capsules, change model weights, or justify a
SOTA claim.

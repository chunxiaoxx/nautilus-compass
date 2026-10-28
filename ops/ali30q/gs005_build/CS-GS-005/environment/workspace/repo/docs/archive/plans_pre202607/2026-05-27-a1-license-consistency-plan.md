# A1 License Consistency Sweep · Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align 3 phase3 setup.py files and root pyproject.toml with the existing Apache 2.0 root LICENSE · single commit · zero runtime impact.

**Architecture:** Metadata-only sweep. 5 string edits across 4 files. No new files. No test code (license fields are not exercised by the 198 engine tests + 2 CLI tests). Verification via `grep` post-edit.

**Tech Stack:** setuptools (phase3 setup.py · trove classifier strings) · PEP 639 SPDX license expression (pyproject.toml).

---

## Pre-flight

**Confirm working state before starting:**

Run: `git status`
Expected: clean working tree on `master` · ahead origin 14 commits (13 from 5/26 session + 1 design doc from this session)

Run: `git log -1 --oneline`
Expected: `0e332e3fe docs: brainstorming · A1 license consistency design (Apache 2.0 sweep · 5 edits)`

If state diverges, stop and reconcile before proceeding.

---

### Task 1: Sweep phase3/sdk/setup.py classifier

**Files:**
- Modify: `phase3/sdk/setup.py:15`

**Step 1: Read current line**

Use Read tool on `phase3/sdk/setup.py` (full file is 18 lines).

Expected line 15:
```
        "License :: OSI Approved :: MIT License",
```

**Step 2: Apply edit**

Use Edit tool:
- old_string: `"License :: OSI Approved :: MIT License",`
- new_string: `"License :: OSI Approved :: Apache Software License",`

This string appears in 3 files but only this file in this Task. Use unique surrounding context if Edit complains about uniqueness across the multi-file edits later (it should not, since Edit operates per-file).

**Step 3: Verify**

Run: `grep -n "Apache" phase3/sdk/setup.py`
Expected: 1 hit on line 15.

Run: `grep -n "MIT" phase3/sdk/setup.py`
Expected: 0 hits.

**Step 4: Do not commit yet.** Single commit at the end (Task 6).

---

### Task 2: Sweep phase3/cli/setup.py license field + classifier

**Files:**
- Modify: `phase3/cli/setup.py:17`
- Modify: `phase3/cli/setup.py:29`

**Step 1: Apply first edit (license field)**

Use Edit tool on `phase3/cli/setup.py`:
- old_string: `    license="MIT",`
- new_string: `    license="Apache-2.0",`

**Step 2: Apply second edit (classifier)**

Use Edit tool on `phase3/cli/setup.py`:
- old_string: `        "License :: OSI Approved :: MIT License",`
- new_string: `        "License :: OSI Approved :: Apache Software License",`

**Step 3: Verify**

Run: `grep -n "Apache" phase3/cli/setup.py`
Expected: 2 hits (line 17 license field · line 29 classifier).

Run: `grep -ni "MIT" phase3/cli/setup.py`
Expected: 0 hits.

---

### Task 3: Sweep phase3/backend/sdk/python/setup.py classifier

**Files:**
- Modify: `phase3/backend/sdk/python/setup.py:23`

**Step 1: Apply edit**

Use Edit tool on `phase3/backend/sdk/python/setup.py`:
- old_string: `        "License :: OSI Approved :: MIT License",`
- new_string: `        "License :: OSI Approved :: Apache Software License",`

**Step 2: Verify**

Run: `grep -n "Apache" phase3/backend/sdk/python/setup.py`
Expected: 1 hit on line 23.

Run: `grep -ni "MIT" phase3/backend/sdk/python/setup.py`
Expected: 0 hits.

---

### Task 4: Add license field + bump setuptools in root pyproject.toml

**Files:**
- Modify: `pyproject.toml:2` (bump setuptools)
- Modify: `pyproject.toml` (insert license field after authors line, line 9 in current file)

**Step 1: Bump setuptools requirement**

PEP 639 SPDX `license = "..."` form requires `setuptools >= 77`. Current `setuptools>=45` would emit a deprecation warning on PEP 639 usage.

Use Edit tool on `pyproject.toml`:
- old_string: `requires = ["setuptools>=45", "wheel"]`
- new_string: `requires = ["setuptools>=77", "wheel"]`

**Step 2: Insert license field**

Current pyproject.toml has no `license` field. The `[project]` table block:
```toml
[project]
name = "nautilus-core"
version = "1.0.0"
description = "AI Agent Mining Pool System"
authors = [{name = "Nautilus Team"}]
readme = "README.md"
requires-python = ">=3.8"
```

Use Edit tool on `pyproject.toml`:
- old_string: `authors = [{name = "Nautilus Team"}]\nreadme = "README.md"`
- new_string: `authors = [{name = "Nautilus Team"}]\nlicense = "Apache-2.0"\nreadme = "README.md"`

(Edit tool preserves literal newlines · the `\n` above are illustrative · in the actual tool call use real newlines in the string.)

**Step 3: Verify**

Run: `grep -n "license\|setuptools" pyproject.toml`
Expected:
- line 2: `requires = ["setuptools>=77", "wheel"]`
- line 9 (or wherever inserted): `license = "Apache-2.0"`

---

### Task 5: Repo-wide verification grep

**Files:** none modified · read-only sanity.

**Step 1: Confirm no MIT residue in phase3 setup.py files**

Run: `grep -rn "MIT" phase3/sdk/setup.py phase3/cli/setup.py phase3/backend/sdk/python/setup.py`
Expected: 0 hits.

**Step 2: Confirm Apache strings present in all 3 files**

Run: `grep -rn "Apache" phase3/sdk/setup.py phase3/cli/setup.py phase3/backend/sdk/python/setup.py`
Expected: 4 hits total (1 in sdk · 2 in cli · 1 in backend/sdk).

**Step 3: Confirm root LICENSE unchanged**

Run: `grep -n "Apache License" LICENSE | head -2`
Expected: line 1 contains `Apache License`.

**Step 4: Confirm README badge unchanged**

Run: `grep -n "License-Apache" README.md`
Expected: 1 hit (badge line).

**Step 5: Confirm pyproject.toml license field**

Run: `grep -n "Apache-2.0" pyproject.toml`
Expected: 1 hit.

If any grep fails expectations, stop and diagnose before commit.

---

### Task 6: Commit

**Files:** stage 4 modified files.

**Step 1: Stage edits**

Run:
```
git add phase3/sdk/setup.py phase3/cli/setup.py phase3/backend/sdk/python/setup.py pyproject.toml
```

**Step 2: Confirm stage is only what we expect**

Run: `git status --short`
Expected output (order may differ):
```
M  phase3/sdk/setup.py
M  phase3/cli/setup.py
M  phase3/backend/sdk/python/setup.py
M  pyproject.toml
```

No other files should be staged. If any extra file appears, unstage with `git restore --staged <file>` before commit.

**Step 3: Diff sanity**

Run: `git diff --cached --stat`
Expected: 4 files changed · ~5 insertions(+) · ~5 deletions(-) (license field add nets +1).

Run: `git diff --cached pyproject.toml`
Expected: 2 hunks · setuptools bump + license field insert.

**Step 4: Commit**

Run:
```
git commit -m "chore(license): A1 · sweep phase3 setup.py + pyproject.toml to Apache 2.0

Aligns 3 phase3 setup.py files and root pyproject.toml with the existing
Apache 2.0 root LICENSE. Removes the MIT/Apache split-brain that the
5/27 handoff misidentified. Zero runtime impact · metadata-only.

Closes Path A W1 item A1."
```

**Step 5: Verify commit landed**

Run: `git log -1 --stat`
Expected: 4 files · ~10 lines changed · commit message as above.

Run: `git status`
Expected: clean working tree · ahead origin 15 commits (13 from 5/26 + design doc + this).

---

### Task 7: Post-ship sanity (optional but recommended)

**Step 1: Confirm engine tests still pass**

License metadata does not affect runtime. This is a paranoia check.

Run: `cd engine && pytest -q` (or whatever the canonical test command is · check 5/26 handoff for actual command if unsure)

Expected: 196 engine tests pass · 6 skipped (PG integration when DATABASE_URL unset).

If failures appear, they are unrelated to this commit (license metadata cannot break tests). Note them for separate triage but do not block A1 completion.

**Step 2: Update task tracking**

Mark A1 as complete in the platform dialog handoff line (will be done in next session's handoff doc, not in this plan).

---

## Out of Scope (Do Not Touch)

- `LICENSE` file at root (already Apache 2.0)
- `README.md` badge (already Apache 2.0)
- `NOTICE` file (defer)
- `CONTRIBUTING.md` (defer to A6)
- `phase3/CLAUDE.md` and other internal doc license references (defer to A2)
- `alembic/versions/` (user hard constraint · cross-dialog · Gap 3 W4)
- Path B (Gap 3-5 · deferred to W4)
- Any test file (zero test impact)

## Risk + Rollback

- Risk: negligible · all 5 edits are metadata.
- Rollback: `git revert <commit-hash>` · no schema / data / runtime state to undo.

## Done Criteria

1. 4 phase3 setup.py edits applied · 0 MIT residue in those 3 files.
2. pyproject.toml has `license = "Apache-2.0"` and `setuptools>=77`.
3. Single commit landed on master · clean working tree.
4. All 5 verification greps return expected results.

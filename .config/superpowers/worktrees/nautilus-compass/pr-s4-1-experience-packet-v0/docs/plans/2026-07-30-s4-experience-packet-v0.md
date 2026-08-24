# S4 Experience Packet v0 Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a backward-compatible Experience Packet v0 schema and serialization helpers for the Compass S4 Agent Harness post-training flywheel.

**Architecture:** Create one side-effect-free `gep` module containing a frozen dataclass and two module-level helpers. Keep every field optional, serialize only present values, and accept argparse namespaces or mappings without coupling to any runtime writer.

**Tech Stack:** Python 3.10+ dataclasses and typing, pytest, Ruff.

---

### Task 1: Specify the schema behavior with tests

**Files:**
- Create: `tests/gep/test_experience_packet.py`

**Step 1: Write the failing tests**

Cover all-optional defaults, a complete packet, frontmatter omission of `None`, retention
of explicit false and zero values, tool-chain normalization, unrelated argparse fields,
explicit overrides, and mapping input.

**Step 2: Run the test to verify it fails**

Run: `python -m pytest -q tests/gep/test_experience_packet.py`

Expected: collection fails because `gep.experience_packet` does not exist.

### Task 2: Implement the minimal schema

**Files:**
- Create: `gep/experience_packet.py`
- Test: `tests/gep/test_experience_packet.py`

**Step 1: Add `ExperiencePacket`**

Use a frozen dataclass whose eleven requested fields all default to `None`. Represent a
present tool chain as `tuple[str, ...]`.

**Step 2: Add `from_args`**

Read allowlisted schema fields from an argparse namespace or mapping, ignore unrelated
arguments, apply explicit schema-field overrides, and normalize tool chains without
guessing string delimiters.

**Step 3: Add `to_frontmatter`**

Return a new plain dictionary containing only non-`None` values. Convert a tuple tool
chain to a list while retaining `False`, `0`, and `0.0`.

**Step 4: Run the focused test**

Run: `python -m pytest -q tests/gep/test_experience_packet.py`

Expected: all tests pass.

### Task 3: Verify compatibility and quality

**Files:**
- Verify: `gep/experience_packet.py`
- Verify: `tests/gep/test_experience_packet.py`

**Step 1: Run the GEP suite**

Run: `python -m pytest -q tests/gep`

Expected: all existing capsule and PoI tests plus Experience Packet tests pass.

**Step 2: Run static and patch checks**

Run: `python -m ruff check gep/experience_packet.py tests/gep/test_experience_packet.py`

Run: `git diff --check`

Expected: both commands exit successfully.

**Step 3: Review the diff against non-goals**

Confirm that no database, daemon, ingestion, governance, PoI reranking, capsule-generation,
or model-training file changed.

**Step 4: Commit**

Run:

```bash
git add docs/plans/2026-07-30-s4-experience-packet-v0-design.md \
  docs/plans/2026-07-30-s4-experience-packet-v0.md \
  gep/experience_packet.py tests/gep/test_experience_packet.py
git commit -m "feat (s4): add Experience Packet schema for agent harness post-training"
```

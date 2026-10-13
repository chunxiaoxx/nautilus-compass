---
name: orgfuel-ORGG-5b4d38e112670ef1-fcedb57379
description: "判读档判例 2026-07-30-s4-experience-packet-v0 · (全文) # S4 Experie"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-5b4d38e112670ef1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-30-s4-experience-packet-v0 · (全文)
# S4 Experience Packet v0 Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a backward-compatible Experience Packet v0 schema and serialization helpers for the Compass S4 Agent Harness post-training flywheel.

**Architecture:** Create one side-effect-free `gep` module containing a frozen dataclass and two module-level helpers. Keep every field optional, serialize only present values, and accept argparse namespaces or mappings without coupling to any runtime writer.

**Tech Stack:** Python 3.10+ dataclasses and typing, pytest, Ruff.

---

### Task 1: Specify the schema behavior with tests

**Files:**
- Create: `tests/gep/test_experience_packet.py`

**St

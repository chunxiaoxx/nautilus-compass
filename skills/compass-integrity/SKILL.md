---
name: compass-integrity
description: Use when the user is about to rely on prior session memory for a non-trivial decision, or when something feels off about a recall hit — runs the Merkle chain check, drift summary, and daemon liveness in one pass and surfaces any tampering, drift bursts, or daemon-down state before the user acts on stale or corrupted memory.
---

# Compass Integrity Check

## Overview

Compass writes a Merkle hash chain over project memory and a per-session drift signal. Both can be silently broken — a chain mismatch means a memory file was edited outside the writer; a drift-red session means the past assistant output diverged from intent. **A recall hit on tampered or red-drift memory is worse than no recall**.

This skill runs the integrity checks **before** the user commits to acting on memory.

## When to invoke

Trigger conditions (any one):

1. User says "do we remember", "did we discuss", "based on past sessions" — they're about to lean on memory.
2. User points at a specific memory file or session ID — verify the chain covers it cleanly.
3. Drift incident already suspected ("why did the assistant flip on X?", "this looks like a regression") — pull recent drift history.
4. Session start in a project with memory/, before any recall fires — preflight.
5. After a crash, conflict resolution, or merge — chain may have been broken by a non-writer edit.

Skip when:
- The work is purely procedural (no memory dependency).
- The user explicitly said "ignore memory" / "don't use prior context".

## How it works

The skill is a one-pass orchestrator over four already-shipped CLIs in this plugin:

| Check | Tool | What it tells you |
|-------|------|-------------------|
| Daemon liveness | `nc 127.0.0.1 9876` ping | Is BGE-m3 up? If not, recall is metadata-only. |
| Chain integrity | `compass_verify.py` | Are any memory files tampered/missing? |
| Drift trend | `drift_history.py 7` | What is the green/yellow/red split for the last 7 days? |
| Memory size | `recall.find_active_project_memory_dir` | How many entries exist for the current project? |

The fastest path is the `/compass-status` slash command, which bundles all four. Use that as the primary entry; only call the individual CLIs if you need finer control (e.g. `/compass-drift 30` for a longer window after a yellow signal).

## Decision rules

Run the bundle, then apply this triage:

| State | Action |
|-------|--------|
| All ✓, drift mostly green | Proceed with recall. One-line greenlight to user. |
| Daemon DOWN | Tell user; recall falls back to keyword/metadata mode (lower recall@k); offer to start daemon. |
| Chain TAMPERED | **Stop.** Surface tampered file list verbatim. Do not recall those files. Ask user whether to audit diff or regenerate chain. Document in session notes. |
| Drift red ≥ 5% in window | Pull `/compass-drift 30 --top 10`. Surface most recent red incidents. Warn user that prior assistant outputs in those sessions may have been off-intent. |
| Memory empty | Tell user — no recall hits available. Don't pretend to find them. |

Two failure modes can stack (daemon down AND red drift). Surface both, don't pick one.

## Examples

### Greenlight path

```
User: "Did we already pick a logging format?"
Assistant: [runs /compass-status]
  daemon  : ✓ pong
  chain   : ✓ C--Users-chunx-Projects-foo
  drift   : G:91% Y:8% R:1% (7d)
  memory  : foo · 23 entries
[runs /compass-recall "logging format"]
"Yes — 2 hits. Decision in feedback_logging.md from 2026-04-22: structured JSON + level filtering ..."
```

### Tampered path

```
User: "What were our deploy criteria?"
Assistant: [runs /compass-status]
  chain   : ✗ TAMPERED · 1 file (deploy_criteria.md)
"Memory chain mismatch on deploy_criteria.md — it was edited outside the writer. I won't recall from it
until we audit. `git log --diff-filter=M deploy_criteria.md` should show what changed; want me to run that?"
```

### Daemon-down path

```
User: "Search prior sessions for the Postgres pool size we settled on."
Assistant: [runs /compass-status]
  daemon  : DOWN (timed out)
  chain   : ✓
  drift   : G:84% Y:13% R:2% (7d)
"BGE daemon is down — falling back to keyword search. Hits will miss paraphrases. Start it with
`bash ~/.claude/plugins/nautilus-compass/daemon_start.sh`. Want me to keyword-search now or wait?"
```

## Anti-patterns

- ❌ Recalling silently on a tampered chain. The user should see the tamper alert before any hit lands in the response.
- ❌ Treating yellow drift as failure. Yellow = "small drift, recovered" — historically benign.
- ❌ Reading every memory file to "verify" — the chain is the verification. Don't reinvent it by content-diffing.
- ❌ Auto-regenerating the chain on tamper detection. **Always** ask the user — regenerating without auditing buries the evidence.

## Failure & escalation

If `/compass-status` itself errors (e.g. ImportError, missing CLI):
1. Note the failure in plain text.
2. Fall back to letting the user proceed without memory (don't pretend to verify).
3. Open a follow-up to fix the broken check — never "best-effort silent skip".

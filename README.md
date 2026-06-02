# nautilus-compass

<!-- mcp-name: io.github.chunxiaoxx/nautilus-compass -->

> **Reliability layer for multi-agent setups** ·
> keep multiple agents — or your own long-running sessions — coordinating
> reliably **without an orchestrator**.
> Cross-dialog contracts + drift detection + a 4-tier memory lifecycle.
> Plugin for Claude Code/Desktop · Cline · Cursor · Continue.dev · Zed.
>
> When an agent drifts from a rule you set, takes a shortcut you flagged,
> or claims a prior agreement that never happened — compass catches it
> **before the agent acts**.
>
> *Why it holds up technically:* the memory underneath is **black-box** —
> raw text embedded locally with BGE-m3, no LLM extraction step, no graph,
> no data leaving your machine (~14× cheaper to reproduce than white-box
> stacks like Mem0 / Letta / Cognee / Zep / MemOS). That same raw-prompt
> index is exactly what lets compass score the next action against your
> past mistakes — drift detection that white-box entity-graph memory
> structurally can't do. Full argument:
> [paper/BLACKBOX_VS_WHITEBOX.md](paper/BLACKBOX_VS_WHITEBOX.md).
>
> **Built by [Nautilus Platform](https://nautilus.social)** · open agent ecosystem · [join as agent →](https://nautilus.social)


🇬🇧 English (this file) · [🇨🇳 中文](README.zh-CN.md)

[![CI](https://github.com/chunxiaoxx/nautilus-compass/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/chunxiaoxx/nautilus-compass/actions/workflows/ci.yml)
[![arXiv build](https://github.com/chunxiaoxx/nautilus-compass/actions/workflows/build-paper.yml/badge.svg?branch=main)](https://github.com/chunxiaoxx/nautilus-compass/actions/workflows/build-paper.yml)
[![LongMemEval-S](https://img.shields.io/badge/LongMemEval--S-56.6%25-brightgreen)](paper/RESULTS_v0.8.md)
[![EverMemBench](https://img.shields.io/badge/EverMemBench-44.4%E2%80%9347.3%25-brightgreen)](paper/sections/paper2_06_5_evermembench.tex)
[![drift-AUC](https://img.shields.io/badge/drift_AUC-0.83_held--out-brightgreen)](#how-it-works)
[![PyPI](https://img.shields.io/pypi/v/nautilus-compass?label=PyPI&color=blue)](https://pypi.org/project/nautilus-compass/)
[![MCP](https://img.shields.io/badge/MCP-7%20tools%20%C2%B7%20TLS%20%C2%B7%20RBAC-blue)](docs/mcp-usage.md)
[![A2A](https://img.shields.io/badge/A2A-mTLS%20%C2%B7%20scoped%20peers-blue)](examples/a2a_tls_demo.py)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 30-second pitch

compass's #1 job is multi-agent **reliability** without an orchestrator.
The reason it can do that — and not be just another memory store — is its
black-box memory core:

```
White-box memory layers (Mem0, Letta, Cognee, Zep, MemOS, smrti):
  "I call an LLM to extract facts from your conversation,
   then store them in a graph. Pay extraction tokens. Send
   data to the provider."

Black-box memory (compass · this project):
  "I embed raw text locally with BGE-m3. No extraction LLM.
   No graph. No data leaving your machine. And because raw
   prompts are still in the index, I can score the next
   prompt against your past mistakes before the agent acts."
```

The trade is real: −30 points on LongMemEval-S vs white-box leaders that
build entity graphs, in exchange for 14× cheaper reproduction, full
local-deployment, cross-LLM portability, and drift detection that
white-box systems can't offer. Full argument:
[paper/BLACKBOX_VS_WHITEBOX.md](paper/BLACKBOX_VS_WHITEBOX.md).

**In one line**: when the AI is about to forget a rule you set, take a
shortcut you flagged, or fabricate a prior agreement, it gets stopped
by its own history of failure patterns.

---

## What's new in v2.1.0 · drift v2 + line reconciliation

v2.1.0 unifies two development lines (daemon/reliability + lifecycle/PoI) onto a
single `main` and hardens the drift loop.

### Drift v2 cutover (cry-wolf fix)

The old OR-vote firing (`neg_cos ≥ 0.538`) fired on **64.5%** of events in 11.5k
records of real traffic — benign prompts with high anti-anchor cosine overlapped
genuine drift, so agents tuned out (act-on rate 9.87%). v2.1.0 makes firing
high-signal:

```
should_alert = rule_hit (danger-command regex) OR drift_score < −0.07
```

Production-measured fire rate **0.5%** · danger commands (rm -rf / force push /
DROP / hardcoded key) always caught · the multi-signal `drift/firing.py` vote is
retained behind an env flag for A/B.

### Cross-agent contract scanner (L4 substrate)

- implicit contracts derived from `inbound_/outbound_` handoff files
- auto-consume detection (1:1 greedy · receiver-authorship guarded · opt-in)
- idempotent contract ledger · 720h close-loop window

### L3 tier promotion + Proof-of-Impact

- daily idempotent tier-promotion driver (impact-based · LLM-free)
- PoI candidate emission at recall time + impact-weighted ranking boost
- L1 session-summary overlay

### Daemon hardening (P4–P9)

bounded handler pool · in-flight semaphore (CLOSE_WAIT cure) · server-side recall
cache · pkl warmup (cold-start CPU cure) · BM25 + vector RRF fusion (opt-in) ·
inotify cache invalidation.

---

## What's new in v2.0.0 · Opinionated EvoMap

v2.0.0 ships a deterministic **lifecycle layer** on top of the black-box
memory base — paradigm fuse of [llm-wiki2](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) (Karpathy v2),
[agentmemory](https://github.com/rohitg00/agentmemory) (LongMemEval-S 95.2% R@5),
and [GBrain](https://github.com/garrytan/gbrain) (Garry Tan · MIT).

**The bet**: every other memory project (Mem0, Letta, Cognee, Zep, MemOS,
llm-wiki2, agentmemory) calls an LLM at *some* lifecycle decision —
ingest, promotion, consolidation, or forgetting. compass v2.0.0 makes
them all schema-declared.

### 5 new frontmatter fields (write-time LLM-free)

```yaml
tier: working | episodic | semantic | procedural   # 4 tiers verbatim from llm-wiki2
decay_rate: 0.5                                     # Ebbinghaus exponential decay
forget_at: 2026-06-01T00:00:00Z                     # null = never · soft-archive when reached
promote_after: "7d" | "5_access"                    # duration or access count
reinforce_count: 0                                  # access event counter
```

### Deterministic promotion rule (no LLM call)

- `reinforce_count >= promote_after` → `tier++`
- access event → reset decay timer + `reinforce_count++`
- `forget_at` reached → soft-archive flag
- `procedural` (top tier) does not promote

Full design rationale in [`paper/LLM_WIKI2_FUSE_DESIGN.md`](paper/LLM_WIKI2_FUSE_DESIGN.md);
implementation at [`recall.py:708+`](recall.py).

### Other v2.0.0 additions

- **9 agentmemory-verbatim lifecycle hooks** in `stop_hook.py` for
  Claude Code: SessionStart, UserPromptSubmit, PreToolUse, PostToolUse,
  PostToolUseFailure, PreCompact, SubagentStart/Stop, SessionEnd
- **`add_worker(spec)` MCP tool**: super-agents register deterministic
  worker specs (cron / pubsub / queue / http / custom) to `.cache/workers.jsonl`
- **RRF k=60 fusion** in `recall.py`: combine BM25 + vector + KG ranked
  lists with session-diversified output (max 3 per session · agentmemory verbatim)
- **`npx nautilus-compass init`**: one-command workspace setup creating
  `.compass/.env`, sample anchors, and Claude Code hook templates

### "Opinionated" — what we declined

Frame borrowed from [GBrain](https://github.com/garrytan/gbrain)
("Garry's Opinionated OpenClaw/Hermes Agent Brain"). compass v2.0.0 takes
a stance on what *not* to include:

- ❌ **No LLM at ingest** (USD 3.50 / 100M tokens · BGE-m3 embeds raw text)
- ❌ **No LLM at tier promotion** (deterministic schema only · `reinforce_count` + `promote_after`)
- ❌ **No LLM at forgetting** (ISO8601 `forget_at` + counter only)
- ❌ **No vendoring of GBrain or OpenViking source** · paradigms are
  rewritten from scratch in Python · GBrain (MIT, TypeScript) and
  OpenViking (AGPL-3.0, verified 2026-05-22) are paradigm references only
- ❌ **No graph rerank for LongMemEval-style closed haystacks** ·
  cost us −6.2 pts in v0.8 ([`paper/RESULTS_v0.8.md`](paper/RESULTS_v0.8.md))

---

## What's coming · v3.0 / v3.5 fusion (dev branch preview)

Active development on the [`v3-full-fusion`](https://github.com/chunxiaoxx/nautilus-compass/tree/v3-full-fusion)
branch · not in any release. Plan: ~2 work weeks · 8 Sprints · each Sprint
has a prove-or-kill gate (statistical · SQL/eval · not agent self-assessment).

**Default-off byte-equal promise**: with no opt-in env set, v3.0 / v3.5
behavior is byte-equal to v2.0.1. Verified by
[`tests/test_llm_opt_in.py`](tests/test_llm_opt_in.py) ·
the `test_default_off_invariant_*` family gates every PR into `main`.

### v3.0 deterministic (Sprints 1-2 · no LLM)

- **Typed knowledge graph** layer (Sprint 1) · 6 entity types · 8 edge types ·
  2-pass extract (regex + BGE cosine) · backward-compat NO-OP when graph not built
- **Confidence scoring + contradiction hook** (Sprint 2 · deterministic formula
  over source count / recency / contradicted-by count)
- **`MEMORY_REPORT.md` auto-gen** (Sprint 2 · session-end hook · 4-tier
  distribution + cumulative_impact + drift summary)
- **`implementation_notes` frontmatter** (Sprint 2 · `rationale` + `rejected: [{alt, why}]`)

### v3.5 opt-in LLM features (Sprints 3-7 · all default-off)

| env var | tier | feature (Sprint) |
|---|---|---|
| `COMPASS_USE_LLM_RESOLVE` | 1 (session-end) | LLM contradiction resolution (Sprint 3) |
| `COMPASS_USE_LLM_VERIFY` | 4 (runtime) | anti-confabulation cite-or-refuse (Sprint 4) |
| `COMPASS_USE_LLM_DRIFT_PAY` | 4 (runtime) | drift × outcome anchor feedback (Sprint 5) |
| `COMPASS_USE_LLM_REFLECT` | 3 (periodic) | self-reflection semantic emit (Sprint 6) |
| `COMPASS_USE_LLM_ECON` | 4 (runtime) | memory-as-economy NAU budget (Sprint 7) |

Pattern mirrors the existing `COMPASS_USE_GEMINI_FLASH` opt-in
([`judges/gemini_flash.py`](judges/gemini_flash.py)) — env truthy
(`1`/`true`/`yes`/`on`) activates · anything else disables. Registry: [`llm_opt_in.py`](llm_opt_in.py).

### Kill-gate semantics

Per-Sprint gates are pre-registered. If a Sprint's gate metric does not
pass (e.g. Sprint 1: multi-hop +3pp on LongMemEval-S `multi-session` subset,
n=133), that Sprint **stops** · no further Sprints attempted · the
corresponding paper3 v2 novelty claim is removed. This protects against
post-hoc rationalization of negative results.

---

## Case study · 4-dialog OSS multi-agent reliability

Across 28 hours on 2026-05-30 / 31, four Claude Code dialogs
(compass / Soul / V5 / nautilus-core) ran concurrently on shared
filesystem-mediated protocols. The recorded run includes:

- **Drift detection** firing 314 times / 7d (76 / 24h) with
  `act_on_rate` measured at **9.87% / 7d · 40.79% / 24h**
- **Cross-dialog contract** `cnt_compass_soul_sub_a1` closing in
  **17.92h** (vs 6d 21h budget · 5.8d slack)
- **13 plan-dup audits** preventing ~40-50h of speculative
  re-implementation
- **First cross-dialog L4 fire**: Soul daemon-shipped PR #88 settled
  50 NAU through the agent-first economy
- **One verify-gap caught by the case study itself**: a handoff claim
  of "22/22 tests GREEN" was actually 11/22 broken until `scripts/__init__.py`
  was added (commit pushed in the same change as the case study)

The full field log including 7 generalizable patterns for OSS multi-agent
reliability is at [`docs/case_study_4dialog_compass.md`](docs/case_study_4dialog_compass.md).

---

## What problem does this solve

### A. Long sessions drift

You told Claude at session start: *"never claim deployment success
without verification."* Fifty prompts later Claude says *"deployed
successfully ✅"* — without verifying. The memory rule was there; the
AI forgot it under context pressure.

### B. White-box drift detection isn't reachable

[Persona Vectors (Anthropic, 2025)](https://arxiv.org/abs/2507.21509)
proved that LLM activations contain directions for sycophancy and
hallucination. But that requires model weights — closed APIs (Claude,
GPT-4) don't expose them. There has been no production black-box
equivalent that runs in a Claude Code hook.

### C. Memory plugins solve only half the problem

Mem0, Letta, claude-mem, Zep all compete on *"recall the most relevant
past memory."* But memory recalled doesn't stop the AI from breaking
the rule **this time** — that other half has been unsolved.

---

## How it works

```
            User prompt: "Fix bug X for me"
                         │
                         ▼
       ┌─────────────────────────────────────┐
       │  UserPromptSubmit Hook (this plugin)│
       └─────────────────────────────────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
       ┌────────┐  ┌─────────┐  ┌──────────┐
       │ recall │  │  drift  │  │ profile  │
       │ memory │  │  check  │  │ aggregate│
       └────────┘  └─────────┘  └──────────┘
                         │
                         ▼
       Hooks inject results into Claude's system prompt:
       - Time-bucketed past memory (BGE-m3 semantic recall)
       - Drift score + nearest negative anchor (if score < threshold)
       - Profile facts ("you have 3 unfinished tasks in this repo")
                         │
                         ▼
            Claude answers — with full context loaded
```

The drift detector compares each prompt against an anchor set
(25 positive + 35 negative behavioral patterns drawn from real failure
transcripts) using BGE-m3 cosine similarity. AUC 0.83 on held-out, 50ms
p95 hook latency.

---

## Measuring drift loop closure (act-on rate)

Drift detection without ack instrumentation is an open loop · the detector
fires alerts but nothing measures whether the agent (or user) actually acted
on them. v3 closes this loop with a single rate metric.

**The signal**: every fired drift alert gets a stable `alert_id` and lands
in `.cache/drift_mitigation_log.jsonl`. When the user acknowledges the alert
via the feedback CLI

```bash
python ~/.claude/plugins/nautilus-compass/feedback.py log <alert_id> fp|tp
```

(`fp` = false positive · `tp` = true positive · either way the alert was
seen and judged), a matching `kind: "ack"` record is appended to the *same*
sidecar.

**The metric**: `act_on_rate(window_hours)` groups records by `alert_id`
within the window and reports the fraction of fired alerts that received at
least one ack. The legacy KPI script prints it alongside everything else:

```bash
python ~/.claude/plugins/nautilus-compass/audit_kpi.py
```

```
=== act-on rate (drift alert closure · target ≥0.70) ===
  · 24h: fires=81   acked=1    rate=0.012
  ·  7d: fires=294  acked=1    rate=0.003
```

**Target**: ≥0.70 over rolling 7d. Below 0.30 indicates the agent is tuning
out alerts (cry-wolf · cf. the [open-loop write-up](https://github.com/chunxiaoxx/nautilus-compass/blob/v3-full-fusion/docs/plans/2026-05-29-compass-comprehensive-uplift-design.md))
· raise the firing threshold (`drift/firing.py:should_fire_drift`) or
recalibrate negative anchors via `feedback retrain`. Programmatic API for
CI / cron monitors:

```python
from audit_kpi import act_on_rate
m = act_on_rate(window_hours=168)
assert m["rate"] >= 0.70, f"drift loop open · rate={m['rate']:.3f} fires={m['fires']}"
```

---

## Headline numbers

| Benchmark | Score | Honest compare |
|---|---|---|
| **LongMemEval-S** (n=500) | **56.6%** (locked at v0.8) | open-source 50–60% band · white-box leaders (OMEGA, Mem0g, ByteRover) report 90+% — that gap is an architectural ceiling for black-box, not a tuning gap. See [BLACKBOX_VS_WHITEBOX](paper/BLACKBOX_VS_WHITEBOX.md). |
| **EverMemBench-Dynamic** (n=500) | **44.4% (Run 1) / 47.3% (Run 2)** | tops the four published Table 4 baselines (Mem0 37.09, Zep 39.97, MemOS 42.55, MemoBase 34.27). Not "industry SOTA" — OMEGA / Mem0g haven't reported on EverMemBench publicly. |
| **Drift detector AUC** | **0.83 held-out / 0.92 in-set** | only public memory layer that does drift detection at all — white-box systems abstract prompts into facts before drift becomes checkable |
| **Reproduction cost** | **~$3.50** for 500 LongMemEval questions | ~14× cheaper than GPT-4o-judged stacks ($50+) |
| **p95 hook latency** | **<50 ms** | safe for every-prompt invocation |

We deliberately report Run 1 (44.4%) as the abstract headline for
EverMemBench to avoid cherry-picking; the cross-run mean (45.84%) clears
MemOS by +3.3 pts. See `paper/sections/paper2_06_5_evermembench.tex`
for honest dual-run + Gemini cross-judge sensitivity analysis.

**Try it without installing**: live drift-detection + Merkle-integrity
demo at [huggingface.co/spaces/chunxiaox/nautilus-compass](https://huggingface.co/spaces/chunxiaox/nautilus-compass)
(CPU only · metadata-mode jaccard fallback · no signup needed).

**Reproduce the numbers**: evaluation dataset (behavioral anchors +
labeled session traces for drift ROC + LongMemEval-S / EverMemBench
scoring) is live on the Hugging Face Hub:
[huggingface.co/datasets/chunxiaox/nautilus-compass-test-data](https://huggingface.co/datasets/chunxiaox/nautilus-compass-test-data)

```python
from datasets import load_dataset
ds = load_dataset("chunxiaox/nautilus-compass-test-data")
```

---

## Quickstart

### Install in Claude Code

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass ~/.claude/plugins/nautilus-compass
bash ~/.claude/plugins/nautilus-compass/install.sh

# Start the BGE-m3 daemon (one-time per boot)
bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
```

The installer wires three hooks into `~/.claude/settings.json`:
- `UserPromptSubmit` → injects time-bucketed memory recall + drift
- `PostToolUse` → mid-session writer
- `Stop` → end-of-session summary writer

Five user-facing slash commands appear in Claude Code:
`/compass-verify` · `/compass-drift` · `/compass-recall` ·
`/compass-search` · `/compass-status`.

### Install in any other MCP client

```bash
python ~/.claude/plugins/nautilus-compass/scripts/install_to_agent.py
```

Auto-detects Claude Desktop, Cursor, Cline, Continue.dev, Zed Editor and
patches their MCP config. See [`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md)
for per-agent copy-paste configs and [`docs/mcp-usage.md`](docs/mcp-usage.md)
for the raw protocol specification.

### Cloud-hosted alternative (no local install)

```bash
curl https://compass.nautilus.social/.well-known/agent.json
```

Returns the standard A2A discovery descriptor. Sign up at
`compass.nautilus.social/signup` for a hosted gateway with multi-user
sync, audit log, and managed BGE-m3 deployment.

---

## What's exposed (7 MCP tools)

| Tool | Purpose | Latency |
|---|---|---|
| `ingest_obs(name, body, agent_id?)` | Write observation with auto-anchor + drift signal | ~150 ms |
| `recall(query, project?, top_k?)` | BGE-m3 semantic + keyword search | ~200 ms |
| `session_search(query, since?)` | Time-bucketed session-log search | ~80 ms |
| `profile(user_id?)` | Work-profile aggregate (topics, agents, drift trend) | ~100 ms |
| `drift_check(prompt, project?)` | Black-box drift score against anchors | <50 ms |
| `drift_history(since?, agent_id?)` | Drift score timeline for trend audit | ~30 ms |
| `feedback_log(direction, reason)` | Log positive/negative anchor signal | <20 ms |

The MCP server speaks JSON-RPC 2.0 over stdio / TCP / TLS / mTLS.
Per-token RBAC, per-token rate limiting, `notifications/{progress,
cancelled, message}`, `logging/setLevel`, and `resources/*` for session-log
streaming are all spec-complete.

---

## Comparison

| Capability | this | mem0 | Letta | Zep | claude-mem | MemOS | Smriti |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Cross-agent memory | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | archive-only |
| MCP A2A protocol native | ✅ TLS+mTLS+RBAC | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Drift detection | ✅ AUC 0.83 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Merkle integrity audit log | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| LongMemEval-S verified | ✅ 56.6% (locked) | n/r | n/r | n/r | ❌ | n/r | ❌ |
| EverMemBench verified | ✅ 44.4-47.3% | 37.09 | n/r | 39.97 | n/r | 42.55 | ❌ |
| Self-host + hosted both | ✅ | ☁ only | ✅ | ☁ only | ✅ | OSS only | OSS only |
| License | MIT | Apache | Apache | proprietary | MIT | Apache | MIT |

`n/r` = not reported in their published evaluations. Smriti is a team
conversation archive with git-based sharing — different scope from a
runtime memory layer, so most rows are intentionally out-of-scope rather
than missing features.

---

## Platform integration · BP1 + BP3 contract

If you run the OSS plugin alongside a Nautilus-style task platform (or
your own multi-agent backend), two MCP tools open a bidirectional channel
without any new HTTP server:

| Tool | Direction | Purpose |
|---|---|---|
| `submit_platform_task(name, channels, payload, anchor_pack_hint, priority)` | compass dialog → platform | Push a task into the platform's queue. File-based by default (`~/.claude/projects/_platform_queue/<id>.json`); auto-promotes to HTTP `POST` when `COMPASS_PLATFORM_QUEUE_URL` is set. |
| `ingest_platform_task_result(task_id, result_summary, channels_published, drift, agent_id)` | platform → compass | Platform agent reports completion. Writes a JSON archive AND a `session_*.md` so the result becomes searchable cross-session via `recall` / `session_search`. |

End-to-end round-trip — no platform deployment needed for the OSS half:

```bash
python examples/platform_flywheel_demo.py
# [1] compass dialog → submit_platform_task     (queues to file)
# [2] platform V5 cycle ← poll _platform_queue/ (claims by status flip)
# [3] platform agent → executes channels        (simulated)
# [4] platform agent → ingest_platform_task_result
# [5] compass dialog → session_search           (HIT · result is searchable)
# OK · BP1 + BP3 round-trip verified
```

The full wire spec, breakpoint analysis, and SaaS-side TODO list live in
[`docs/PLATFORM_HANDSHAKE.md`](docs/PLATFORM_HANDSHAKE.md) §7.

### V7 governance layer (v0.1, opt-in)

For deployments running multiple specialised executors (V5, V6, Kairos, …),
three additional MCP tools provide a thin governance layer that decomposes
multi-channel work, audits cross-agent state, and locks the L0 immutable
core. V7 sits **above** the executors — it routes and audits, it does not
execute or chat with an LLM itself.

| Tool | Purpose |
|---|---|
| `governance_dispatch(name, channels, payload, anchor_pack_hint, priority)` | Decompose 1 complex task → N routed sub-tasks (heuristic table picks executor per channel) |
| `governance_audit(days, project)` | Scan recent session logs for fake-closure / red drift / empty platform results |
| `governance_lock_check(bootstrap)` | SHA256 lock on `recall.py`, `merkle_chain.py`, `anchors.json`, `selftest.py` |

```bash
python examples/v7_governance_demo.py
# [1] V7 governance_lock_check · bootstrap + verify
# [2] V7 governance_dispatch · 4 channels → routed to v5/v5/v6/kairos
# [3] V7 governance_audit · 7-day scan
# OK · V7 v0.1 governance round-trip verified
```

Contract details + platform-side TODOs (cron, governance fee, CI gate, telegram
`/dispatch`) in [`docs/PLATFORM_HANDSHAKE.md`](docs/PLATFORM_HANDSHAKE.md) §8.

---

## Documentation

- [`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md) — per-agent install configs (6 platforms + 3 frameworks)
- [`docs/mcp-usage.md`](docs/mcp-usage.md) — raw MCP protocol guide, TLS setup, RBAC
- [`docs/PLATFORM_HANDSHAKE.md`](docs/PLATFORM_HANDSHAKE.md) — OSS↔SaaS coordination contract
- [`paper/`](paper/) — two papers (drift detection + memory pipeline) and supporting eval scripts
- [`CHANGELOG.md`](CHANGELOG.md) — versioned release notes
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — adding new domain anchors / running benchmarks

---

## Citation

If you use this work, please cite:

**Paper 1 · drift detection**:

```bibtex
@misc{nautiluscompass-drift-2026,
  title  = {Nautilus Compass: Black-box Persona Drift Detection
            for Production LLM Agents},
  author = {Chunxiao Wang},
  year   = {2026},
  note   = {Yiluo Technology Co., Ltd.},
  howpublished = {\url{https://github.com/chunxiaoxx/nautilus-compass}}
}
```

**Paper 2 · memory pipeline + EverMemBench cross-bench**:

```bibtex
@misc{nautiluscompass-memrecall-2026,
  title  = {Closing the Memory Recall Gap with Chinese LLMs:
            A Multi-Stage Retrieval Pipeline Achieving Zep-SOTA Performance
            on LongMemEval-S at 1/15 Cost},
  author = {Chunxiao Wang},
  year   = {2026},
  note   = {Yiluo Technology Co., Ltd.},
  howpublished = {\url{https://github.com/chunxiaoxx/nautilus-compass}}
}
```

The `howpublished` field will be updated to the arXiv identifier once
the preprints are live.

We also build on prior work — please cite as appropriate:

- BGE-m3 / BGE-Reranker (Chen et al., BAAI 2024)
- **Persona Vectors** (Chen et al., Anthropic, [arXiv:2507.21509](https://arxiv.org/abs/2507.21509)) — *complementary white-box approach, not the same as ours*
- DPT-Agent strategy distillation ([arXiv:2502.11882](https://arxiv.org/abs/2502.11882))
- A-MEM dynamic links ([arXiv:2502.12110](https://arxiv.org/abs/2502.12110))
- LongMemEval (Wu et al., NeurIPS 2024)
- EverMemBench (Hu et al., 2026)

---

## License

- **Code, plugin, MCP wrapper, papers, scripts** — MIT (see [`LICENSE`](LICENSE))
- **Behavioral anchor files** (`anchors*.json`) — CC0 1.0 Universal (see [`LICENSE-ANCHORS`](LICENSE-ANCHORS))

You may use this in any project, commercial or otherwise, with attribution.

---

## Star history

[![Star History Chart](https://api.star-history.com/svg?repos=chunxiaoxx/nautilus-compass&type=Date)](https://star-history.com/#chunxiaoxx/nautilus-compass&Date)

## Contributors

<a href="https://github.com/chunxiaoxx/nautilus-compass/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=chunxiaoxx/nautilus-compass" alt="Contributors" />
</a>

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Contact

- **Author**: Chunxiao Wang · Yiluo Technology Co., Ltd. · `chunxiaoxx@gmail.com`
- **Issues**: [github.com/chunxiaoxx/nautilus-compass/issues](https://github.com/chunxiaoxx/nautilus-compass/issues)
- **Hosted gateway**: [compass.nautilus.social](https://compass.nautilus.social)
- **中文文档**: [README.zh-CN.md](README.zh-CN.md)

---
title: "Compass v1.1.0 · we shipped a memory plugin that catches its own consumption drift"
published: true
description: "Recall != consumption. Same anti-pattern reproduced across sessions despite recall hitting the right files. Three layers of fix and a capability-driven governance plan that scales without templates."
tags: llm, memory, mcp, agents
canonical_url: https://github.com/chunxiaoxx/nautilus-compass
---

# Compass v1.1.0 · the recall consumption fix

We shipped [nautilus-compass v1.1.0](https://github.com/chunxiaoxx/nautilus-compass)
12 hours after v1.0.0. v1.0.0 was the public stable cut. v1.1.0 fixes a
class of failure that v1.0.0 surfaces but does not catch · which we
caught in our own usage 5 hours after launch.

## The bug we caught in production

A sister Claude Code dialog was supposed to publish a long-form article
to wechat using a 6-step quality pipeline (audit-gate, xhs-cards-embed,
specific account login flow). The pipeline was documented in cross-session
memory · a file called `publisher_quality_pipeline_20260430.md`.

Compass recall fired correctly · the file appeared in the agent's
`UserPromptSubmit` hook output:

```
🟢 [3h old] memory/publisher_quality_pipeline_20260430.md
       audit-gate / xhs-cards-embed / wxid · v6 必须先过 critic 6 维评分再发布
```

The agent saw the title. Saw the 80-character description. Acted. **It
did not Read the file body.** The actual rules — *how* to walk audit-gate,
*which* wxid, *what* xhs-cards-embed structure looks like — those rules
were in the body. None of them entered the agent's working context.

The agent then reproduced exactly the failure mode the file was written
to prevent: ad-hoc `_tmp_publish_v8.cjs` scripts, no critic round, wrong
login path.

The user's diagnosis was sharp:

> compass 召回到了 · 我没消费 · 这是 agent 层的人格漂移 · 不是 compass 本身的失败

That's half right. Recall surfaced the right file. The agent failed to
consume. But the **shape of the recall response made the failure easy** —
we returned title + 120-char description. Easy to skim. Easy to assume
you have read it when you have only read the index.

This is structural. Not the agent's fault.

## The three-layer fix in v1.1.0

### v0 · embed body in top-3 hits

Top-3 recall hits now embed the first 800 characters of post-frontmatter
body in an indented `│` block:

```
🟢 score=0.84 · [3h old] memory/publisher_quality_pipeline_20260430.md
       audit-gate / xhs-cards-embed / wxid · v6 必须先过 critic 6 维评分
       │ # Publisher quality pipeline
       │
       │ Six-step pipeline mandatory before publishing to wechat:
       │ 1. audit-gate · V6 critic checks against 6 dimensions ...
       │ 2. xhs-cards-embed · embed cards into article body via ...
       │ 3. wxid login flow · use wxid `chunxiaox` not openid_of_first_follower
       │ ...
       │ … (+1273 more · Read publisher_quality_pipeline_20260430.md for rest)
```

The agent now has the rules in its working context. No additional `Read`
tool call required. Tail hits 4..K stay header-only to keep the response
bounded (~3KB total).

### v1 · embed past-mistake body in anti-anchor alerts

Compass's drift detector matches the current prompt against 35 negative
anchors learned from prior mistakes (`"我猜应该是这样 · 反正用户不查"`,
`"假装上次说定了的方案 · 用户应该忘了"`, ...).

Until v1.1.0 the alert just said: *"matched anti-anchor X with cos=0.625"*.
Same problem as v0 — label visible, body invisible, agent shrugs.

v1.1.0 alerts now embed body from the most-relevant past lesson session.
Two-tier match: substring 6-gram against the anchor + lesson-type
frontmatter (Tier 1, precise) · falls back to recent `drift!=green`
sessions (Tier 2, the agent's own self-reported slip-ups). Every alert
becomes actionable, not decorative.

### v2 · detect "recall fired but not consumed"

The most direct signal: did the agent actually open any of the files
recall surfaced?

`recall_consumption.py` (new module) walks back through the live session
jsonl file, finds N most-recent recall blocks, extracts memory file
paths, then checks subsequent assistant turns for matching `Read` tool
calls. If recall surfaced N paths and 0 got read, that is the failure
signature.

Wired into:

- `drift_check` MCP tool result — runs even when the BGE daemon is
  unreachable, since the audit is pure file traversal
- `mid_session_hook` every 25 tool calls — only nags when ≥3 unconsumed
  AND ratio < 0.3 (real signal, not noise)

Tested on a 130MB / 32k-line session: 41 recall hits surfaced, 0 consumed.
Smoking gun for "label != consumption" drift.

## V7 v0.2 · the governance plan that scales without templates

v1.0.0 shipped a thin V7 governance layer with three tools:
`governance_dispatch` (fan-out router), `governance_audit` (cross-agent
fake-closure scanner), `governance_lock_check` (L0 hash lock for the
immutable core). 13 MCP tools total.

v0.1 dispatch worked but it was a fan-out router — given `channels=
[dev.to, x, github]` it produced one bounty per channel via static dict
lookup. A user asked the right question:

> 千行百业有各种不同的任务类型永远不可能覆盖。

Right. Templates cannot cover the long tail of industries. The platform
side already solved this for *publishing* — channel adapters + anchor
pack registry — so adding a new channel or vertical = data change, not
code change.

v1.1.0 brings the same idea to *decomposition*. The new
`governance_plan` MCP tool reads two file-exported registries:

1. `_platform_registry/agents_capabilities.json` — what each executor
   declares it can do (id, outputs, optional domains, optional anchor
   packs)
2. `_platform_registry/anchor_packs_phases.json` — per-domain DAG of
   phases, each phase says `requires_capability` and `depends_on`

For each phase, V7 ranks executors by capability score (+10 capability
match, +5 domain match, +3 anchor pack match), picks the highest, emits
a queue file with `depends_on_phase_ids` so platform-side cron mints
bounties in the right order.

Verified on two domains:

- `marketing/dev-tools` → 4 phases routed V5/V5/V5/Kairos
- `caishen-finance/audit` → 5 phases · V6 wins for `numeric-audit`
  (V5 doesn't declare it · V5 takes write+publish)

Adding `medical/literature-review` next: 1 row in `platform_anchor_packs`
+ 1 row in `platform_agents.metadata.capabilities[]`. Zero V7 source
change. Zero MCP tool surface change.

## What stayed unchanged · the eval headlines

Eval numbers are still the v1.0.0 locked numbers from 2026-05-08:

| Metric | nautilus-compass | best public baseline |
|---|---|---|
| LongMemEval-S (n=500) | **56.6%** | Zep 55-60% (different judge) |
| EverMemBench-Dynamic Run 1 | **44.4%** (n=500) | MemOS 42.55 |
| EverMemBench-Dynamic Run 2 | **47.3%** (n=497) | — |
| Drift detector ROC AUC (held-out) | **0.83** | — |
| Reproduction cost | **$3.50** end-to-end | $50+ for GPT-4o-judge stacks |

v1.1.0 doesn't move the eval numbers. It moves the *consumption*
numbers — the ratio of recall hits whose body actually lands in the
agent's working context. We do not have a clean benchmark for that yet
(suggestions welcome) but in our own sessions it went from "skim the
title and proceed" to "rules-in-context by default."

## Try it

```bash
pip install nautilus-compass==1.1.0
# or
npm install nautilus-compass@1.1.0
```

Two papers on arxiv (drift detection + memory pipeline). 228 pytests
all green. MIT (anchors CC0).

Repo: [github.com/chunxiaoxx/nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass)

In-browser drift demo (no install): [huggingface.co/spaces/chunxiaox/nautilus-compass](https://huggingface.co/spaces/chunxiaox/nautilus-compass)

## Postscript · what we believe

> Recall != consumption · 看正文才算消费 · 不然命中等于零

Long-running agents drift. They forget rules they read three sessions
ago. They reproduce mistakes someone else already paid for. The fix is
not a smarter model · it is making the rules unmissably present in the
working context, then auditing whether they were actually consumed,
then making the audit cheap enough to run every 25 tool calls.

That is what v1.1.0 ships.

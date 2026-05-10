---
title: "Black-box vs white-box agent memory · why compass is the only zero-LLM-extraction OSS layer"
published: false
description: "Mem0, Letta, Cognee, Zep, MemOS, smrti all burn LLM tokens to extract facts before they store. compass doesn't. Here's the architectural trade and who it's for."
tags: llm, memory, mcp, agents
canonical_url: https://github.com/chunxiaoxx/nautilus-compass/blob/main/paper/BLACKBOX_VS_WHITEBOX.md
---

# Black-box vs white-box agent memory

Every public agent-memory project we benchmarked — **Mem0, Letta, Cognee,
Zep, MemOS, smrti** — burns LLM tokens to extract facts, entities, or graph
edges *before* it stores anything. They're white-box memory: the system has to
look inside your conversation, send it to OpenAI / Anthropic / a configured
provider, and pay extraction tokens to build its index.

`nautilus-compass` is the one we found that doesn't. It runs BGE-m3 locally,
embeds raw conversation text, and never asks an LLM "what's a fact in here." We
call this **black-box memory**, and the rest of this post is about what that
architectural choice buys, what it costs, and who it's for.

## What we verified (6/6 public projects)

| Project | Architecture | Evidence |
|---|---|---|
| **Mem0** | white-box | "Mem0 requires an LLM to function, with `gpt-5-mini` from OpenAI as the default" · `memory.add(messages)` calls the LLM internally to extract facts |
| **Letta** *(formerly MemGPT)* | white-box (deeper · is the agent runtime) | `Letta(api_key=...)` · `agents.messages.create()` · `model="openai/gpt-5.2"` · Letta *is* the agent server, not a sidecar |
| **Cognee** | mixed: hook-based ingestion (like compass), white-box internals | `LLM_API_KEY=YOUR_OPENAI_KEY` · `cognify` pipeline calls an LLM to extract entities and build a knowledge graph |
| **Zep** *(YC W24)* | white-box | "Zep automatically extracts relationships and maintains a temporal knowledge graph" · powered by Graphiti, which uses an LLM to build the graph |
| **MemOS** | white-box | `MOS_CHAT_MODEL_PROVIDER=openai/qwen/deepseek/minimax` · provider must be configured, extraction runs through it |
| **smrti** | white-box (with optional local-only mode) | "hybrid GLiNER2 + LLM pipeline auto-extracts entities" · proxy intercepts OpenAI requests; default mode calls an LLM |
| **compass** *(this project)* | **black-box** | BGE-m3 embeds raw text locally · no fact / entity / graph extraction step · judge LLM only used at eval time, never at index or query time |

The Cognee row is the one we want to be careful about. Cognee ships a Claude
Code plugin that hooks into the same lifecycle events as compass
(`UserPromptSubmit`, `SessionEnd`, etc.). At the **integration layer**, it
looks like compass. But behind the hook, `cognify` still calls an LLM to
build a knowledge graph. So the right framing isn't *"compass is the only
hook-based memory"* — it's *"compass is the only one that doesn't burn LLM
tokens to populate its index."*

## The architectural choice and what falls out of it

```
no LLM extraction at index time  (the choice)
          │
          ├── reproduction cost ~14× cheaper
          │     (GPT-4o-judged stacks: $50+ on LongMemEval-S
          │      compass: $3.50, end-to-end, judge-only)
          │
          ├── data can stay fully local
          │     (no extract step → no payload to send to OpenAI)
          │
          ├── LLM-agnostic
          │     (BGE-m3 doesn't care which LLM the agent itself uses)
          │
          └── drift detection becomes possible
                (raw prompts are still in the index. You can score
                 the next prompt against behavioral anchors before
                 the agent acts. White-box systems have already
                 abstracted prompts into facts — the surface
                 needed for drift is gone.)
```

Four properties, one root cause. They're not four marketing bullets — they're
the same architectural decision viewed from four sides.

## What "fully local" actually means here

A note before the trade-off section, because this matters for
production deployment decisions:

- **The compass memory layer itself is fully local**: BGE-m3 embedding,
  drift anchor scoring, memory storage, and recall retrieval all run
  on the user's machine with no network calls.
- **The agent LLM** (Claude, GPT-4, DeepSeek, Gemini, etc.) and the
  **judge LLM** (used at evaluation time only, not at production
  query time) are cloud APIs in our default configuration. Both can
  be replaced with local models via Ollama or vLLM, but this is a
  deployment choice the user makes, not a default.
- **Reproduction cost** ($3.50 for 500 LongMemEval-S questions) is
  measured on Volcengine DeepSeek pricing (Volc Ark coding plan,
  China region). On AWS / GCP with Anthropic or OpenAI APIs, the
  same eval costs roughly 5–10× more — still well below GPT-4o-judged
  white-box stacks at $50+, but not the literal "$3.50 anywhere."
- The 14× cheap-to-reproduce framing is therefore a **regional
  advantage** for users in China, and a **judge-choice advantage**
  (GPT-4o-mini vs GPT-4o) for users elsewhere. We disclose this
  explicitly in `paper2_06_limitations.tex`.

## What it costs · the trade-off, said out loud

Black-box memory has no entity-aware retrieval, no temporal knowledge graph,
no fact consolidation, no relationship reasoning. That hurts on benchmarks
that reward exactly those things.

On **LongMemEval-S** (n=500, GPT-4o-mini judge, top-K=5) compass scores
**56.6%**. Recent white-box leaders — OMEGA, Mem0g, ByteRover — report
**90+%** on the same benchmark. We're behind by roughly 30 points. Setup
isn't perfectly comparable (their judges, top-Ks, and entity graphs are
heavier), but even after pulling setups closer we don't expect black-box
to close that gap. **It's an architectural ceiling, not a tuning gap.**

On **EverMemBench-Dynamic** (n=500, two runs · 44.4% / 47.3%) compass tops
the four published baselines in Table 4 (MemOS 42.55, Zep 39.97, Mem0 37.09,
MemoBase 34.27). We don't claim "industry SOTA" because OMEGA/Mem0g/ByteRover
haven't reported on EverMemBench in a public table we can find. *Topping the
EverMemBench Table 4 is a real result; calling it "the new SOTA" without
those entries would be over-claim.*

On **drift detection** (held-out AUC 0.83) compass is the only public
project we can find that does this at all. White-box systems can't —
they've already lossy-compressed prompts into facts before drift is
checkable.

So the trade is:

> **−30 points on LongMemEval-S** (no entity graph, no temporal reasoning)
> in exchange for
> **14× cheaper reproduction · fully local option · cross-LLM and cross-client
> portability · drift detection that the white-box systems can't offer.**

If you need 90+% on LongMemEval and you're willing to pay extraction tokens
and ship data to a provider for that, white-box is the right answer and Mem0g
or OMEGA is your tool. If you need any of the four properties on the right —
and especially if you need *more than one of them at once* — black-box is
the only open-source choice we found.

## Who this is for

- **You're building agent products with regulated data** (medical, legal,
  finance). You can't send conversation content to OpenAI for fact
  extraction. White-box is closed off; compass works.
- **You're cost-bound.** Pay-per-call extraction at scale gets expensive
  fast. compass eliminates that line item entirely; the only LLM cost is
  the agent's own reasoning calls (which all of these tools incur anyway).
- **You want the same memory across Claude Code, Cursor, Cline, Continue,
  Zed, Claude Desktop.** White-box systems tend to bind to a runtime or
  SDK; compass is plain MCP and works wherever MCP is supported.
- **You care about catching the agent before it repeats a mistake**, not
  just answering "did we discuss this." Drift detection is currently
  unique to compass among public memory layers.

If your task is "answer factual questions accurately given a long history,
and accuracy is everything," white-box is better. We don't pretend
otherwise.

## What we are not claiming

- Not "the best memory layer." On LongMemEval-S we are 30 points behind the
  leaders. That's real and we publish the number on the front page.
- Not "the first hook-based memory layer." Cognee uses the same Claude Code
  hooks we do. The differentiator is below the hook, not at the hook.
- Not "industry SOTA on EverMemBench." We top the four published baselines
  in Table 4. Multiple white-box systems with stronger LongMemEval numbers
  haven't reported on EverMemBench publicly; until they do, "SOTA" is
  premature.
- Not "1× the cost of GPT-4o-judged stacks always." 14× cheaper is on
  LongMemEval-S reproduction; absolute number depends on which LLM you
  judge with and how many questions you replay.

## What we are claiming, precisely

> Among open-source agent memory layers we could find and verify
> (Mem0, Letta, Cognee, Zep, MemOS, smrti — six projects, READMEs and code
> examples checked May 2026), `nautilus-compass` is the only one that does
> not call an LLM to extract facts, entities, or graph edges at index time.
> That single choice is what makes it ~14× cheaper to reproduce, fully
> local-deployable, LLM-agnostic, MCP-portable, and drift-aware. The cost
> of the choice is roughly 30 points on LongMemEval-S vs. white-box leaders
> that do entity-graph extraction.

If a reader can show us another public project with the same architectural
property, we'll update this post. We'd rather be corrected than wrong.

## Try it · short version

```bash
pip install nautilus-compass==1.1.0
bash daemon_start.sh    # downloads BGE-m3 (~2GB), CPU is fine
npx -y nautilus-compass  # MCP mode for Claude Code / Cursor / Cline / etc
```

Live demo (no install): https://compass.nautilus.social
HF Space: https://huggingface.co/spaces/chunxiaox/nautilus-compass
GitHub: https://github.com/chunxiaoxx/nautilus-compass

MIT license · BGE-m3 weights are CC0 mirrored separately.

---

*Written 2026-05-10 after a brutal product audit suggested the LongMemEval
gap meant we were "not SOTA." That was true, and also the wrong frame:
we're in a different architectural niche, and we should describe ourselves
as that niche's first publicly verified entrant — not as a follower in a
race we structurally can't win. This post is the corrected framing.*

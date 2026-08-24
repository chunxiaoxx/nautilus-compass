---
title: "Benchmarks can't tell you if agent memory helps your team. A paired control can — here's ours"
published: false
description: "Every memory layer claims it helps. We built a paired control experiment with deterministic oracles to test ours — including the results that hurt."
tags: llm, ai, memory, agents
canonical_url: https://github.com/chunxiaoxx/nautilus-compass
---

# Does agent memory actually help? We ran the experiment nobody runs

We maintain [nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass), an
open-source memory layer for coding agents (MCP tools: recall, ingest, drift
detection). Like everyone in this space, we *claimed* memory makes agents
better. Public benchmarks (LongMemEval and friends) measure QA over
conversation transcripts — but as the MEM-α authors note, with/without-memory
comparisons are noisy precisely because models often answer from internal
knowledge anyway. What was missing, for our own product, was a *product-side*
paired control: deterministic task validators, facts a model has no channel to
know, retrieval scored separately from knowledge. So we ran one on ourselves.

This post is the full result — including two findings that hurt. (Ablation studies exist in the literature; what we add is the operator's view: what broke, what the fuel taxonomy should be, and what we now run hourly to keep memory honest.)

## The setup

We took three facts our team had learned the hard way and stored them in
compass memory. Crucially, we picked them by *type*:

- **F1** — a tribal API fact: a third-party API silently destroys data unless
  you forward server-assigned IDs in update payloads. Undocumented, learned
  from a production incident. A model has no channel to know this.
- **F2** — a tribal infra fact: which port our internal memory daemon listens
  on. Trivially knowable *if you have our memories*; unknowable otherwise.
- **F3** — a general engineering fact (explicit UTF-8 encoding on Windows).
  Any decent model already knows this. Included as a **negative control**.

Then, per fact, three runs of each arm:

- **Control arm:** the model answers a natural-language task question cold.
- **Treatment arm:** a *natural language* recall query (never containing the
  answer) retrieves top-3 memories; those get injected as context; then the
  same question.

Answers are judged by **deterministic validators** — the same kind of oracle
we use for benchmark fuel — never by an LLM judge grading its own homework.
Retrieval misses are scored separately from knowledge failures. Total: 9
retrievals, 18 model calls.

## Results

| Fact | Retrieval hit@3 | Control | With memory | Delta |
|---|---|---|---|---|
| F2 (port) | 3/3 | **0/3** | **3/3** | **+1.0** |
| F1 (API gotcha) | 3/3 | 0/3 | 1/3 | +0.33 |
| F3 (utf-8, negative control) | 3/3 | 0/3* | 1/3* | ~0 |

\* the F3 numbers came back noisy on this run — earlier runs of the same
control pass 10/10 cold. The honest summary: general engineering knowledge
shows **no reliable lift** from memory, which is exactly what a working
negative control should show.

The headline: **retrieval worked 9/9 times, and on the fact the model truly
could not know, memory flipped a 0/3 into 3/3.** That's the first externally
checkable evidence we've ever produced for our own product's core claim —
and it took an afternoon, not a research budget.

## Finding #1 that hurt: general knowledge is worthless fuel

Before this experiment we'd been feeding the memory pool everything — every
lesson, every gotcha. Two earlier runs of the same protocol on *general*
engineering facts returned **delta = 0.0, repeatedly**. The model already
knows that stuff. Storing it doesn't help; it just fills your index.

This forced a three-way classification of "learning fuel" that now gates what
we keep:

1. **General engineering knowledge** → zero headroom, don't store.
2. **Derivable good design** → unstable: the model sometimes re-derives it.
3. **Tribal facts** (private API behavior, internal conventions, incident
   lore) → **the only reliably useful category** — because the model has no
   channel to know them *except* through your memory.

If you run a memory layer, this is the uncomfortable implication: most of
what your auto-summarization pipeline diligently stores is category 1. The
moat is category 3, and category 3 mostly comes from incidents, not chats.

## Finding #2 that hurt: our memory had been silently dead

While building the experiment, every recall call failed. Root cause: on
Windows, our embedding stack crashed on import — a path-length limitation in
a system Python install. The keyword-matching fallback had been quietly
masking it. **Our semantic recall had been 100% broken, on the main
development machine, for an unknown length of time.** Nobody noticed because
nothing *measured* recall health.

That's the real lesson of this post, more than delta = 1:

> If you don't have a probe, your memory layer's failures are indistinguishable
> from "the agent didn't find it relevant."

We now run an hourly heartbeat: a real semantic query against the daemon,
with auto-restart on failure and an alert written into the memory pool itself.
The first night it ran, it caught the daemon dying and revived it. Boring,
unglamorous — and worth more than any feature we shipped that week.

## What this doesn't prove

One experiment, one model, three facts, n=3 per cell. It proves the *effect
exists* for tribal facts on our stack, not that it generalizes. The
distillation arm (does fine-tuning on stored incident knowledge move a held-out
benchmark?) is running now; pre-registered, honest either way.

## Try it

The experiment harness, the fuel-pool QC gates (a memory must fail a
cold-model control before it's worth keeping), and the heartbeat are all in
the repo. If you run an agent memory layer — yours or someone else's — we'd
genuinely love to see your numbers. The field has too many demos and too few
controls.

---
title: We quantized our AI judge. Here's exactly what broke.
published: true
tags: ai, llm, testing, mlops
ai: ai-assisted
---

Our production judge — a small 1.7B model with a LoRA adapter that grades other
AI outputs as **pass / fail / insufficient_evidence** (88.5% accuracy, ECE 0.072) —
is cheap to run. The obvious next step was quantization: serve it in int8 or int4
and cut the serving cost further.

Before flipping the switch, we did something unfashionable: we **froze the
acceptance criteria first** — "a quantized judge may ship only if it agrees with
the bf16 anchor on **≥99% of 291 held-out cases**" — and published them before
looking at any number.

**Results (all measured, artifacts sha-anchored):**

| Precision | Agreement with bf16 | Verdict |
|---|---|---|
| fp16 | **100.00%** (0 flips) | ✅ ships |
| int8-nf4 | 98.28% (5 flips) | ❌ fails the gate |
| int4-nf4 | 94.16% (17 flips) | ❌ fails the gate |

Drift grows monotonically with quantization strength. The five int8 flips and
seventeen int4 flips are each a case where the judge changed its *verdict* —
not its confidence, its answer. In a self-improving training loop, a judge flip
is not a leaderboard wobble; **it is wrong training data, injected silently.**

## The four-rule deployment discipline

1. **bf16/fp16 only** for production judges — int8/int4 are off the table until
   re-certified against a new frozen gate.
2. **Freeze criteria before running.** Criteria may only move stricter; loosening
   means a fresh preregistration.
3. **Label every claim** measured / inferred / unverifiable — and publish the
   unverifiable ones anyway.
4. **Two-way judging records**: judges grade, and get graded; errata ship as
   first-class artifacts.

## The full study

Complete per-case judgment matrix, gating criteria, runner, and the pre-registered
protocol: [`nautilus-compass` on GitHub](https://github.com/chunxiaoxx/nautilus-compass)
and [Hugging Face](https://huggingface.co/nautilus-compass). The arXiv version
ships this week.

---

**Need an independent judge for your own benchmark?** Our judging lane is free:
preregistered criteria, three-state verdicts, every artifact recomputable.
Intake is open at [nautilus.social/intake.html](https://nautilus.social/intake.html)
· live example: [nautilus.social/leaderboard.html](https://nautilus.social/leaderboard.html)

*Disclosure: this post was written by the author with AI assistance; every number
in it is measured and sha-anchored in the linked artifacts.*

*Chunxiao — nautilus-compass, Nautilus Platform*

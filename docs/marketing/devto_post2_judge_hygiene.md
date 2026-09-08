---
title: "Our AI Judge Silently Failed 14% of Our Eval — the Hygiene Protocol That Caught It"
description: "LLM-as-judge failures don't crash. They return wrong answers that look like data. A field taxonomy from 5 real failures in one 500-question eval, and the protocol we now run."
tags: ai, llm, machinelearning, opensource
ai_disclosure_level: some_ai
published: false
publish_at: 2026-09-10 21:00 (Beijing) — title 定稿需用户过目后 API 发布(dev.to title 发布后锁死)
cover_image: https://raw.githubusercontent.com/chunxiaoxx/nautilus-compass/main/docs/marketing/deck_assets/arch.png
---

While running a full-500 LongMemEval-S end-to-end evaluation of our agent memory layer ([nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass)), 71 questions — 14.2% of the benchmark — got silently recorded as *wrong answers*.

Not because the system answered them wrong. Because the judge did.

An LLM-as-judge gateway failed intermittently, and each failure was logged as a zero. The eval "completed" with a clean-looking score. Nothing crashed. That's the part that should scare everyone running LLM evaluations in 2026: **judge failures don't look like failures. They look like your model getting dumber.**

Here's the taxonomy of silent judge failures we hit in this one project, and the hygiene protocol that now catches them.

## The five failures (all real, all in our logs)

1. **Silent gateway outage → zero.** The judge endpoint timed out or reset intermittently. The harness recorded each failed call as "incorrect". 71/500 questions. A 14-point error band in the headline metric, from infrastructure, not intelligence.
2. **Reasoning eats the context window → systematic zeros.** One judge configuration produced pages of reasoning that consumed its 4096-token budget before emitting a verdict. The result was a *structured* run of zeros — not random noise, so it hid inside aggregate metrics for days. Cross-checking judges requires budgeting for output, not just input.
3. **Auth env mismatch → 100% failures that look like a bad model.** The harness read `OPENAI_API_KEY` while the environment exported `ARK_API_KEY`. Generation looked fine; every judgment call returned 401 and the pipeline kept walking. A credentials bug masquerading as a capability result.
4. **Refusal-template ≠ refusal-of-answer.** Our sweep for "judge refused" matched surface templates. Real refusals (contamination suspicion, ambiguity) hid behind different phrasings — and template positives included paraphrases that weren't refusals at all. Both directions of error, from one regex.
5. **The 12-question subset that lied.** An early 12-question read showed +16.7pt from one intervention. All twelve were the same question type. We nearly shipped the story. A 30-question mixed re-run collapsed it. Sampling bias is a judge-side failure too — the judge was the subset selector.

## The protocol (what we now do)

**Dual accounting, always disclosed.** Final full-500 verdict: 42.6% → 75.4%, where every question has a real judge verdict (the 71 outage questions were re-judged with the same judge, retry-only), and 81.6% like-for-like excluding them. We publish both numbers in the same sentence. If your eval report has one number and no error provenance, it's a marketing document.

**Preregistered gates.** Pass/fail thresholds committed *before* the run. We shipped a summary layer with its acceptance gates committed first; the final verdict cited the preregistered doc. Preregistration is cheaper than rerunning an eval you've already rationalized.

**Judge identity in every number.** Our e2e judging used our own harness with a glm-5.3-flash judge; the upstream benchmark's official harness uses GPT-4o. Cross-harness numbers are not comparable — when mem0 self-reports 94.4% and we report 75.4%, those are different judges, subjects, and possibly data versions. The comparison we *can* stand behind is retrieval-level, same questions, same criteria: P@1 0.890 vs 0.774 (scripts open, ~$3.50 to reproduce).

**Treat judge output as data with its own failure modes.** Verdicts get validated like any telemetry: unexpected zero-runs, latency outliers, and budget exhaustion are alerts, not aggregates.

**Independent reproduction over self-report.** We put a [Reproducibility Wall](https://github.com/chunxiaoxx/nautilus-compass/blob/main/docs/REPRODUCIBILITY_WALL.md) in the repo: anyone runs the head-to-head, their numbers go on the wall — favorable or not. Self-reported numbers from unverifiable harnesses are how this field inflates itself; the only durable fix is making reproduction cheap (~$3.50 and one command) and publishing disagreement.

## Why this matters beyond benchmarks

Everything agentic now gets graded by an LLM — eval harnesses, agent guardrails, RL reward models, CI for prompts. The failure mode generalizes: **when the grader degrades, the system optimizes against a fiction.** The RL loop doesn't notice your reward model had a bad night. Your eval CI doesn't fail when the judge has a 5% silent error rate — it fails when you *act* on it, weeks later.

Judge hygiene is not a benchmarking nicety. It's load-bearing infrastructure for every "AI judges AI" system shipping this year.

The full taxonomy + protocol is written up as a paper (in submission; link when it lands). Meanwhile the operational version lives in our repo, warts and all: every failed experiment above has its run log in `docs/evidence/`.

*Repo: [nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass) · hosted beta (self-serve): [compass.nautilus.social](https://compass.nautilus.social) · Reproducibility Wall: your numbers, favorable or not.*

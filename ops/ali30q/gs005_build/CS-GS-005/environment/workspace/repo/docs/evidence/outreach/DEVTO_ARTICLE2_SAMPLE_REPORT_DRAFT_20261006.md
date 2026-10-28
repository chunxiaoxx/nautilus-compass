---
title: "What a $199 AI Agent Evaluation Report Actually Looks Like (Full Sample, No Marketing)"
published: false
tags: ai, llm, evaluation, benchmark
---

<!-- 草稿 · B级制:呈用户过目后方可发布(内容触达第二篇,承推进队列③)· 2026-10-06
     发布通道:Dev.to API(实测可用);CTA 落点 nautilus.social/unipat.html
     数据口径:全部来自判分侧实测定版(#9896)与样例正本(sha16=6315954f45f2c715),禁改数 -->

You've seen a hundred LLM leaderboards. You've seen almost zero **harness** evaluations — and close to zero samples of what an evaluation report you'd actually pay for contains. So instead of writing another "benchmarks are broken" post, we published the full sample of our $199 deep-dive report, and this post walks through it.

**The sample (markdown, no gate):** https://org.nautilus.social/L2_report_sample.md

## What's inside the sample

The sample evaluates **v5-harness** (our in-house agent harness) on **J2-RL tool-call three-gate** — three rounds (r75/r76/r77) of raw readouts, plus:

1. **δ-judged deltas, not vibes.** We pre-register a minimum detectable difference (δ = 2.1pp from our RSI line). Any improvement below δ is recorded as `flat`. You cannot claim "better" from noise on our watch.
2. **Measured vs self-reported layering.** Data-provider claims are tagged `self-reported`; judge-side re-runs are tagged `measured`. The two never mix in one column.
3. **A fix-diff case.** A real regression found, root-caused, and re-measured after a gateway fix — because "we found and fixed a bug" is only credible with before/after numbers.
4. **Fuel-fit analysis** — which failure traces became training data, and which didn't qualify (with reasons).

## The leaderboard it feeds: a paired, pre-registered Round 1

Our Round 1 board ran two agent harnesses on the same 30-problem panel, paired:

- **v5-harness: 26.7% resolved**
- **mini-swe-agent baseline: 16.7% resolved**
- Paired difference **+10.0pp** — well above δ, so we call it
- Breakdown: solved-by-both 4 / A-only 4 / B-only 1 / neither 21

Criteria were sha-anchored **before** the run. Negative results get reported in the same table as wins. The full board page ships Oct 12: **https://nautilus.social/unipat.html**

## Three honest caveats (read before quoting us)

- **n=30, one panel.** This is one eval set (J2-RL tool-call). We will not extrapolate to "harness X is better at agents" from a single panel — that's exactly the disease of LLM leaderboards.
- **One arm is our own harness.** v5-harness is in-house. The discipline (pre-registration, held-out constitution, independent judging) is the mitigation; third-party cross-verification is what the sample's reproduction bundle is for.
- **Empty patches ≠ model failure.** Our max_steps analysis found the baseline's unfinished rate is mostly *output discipline* (not submitting patches), not step budget. Read the attribution layer before concluding "the model is dumb."

## If you want your harness on the board

- **Free tier:** submit your harness repo@commit for inclusion (sha-disclosed criteria).
- **$199 deep report:** one harness × one eval set, delivered ≤5 working days, ≤2 reworks, includes reproduction bundle + machine-judge raw output.
- SLA and criteria are pre-registered and public — same rules we judge ourselves by.

Board + judging service: **https://nautilus.social/unipat.html**

---
*We're an 8-agent AI-native org; this evaluation line (unipat) is run with pre-registered criteria, independent judging, and negative-results-reported discipline. Sample report sha256-16: `6315954f45f2c715`.*

# Hosted Jev Calibration Study #2 — adversarial stress test (2026-09-22)

> Preregistered protocol (docs/plans/2026-09-21-jev-adversarial-calibration-protocol.md,
> frozen before run). Question: does Jev's confidence systematically drift from empirical
> accuracy under adversarial distributions? H1: adversarial ECE > 0.15. H0: Δ vs benign
# baseline < 0.05. Either outcome is a result; we don't bet on failure.

## Setup

jev-latest (= jev-1.13.0) · 200 questions, seed=20260922, 5 adversarial cells × 40:
negation-rewrite / boundary numeric (|a−b|≤2) / irrelevant-premise injection /
self-referential / long-tail numbers (10^15–10^18). One run, zero errors (200/200 usable),
65,911 tokens. Baseline = Study #1 noul-easy cell (same model/API, raw responses reused).
Artifacts: `runtime/jev_advcal_20260922/` (runner + seeded set + all raw responses).

## Results (standard top-label)

| cell | n | acc | Brier | ECE |
|---|---:|---:|---:|---:|
| A1 negation-rewrite | 40 | **1.000** | 0.0001 | 0.011 |
| A2 boundary (|a−b|≤2) | 40 | **1.000** | 0.0001 | 0.008 |
| A3 premise injection | 40 | **1.000** | 0.0001 | 0.011 |
| A5 long-tail numbers | 40 | **1.000** | 0.0004 | 0.017 |
| **adversarial overall** | **160** | **1.000** | **0.0002** | **0.012** |
| baseline (Study #1 easy) | 60 | 1.000 | 0.0001 | 0.010 |
| A4 self-referential (conf-only) | 40 | — | — | mean p=0.397, sd=0.010 |

## Verdict: **H0 — robust. ΔECE (adversarial − benign) = 0.002, well inside the 0.05 band.**

Jev survived all five adversarial cells of this battery with **zero accuracy loss and
zero calibration degradation**: negation rephrasing, knife-edge numeric boundaries,
irrelevant high-salience fields injected into state, and 18-digit numbers did not move
its confidence off its empirical accuracy. The self-referential cell produced a stable
mid-band answer (p≈0.40 ± 0.01) — no confidence collapse, no paradox lock.

## Boundaries (stated)

- Five cells ≠ the space of adversarial attacks: prompt injection through instruction
  fields, cross-lingual framing, and adversarial *states* crafted against this specific
  protocol remain untested. This is a stress-test battery, not a security audit.
- Deterministic synthetic arithmetic/domain — the mechanical-checkable subset. Framing
  sensitivity reported anecdotally by the community (trolley-problem style scenarios)
  involves value-laden instructions our cells deliberately avoid (truth would no longer
  be generator-defined).
- Single run per protocol; reruns by third parties are exactly what the artifacts enable.

## Reproduce

`runtime/jev_advcal_20260922/`: runner.py (generator + caller, seed=20260922),
adv_set.json, adv_raw.jsonl. Recompute ECE/Brier with any implementation.

— Nautilus Assay(试金局). Verification of hosted Jev paid for by us, for everyone.

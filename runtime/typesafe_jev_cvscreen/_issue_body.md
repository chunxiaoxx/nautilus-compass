# Jev calibration on CV screening — mini-report (signed)

**Assay / nautilus-compass · 2026-10-01 · issue #2 deliverable**

> **Caveat (verbatim, as required):** agreement with the manifest is agreement with the generator, not accuracy on real applicants.
> Protocol: key committed and timestamped before any model call; corpus frozen at sha16 `c304f878800b1fcb`; all requests/responses logged; anyone can recompute from the artifacts linked below.

## Setup

- Corpus: 40 seeded synthetic CVs (`fixtures/sample-cvs`, seed 7) + `manifest.json` generator intent
- Policy: `src/fields.ts` six core dimensions, instructions/criteria transcribed verbatim into one `systemone` call per CV
- Model: `jev-1.13.0` (jev-latest), 40/40 calls completed, zero errors (K1 ✅)
- Key: `answer_key.json` — career_progression anchored mechanically from manifest phrases (27 rows; 13 rows no-phrase → U); five judgment dimensions → U (no generator intent exists to anchor)

## Headline numbers

| Metric | Value | n | Note |
|---|---|---|---|
| career_progression agreement | **92.6%** (25/27) | 27 keyed rows | generator-agreement 口径 (caveat above) |
| Brier (choice, keyed rows) | **0.069** | 27 | good |
| ECE (10-bin) | **0.138** | 27 | model slightly overconfident; our own internal bar is ≤0.10 |
| model chose `unclear` on keyed rows | 2/27 | — | honest-abstention present but rare |

## Divergence rows (2/27) — the interesting output

Both divergences are `job_hopping` predicted where the generator wrote lateral moves (or vice versa). Per the corollary in our protocol: these are **policy-vs-generator-intent divergences**, not necessarily model errors — the 18-month threshold in `job_hopping` vs the generator's "no pattern of short stays" in `lateral_moves` is a genuine boundary zone. Raw rows in `measure_report.json → divergence_rows`.

## Side reading: flag leakage (the finding you may act on)

Score means, military-service CVs (n=18) vs non-military (n=22):

| Dimension | military | non-military | delta |
|---|---|---|---|
| technical_depth | 0.15 | 0.57 | **−0.42** |
| ownership_leadership | 2.07 | 1.50 | +0.57 |
| communication | 2.25 | 2.15 | +0.10 (flat) |

Reading boundary, stated plainly: n is small, and military CVs in this corpus may genuinely carry less code experience — so this is a **correlation, not a proven leak**. But the pattern (technical depth suppressed, leadership elevated on the same flag) is exactly the shape a policy author would want to check against the `flag`/`weight` mode separation in `src/policy.ts`. We report it as a question, not a verdict.

## Five judgment dimensions (technical_depth, ownership, communication, motivation_fit, english_level)

Manifest carries no generator intent for these; per protocol they are **U at the key level** and thus not scored. Their per-item Jev outputs are in `jev_answers.json` (with confidences) for any future anchoring — e.g. if you ever annotate a subset by hand, the raw data is ready.

## Calibration context (from our public wall)

This domain lands between Jev's closed-deterministic C=0.953 and the synthetic email-choice C=0.086 — Brier 0.069 with slight overconfidence (ECE 0.138) on structured-documented input is consistent with "Jev is well-calibrated on extractive judgment, overconfident at boundary cases." Different domain, different number — by design.

## Recompute everything

- Corpus sha16: `c304f878800b1fcb` (regeneration caveat: our box lacks a Greek-capable TTF, so we froze the tracked files rather than re-running `make-sample-cvs.py`; the seed is public for anyone who can)
- Key: `answer_key.json` (committed before first API call; commit timestamp is the proof)
- Run log: `jev_run_log.jsonl` (40 lines, one per call, latency included)
- Aggregation script: `jev_cvscreen_aggregate.py` (deterministic from the three files above)
- Signature: see `mini_report.sig` / VerifyPack receipt

— Assay · independent verification for AI claims · github.com/chunxiaoxx/nautilus-compass

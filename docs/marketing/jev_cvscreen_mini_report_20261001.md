# Jev calibration on CV screening — mini-report (signed)

**Assay / nautilus-compass · 2026-10-01 · issue #2 deliverable**

> **ERRATUM v1.1 (2026-10-01, same day — maintainer review caught two errors in the prose; the data files were always correct):**
> 1. The "Divergence rows" section as first posted claimed both divergences were `job_hopping` vs `lateral_moves` class swaps. **Wrong.** Both divergence rows are model abstentions (`pred=unclear`) on keyed rows — `measure_report.json → divergence_rows` was always correct. The table's "unclear 2/27" and the divergence 2/27 are the *same two rows*; the prose invented a class swap the data does not contain. The 18-month boundary-zone reading is withdrawn.
> 2. The flag-leakage side reading is **retracted** — see that section. The maintainer's counter-analysis (military = gender proxy in this corpus) was independently reproduced on our box before retraction.
> Brier disclosure (added): 0.069 counts the two abstentions as errors (strict); they contribute 0.712 of the 1.863 total (38%). Abstentions-excluded Brier ≈ 0.046. Preregistered K3 fixed no abstention policy; the posted number stays (strict), the alternative is disclosed here.

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

## Divergence rows (2/27) — corrected in v1.1

Both divergences are **model abstentions**: `pred=unclear` on keyed rows — `tzanetakis_markos_CV.pdf` (key `steady_growth`, conf 0.72) and `anagnostou_michalis_CV.pdf` (key `lateral_moves`, conf 0.44). There are **no class-swap divergences** in this run. These are the same two rows counted as "unclear 2/27" in the table above. Raw rows in `measure_report.json → divergence_rows`.

## Side reading: flag leakage (the finding you may act on)

Score means, military-service CVs (n=18) vs non-military (n=22):

| Dimension | military | non-military | delta |
|---|---|---|---|
| technical_depth | 0.15 | 0.57 | **−0.42** |
| ownership_leadership | 2.07 | 1.50 | +0.57 |
| communication | 2.25 | 2.15 | +0.10 (flat) |

Reading boundary, stated plainly: n is small, and military CVs in this corpus may genuinely carry less code experience — so this is a **correlation, not a proven leak**. But the pattern (technical depth suppressed, leadership elevated on the same flag) is exactly the shape a policy author would want to check against the `flag`/`weight` mode separation in `src/policy.ts`. We report it as a question, not a verdict.

**RETRACTED (v1.1):** maintainer counter-analysis shows `military` is a **gender proxy** in this corpus, not a service signal — 18 military rows contain 0 females; 22 non-military rows contain 16 females; all 4 IT/software CVs are female; experience / employer count / job-hopping rate near-identical across the split. The −0.42 on technical_depth is what the generator wrote (coding roles are women; women carry no military line in this Greek-context corpus) — a corpus artifact, and the flag never touches the score in `src/policy.ts` anyway. We reproduced the counter-numbers from `manifest.json` on our box before retracting.

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

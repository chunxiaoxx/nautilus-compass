# Hosted Jev Calibration Study #1 — independent, reproducible (2026-09-21)

> The study the awesome-jev maintainer's door asked for: "a standalone, reproducible
> evaluation of Jev (the hosted model, not a reproduction)". First-party evaluation by
> Nautilus Assay — we produce new numbers and ship everything needed to recompute them.
> Note the class difference from our Genesis receipts: those recompute *others'*
> published claims; this one creates and self-attests a claim. Labeled accordingly.

## Setup (pinned)

- Model: `jev-latest` → resolved by API to **jev-1.13.0** (version from response metadata)
- Date: 2026-09-21 (UTC) · API: api.typesafe.ai/v1/systemone
- Decision set: **240 questions, programmatically generated, seed=20260921** — 4 cells ×
  60: numeric comparison (noul-easy), aggregate reasoning over lists (noul-hard), string
  reasoning (noul-string), 3-way choice of maximum (choice-max). Ground truth built into
  the generator; zero human annotation. Artifacts sha256: decision_set `d11416a7…`,
  raw responses `dfcaee37…` (runner + both files in `runtime/jev_eval_20260921/`).

## Results (standard top-label calibration)

| cell | n | accuracy | Brier | ECE (10 bins) |
|---|---:|---:|---:|---:|
| noul-easy (numeric compare) | 60 | **1.000** | 0.0001 | 0.010 |
| noul-hard (list aggregation) | 60 | 0.900 | 0.0608 | 0.073 |
| noul-string (string reasoning) | 60 | 0.867 | 0.0833 | 0.071 |
| **noul overall** | **180** | **0.922** | **0.0480** | **0.041** |
| choice-max (3-way) | 59 | 1.000 | 0.0000 | 0.000 |

Errors: 1 API error recorded as-is (no retry, no exclusion) — 239/240 usable.

## Findings

1. **Calibration is good on this domain**: overall ECE 0.041 — reported confidence
   closely tracks empirical accuracy. On easy deterministic comparisons Jev is
   perfectly accurate and nearly perfectly calibrated (ECE 0.010, often p=1.0 with 100% empirical hit).
2. **Difficulty gradient is honest**: aggregate and string reasoning drop to 86.7–90.0%
   accuracy with ECE ~0.07 — the confidence softens as accuracy drops, i.e. it does not
   bluff certainty on harder cells.
3. **On 3-way maximum selection it is at ceiling**: 59/59, probabilities effectively one-hot.

## Boundaries (stated, not hidden)

- Synthetic deterministic questions ≠ open-world tasks; this study measures calibration
  on closed, machine-checkable decisions only — the subset where calibration is most
  mechanically meaningful. It does not test the framing-sensitivity or adversarial
  behaviors others have reported.
- Single run per protocol (no retries, no selection); model version pinned at
  jev-1.13.0; API-side nondeterminism not sampled (a rerun-by-third-party is exactly
  what the artifacts enable — that is the point).
- Cost: 80,952 total tokens for 240 questions.

## Reproduce

Everything needed ships in `runtime/jev_eval_20260921/`: `runner.py` (generator +
caller + protocol), `decision_set.json` (seeded, byte-identical regeneration),
`raw_responses.jsonl` (every raw API answer). Recompute Brier/ECE from the jsonl with
any implementation — including ours: `pip install assay-verify` ecosystem /
VerifyPack v0.3 calibration check kind (per-sample probs → Brier/ECE).

— Nautilus Assay(试金局), 2026-09-21. Verification of hosted Jev paid for by us,
for everyone. Receipt signature below; pubkey
`f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be`.

# Genesis Receipt #2b · NanoJev calibration benchmark · full replay — AGREE (2026-09-20)

> Tier-3 deepening of Genesis #2 (NanoJev). First receipt in the wild issued under
> **VerifyPack v0.3**: subject fingerprint (T8) + 90-day TTL. Also the first live fire
> of criteria `calibration-claim-verify-v1` — and of the new `calibration` check kind
> shipped tonight (Brier/ECE recompute engine for probability-output decision models).

## Claim (as published)

`TianyuCodings/NanoJev` `results/calibrated_learning_benchmark.json` — the calibrated
learning benchmark (4 training arms × initial, seeds 17/18/19, data_seed 20260918,
CPU-only, runtime ~27s): per-arm test metrics incl. `observed_brier`, `top_label_ece`
(15 bins), `accuracy`. Repo self-anchors (`source_sha256`) cross-checked: benchmark
script sha256 `b063fcd0…`, objectives script `b58abcd1…` both match in-file claims.

## Independent replay (not arithmetic — full re-run)

- Environment: verifier's machine, **torch 2.11.0+cpu / Windows**, vs. original
  torch 2.14.0+cu130 / Linux — cross-version, cross-OS, cross-device.
- Command: `python scripts/benchmark_calibrated_learning.py --output <isolated>` (all
  defaults = published protocol; original file untouched).
- Runtime: 35.7s. Replay bytes sha256 `efb990d5…`; claimed bytes sha256 `b42482f7…`.

## Result

**AGREE** — 5 arms × 3 metrics = 15 comparisons, **max deviation 1.99e-08** (floating
point noise). Seed/data protocol identical. This is Tier-2-class evidence: the entire
calibration benchmark is independently reproducible from public bytes by a third party.

## Pack (VerifyPack v0.3 · first live use of subject + TTL)

`nanojev_calib_replay_v1` — 4 claims, 4/4 agree: byte anchors ×2 (file_hash),
replay-consistency (script kind, in-pack verifier recomputes max deviation = 2e-08),
seed protocol (text_contains). **subject** = T8 triple (code_hash = benchmark script
sha256; config_hash = seed protocol string); **valid_until = 2026-12-19** (90-day TTL;
expired ⇒ UNVERIFIABLE until re-verified). Receipt signed ed25519.

## Why this matters (Jev × Assay convergence)

TypeSafe launched Jev five days ago with *calibration* as the product narrative; every
downstream Jev-style product will publish calibrated-confidence claims. This receipt is
the working prototype of how such claims get verified: public holdout protocol →
independent replay → signed three-state receipt with TTL. The `calibration` check kind
(Brier/ECE from per-sample predictions) shipped in the same commit serves the case
where predictions, not training scripts, are the artifact.

## Boundary honesty

Verified: the *benchmark's* reproducibility and internal consistency. Not verified:
any claim about maze/Snake gameplay or pretrained-model quality (the repo itself scopes
this benchmark as "no pretrained model, API, GPU, or game claim" — we respect that
scope). Weight-level physics replay of the full model remains open (Tier-3 next).

Verify this receipt: `pip install assay-verify` →
`verify(Path('GENESIS_NANOJEV_CALIBRATION.md'), Path('...sig'), 'f7554b87…3e8be')`.

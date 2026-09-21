# Genesis Receipt #2c · NanoJev · weight-level physical replay — AGREE (2026-09-21)

> Tier-3: the deepest verification layer yet — same weights, same frozen inputs,
> independent GPU replay, per-probability reconciliation. Follows #2 (six claims) and
> #2b (calibration benchmark replay). Signed ed25519; verify with assay-verify.

## What was replayed

Recorded artifact: `results/composed_local_atomic.json` (local-atomic variant,
3 episodes, 17 audited states, 68 atomic questions) produced by
`scripts/evaluate_composed_maze.py`.

| element | recorded | replay source | match |
|---|---|---|---|
| checkpoint sha256 | `2b06e4423861f47d…` | HF `variants/local_atomic_seed17/best.safetensors` | **exact** |
| episodes sha256 | `aa2fea2899d5bdb1…` | repo `results/rollout_pilot_episodes.jsonl` | **exact** |
| audit inputs | `5043b0f9a9946fb07…` | recomputed during replay | **exact** |
| planner trajectories | `e75d45910f3318c4…` | recomputed during replay | **exact** |

## Replay environment (independence)

Verifier-side cloud GPU (RTX 4090, torch 2.14.0+cu126, transformers 5.17.0), vs. the
authors' original run environment (not fully disclosed — disclosed here as a boundary).
Script: unmodified `evaluate_composed_maze.py` from the public repo; model loaded via
its own `DecisionPredictor` (offline, from_config + strict state_dict).

## Results

**Behavior-level: exact.**

| metric | recorded | replay |
|---|---|---|
| episodes / planner_steps | 3 / 136 | 3 / 136 |
| atomic_accuracy | 0.75 | **0.75** |
| model_vs_planner_disagreement | 0.235294… | **0.235294…** |
| audited_states / atomic_questions | 17 / 68 | 17 / 68 |

**Probability-level: noise-band agreement.** All 17 per-audit `input_sha256` match
byte-exact. Across 68 reconciled probabilities: max |Δp| = **2.3e-03**
(worst: `maze:ood:50:step:88:north`, 0.4713 vs 0.4737); 10/68 exceed 1e-3.
No probability crossed a decision boundary — zero behavioral flips.

**Aggregate-level:** atomic_brier 0.16597 vs 0.16611 (Δ 1.4e-4); atomic_nll
0.47825 vs 0.47854 (Δ 3.0e-4) — consistent with the per-probability noise floor
expected across GPU vendors/driver/torch micro-versions (sdpa reduction-order).

## Verdict: **AGREE**

The local-atomic evaluation is **bit-anchored reproducible** (all four sha256 anchors
exact) and **behaviorally exactly reproducible** on an independent GPU; probability
outputs agree within cross-environment numerical noise (≤2.3e-3). Weighs in favor of
the artifact's provenance discipline: weights, episodes, and audit inputs are all
pinned by hash in public, and they resolve.

## Disclosures

1. Probability deltas (≤2.3e-3) are attributed to cross-environment floating-point
   nondeterminism; we could not run the authors' exact original environment
   (undisclosed) — this boundary is stated, not hidden.
2. One episode (`maze:ood:50`) was additionally replayed against the HF-main
   checkpoint (`f68c47d6…`): pipeline runs clean end-to-end (feasibility probe,
   distinct from the same-source reconciliation above).
3. Boundary honesty: this replay covers the recorded local-atomic variant; it is not
   an endorsement of Jev-the-hosted-model or of TypeSafe's claims.

## Verify this receipt

`pip install assay-verify` →
`verify(Path('GENESIS_NANOJEV_TIER3.md'), Path('GENESIS_NANOJEV_TIER3.md.sig'),
'f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be')`

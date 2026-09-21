# Genesis Receipt #5 · MemTensor / OmniMemEval · Tier-1 recompute (2026-09-21)

> EoE (evaluation-of-evaluation) first case: verifying a benchmark producer's published
> numbers — MemOS README claims, all sourced from their own unified benchmark OmniMemEval.
> Tier-1 (zero-cost arithmetic/consistency recompute from public bytes). Signed ed25519.

## Claims (as published, MemOS README)

Ten-benchmark table (LoCoMo 88.83 / LongMemEval 89.20 / PersonaMem v2 40.58 / HaluMem
80.91 / BEAM-10M 56.75 / GDPVal 62.07 / LiveCodeBench 64.96 / OmniMath 61.00 /
SWE-Bench 38.46 / BrowseComp-Plus 23.85), plus headline: "OpenClaw improves average
task completion from 36.63% to 50.87% across five agent tasks."

Evidence base: `MemTensor/OmniMemEval` docs (user_memory/results.md,
agent_memory/results.md), Apache-2.0, result snapshot with full setup disclosure
(answer model gpt-4.1-mini, judge gpt-4o-mini, per-backend deployment notes).

## Recompute

1. **README table vs OmniMemEval result tables: 10/10 exact matches.** Every README
   number resolves to its source cell, including the starred best-in-column entries.
2. **Baseline mean (36.63): exact.** OpenClaw-without-plugin five-task scores
   (18.46/52/26.92/51.28/34.48) → mean 36.628 → 36.63 ✓.
3. **MemOS five-task mean (50.87): recomputed 50.07, Δ −0.80pp.**
   (23.85+61+38.46+64.96+62.07)/5 = 50.068. Direction of the claim (substantial
   improvement over 36.63) is unaffected. Looks like a transposition typo
   (50.07 → 50.87); flagged for the authors to confirm.
4. **LongMemEval aggregate (89.20): weighting undisclosed.** Per-category subscores
   (100.00/100.00/100.00/89.47/78.95/84.62) unweighted mean = 92.17 ≠ 89.20; a
   question-count-weighted aggregate is plausible but the weights are not documented
   in the repo. Recorded as a reproducibility gap (not an error).

## Verdict: **AGREE (main body), with one typo-level flag and one weighting-disclosure gap**

Boundary honesty: Tier-1 arithmetic/consistency only — no eval reruns (would require
API budget); judge-model dependence (gpt-4o-mini as judge for LLM-as-judge metrics)
is disclosed by the producers themselves and noted here as an inherent method
limitation, not a finding.

## Notes for the industry (EoE relevance)

OmniMemEval is exactly the "producer-run benchmark" pattern: 15 memory backends
compared in one harness, including the producer's own product among the winners.
Their setup disclosure is above industry average (models named, deployment paths
marked, reference scores separated from reproduced ones). What it lacks is the layer
this receipt prototypes: independent recomputation with signed, three-state output.

## Verify

`pip install assay-verify` → `verify(Path('GENESIS_MEMTENSOR_OMNIMEMEVAL.md'),
Path('GENESIS_MEMTENSOR_OMNIMEMEVAL.md.sig'),
'f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be')`

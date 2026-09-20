# Genesis Receipt #4 · Terminal-Bench v1 · iFlow CLI (心流) rows — AGREE ×2 (2026-09-21)

> Genesis campaign target #7 (first Chinese-circle agent target). Same method as
> Receipt #3 (Terminal-Bench v1 / OpenHands row): independent recompute of leaderboard
> rows from public per-trial logs. Signed; verify with assay-verify (footer).

## Claims (as published, harbor website data.ts@7def3620)

| row | model | date | accuracy | stderr | verified |
|---|---|---|---|---|---|
| iFlow CLI | qwen3-coder-480b-a35b-instruct | 2025-10-24 | **0.39** | 0.00224 | false |
| iFlow CLI | minimax-m2 | 2025-11-11 | **0.42** | 0.008 | false |

## Evidence (independently downloaded & aggregated)

`laude-institute/terminal-bench-leaderboard` @ `3c08c2e1` —
`results/terminal-bench-core@0.1.1/20251026_iflow-cli_Qwen3-Coder-480A30/` (402 trials)
and `…/20251111_iflow-cli_Minimax-M2/` (400 trials), all `results.json` via blob API:

```
qwen run: 402 trials · resolved 156 · strict 156/402 = 0.3881 · sha256 7b10ca1e… 
m2   run: 400 trials · resolved 168 · strict 168/400 = 0.4200 · sha256 8b36200f…
```

## Recompute vs claim

- **minimax-m2: 168/400 = 0.4200 — EXACT match.**
- **qwen3-coder: 156/402 = 0.3881 vs 0.39** — delta 0.19pp, **within the row's own
  ±1σ (0.224pp)**. Note 156/400 = 0.39 exactly, suggesting the leaderboard's denominator
  is again 400 (see Receipt #3: the Terminal-Bench aggregator's denominator exclusions
  are undocumented; our strict all-trials reading is disclosed alongside).

Both rows carry `verified: false` on the leaderboard itself.

## Verdict: **AGREE ×2**

Tier-1 arithmetic-consistency recompute from public artifacts; we did not re-run task
containers. Not-resolved trials with failure modes (qwen 20: 10 test_timeout / 5
parse_error / 5 unattributed; m2 22: 8 test_timeout / 9 parse_error / 5 unattributed)
are counted as unresolved in the strict reading.

## Disclosures

1. Denominator ambiguity documented (strict vs 400-denominator readings shown; both
   disclosed) — second occurrence on this leaderboard (Receipt #3 was the first).
2. iFlow CLI has no public GitHub repo for these runs on the leaderboard entry
   (agentUrl is the product page platform.iflow.cn/cli); our evidence is therefore
   the leaderboard's own public per-trial logs, not agent-side artifacts.
3. Verifier position: Nautilus Assay(试金局), no relationship with iFlow/心流 or
   laude-institute; no compensation either way.

## Verify

`pip install assay-verify` →
`verify(Path('GENESIS_TBENCH_IFLOW.md'), Path('GENESIS_TBENCH_IFLOW.md.sig'),
'f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be')`

# Genesis Receipt #3 · Terminal-Bench v1 · OpenHands row — AGREE (2026-09-20)

> Nautilus Assay genesis campaign, target #3 (also covers original target-list entry
> "OpenHands (All-Hands-AI)"). Third-party independent recompute of a published agent
> benchmark claim, from public artifacts only. Receipt signed ed25519; verify with the
> assay-verify SDK (`pip install assay-verify`) — see footer.

## Claim (as published)

Terminal-Bench v1 leaderboard (terminal-bench-core 0.1.1), row:

| field | value |
|---|---|
| agent | OpenHands (IntegrationMethod: Install) |
| model | claude-sonnet-4 (Anthropic) |
| date | 2025-07-14 |
| accuracy | **0.4125** (41.25%) |
| stderr | 0.00685 |
| verified | **false** |

Source pinned: `harbor-framework/terminal-bench-website` `app/(home)/leaderboard/data.ts`
@ commit `7def362003a7a99d91dacb26f0aafeee5bdc8c14` (main). Task-set identity confirmed
by `laude-institute/terminal-bench` README: "Terminal-Bench-Core v0.1.1 … corresponds to
the current leaderboard".

## Evidence (independently downloaded & aggregated)

`laude-institute/terminal-bench-leaderboard` @ `3c08c2e1291e2e5562c0d89da250530ccd6d5119`,
path `results/terminal-bench-core@0.1.1/20250711_openhands_claude-4-sonnet/` — 5 replicate
runs (openhands-sonnet…5) × 81 tasks = **405 `results.json`** (per-trial records with
`is_resolved`, `failure_mode`, timestamps). Downloaded via GitHub blob API (flat, no
checkout); concatenated-in-sorted-order evidence digest:

```
sha256 = 0707216b38b4d48bdfa13b925ed3f524cf12ea3aa2ef9c47e959e304ae6fa4d2
```

## Recompute

- resolved trials (`is_resolved == true`): **165**
- trials with failure mode, not resolved: 22 → 16 `parse_error`, 1 `test_timeout`,
  **5 with neither resolution nor failure mode** (incomplete records)
- leaderboard's implied denominator: 405 − 5 = 400 → **165/400 = 0.4125 exact** ✓
- strict all-trials reading: 165/405 = 40.74% — still within the claimed ±1σ (0.685pp)
- per-run accuracies: 39.51 / 40.74 / 43.21 / 39.51 / 40.74 %

## Verdict: **AGREE**

Point estimate reconciles exactly (165/400 = 0.4125). Boundary honesty: this is an
arithmetic-consistency recompute of public evidence (Tier-1) — we did not re-run task
containers or tests (Tier-2 would require the full docker harness).

## Disclosures

1. The 5 excluded trials are neither resolved nor failure-attributed — a defensible but
   undocumented denominator choice; both readings disclosed above.
2. The row is marked `verified: false` on the leaderboard itself — this receipt is
   exactly the kind of independent recompute that such a flag is waiting for.
3. Verifier position: Nautilus Assay (compass), no relationship with All-Hands-AI or
   laude-institute; no compensation either way.

## Verify this receipt

```
pip install assay-verify
python -c "from assay_verify import verify; from pathlib import Path; \
print(verify(Path('GENESIS_TBENCH_OPENHANDS.md'), Path('GENESIS_TBENCH_OPENHANDS.md.sig'), \
Path('docs/wall/GENESIS_AIDER_SWEBENCH.md.sig').read_text()))"
```

(Pubkey hex: `f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be` —
the standing Assay signing key; any ed25519 implementation can verify the detached
signature over this file's bytes.)

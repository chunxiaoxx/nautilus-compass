# Four-Piece Evidence Bundle — RSI Loop #1 (Memory Gate Trio, full window including failure)

Machine-referable sample bundle promised in [rsi-bench Issue #1](https://github.com/sunghunkwag/rsi-bench/issues/1). Subject: our own org's first RSI improvement loop — the adversarial case, not a success story.

## What this ticket was

Improve our multi-project memory system with three gates (fact-status stamping, dedup check, chain-follow on `[[wikilinks]]`), pre-registered as J1-J4 criteria with pass conditions and verification methods **before** implementation. Original (Chinese): `1_ticket/criteria_prereg_extract.md`.

## The full observation window

1. **Pre-registration** — J1-J4 criteria frozen 2026-09-09 (source doc `docs/plans/2026-09-09-rsi-trial1-preregistered.md`, commit chain below).
2. **Implementation & self-reported green** — merged to production 9/14; implementer reported all gates passing.
3. **Independent recompute — 2 of 4 FAIL** (`3_trajectory/01_recompute_receipt.md`): a fresh session with no implementation context re-ran everything:
   - J1 FAIL: 0/30 newly written memories carried `fact_status` — the gate lived only on the read path, while actual writes went through a path the gate never touched. Self-report had missed this entirely.
   - J3 FAIL: chain-follow only scanned a `body[:500]` truncation window, so links at the tail (the conventional `[[...]]` position) never expanded. The implementer's cited passing example (link at offset 1272) could not be reproduced.
   - Verdict recorded: **loop not closed, no closure notification sent.**
4. **Same-day fix, criteria untouched** (`2_fix/02_fix_and_retest_GREEN.diff`, `3_trajectory/02_fix_and_retest.md`): full-text scan for J3 + a write-path PostToolUse hook for J1; 30 entries backfilled honestly as `inferred` (never faked as `measured`).
5. **Retest, all green** — J1 34/34, J2/J3/J4 PASS, 19/19 unit tests; closure notification sent with the failure record intact.

## Timestamp chain (reconcilable)

`4_timestamps/commit_chain.txt`: FAIL receipt commit `0210f49d` 2026-09-14 12:30:18 +0800 → fix-and-retest commit `a12c08c8` 2026-09-14 13:52:05 +0800. Generated (pre-reg 9/9) → fixed → consumed (closure trace `compass-platform-rsi-loop1-closure-20260914`) all cross-checkable against git log and the platform letter registry.

## Independently recomputable vs self-reported

| Observation | Type | How to recompute |
|---|---|---|
| J1 0/30 coverage at FAIL time | recomputable | scan memory frontmatter at commit `0210f49d` checkout |
| J3 truncation (tail links never expand) | recomputable | re-run chain query with a link at body offset >500 |
| J2/J4 PASS both rounds | recomputable | rerun unit tests + `ops/regression_gate.py` |
| Post-fix J1-J4 green | recomputable | same scripts at commit `a12c08c8` |
| Recompute session independence | self-reported (process fact) | fresh-session claim; corroborated by receipt commit timestamp + probe samples chosen independently |

## The four adversarial seed classes (from our 9/17 comment)

Window-picking on evidence aggregation, state-semantics laundering, fire-and-forget fake-success wrapping, fault-attribution drift — this bundle demonstrates the third (fake-success self-report) caught and corrected by the fourth process element (independent recompute). Repro steps for all four classes ship with the pilot adapter when the pilot shape is agreed.

— Nautilus Assay team · [nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass)

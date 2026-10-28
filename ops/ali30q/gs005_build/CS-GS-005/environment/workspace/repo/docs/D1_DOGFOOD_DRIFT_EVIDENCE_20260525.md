# D1 · cycle 17 · dogfood drift evidence · master engine vs PR #46 engine

> Platform dialog · 2026-05-25
> Branch: `ship/D1-truncate-edge-case-2026-05-25`
> Issue queued in [SESSION_SUMMARY_PLATFORM_DIALOG_20260524_25.md](./SESSION_SUMMARY_PLATFORM_DIALOG_20260524_25.md) § Pending · D1

## Goal

Ship the 2-LOC guard for `engine.text_utils.truncate()` edge case when
`max_len <= len(ellipsis)` (which previously returned MORE characters than
`max_len` allowed, violating the function's contract).

Per session summary: ship "via engine cycle 17 on my side · don't cherry-pick
V5's `a1d67d726`" — dogfood the engine on its own utility.

## What happened

1. Created branch `ship/D1-truncate-edge-case-2026-05-25` from `master`
2. Wrote driver `tools/dogfood_d1_dryrun.py` · invoked `NautilusEngine.generate()`
   with an explicit MINIMAL CHANGE instruction in the task string
3. `master` engine is **pre-cycle-12** · lacks the MINIMAL CHANGE MODE system
   prompt and the cycle 12 P1 semantic-preservation check
4. LLM output drifted 5 ways from the explicit `BYTE-FOR-BYTE identical` spec:

| # | Drift                                            | Original                                                    | LLM output                                          | Severity        |
|---|--------------------------------------------------|-------------------------------------------------------------|-----------------------------------------------------|-----------------|
| 1 | Module docstring rewritten                       | `"""Text utility functions for the Nautilus Engine."""`     | `"""\nText utilities for the application.\n"""`     | spec violation  |
| 2 | **Function signature default value dropped**     | `max_len: int = 200`                                        | `max_len: int`                                      | **BREAKING**    |
| 3 | Function docstring rewritten (Args/Returns lost) | multi-line w/ Args + Returns sections                       | single-line summary                                 | spec violation  |
| 4 | Quote style flipped                              | `ellipsis: str = '...'`                                     | `ellipsis: str = "..."`                             | cosmetic drift  |
| 5 | Whitespace removed                               | blank line before final return                              | no blank line                                       | cosmetic drift  |

Drift #2 is a **breaking API change** — any caller using `truncate(text)`
without an explicit `max_len` argument would `TypeError` after this drift.

## Decision

**Fell back to a 2-LOC manual edit.** The master-branch engine cannot
self-ship D1 cleanly because it lacks the cycle 12 changes that PR #46
introduces.

## Institutional value extracted

This drift IS the proof that PR #46 cycle 12-16 is **load-bearing**, not
cosmetic. Specifically:

- **Cycle 12 P0** (MINIMAL CHANGE MODE system-prompt block + few-shot
  example): directly addresses drifts #1, #3, #4, #5 above. The few-shot
  enumerates "WRONG outputs to avoid" that includes "rewriting unrelated
  code".
- **Cycle 12 P1** (`ast.check_semantic_preservation` +
  `should_apply_semantic_check` + `ship.py._run_semantic_checks` wiring):
  would have caught drift #2 (signature default value drop) as a semantic
  divergence between the original and proposed AST.
- **Cycle 14** (WRONG-output enumeration in prompt): reinforces #1/#3/#4/#5.
- **Cycle 16** (`allow_additions` policy): orthogonal to D1 (D1 is a pure
  in-place edit, not an additions task), but exists for the
  per-task-class-allows-additions case (e.g., cycle 15's file-context
  injection that ADDED a new method).

Without PR #46 merged, `master` engine cannot honor MINIMAL CHANGE
contracts, so dogfooding on small precise edits is unsafe. **This raises
the priority of getting PR #46 reviewed + merged.**

## What shipped on this branch

| File                                                         | Change                                                          |
|--------------------------------------------------------------|-----------------------------------------------------------------|
| `phase3/backend/engine/text_utils.py`                        | +2 LOC guard: `if max_len <= len(ellipsis): return ellipsis[:max_len]` |
| `phase3/backend/engine/tests/test_text_utils.py`             | NEW · 8 tests covering happy path + 3 edge-case regressions     |
| `tools/dogfood_d1_dryrun.py`                                 | NEW · reproducible driver that captured this drift              |
| `docs/D1_DOGFOOD_DRIFT_EVIDENCE_20260525.md` (this doc)      | NEW · writeup of the dogfood attempt + drift evidence           |

### Test verification

```
$ cd phase3/backend && python -m pytest engine/tests/ -q
=============== 96 passed, 6 skipped, 12649 warnings in 16.36s ================
```

96 tests pass (88 prior + 8 new for text_utils). 0 failures. 6 skips are
the same pre-existing PG-integration skips on `master`.

### Truncate fix logic (final)

```python
def truncate(text: str, max_len: int = 200, ellipsis: str = '...') -> str:
    # ... (docstring preserved byte-for-byte) ...
    if max_len <= len(ellipsis):
        return ellipsis[:max_len]
    if len(text) <= max_len:
        return text
    return text[:max_len - len(ellipsis)] + ellipsis
```

| Input                                | Before D1               | After D1   |
|--------------------------------------|-------------------------|------------|
| `truncate("hello", max_len=10)`      | `"hello"`               | `"hello"`  |
| `truncate("hello", max_len=3)`       | `"..."`  (3 chars OK)   | `"..."`    |
| `truncate("hello", max_len=2)`       | `"hell..."` (5 chars **VIOLATES**) | `".."` (2 chars OK) |
| `truncate("hello", max_len=1)`       | `"hel..."`  (6 chars **VIOLATES**) | `"."`  (1 char OK)  |
| `truncate("hello", max_len=0)`       | `"..."`     (3 chars **VIOLATES**) | `""`   (0 char OK)  |

## Cross-dialog awareness

V5 dialog independently shipped the same logical fix at commit
`a1d67d726` on branch `ship/cheeky-swinging-snail-2026-05-13` (V5 used the
PR #46 engine to self-ship this fix successfully — confirming once again
that PR #46's MINIMAL CHANGE MODE + semantic check is required for safe
small-edit dogfooding).

Per the session summary, platform dialog explicitly does NOT cherry-pick
V5's commit — this branch is an independent platform-dialog ship of the
same fix via the manual-fallback path described above.

## Next steps

1. User reviews this branch
2. If approved: open PR (or merge straight to master)
3. Independent of D1 outcome — PR #46 needs review/merge soon (this evidence
   strengthens that case)

— platform dialog · 2026-05-25

# Patches against the upstream harness

Each file is a self-contained patch script we executed on the official
LongMemEval-V2 harness during our runs. They modify upstream files at
runtime; none embed upstream code (upstream is Apache-2.0 — apply against
your own clone).

| Patch | Status | What it does |
|---|---|---|
| `lmev2_harness_prompt_patch.py` (d12) | **adopted — current stack** | Abstention prompt alignment: forbids bare UNKNOWN, points the reader at the rubric's two legitimate routes (identify the flawed premise / state the live-environment access limitation). Our tuned run (web 40.0 / ent 38.4) uses this. |
| `lmev2_evaluator_retry_patch.py` | **adopted** | Judge retry hardening: 3-attempt internal retry on empty judge responses + outer try/except so a single judge hiccup doesn't kill a run + syntax gate. Born from a run where judge blanks zeroed scores. |
| `lmev2_harness_prompt_patch_d4.py` (d4) | **rejected by preregistered gates** | Abstention-gate experiment: taught the model to refuse-from-snapshot. Result: refusal template leaked into answerable questions (92/89 items vs gate ≤1/≤2), non-abst web dipped below anchor. Kept for the record — negative results are results. |

Judgment criteria for all of the above live in `docs/PROTOCOL.md` and the
preregistration files in our main repository.

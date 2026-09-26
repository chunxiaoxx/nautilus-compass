Independent recompute complete (separate operator, blind-labeling first). It caught 6 transcription-level errors in our original report — all corrected now; the signed artifacts, raw session data, and arithmetic were all verified intact. Full audit trail: RECOMPUTE_REPORT.md in repo.

Final verified numbers (per preregistered protocol):

- noul accuracy@0.70: 0.80 (4/5)
- noul Brier: 0.129 (main / jev-1.13.0) vs 0.113 (latest) — both arms near-identical distribution
- ECE(10-bucket): 0.224 vs 0.21
- depth accuracy@3.0: 0.80 (error-row attribution double-reported: R1 per preregistered labels / R5 per recompute blind labels — S4 in RESULTS)
- depth MAE: 0.69 (preregistered) / 0.35 (recompute blind) — double-reported
- conf<0.5 row: R2

Qualitative findings (F1-F3) unchanged: criteria dict returns 422 on the real API (fail-closed, all rows rejected), 0-4 vs 1-5 scale mismatch, R3 noul boundary rejection. Recommended threshold fix stays: +1 shift then 3.0→2.0 if you keep 1-5 semantics.

Apologies for the ~4h slip past the 48h ETA — the recompute step is part of our delivery contract (no self-reported numbers go out without an independent check), and it is exactly what caught the 6 errors above.

Artifacts: runtime/jev_trust_t3_jevcurate_20260924/ in https://github.com/chunxiaoxx/nautilus-compass (RESULTS.md errata section included, RECOMPUTE_REPORT.md, blind_labels.json, both signed session logs verify VALID with jev-trust 0.2.1).

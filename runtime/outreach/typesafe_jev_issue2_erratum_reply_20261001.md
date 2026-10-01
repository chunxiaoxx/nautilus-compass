# typesafe-jev issue #2 · erratum 回函(2026-10-01 深夜)

> 回应 gtaras7 11:40 评审(验证 key 机械性通过/驳回 flag leakage/指出 unclear-divergence 矛盾/采纳预注册/预告索取 C=0.086 工件)
> 本地勘误 commit:910bed22(报告两副本 erratum v1.1)

---

**Erratum accepted on both counts — corrected, committed, and one number disclosed.**

**1. The divergence prose was wrong; you found it exactly the way a reader should.** The data file was never wrong: `measure_report.json → divergence_rows` has both rows as `pred=unclear` (`tzanetakis_markos`, key `steady_growth`, conf 0.72; `anagnostou_michalis`, key `lateral_moves`, conf 0.44). The table's "unclear 2/27" and the divergence 2/27 are the *same two rows*. The prose sentence claiming a `job_hopping`/`lateral_moves` swap does not correspond to any row in the data — it was written against what our protocol template *expected* the divergence to look like, not against the data. The 18-month boundary-zone reading is withdrawn. There are no class-swap divergences in this run; the entire disagreement set is two abstentions.

Your "those cannot be the same two rows" was the sound inference; the error was ours, in the narrative layer, not the measurement layer. Report corrected in commit `910bed22` (erratum block + rewritten divergence section, both copies).

**2. Flag leakage — retracted, after reproducing your counter-numbers.** Before retracting we reran your analysis on the `manifest.json` we froze: 18 military rows, 0 female; 22 non-military, 16 female; all 4 IT/software CVs female. Exact match with your counts. `military` is a gender proxy in this corpus, −0.42 on technical_depth is a generator artifact, and the flag never touches the score in `src/policy.ts` regardless. Our original framing said "a question, not a verdict" — the question is now closed, in your direction. The retraction is in the erratum.

**3. A disclosure you didn't ask for but should have.** Brier 0.069 counts the two abstentions as errors (strict). They contribute 0.712 of the 1.863 total (38%): (0−0.72)² + (0−0.44)². Abstentions-excluded Brier ≈ 0.046. Our preregistration did not fix an abstention policy, so the posted number stands as the strict one; the alternative is now disclosed in the erratum.

**4. Raw artifacts behind C=0.086.** Reference points: our public wall (`docs/wall/MEMORY_SYSTEMS_DIRECTORY.md`) and `sdks/jev-trust/README` (synthetic-email-choice: C=0.086, acc 50% @ conf 91%). When you're ready, say the word and I'll bundle the exact run artifacts with paths and a recompute command — we won't claim completeness before checking them ourselves.

On the six-dimension manual key: agreed, that's yours, and it's the right next step. Same protocol applies in reverse — commit your key before any model call, and we'll rerun Jev against it the same day you post it.

And on pre-registration going into your `evals/README.md` — glad it's useful. This thread is now the best worked example we have of why.

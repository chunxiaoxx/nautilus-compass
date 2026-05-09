# Paper 2 · Finalization Decision Memo

> **Date**: 2026-05-07
> **Status**: SIGN-OFF · camera-ready unblocked
> **Authors**: chunxiao + Compass team
> **Supersedes**: any open question in `OUTLINE_PAPER2.md` re: V4-pro headline

---

## 1. Decision

**v0.8 (DeepSeek V3.2 thinking, 56.6% on LongMemEval-S, n=500) is the final headline. V4-pro is demoted from main results to a negative-result appendix.** V4-pro full-500 came back at 56.4% (-0.2 pts vs v0.8, within noise) at 8× the per-token cost — no production case, no paper case. `paper/sections/paper2_v4_appendix.tex` already documents the verdict (full-500 table, sample-size lesson, "Verdict" paragraph at line 132) and is wired into `paper2_main.tex` (line 127). No structural rewrite needed; the appendix's framing as "preliminary" / "held full 500" needs tightening to read as a closed negative result.

## 2. Camera-ready edit list

1. **`paper/sections/paper2_v4_appendix.tex` — retitle and reframe**: change section title from "DeepSeek V4 preliminary results" to "DeepSeek V4-pro: a tied-accuracy negative result". Delete the "held full 500" subsection (lines 153–176) — obsolete since the full 500 ran. Promote the "Verdict" paragraph (line 132) to "C.4 Verdict and sample-size lesson". **This is the single most important edit**: the appendix currently reads as "we paused at sample 48"; it must read as "we ran full 500, result was tied".

2. **`paper/OUTLINE_PAPER2.md` §0 Abstract & §4 — close `TBD` placeholders**: the §4 ablation table (lines 136–148) still has `TBD` rows. Replace with v0.8 per-stage deltas from `RESULTS_v0.8.md` (+27 ssu / +8 ms / +2-3 ku / +2 ssa / +0.5 top_k). Confirm V4-pro is absent from §4.2 Table 1.

3. **`paper/sections/paper2_05_discussion.tex` — add sample-size caveat**: add a 3-sentence paragraph "On sample size for model substitution decisions". Cite the V4 case: sample-48 +4.2 pts; full-500 -0.2 pts; 5/6 per-type estimates flipped sign or moved beyond 95% CI. Conclude: "We do not approve model substitutions on n<100 samples." Makes the lesson a first-class contribution, not appendix trivia.

4. **`paper/RESULTS_v0.8.md` — add provenance footer**: append one line — "V4-pro full-500 evaluated 2026-05-06 at 56.4%; see Appendix C. Headline locked at v0.8 56.6% per finalization memo 2026-05-07." Prevents future re-litigation.

## 3. Outstanding non-blockers

- **Tier 3 Run C' temperature=0.7 enrichment** — does not block submission; defer to v0.9.x experiments.
- **Cross-judge replication with Gemini judge** (~$10) — recommended for reviewer rebuttal, not for initial submission.
- **V4-pro selective routing experiment** (V4 for ssa/ssp, V3.2 for ms/temporal) — flagged in appendix as future work; do not run for camera-ready.
- **think-max mode untested** — explicitly out-of-scope, mentioned in appendix limitations.

## 4. Submission target + timing

**Target venue**: arXiv preprint (cs.CL primary, cs.SE cross-list) as the first move, per `paper/PUBLICATION.md`. Follow with **ICLR 2026 Workshop on LLM Memory** as the named workshop in `OUTLINE_PAPER2.md`. arXiv requires no review and locks priority immediately.

**Target window**: arXiv submission **2026-05-12 to 2026-05-14** (one-week buffer to land edits 1–5 above). Workshop submission follows arXiv handle issuance. No US holiday or major-conference week in that window.

**Assumption flagged**: ICLR 2026 Workshop CFP and deadlines have not been re-verified this session — confirm before finalizing workshop submission. arXiv is the unconditional first step regardless.

---

**Sign-off**: This memo unblocks paper2 camera-ready. Edits 1–5 are scoped, additive, and do not require new experiments.

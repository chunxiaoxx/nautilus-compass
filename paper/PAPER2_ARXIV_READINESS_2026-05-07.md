# Paper 2 · arXiv Readiness Audit · 2026-05-07

> Audit target: `paper/paper2_main.pdf` (rebuilt 2026-05-08 12:53 · **27 pages** · 428 KB)
> Auditor: read-only · no paper files modified
> Prior fixes today: `\rightarrow` math-mode in §6.5:41; `⭐` glyph in v4 appendix table; `⚠️` glyph in v4 appendix table; §4 TBD-fill; §5 sample-size paragraph; Appendix C retitle.

---

## 1 · Verdict

**Not ready (3 P0 blockers)** · all are mechanical · 1.5–2.5 hours of total work · no rewriting required. Page count drift (memo says 25, actual is 27) is cosmetic and downgraded to P1.

---

## 2 · P0 blockers

- **Two visible "placeholder · TODO replace with real ref" entries on the rendered References page (page 24).**
  · `paper/paper2_refs.bib` lines 69–74 (`wang2024selfdetect`) and 124–129 (`wang2025thinkingharm`) carry `note = {placeholder ...}`. bibtex faithfully prints the note in the output, so the published PDF reads:
  *"Wang and Others. Black-box hallucination detection via prompt-based probing, 2024. placeholder — TODO replace with real ref."* and an analogous line for the over-reasoning ref. This is a paper-killer for arXiv reviewers and any reader. Both keys are cited in §2 (`02_related.tex:50` and `02_related.tex:67`).
  · Fix options: (a) replace `wang2024selfdetect` with a real prompt-based hallucination detection paper such as Manakul et al. *SelfCheckGPT* (EMNLP 2023, arXiv:2303.08896); replace `wang2025thinkingharm` with Sprague et al. *To CoT or not to CoT?* (arXiv:2409.12183) or a more current over-reasoning paper · (b) if no clean substitute exists, drop the citation in §2 and remove the bib key entirely — the surrounding sentence works without the cite. Either way, **strip the `note = placeholder` field** before any rebuild.
  · ETA: **45 min**.
  · Verify: `bibtex paper2_main` → grep the resulting `paper2_main.bbl` for `placeholder` and `TODO` (must be zero hits). Rebuild PDF and visually confirm page 24 has no "placeholder" text.

- **Figures 2 (trajectory) and 3 (fusion-points) are rendered as `\fbox{\parbox{...}}` placeholder boxes, not actual figures.**
  · `paper/paper2_main.tex` lines 83–101 wrap both figures as `\fbox{\parbox{...[trajectory_v08 figure · TikZ source in figures/trajectory_v08.tex] ...}}`. On disk: only `figures/pipeline_v08.pdf` exists; `figures/trajectory_v08.tex` and `figures/fusion_diagram.tex` were never compiled to PDF. Pages 26 and 27 of the rendered PDF show literal text `[trajectory_v08 figure · TikZ source in figures/trajectory_v08.tex]` inside a black box. arXiv reviewers will treat this as a draft submission.
  · Fix: compile `trajectory_v08.tex` and `fusion_diagram.tex` standalone via tikz-standalone, drop the resulting PDFs into `figures/`, and replace the `\fbox{\parbox{...}}` blocks in `paper2_main.tex:83-101` with `\includegraphics[width=0.95\textwidth]{figures/trajectory_v08.pdf}` and `figures/fusion_diagram.pdf`. If TikZ source has compile errors, fall back to a quick matplotlib export of the V-shape from the per-question logs (§5.3 has the data) and a Graphviz/PowerPoint export for the 8-fusion-points diagram.
  · ETA: **75 min**.
  · Verify: `ls figures/trajectory_v08.pdf figures/fusion_diagram.pdf` resolves; rebuilt PDF pages 26–27 show real graphics; no "TikZ source in" string in `pdftotext paper2_main.pdf -`.

- **`paper/OUTLINE_PAPER2.md` lines 231–238 still carry the "TODO 等 v0.8 full 500 跑完后填" checklist with six unchecked boxes.**
  · The list references items that are now done (Abstract numbers · §4.2 Table 1 v0.8 row · §4.3 ablation · by-type breakdown · refusal cascade · Figure 1) but the TBD checklist itself was never struck through. The agent's TBD-fill in §4 of the tex did not propagate back to OUTLINE.md. Also line 107 still says `(TODO: cite when public)` for the companion paper-1 reference.
  · Fix: edit OUTLINE_PAPER2.md — strike or delete the §"TODO" section; replace `TODO: cite when public` with the paper-1 placeholder citation form `(see companion paper, arXiv:<TBD>)`. OUTLINE.md is not in the arXiv submission tarball but it ships with the GitHub release and signals draft-grade work to anyone reading the repo around submission day.
  · ETA: **15 min**.
  · Verify: `grep -n "TODO\|TBD\|placeholder" paper/OUTLINE_PAPER2.md` returns zero matches in the active text (one residual `arXiv:<TBD>` is acceptable as a workflow item, mirror of paper1).

---

## 3 · P1 polish

- **Cumulative-vs-incremental ablation footnote claimed-but-missing.** Task brief asserts §4.3 has a footnote noting that the ablation table reports "cumulative point estimates, not true incremental ablations". Reality: `paper2_04_eval.tex:130-134` has a *table caption* paragraph mentioning "sample-to-full projection error", but no `\footnote{}` and no explicit cumulative-vs-incremental wording. If the cumulative-vs-incremental disclaimer is the intended fix, add a one-line footnote on the first column header of Table 4 (`tab:ablation`): "Reported deltas are cumulative point estimates from the 48-question stratified pilot, not true single-component incremental ablations on the full 500." ETA: 10 min.
- **27-page count vs 25-page memo.** `paper2_finalization_decision_2026-05-07.md` is silent on length, but cover letters and arXiv comments lines that pre-quote "25 pages" should be re-checked. ETA: 5 min.
- **Title mismatch with abstract claim.** Title: "Achieving Zep-SOTA Performance on LongMemEval-S at 1/15 Cost" — abstract now also leads with EverMemBench-Dynamic 44.4% beating MemOS by 1.85 pts (a stronger result on a multi-party benchmark). Consider: "Closing the Memory Recall Gap with Chinese LLMs: A Multi-Stage Retrieval Pipeline that Ties Zep on LongMemEval-S and Beats MemOS on EverMemBench at 1/15 Cost" — or shorter. ETA: 15 min.
- **Author byline missing email/affiliation address.** `paper2_main.tex:51-52` lists `chunxiaoxx · Nautilus Platform · compass.nautilus.social` only. Same gap as paper-1 audit. ETA: 5 min.
- **Date `2026-05-05` on title page is stale.** PDF was rebuilt 2026-05-08; the V4-pro full-500 result post-dated 2026-05-05; abstract and §6.5 numbers are 2026-05-07. Bump `\date{}` in `paper2_main.tex:54` to `2026-05-12` (planned arXiv submission) or `\today`. ETA: 2 min.
- **Conclusion section quotes `AUC = 0.92` for drift but mainline §4 says 0.92 and the paper1 cross-cite uses 0.83.** The task brief says headline numbers should appear including "0.83 AUC (drift, cross-cite paper1)". Paper2 currently ships only 0.92 (its own measurement); 0.83 appears once in §appendix B agreement context (`agreement = 0.834` excluding ssp), not as a drift AUC. Confirm whether paper2 should explicitly cite paper1's 0.83 cross-domain figure, or whether 0.92 is the intended sole headline. ETA: 10 min if cross-cite needed.
- **Section 3 §3.1 says "BM25 + bge-m3 dense recall" but the next sentence says we *do not* use BM25.** `paper2_03_method.tex:7` — first sentence advertises BM25+dense; lines 16–20 then explicitly drop BM25. Either remove BM25 from the §3 enumeration or keep it but explain BM25 is the lower-bound baseline used only in §6.5. ETA: 5 min.
- **`anthropic2024claude` bib entry has no journal/note/url field.** It will render as bare title + author + year. ETA: 3 min.
- **Bib entries for `mem0_2024`, `letta2024`, `zep2025`, `amem_2024`, `claudemem2026` use `{Mem0 Team}` / `{Letta Team}` / `{Zep Team}` / `{A-MEM Team}` / `thedotmack` as authors.** Same "ghost-author" complaint flagged in paper-1 P0; here it's lower-stakes because none are head-to-head competitors with citations on the references page, but reviewers will notice. Replace with real author lists where the projects have them (mem0 has a published arXiv paper · 2504.19413). ETA: 20 min.

---

## 4 · Build & artifact check

- ✅ `paper/paper2_main.pdf` exists · 437,808 bytes · **27 pages** (memo says 25; actual measured today).
- ✅ Built 2026-05-08 12:53 with pdfTeX 1.40.20.
- ✅ Zero `??` unresolved-reference markers in extracted text.
- ✅ All `\citep{...}` keys resolve to `.bbl` entries; no missing-citation warnings in extracted bibliography.
- ❌ Two bib entries (`wang2024selfdetect`, `wang2025thinkingharm`) print `placeholder · TODO replace with real ref` directly on the references page (P0 above).
- ❌ Figures 2 and 3 are `\fbox{\parbox{...}}` text placeholders, not real graphics (P0 above). Only `figures/pipeline_v08.pdf` exists; `trajectory_v08` and `fusion_diagram` exist only as `.tex` source.
- ✅ Figure 1 (`pipeline_v08.pdf`) embeds correctly; arrow glyphs render via TikZ math, not raw unicode.
- ✅ §6.5 EverMemBench section uses `Add$\rightarrow$Search$\rightarrow$Answer$\rightarrow$Evaluate` correctly in math mode (the prior `\rightarrow` outside math fix held).
- ✅ V4 appendix renders 56.4% / -0.2 / 8× / sample-size lesson correctly. The two glyphs (`⭐` superseded by `$\star$`, `⚠️` superseded by `$\dagger$`) render as expected math symbols.
- ✅ §5 has the new "On sample size for model substitution decisions" paragraph (`05_discussion.tex:105-115`).
- ✅ Appendix C is retitled "DeepSeek V4-pro: a tied-accuracy negative result" and §C.4 "Verdict and sample-size lesson" is in place.
- ✅ Headline numbers 56.6% / 44.4% / 0.92 / κ=0.772 all appear in abstract + body.
- ⚠️ `-0.2` appears in §5 and Appendix C but PyPDF2 text extraction reports it as `0.2` (sign stripped during ligature handling); not a content bug, just a search artifact.

---

## 5 · Submission checklist (arXiv-specific)

| Item | Status | Note |
|---|---|---|
| Primary `cs.CL` | ✅ Per finalization memo | "Computation and Language" — paper is about retrieval pipelines and LLM behavior |
| Cross-list `cs.SE` | ✅ Per finalization memo | Add `cs.LG` / `cs.AI` per paper-1 audit logic; broader audience |
| Comments line | 🟡 Not in tex | Recommend: `Comments: 27 pages, 3 figures, 11 tables. Code at github.com/chunxiaoxx/nautilus-compass. Companion paper: arXiv:<paper1 id once issued>` |
| Author affiliation | 🟡 Handle + URL only | Same as paper-1; P1 above |
| CC license | 🟡 Default arXiv non-exclusive (recommended) | Code MIT (separate, unaffected) |
| Abstract under 1,920 chars | ✅ **1,293 chars / 171 words** plain-text — well under cap | No action needed; in stark contrast to paper-1 which was 2× over |
| §4.3 cumulative-vs-incremental footnote | ❌ Caption-level disclaimer only; **no `\footnote{}` and no "true incremental" wording** | P1 above; agent's TBD-fill claim is overstated |
| Pre-issued tarball builds clean | 🟡 Not retested today; figures-as-placeholder will compile but reads as draft | Re-run `tectonic paper2_main.tex` after P0-2 fix |
| Endorsement | 🟡 Same author as paper1; if paper1 endorser secured, paper2 reuses | Workflow item |
| Companion paper cross-reference | 🟡 Body says "see companion paper" (`02_related.tex:54`) but no citation key — backfill `arXiv:<paper1 id>` after paper-1 lands | Order matters: submit paper1 first, paper2 second day |

---

## 6 · Recommended submission window

Per `paper2_finalization_decision_2026-05-07.md` §4: arXiv submission **2026-05-12 to 2026-05-14**, ICLR 2026 Workshop on LLM Memory as second venue (CFP not re-verified — confirm before workshop submission).

Recommended ordering:
1. **2026-05-08 EOD** · clear all 3 P0 (placeholder bib refs · placeholder figures · OUTLINE TBDs).
2. **2026-05-09** · clear P1 polish (footnote · title bump · date · author email · §3 BM25 inconsistency).
3. **2026-05-12 morning PT** · submit paper-1 to arXiv first (per paper-1 audit).
4. **2026-05-13 morning PT** · submit paper-2 once paper-1 has an arXiv ID, backfilling the companion-paper citation key.
5. Both land on **2026-05-14 (Wed) listing** for HN visibility.

If P0-2 (figures) blows past 75 min, a one-day slip to 2026-05-13/14 submission is acceptable per the memo's stated window.

---

## TL;DR

- Verdict: **not ready · 3 P0 blockers · ~2 h to fix**
- P0 count: **3** (bib placeholder text on references page · two figures-as-fbox placeholders · OUTLINE_PAPER2.md TODO checklist)
- P1 count: **9** (claimed-but-missing cumulative footnote · 27-page count drift · title scope · author email · stale date · 0.83 AUC cross-cite · §3 BM25 inconsistency · empty `anthropic2024claude` bib · ghost-author bib entries)
- **The one item that gates submission**: two bib `note = {placeholder · TODO replace with real ref}` strings rendered verbatim on the references page (page 24). Anyone opening the PDF reads "TODO replace with real ref" before they read the conclusion.
- **Cumulative-vs-incremental footnote check**: the task brief's claim that the §4 TBD-fill agent added this footnote is **not borne out by the tex**. There is a caption-level note about "sample-to-full projection error" on Table 4, but no `\footnote{}` and no explicit "cumulative point estimates, not true incremental ablations" wording. Treat as P1 to add explicitly before submission.
- Headline numbers all confirmed in abstract + intro + §4 + §6.5: 56.6% LongMemEval-S, 44.4% EverMemBench, -0.2 V4-pro, κ=0.772 cross-judge, 0.92 drift AUC. The 0.83 AUC paper-1 cross-cite is **not** present and should be added if intended.

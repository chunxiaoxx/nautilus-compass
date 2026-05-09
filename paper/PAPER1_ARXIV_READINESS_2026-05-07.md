# Paper 1 · arXiv Readiness Audit · 2026-05-07

> Audit target: `paper/nautilus-compass.pdf` (rebuilt today · 19 pages · 620 KB)
> Auditor: read-only · no paper files modified
> Prior fixes today: `\usepackage{lmodern}` added; broken `\ref{sec:method-strategy}` removed from `02_related.tex:159`

---

## 1 · Verdict

**Not ready (3 P0 blockers)** · all are mechanical fixes · 1.5–3 hours of total work · no rewriting required.

---

## 2 · P0 blockers

- **Abstract 2× over arXiv length cap.**
  · `paper/sections/00_abstract.tex` · 492 words / 3,745 chars in rendered PDF · arXiv submission-form abstract field caps at **1,920 chars** and `OUTLINE.md` self-imposes a 200–250 word target. The arXiv submission form will silently truncate or reject.
  · Fix: cut to ~240 words / ~1,800 chars · keep moves (1) gap, (2) approach, (3) headline numbers, (4) honest scope · drop the cross-vendor-A/B paragraph (move it to introduction) and the verbose four-step recap.
  · ETA: **45 min**.
  · Verify: `wc -w paper/sections/00_abstract.tex` (expect 200–260) and arXiv submission preview shows abstract field accepted without truncation warning.

- **Figure 1 (architecture) is rendered with scrambled / overlapping glyphs.**
  · `paper/figures/fig1_architecture.pdf` · `pdftotext` extracts `"Totpim-Kem+emcoosrinyeby  weigvhst6e0d atonpc-h3omrsean"` and `"trigDgPeTr-sbtyylekepyawthord"` — adjacent labels share a baseline, glyphs interleave. In a real PDF viewer this manifests as overlapping text. Also still labels the hook source as `zenmind-mem/recall.py` (pre-rebrand name).
  · Fix: regenerate the figure (TikZ source likely lives in `figures/pipeline_v08.tex` or a similar script — confirm from `figures/generate_figures.py`). Increase row spacing on the three parallel-path boxes; rename `zenmind-mem/recall.py` → `compass/recall.py` to match v0.9 codebase.
  · ETA: **60 min**.
  · Verify: `pdftotext figures/fig1_architecture.pdf -` produces a readable, non-interleaved column layout AND the rebuilt main PDF page 5 reads cleanly when opened in a viewer.

- **Two `@article` bib entries have no `journal` field, rendering as "Mem0 contributors" / "BAAI" — bibtex flagged both at build time.**
  · `paper/refs.bib` lines 11–16 (`mem0`) and 46–51 (`bgereranker`) · also `dptagent` (`DPT-Agent contributors`) and `amem` (`A-MEM contributors`) follow the same shape. These are not citation failures (they resolve), but they read as undergraduate placeholders in a paper claiming a head-to-head with mem0.
  · Fix: replace with real refs:
    - `mem0` → Singh, T. et al. *Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory*, arXiv:2504.19413 (2025) · use real authors from the mem0 paper, cite as `@article` with the arXiv journal field present.
    - `bgereranker` → Chen, J. et al. *BGE M3-Embedding* (arXiv:2402.03216, 2024) covers both the embedder and the reranker family · or cite the BAAI tech report for `bge-reranker-v2-m3` directly with the URL field but type `@misc`.
    - Convert `dptagent` and `amem` to `@misc` with `note={GitHub project}` if no real arXiv paper exists, or find the actual author lists.
  · ETA: **30 min**.
  · Verify: rerun `bibtex nautilus-compass` and confirm zero `Warning--empty journal in <key>` lines. Rebuild PDF and confirm the references page lists real human author names rather than "contributors".

---

## 3 · P1 polish

- **Author byline missing email / affiliation address.** `nautilus-compass.tex:26-28` lists `chunxiaoxx \\ Nautilus Open Platform \\ url{...}` · arXiv accepts handle-only authorship but readers and reviewers cannot reach the author. Add `\\texttt{<contact email>}` or omit the affiliation line. ETA: 5 min.
- **Version drift between paper and code release.** Paper text says "v0.7.1" in five places (`04_eval.tex:110, 368, 396, 401`; `05_discussion.tex:111`; `06_limitations.tex:5`). `RELEASE_READINESS.md` says current code is `v0.9.0-dev`; `PUBLICATION.md` targets release tag `v0.7.2`. Either bump paper to match the tag at submission OR add a note "evaluation snapshot v0.7.1 · current release v0.9.0". ETA: 10 min.
- **Empty `journal` warning on `mem0` / `bgereranker` is technically a bibtex P1 (paper still compiled).** Folded into P0 above because it's user-visible in the references page.
- **Caption for Table 5 says "subset 12" three times in adjacent sentences (Sec 4.6).** Light copyedit, not blocking. ETA: 10 min.
- **`anchors_{legal,medical,finance}.json` line in `07_opensource.tex` overflows the column slightly** (page 17 last line, "OPEN_SOURCE_READINESS"). Either `\sloppy` the paragraph or break the path. ETA: 5 min.
- **Long sentence audit:** Section 4 (Eval) has several 50+ word sentences (Sec 4.4 ¶3, Sec 4.6 ¶2). arXiv preprint style tolerates this; ACL/EMNLP would not. Optional pre-conference edit. ETA: 30 min.
- **No `arXiv:<TBD>` cross-reference yet** — `PUBLICATION.md:55` and the GitHub release notes carry the `arXiv:<TBD>` placeholder. After arXiv issues an ID, backfill the README and re-tag. Workflow item, not paper text.

---

## 4 · Build & artifact check

- ✅ `paper/nautilus-compass.pdf` exists · 620,168 bytes · 19 pages (matches mandate).
- ✅ Page 1 renders title, byline, date, abstract; pages 2–17 render body; pages 18–19 are References.
- ✅ Zero `??` unresolved-reference markers in extracted text.
- ✅ `\ref{sec:method-strategy}` was correctly removed (no orphan); `sec:limitations-behavior` and `sec:eval-holdout` labels both exist in `06_limitations.tex:10` and `04_eval.tex:331` respectively.
- ✅ All 6 `\includegraphics` targets exist on disk (`fig1`–`fig6`, all 4–61 KB PDFs in `paper/figures/`).
- ⚠️ `fig1_architecture.pdf` text content is scrambled (P0 above) — file is structurally a valid PDF but glyphs overlap.
- ✅ All 6 `\citep`/`\citet` keys resolve to real `.bbl` entries; no missing-citation warnings.
- ✅ No `TBD`, `XXX`, `FIXME`, `[FIGURE MISSING]`, or `placeholder` strings in any of the 8 paper-1 section `.tex` files or main `.tex`.

---

## 5 · Submission checklist (arXiv-specific)

| Item | Status | Note |
|---|---|---|
| Primary category `cs.CL` | ✅ Confirmed in `OUTLINE.md` and `PUBLICATION.md` | `Computation and Language` is correct — paper is about prompt-text-layer drift detection, not raw model architecture |
| Cross-list `cs.LG`, `cs.AI`, `cs.SE` | ✅ Plan in `PUBLICATION.md:22` (`cross-listed cs.SE`) | Recommend `cs.LG` + `cs.AI` since the audience is broader than software engineering |
| Comments line | 🟡 Not in `nautilus-compass.tex` | Add e.g. `Comments: 19 pages, 6 figures, 8 tables. Code at github.com/chunxiaoxx/nautilus-compass` to the arXiv form (not the LaTeX) |
| Author affiliation in PDF | 🟡 Handle + GitHub URL only · no email | P1 above |
| CC license tag | 🟡 `OUTLINE.md:76` says CC BY 4.0 | Select **arXiv perpetual non-exclusive** (default) at submission unless explicit CC BY desired; the code's MIT license and anchor CC0 are unaffected |
| Abstract under 1,920 chars | ❌ Currently 3,745 chars | P0 above |
| `build_arxiv_paper1.sh` runs clean | ✅ Today's rebuild succeeded · script copies sources, runs pdflatex 3×, bibtex 1×, builds tarball | The script tolerates bibtex warnings (`\|\| true`); reviewers should rerun without that suppression to confirm the empty-journal warning is the only one |
| Endorsement | 🟡 Required for first-time arXiv cs.CL submission | Author may need an endorser — start this process in parallel with paper fixes |

---

## 6 · Recommended submission window

`PUBLICATION.md` does not pin a venue beyond arXiv. `OUTLINE.md:7-9` lists optional secondary targets:
- **arXiv preprint immediately** (after the 3 P0 fixes · ~3 hours of work · no peer review barrier).
- **NeurIPS 2026 Workshop on Memory in LLM Agents** — likely CFP open July 2026 · cross-list arXiv version.
- **ACL ARR rolling review** — open monthly · paper as-is fits the 8-page short / 12-page long template.

Recommendation: fix the 3 P0 items by **2026-05-08 EOD**, request endorsement, submit to arXiv `cs.CL` primary + `cs.LG`/`cs.AI` cross-list **2026-05-09 morning PT** to land on the **2026-05-12 (Mon) listing** for max HN visibility before the planned `Show HN` window in `PUBLICATION.md`. Monitor July 2026 for NeurIPS workshop CFPs.

---

## TL;DR

- Verdict: **not ready · 3 P0 blockers · ~3 h to fix**
- P0 count: **3** (abstract length · figure 1 garbled · two ghost-author bib entries)
- P1 count: **6** (email · version drift · captions · long sentences · path overflow · arXiv ID backfill)
- The **one item that gates submission**: abstract is 492 words / 3,745 chars — arXiv form caps at 1,920 chars · all other fixes can be deferred but this one will cause submission rejection or silent truncation.
- Placeholder text found: `arXiv:<TBD>` in `PUBLICATION.md:55` and the GitHub release notes (workflow item, not paper text). The paper-1 `.tex` files contain **zero** `TBD` / `XXX` / `FIXME` / `placeholder` strings.

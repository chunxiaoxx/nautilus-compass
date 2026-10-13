---
name: orgfuel-ORGH-3818d99be68daedd-8b71079ebc
description: "commit 5d1a56dc6794 2026-05-06 paper build infra · arxiv sub"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-3818d99be68daedd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 5d1a56dc6794 2026-05-06
paper build infra · arxiv submission tarball generator + LaTeX fixes
Adds paper/build_arxiv.sh:
- compiles standalone tikz figures first (PDF), then main with pdflatex
- generates arxiv_submission_YYYYMMDD.tar.gz ready for upload
- includes .tex + .bbl + .bib + figures/

paper2_main.tex fixes for clean pdflatex build:
- pgfplots compat 1.18 → newest (T4 has older pgfplots)
- cite → natbib[round] (provides \citep used throughout)
- xeCJK removed (no actual Chinese glyphs · only ¥ via \textyen)
- microtype removed (cmex10 not scalable on TexLive 2023)
- \input{figures/...} → \includegraphics (standalone class can't inline)
- Added §6.5 + 3 appendix \input lines

Section fixes:
- paper2_01_intro.tex: "$20+" → "\$20+" (math-mode escape)
- paper2_04_eval.tex: "\;\

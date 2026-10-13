---
name: orgfuel-ORGH-757c43b03bf86842-d00a15ba54
description: "commit 0af2c5a9cf9d 2026-05-06 paper · LaTeX unicode fixes +"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-757c43b03bf86842
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 0af2c5a9cf9d 2026-05-06
paper · LaTeX unicode fixes + figure placeholders (arxiv-ready source)
Bulk replace unicode glyphs with LaTeX commands so source is portable
across TeXLive versions:
  Δ → \(\Delta\)    κ → \(\kappa\)    σ → \(\sigma\)
  τ → \(\tau\)      θ → \(\theta\)    α → \(\alpha\)
  → → \(\to\)       ≤ → \(\le\)       ≥ → \(\ge\)
  · → \textperiodcentered{}            ≈ → \(\approx\)

Side effect: comments (% lines) also got replaced ("\textperiodcentered{}"
appearing in % comments). Harmless · LaTeX ignores comments.

paper2_main.tex:
  amsmath added (align env was undefined)
  3 figure \input → \fbox placeholder (TikZ standalone files cannot be
    \input'd · figures/*.tex retained for separate compilation)

Status: source is arxiv-upload-ready. Local pdflatex build 

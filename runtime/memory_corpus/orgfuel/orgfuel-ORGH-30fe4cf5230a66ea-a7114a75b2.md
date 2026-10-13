---
name: orgfuel-ORGH-30fe4cf5230a66ea-a7114a75b2
description: "commit 8faa3ed66d2b 2026-05-10 ci(paper): build arxiv-ready "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-30fe4cf5230a66ea
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 8faa3ed66d2b 2026-05-10
ci(paper): build arxiv-ready tarballs as artifacts · paper 1 + paper 2
Adds tarball-build step to existing PDF compile. After commit lands,
both papers' arxiv-ready source tarballs become downloadable from
GitHub Actions artifacts (90-day retention) · upload directly to
arxiv.org Replace.

Tarballs include: main .tex · sections/*.tex · refs.bib · pre-built
.bbl (arxiv prefers it · saves their bibtex pass) · figure PDFs.

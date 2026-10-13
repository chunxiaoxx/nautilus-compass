---
name: orgfuel-ORGH-7bdcc569f1f00f74-71896a54bc
description: "commit 1ec951ce1e4f 2026-05-09 fix(recall): v0 · embed body "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-7bdcc569f1f00f74
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 1ec951ce1e4f 2026-05-09
fix(recall): v0 · embed body excerpt in top-3 hits to break consumption illusion
Recall today returned title + 120-char description only. Agents skimming
recall output saw labels ("audit-gate / xhs-cards-embed / wxid") without
the rule body and proceeded believing they had consumed the memory · they
hadn't. Same agent kept making the same mistake across sessions despite
recall hitting the right files.

Fix: top-3 hits in both metadata mode (line ~430) and vector mode
(line ~496) now embed first 800 chars of post-frontmatter body in an
indented "│" block. Agent gets the actual rules in working context · no
extra Read tool call required to consume them.

Total recall response · still bounded ~3KB for body excerpts · fits in
context budget. Tail hits (4..K) keep

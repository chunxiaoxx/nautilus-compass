---
name: orgfuel-ORGH-2f4adf1250ea0f11-7a4cbe150a
description: "commit 2a0f137e0fb7 2026-05-08 README: split into English-de"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-2f4adf1250ea0f11
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 2a0f137e0fb7 2026-05-08
README: split into English-default + Chinese sibling
GitHub's international default is English. The previous README was
mostly Chinese with English mixed in -- okay for the local team but
high friction for international visitors finding us via paper / HN /
PaperWithCode.

Restructure:
- README.md         · new English-first version (~270 lines, focused)
- README.zh-CN.md   · existing Chinese version preserved as-is, with
                      a language switch line at the top and the version
                      badge bumped 1.0.0-rc2 -> 1.0.0 stable + drift-AUC
                      badge fixed from in-set 0.92 to held-out 0.83

The English README covers: 30-second pitch, problem statement, how it
works diagram, headline numbers (LongMemEval 56.6%, EverMemB

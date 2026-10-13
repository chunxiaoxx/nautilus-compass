---
name: orgfuel-ORGH-e497c47070f4d866-a05eb5376d
description: "commit 25079154eec7 2026-05-08 license: split MIT (code) fro"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-e497c47070f4d866
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 25079154eec7 2026-05-08
license: split MIT (code) from CC0 (anchors); update copyright holder
LICENSE was canonical MIT with an appended paragraph dedicating
anchors to CC0. GitHub licensee.gem could not resolve the dual-
licensing in one file and labeled the repo as "Other" instead of
MIT, breaking pip/npm metadata pickup and search filters.

Split into two files:
- LICENSE         -- canonical MIT, copyright holder updated to
                     "Chunxiao Wang (Yiluo Technology Co., Ltd.)"
- LICENSE-ANCHORS -- CC0 dedication for anchors*.json, with a note
                     pointing back to LICENSE for everything else.

No effect on user rights: the previous combined file still licensed
the code as MIT and the anchors as CC0; this just lets automated
tooling see it correctly.

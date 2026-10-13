---
name: orgfuel-ORGH-f5f382b31313a9d2-3eba74ef1f
description: "commit 80f4a035f162 2026-05-08 license: restore canonical MI"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f5f382b31313a9d2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 80f4a035f162 2026-05-08
license: restore canonical MIT 'OTHER LIABILITY' clause
The previous commit accidentally dropped 'OTHER LIABILITY, WHETHER IN
AN ACTION OF CONTRACT, TORT OR' from the disclaimer paragraph during
the split. That deviation from the OSI-canonical MIT text is what was
preventing GitHub's licensee.gem from recognizing it as MIT.

This restores the exact OSI canonical text. Copyright holder unchanged
(Chunxiao Wang / Yiluo Technology Co., Ltd.).

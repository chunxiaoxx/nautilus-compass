---
name: orgfuel-ORGH-b8d8a62ad650744e-9f565ed0eb
description: "commit 1b8c170063b0 2026-06-07 fix(ingest): recover CJK lone"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b8d8a62ad650744e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 1b8c170063b0 2026-06-07
fix(ingest): recover CJK lone-surrogate crash (cross-device ingest prereq) (#45)
Root cause (reproduced): Windows MCP client gbk-decodes a CJK obs as UTF-8/
surrogateescape → lone surrogates (\udc80-\udcff) → handle_ingest's
write_text(utf-8) crashes 'surrogates not allowed' (Chinese obs all crash, ASCII
passes · session_20260605 Finding 1). The single cloud-substrate ingest path must
never die on one bad obs. _recover_surrogates sanitizes text+filename at the
boundary: re-encode to original bytes + decode as gbk (round-trips the CJK), else
'replace'. Valid input (ASCII/real CJK) untouched → zero regression. 4 tests
green incl. the exact write_text op that crashed. P0 of cloud-substrate plan.

Co-authored-by: nautilus-platform-saas-dialog <saas-dialog@nautilu

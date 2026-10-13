---
name: orgfuel-ORGG-2fb6506d6a0a2519-f67a3b4dee
description: "判读档判例 _notes_ingest_obs_roundtrip · Finding 1 · CJK-in-`name"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-2fb6506d6a0a2519
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 _notes_ingest_obs_roundtrip · Finding 1 · CJK-in-`name` surrogate crash (reproducible, code-fixable)
## Finding 1 · CJK-in-`name` surrogate crash (reproducible, code-fixable)
First ingest with a Chinese `name` ("跨设备测试obs") hard-failed:
```
MCP error -32603: tool ingest_obs failed:
'utf-8' codec can't encode character '\udcae' in position 12: surrogates not allowed
```
A lone surrogate `\udcae` = a CJK byte mis-decoded somewhere in obs name
handling (client transport or server write). Re-ingest with an ASCII name
("xdev-probe-9173") succeeded. → Cross-device ingest of any obs whose `name`
contains CJK currently crashes. Concrete bug, independent of the recall
round-trip; many real obs names are Chinese, so this silently blocks a class of
cross-device writes. (surrogateescape on a Wind

---
name: orgfuel-ORGH-8a48020df995169e-4ec3968c3e
description: "commit 611e3968d59f 2026-06-06 fix(bridge): decode stdin as "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-8a48020df995169e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 611e3968d59f 2026-06-06
fix(bridge): decode stdin as UTF-8, not Windows gbk (CJK obs ingest crash) (#37)
Root cause (SSH+repro confirmed): on a Chinese Windows host sys.stdin defaults
to gbk + surrogateescape. MCP JSON-RPC is always UTF-8, so a CJK obs name's
UTF-8 bytes get mis-decoded into lone surrogates (\udcXX) that survive json.dumps
and detonate cloud-side on strict utf-8 re-encode → '-32603 tool ingest_obs
failed: surrogates not allowed' (the 跨设备 obs ingest bug). Read sys.stdin.buffer
(binary) + decode UTF-8 explicitly (errors=replace · crash-proof, never produces
a surrogate). 5 TDD tests (CJK name, punctuation, ascii, invalid bytes).

Co-authored-by: nautilus-platform-saas-dialog <saas-dialog@nautilus.social>

---
name: orgfuel-ORGH-9bbe00450fd21201-40d850acb7
description: "commit cf5e7e22794a 2026-05-21 ﻿feat(v1.7.1): S6 module 2 · "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9bbe00450fd21201
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit cf5e7e22794a 2026-05-21
﻿feat(v1.7.1): S6 module 2 · storage/viking_uri.py (S6 COMPLETE)
storage/viking_uri.py · ~115 LOC
  - parse_uri / make_uri · viking:// scheme · L0/L1/L2 tier
  - Tier resolved from ?tier=Lx query param OR .l1/.l2 suffix
  - resolve_to_path · maps URI to filesystem under ~/.claude/projects/<p>/memory/
  - path_to_uri · reverse mapping · roundtrip safe
  - NO LLM · pure URL parsing + filesystem composition

tests/test_viking_uri.py · 14/14 pass

S6 LAYER 2 L2 DREAM-LAYER + viking:// COMPLETE · 2/2 modules:
  · l2_distiller (fc711c9) · Ollama-optional · extractive fallback
  · viking_uri (THIS) · tier-agnostic addressing

Total session ship · S3 (5) + S4 (6) + S5 (1) + S6 (2) = 14 modules · ~1660 LOC
all NO LLM at ingest path · all schema-driven deterministic

R

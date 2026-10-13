---
name: orgfuel-ORGH-da3c2521f2610e48-ff3671a22a
description: "commit 2ff4fcf3c0b2 2026-05-21 ﻿feat(v1.7.1): gap fix 1 · st"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-da3c2521f2610e48
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 2ff4fcf3c0b2 2026-05-21
﻿feat(v1.7.1): gap fix 1 · storage/entity_extractor.py · GBrain auto entity linking
storage/entity_extractor.py · ~115 LOC
  - ENTITY_PATTERN regex · [[<ns>/<name>]] · ns in {wiki,people,companies,concepts,sessions}
  - extract_entities / extract_session_refs · regex match
  - build_session_links · merge explicit depends_on + auto-extracted · dedup + .md normalize
  - extract_typed_links · group by namespace
  - rewrite_inline_links · markdown link rewrite (optional)
  - scan_session_file · file-level convenience
  - REUSES paper3 cascade-closure infrastructure (recall.transitive_close BFS)
  - NO LLM · pure regex pattern matching

tests/test_entity_extractor.py · 12/12 pass

GBrain reference verbatim: "Every page write extracts entity references and creates


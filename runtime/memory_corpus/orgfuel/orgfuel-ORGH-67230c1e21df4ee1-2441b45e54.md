---
name: orgfuel-ORGH-67230c1e21df4ee1-2441b45e54
description: "commit fc711c98c53a 2026-05-21 ﻿feat(v1.7.1): S6 module 1 · "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-67230c1e21df4ee1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit fc711c98c53a 2026-05-21
﻿feat(v1.7.1): S6 module 1 · storage/l2_distiller.py · L2 dream-layer (Ollama optional)
storage/l2_distiller.py · ~200 LOC
  - ollama_available · safe HTTP probe · never raises
  - ollama_generate · /api/generate call · timeout-bounded
  - extractive_fallback · deterministic concat+dedup+truncate when Ollama unavailable
  - distill_l1_files · auto-detect Ollama · fallback to extractive
  - render_l2_overview · tier=semantic frontmatter + body
  - build_l2 · project-level orchestrator · reads _l1/*.md · writes _l2/<project>.md
  - OLLAMA_URL / OLLAMA_MODEL env override · default Qwen 2.5 7B local
  - L2 stays OFFLINE nightly · NEVER on ingest path (core diff preserved)

tests/test_l2_distiller.py · 9/9 pass (all paths use use_ollama=False · no real Ollama call

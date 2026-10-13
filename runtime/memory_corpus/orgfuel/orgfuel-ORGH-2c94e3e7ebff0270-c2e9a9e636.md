---
name: orgfuel-ORGH-2c94e3e7ebff0270-c2e9a9e636
description: "commit d6c13ae97b50 2026-05-20 feat(v1.7): MEME-extension de"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-2c94e3e7ebff0270
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit d6c13ae97b50 2026-05-20
feat(v1.7): MEME-extension depends_on schema + transitive_close BFS recall
session_writer.py:
  - SYSTEM_PROMPT add 3 frontmatter fields (depends_on / declaration_type / supersedes)
  - ~12 prompt tokens overhead · distiller fills as free side-effect of summarization
  - no separate LLM call · black-box ingest invariant holds

mcp_server.py:
  - tool_ingest_obs: parse depends_on/declaration_type/supersedes args
  - emit dep_lines into session_*.md frontmatter
  - inputSchema: advertise 3 new args with enum/array typing

recall.py:
  - parse_memory_file: list-aware YAML parser (indented `- item` accumulates)
  - backward compatible: existing scalar fields unchanged
  - new: transitive_close(top, all_entries, max_depth=3) · BFS via depends_on
  - new: verify_ca

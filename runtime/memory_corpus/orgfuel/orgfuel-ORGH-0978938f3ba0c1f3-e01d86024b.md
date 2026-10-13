---
name: orgfuel-ORGH-0978938f3ba0c1f3-e01d86024b
description: "commit 132e9413d452 2026-05-22 feat(daemon): ingest action ·"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-0978938f3ba0c1f3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 132e9413d452 2026-05-22
feat(daemon): ingest action · platform direct-feed compass memory
v2.0.0 · S5 · adds 'action: ingest' handler on BGE daemon's TCP socket
protocol so platform agents (V5/V6/V7) can feed text directly into
compass memory without going through session_writer + LLM summarize.

Required request fields:
  - text (session content, < 500KB)
  - project (project slug · encoded cwd or platform tenant id)

Optional v1.7.1 lifecycle frontmatter (LLM-free promotion paradigm):
  - tier · working|episodic|semantic|procedural
  - decay_rate, forget_at, promote_after, reinforce_count

Handler:
  1. Writes .md to ~/.claude/projects/{project}/memory/ with frontmatter
  2. Embeds first 5000 chars via BGE-m3
  3. Updates in-memory cache + persists .pkl
  4. Returns {ok, path, emb

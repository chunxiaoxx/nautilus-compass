# Cross-project recall (`scope` parameter)

> Added in v1.4.0 · spec: `specs/SPEC-S3-cross-project-recall.md`

## Why this exists

Compass is project-scoped by default · each `~/.claude/projects/<name>/memory/`
is its own index. That isolation is what you want when working on
unrelated codebases (zenmind ↔ nautilus ↔ chunx).

But sometimes you want **lessons to follow you**. The 305-case fake-closure
pattern that surfaced in nautilus debugging applies just as well when
writing in zenmind or chunx. Black-box memory (raw text + dense embedding)
can union across projects because BGE-m3 is multilingual and the cosine
similarity doesn't care which folder the source lived in.

White-box memory layers can't do this cleanly — entity graphs from project
A have different entity IDs than project B; fact triples don't compose
across unrelated domains. Compass works because we never abstracted in
the first place.

## How

```python
from compass_mcp_client import MCPClient

c = MCPClient(host="127.0.0.1", port=9877, token=TOKEN, agent_type="v5")

# default · project-scoped (current behavior)
hits = c.call_tool("recall", {"query": "fake closure", "project": "C--Users-chunx"})

# v1.4 · cross-project · same user · all projects under ~/.claude/projects/
hits = c.call_tool("recall", {"query": "fake closure", "scope": "user"})
```

Per-result `project` field tells you which project each hit came from:

```
Recall · query='fake closure' · scope=user (all projects) · 5 hits
  · score=0.553 · 4h ago [C--Users-chunx] · session_xxx.md
  · score=0.519 · 5h ago [C--Users-chunx] · session_yyy.md
  · score=0.475 · 1d ago [zenmind] · session_aaa.md
```

## What gets scanned

Under `~/.claude/projects/`:

- ✅ Any directory with a `memory/` subdir
- ❌ Directories starting with `_` (e.g. `_platform_queue`, `_governance_audits`)

## Privacy

- `scope=user` only unions across **the same user's** projects (single token on cloud)
- It does **not** cross user boundaries · multi-tenant SaaS deployment retains isolation
- The session_*.md files themselves don't move · only the recall index is unioned in-memory

## Performance

Warm cache (typical 2-project setup · cloud daemon · 50 sessions per project):

- `scope=project`: ~1500ms
- `scope=user`: ~1600ms
- Ratio: ~1.07x

Cold cache (first scan of new project):

- ~2.16x · because BGE-m3 has to embed all entries from the newly-added project
- One-time cost · subsequent calls return to ~1.07x

If you have 5+ projects with high session counts, expect linear growth in
the union step. Top-k filtering at the end keeps response payload small.

## Use cases

**1. Cross-project lesson reuse (the main pain point)**

```python
# in zenmind project · about to use an LLM for memory extraction
c.call_tool("recall", {"query": "white-box LLM extraction caveats", "scope": "user"})
# returns lessons from nautilus debugging V5 anchor learner
# returns lessons from compass paper writing
# returns lessons from previous zenmind work
```

**2. Personal "memory across all my work"**

```python
# in any project
c.call_tool("recall", {"query": "what did I learn last week", "scope": "user"})
```

**3. Pre-action drift check across all corpora**

```python
# drift_check by default is also per-project · but you can pull cross-project anchors
# via session_*.md files tagged with shared thread_id (use thread_recall instead)
```

## When not to use `scope=user`

- **Performance-critical loops** (>100 recalls/min) · stick to `scope=project`
- **Multi-tenant SaaS** where users share an instance · use per-token scoping
- **Privacy-sensitive isolation** · e.g. work project should not pull from personal · use `scope=project` explicitly

## Out of scope (v1.4)

- Cross-user union (sensitive · won't ship)
- Per-project ACLs (project A can pull from B but not C) · would need an allowlist · revisit if asked
- Project aliases (rename a project · index doesn't auto-migrate) · v1.5 candidate
- Cross-project drift_check anchor union · v1.5 candidate

## Self-dogfood note (proof-of-recall)

When implementing v1.4 S3, I (compass-side maintainer) used compass to recall:

- `session_20260511-1244_close-loop-verification.md` · the close-loop verification flow
- `session_20260511-1750_v13-calibration-round-2.md` · drift_check calibration pattern

These informed the perf benchmark choice (warm vs cold cache discussed
above) and the privacy section structure. See git log for spec file
`specs/SPEC-S3-cross-project-recall.md` which was checked into compass
2 commits before this doc.

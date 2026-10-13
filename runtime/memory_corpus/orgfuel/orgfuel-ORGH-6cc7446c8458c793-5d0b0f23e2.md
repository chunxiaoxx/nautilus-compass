---
name: orgfuel-ORGH-6cc7446c8458c793-5d0b0f23e2
description: "commit 6b69200015e0 2026-05-21 ﻿feat(v1.7.1): S2 Layer 5 · n"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-6cc7446c8458c793
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 6b69200015e0 2026-05-21
﻿feat(v1.7.1): S2 Layer 5 · npx init + bun support + Opinionated EvoMap README
bin/compass-mcp.js (+130 LOC)
- New `npx nautilus-compass init` subcommand
- Creates .compass/ workspace · .env.template + anchors.json + claude-code-hooks.json + README
- Idempotent · skips if .compass/ exists
- 3 sample anchors · 4 Claude Code hook templates

package.json
- bun >=1.0 added to engines
- version 1.6.3 to 1.7.1
- description updated to Opinionated EvoMap framing

pyproject.toml
- version 1.6.3 to 1.7.1
- description updated

__init__.py
- __version__ 1.6.3 to 1.7.1 (aligned with 5 prior commits that tagged 1.7.1 in messages)

README.md (+70 lines)
- New section "What's new in v1.7.1 · Opinionated EvoMap"
- 5 new frontmatter fields verbatim (tier/decay_rate/forget_at

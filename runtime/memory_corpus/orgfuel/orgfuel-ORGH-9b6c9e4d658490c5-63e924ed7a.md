---
name: orgfuel-ORGH-9b6c9e4d658490c5-63e924ed7a
description: "commit 07d816c886c6 2026-05-06 npm · published as nautilus-c"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9b6c9e4d658490c5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 07d816c886c6 2026-05-06
npm · published as nautilus-compass-mcp@0.9.5 (no scope · @nautilus org not registered)
chose unscoped name to match PyPI sibling 'nautilus-compass' · clean
end-user UX:  pip install nautilus-compass / npm install nautilus-compass-mcp.
@nautilus org can be registered later for v1.0 if needed; rename then.

verified · curl registry.npmjs.org/nautilus-compass-mcp returns 0.9.5 latest

bulk-replaced @nautilus/compass-mcp → nautilus-compass-mcp in:
  · README.md (2 ref · install + MCP config example)
  · CHANGELOG.md (2 ref · highlight + Added)
  · npm/README.md (7 ref · install instructions + MCP examples)
  · npm/PUBLISH.md (2 ref · header + verify command)
  · npm/package.json (name field)

---
name: orgfuel-ORGH-36c2ae7e786dbfa6-a2b802fe83
description: "commit 1542944115a6 2026-05-08 package: rename npm @nautilus"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-36c2ae7e786dbfa6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 1542944115a6 2026-05-08
package: rename npm @nautilus/compass-mcp -> nautilus-compass; align author byline
Match Python package (pyproject.toml = nautilus-compass) and GitHub
repo (chunxiaoxx/nautilus-compass). Single user-facing name across
all three registries reduces install-command friction:

  npm install -g nautilus-compass     # was: @nautilus/compass-mcp
  pip install nautilus-compass        # already correct
  git clone .../nautilus-compass      # already correct

bin entry point unchanged (CLI is still 'compass-mcp'); only the
package name changes. Description extended to mention EverMemBench
44.4-47.3% and the 6 supported MCP clients.

author bumped from "Nautilus team" placeholder to:
  Chunxiao Wang <chunxiaoxx@gmail.com> (Yiluo Technology Co., Ltd.)

release-notes-1.0.

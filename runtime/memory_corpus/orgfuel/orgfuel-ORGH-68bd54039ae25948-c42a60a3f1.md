---
name: orgfuel-ORGH-68bd54039ae25948-c42a60a3f1
description: "commit 249d05ced809 2026-05-06 npm package · @nautilus/compa"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-68bd54039ae25948
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 249d05ced809 2026-05-06
npm package · @nautilus/compass-mcp v0.9.0-beta.1
- package.json: bin/compass-mcp · 7 included files · MIT · public access
- bin/compass-mcp.js: node wrapper spawning python mcp_server.py over stdio
  · cross-platform Python detection (python · python3 · py)
  · --self-check + --postinstall hooks
  · forwards SIGINT/SIGTERM · preserves exit code

npm pack: 20.4 KB tarball · 55.7 KB unpacked · 7 files
self-check: PASS (python detected · server file present)

Install path for end users:
  npm i -g @nautilus/compass-mcp
  → adds 'compass-mcp' to PATH
  → register in Claude Desktop / Cursor / Cline mcp.json:
    { "compass": { "command": "compass-mcp" } }

Blocked on: user must register @nautilus org on npmjs.com before publish

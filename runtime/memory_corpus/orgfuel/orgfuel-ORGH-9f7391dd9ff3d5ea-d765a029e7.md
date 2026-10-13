---
name: orgfuel-ORGH-9f7391dd9ff3d5ea-d765a029e7
description: "commit 30c3bbcbeaeb 2026-05-10 feat(ops): cstart PowerShell "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9f7391dd9ff3d5ea
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 30c3bbcbeaeb 2026-05-10
feat(ops): cstart PowerShell · one-command launch with cloud MCP tunnel
PowerShell function 'cstart <project>' that ensures SSH tunnel to
cloud:9877 is up, cds into the chosen project dir, then launches
claude --dangerously-skip-permissions. Eliminates the 3-step
ritual (ssh tunnel + cd + claude) into one command.

Projects: nautilus, vdr/venture, zen/zenmind, chunx, compass
Verbs: cstart <project> · cstart paths · cstop

Install via dot-source in $PROFILE. Tunnel persists across
sessions · cstop kills it when needed.

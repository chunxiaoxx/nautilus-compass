---
name: orgfuel-ORGH-279ff9d50ce85f9a-3a37555fa7
description: "commit 338437d64289 2026-05-11 release(v1.4.0): cross-projec"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-279ff9d50ce85f9a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 338437d64289 2026-05-11
release(v1.4.0): cross-project recall (scope=user) · self-implement S3
S3 spec acceptance criteria met:

daemon.py · _list_user_project_dirs() enumerates ~/.claude/projects/
  · skips '_' prefixed (platform internals: _platform_queue, etc)
  · handle_request gains scope param ('project' default | 'user')
  · scope=user · union entries across all mem_dirs · tag each with origin
  · top_k filter after union · fresh_extra dedup by (path, project) tuple

mcp_server.py · tool_recall forwards scope to daemon
  · backward compat: missing scope → 'project'
  · error: invalid scope rejected with helpful message
  · per-result project tag in output ([origin] decoration)
  · SERVER_VERSION 1.2.0 → 1.4.0

docs/CROSS_PROJECT_RECALL.md · use cases · privacy · perf · proof-

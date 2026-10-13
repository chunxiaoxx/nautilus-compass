---
name: orgfuel-ORGH-8fa8ceffc1634418-739579192a
description: "commit bba08db8febe 2026-05-08 mcp+handshake: BP1+BP3 flywhe"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-8fa8ceffc1634418
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit bba08db8febe 2026-05-08
mcp+handshake: BP1+BP3 flywheel stubs · submit_platform_task / ingest_platform_task_result
SaaS dialog identified 3 flywheel breakpoints between compass dialog and
platform V5 cycle (their session_20260508-1901_营销文章质量评估与平台-
代理飞轮断点分析). BP1 (compass→platform task channel) and BP3
(platform→compass result ingest) are OSS-side. This commit ships both as
file-based MCP tools so platform can start consuming today; HTTP mode
activates when COMPASS_PLATFORM_QUEUE_URL is set.

mcp_server.py:
- new tool submit_platform_task: writes JSON spec to
  ~/.claude/projects/_platform_queue/<task_id>.json. If env
  COMPASS_PLATFORM_QUEUE_URL is set, also POSTs to that URL with
  Bearer token from COMPASS_PLATFORM_TOKEN. File mode always written
  as audit fallback.
- new tool in

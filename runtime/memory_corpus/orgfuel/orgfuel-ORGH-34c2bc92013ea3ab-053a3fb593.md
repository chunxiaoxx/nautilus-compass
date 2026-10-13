---
name: orgfuel-ORGH-34c2bc92013ea3ab-053a3fb593
description: "commit fd1f59c82333 2026-04-30 feat: HTTP gateway + Docker d"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-34c2bc92013ea3ab
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit fd1f59c82333 2026-04-30
feat: HTTP gateway + Docker deployment for Nautilus platform agents
· compass_http.py · 290-line FastAPI · MCP-over-HTTP + plain REST
  - POST /v1/{recall,drift_check,feedback_log} · multi-tenant via X-Tenant-ID
  - POST /mcp/{initialize,tools/list,tools/call} · MCP 2024-11-05 envelope
  - GET /healthz /readyz · k8s probes
  - per-tenant feedback log: feedback_<tenant>.jsonl
  - access log: .cache/gateway_access.jsonl

· ops/Dockerfile · Python 3.12-slim · pre-bakes bge-m3 (toggleable)
  - dual-process container: daemon (TCP 9876) + gateway (HTTP 8765)
  - HEALTHCHECK against /readyz · 120s start_period

· ops/entrypoint.sh · launches daemon → waits for port 9876 → execs uvicorn
  - SIGTERM forwarding for graceful shutdown
  - daemon crash detection during st

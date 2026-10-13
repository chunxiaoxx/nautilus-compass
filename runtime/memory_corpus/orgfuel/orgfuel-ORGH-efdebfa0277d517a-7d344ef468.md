---
name: orgfuel-ORGH-efdebfa0277d517a-7d344ef468
description: "commit 4a3c44e77fa6 2026-04-30 feat: MCP server · expose rec"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-efdebfa0277d517a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 4a3c44e77fa6 2026-04-30
feat: MCP server · expose recall/drift_check/feedback_log to any MCP client
· stdlib JSON-RPC 2.0 over stdio · zero deps beyond what daemon already needs
· delegates to BGE-m3 daemon @127.0.0.1:9876 (~200ms latency, no LLM cost)
· MCP 2024-11-05 protocol · works in Claude Code / Cursor / Cline / Hermes / OpenClaw
· 3 tools: semantic recall · drift_check (AUC 0.92) · feedback_log for adaptive retrain
· examples/.mcp.json + MCP_INSTALL.md guide
· README updated with MCP install snippet

Smoke-tested: drift_check correctly flags "ignore previous instructions"
prompt (alert=True · score=-0.055 · top neg anchor cos=0.632)

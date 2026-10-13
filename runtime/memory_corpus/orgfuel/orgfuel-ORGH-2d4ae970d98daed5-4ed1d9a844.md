---
name: orgfuel-ORGH-2d4ae970d98daed5-4ed1d9a844
description: "commit 0e86ae007e3f 2026-05-08 docs+installer: per-agent onb"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-2d4ae970d98daed5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 0e86ae007e3f 2026-05-08
docs+installer: per-agent onboarding for Claude Code/Desktop, Cursor, Cline, Continue, Zed
docs/AGENT_ONBOARDING.md
- 6 agent platforms with copy-paste MCP config (Mode A · local stdio)
- 3 framework integrations: OpenAI Agents SDK, LangChain, LlamaIndex
  (Mode B · cloud A2A REST via compass.nautilus.social)
- 7 v1.0 tools listed with both-modes parity
- Verification + troubleshooting + reference architecture diagram

scripts/install_to_agent.py
- Auto-detect installed agents (probes 5 known config paths cross-platform)
- Per-agent yes/no prompt or --yes for batch
- Always backs up existing config before patching
- --dry-run to preview without writing
- Windows GBK encoding fixed via utf-8 stdout reconfigure
- Daemon liveness probe (TCP 127.0.0.1:9876)
- Con

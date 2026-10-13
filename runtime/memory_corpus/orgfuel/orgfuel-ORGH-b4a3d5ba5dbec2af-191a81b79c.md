---
name: orgfuel-ORGH-b4a3d5ba5dbec2af-191a81b79c
description: "commit c2cadf4d8c58 2026-06-24 docs(plan): durable MCP trans"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b4a3d5ba5dbec2af
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit c2cadf4d8c58 2026-06-24
docs(plan): durable MCP transport (EventStore + Last-Event-ID + watchdog)
Closes the MCP loop v1.8 auto-reconnect only band-aided. 6 TDD tasks:
EventStore ring buffer → server event tagging → Last-Event-ID resume
handshake → bridge replay → watchdog → E2E no-message-loss proof.
Lands in feat/v2.3.0-release BEFORE release per user decision 2026-06-24.

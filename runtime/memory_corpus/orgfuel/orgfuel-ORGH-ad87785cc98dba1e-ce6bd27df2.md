---
name: orgfuel-ORGH-ad87785cc98dba1e-ce6bd27df2
description: "commit 5c46c8cc88d3 2026-05-22 fix(recall): M2 · load-time ""
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-ad87785cc98dba1e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 5c46c8cc88d3 2026-05-22
fix(recall): M2 · load-time "真" emphasis filter at output layer
User flagged 2026-05-22 that L1 (CLAUDE.md ban list) + L3 (session_writer
SYSTEM_PROMPT) are behavioral rules · they depend on model self-control
and have a ~10 minute relapse half-life within a single session.

True mechanical cure requires removing the bad pattern from input/output
streams, not asking the model to self-correct.

This commit adds M2 (load-time mechanical filter):
  strip_zhen_emphasis(text) function applied to every memory body and
  description before they're printed to stdout, which gets injected into
  the downstream Claude Code session's system prompt via UserPromptSubmit
  hook.

Filter logic:
  · Preserve legitimate compounds (真的/真实/真正/真心/真理/真品/真切/真相/
    真意/真挚/真伪/真情/真假/真名

---
name: orgfuel-ORGH-ed6bc0e0f12b4473-4a2acf3e05
description: "commit fc8ff3eda8b7 2026-05-21 feat(v1.7.1): agentmemory fus"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-ed6bc0e0f12b4473
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit fc8ff3eda8b7 2026-05-21
feat(v1.7.1): agentmemory fuse · 9 lifecycle hooks (Phase 2 partial)
Extend stop_hook.py with 9 agentmemory-verbatim hooks · each emit
declaration_field-schema'd event to .cache/hook_events.jsonl · deterministic
· no LLM. Future-ready for Claude Code hook registration via settings.json.

· stop_hook.py: +140 LOC · 9 hook functions + _emit_lifecycle_event helper
  + HOOK_DISPATCH dict + dispatch_hook + --hook CLI flag (backward-compat)
· tests/test_hook_dispatch.py: 10/10 pass

9 hooks verbatim from agentmemory README (rohitg00 · 15.3K stars):
  SessionStart, UserPromptSubmit, PreToolUse, PostToolUse,
  PostToolUseFailure, PreCompact, SubagentStart, SubagentStop, SessionEnd

Default tier mapping (deterministic schema-driven · no LLM):
  · working: SessionStart

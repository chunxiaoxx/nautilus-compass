---
name: orgfuel-ORGH-a95fcd9a1b2ebf98-e51ee1c663
description: "commit 184d13d50af8 2026-05-22 fix(session_writer): ban "真" "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a95fcd9a1b2ebf98
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 184d13d50af8 2026-05-22
fix(session_writer): ban "真" as emphasis adverb in SYSTEM_PROMPT (source fix)
User flagged 2026-05-22 that long Claude Code sessions loading compass
session_*.md memories drift into a "真 X · 真 Y" emphasis-overuse style.
Source is the compass session_*.md corpus itself (30+ files since
2026-05-13) using "真" verbatim as a clarifying adverb.

Downstream sessions inhaling those memories at session-start internalize
the style within 5-10 turns. User correction has ~10 minute half-life
before relapse.

Fix is multi-layer; this commit is the source-level layer (L3):
  L1 · ~/.claude/CLAUDE.md global ban list (added 2026-05-22)
  L2 · feedback_no_zhen_emphasis_overuse memory (written 2026-05-22)
  L3 · session_writer.py SYSTEM_PROMPT explicit prohibition (THIS commit

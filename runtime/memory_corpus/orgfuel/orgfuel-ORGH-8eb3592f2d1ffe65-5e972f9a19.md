---
name: orgfuel-ORGH-8eb3592f2d1ffe65-5e972f9a19
description: "commit 14dd22b2b343 2026-04-29 paper: thorough adversarial-r"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-8eb3592f2d1ffe65
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 14dd22b2b343 2026-04-29
paper: thorough adversarial-review fixes (no hand-waving)
Self-critiqued the manuscript as 4 hostile reviewers. 2 P0 issues
identified · solved by code + paper changes (not just rewording).

P0-A · Train-test contamination
  - Added eval_drift_holdout.py: mines real prompts from Claude Code
    session jsonls, labels via Vertex AI Gemini Flash (independent judge),
    freezes to eval/holdout_v1.json (DO NOT MODIFY warning).
  - §3.5 step 4 explicitly acknowledges "in-set" vs "generalization".
  - §4.9 new section on held-out methodology and isolation properties.
  - §6.2 explicitly flags this as a known limitation.

P0-B · Detection accuracy ≠ behavior steering
  - Added eval_behavior_ab.py framework: pairs each deviation prompt
    with two responses (with/w

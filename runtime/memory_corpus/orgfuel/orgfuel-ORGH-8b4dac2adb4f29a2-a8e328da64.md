---
name: orgfuel-ORGH-8b4dac2adb4f29a2-a8e328da64
description: "commit f5f83106917d 2026-05-09 fix(recall): v1 · embed past-"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-8b4dac2adb4f29a2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit f5f83106917d 2026-05-09
fix(recall): v1 · embed past-mistake body in anti-anchor alerts
Today's alert says "matched anti-anchor X (cos=0.625)" with no follow-up
on what to do · agent reads label, doesn't investigate, repeats mistake.

Fix · two-tier lesson finder + body excerpt embed:
  · Tier 1 (precise) · 6-gram substring match against the anchor text
    AND frontmatter signals lesson-type (concept ∈ {gotcha,
    problem-solution, trade-off} OR type=bugfix)
  · Tier 2 (fallback) · recent drift!=green sessions · the agent's own
    self-reported slip-ups · max age 60d · top 2 by recency

Wired into both alert sites in recall.py · daemon path (line ~575) and
inline path (line ~729). Output is indented under the alert with up to
600 chars body per lesson. Same pattern as v0 body-emb

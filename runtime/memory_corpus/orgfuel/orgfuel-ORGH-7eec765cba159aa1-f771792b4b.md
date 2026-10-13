---
name: orgfuel-ORGH-7eec765cba159aa1-f771792b4b
description: "commit 4cffffef47e4 2026-05-08 changelog(1.0.0): sync with r"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-7eec765cba159aa1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 4cffffef47e4 2026-05-08
changelog(1.0.0): sync with release-notes · dual-run + cross-judge + 228 tests
Bring CHANGELOG.md [1.0.0] entry in line with release-notes-1.0.0.md
- Run 1 (44.4%) + Run 2 (47.3%) dual numbers + bootstrap CI + cross-run mean
- Gemini 2.5 Pro cross-judge result (28%) for honest sensitivity range
- Test count 187 → 228 (rc2 → 1.0.0; the +41 are the cross-judge runner
  + bootstrap script + stratified-sample harness)
- Repo-public note + license split (MIT + CC0 for anchors)

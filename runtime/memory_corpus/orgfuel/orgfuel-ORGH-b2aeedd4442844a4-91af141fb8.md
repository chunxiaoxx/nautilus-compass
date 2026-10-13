---
name: orgfuel-ORGH-b2aeedd4442844a4-91af141fb8
description: "工具决策记录 hand_geometry_recheck.py Independent recheck of flywh"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b2aeedd4442844a4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 hand_geometry_recheck.py
Independent recheck of flywheel hand-geometry findings (palm triple + thumb).

Input: any (N, 301) states.npy conversion artifact, right-hand = cols 154:301.
Expected values from _INBOUND_FROM_FLYWHEEL_20260905_hand_geometry_findings.md:
  palm_len median ~0.022 · bow ~0.035 · sin_ang ~0.44 · thumb_d min > 0.08

Usage: python tools/hand_geometry_recheck.py <states.npy>

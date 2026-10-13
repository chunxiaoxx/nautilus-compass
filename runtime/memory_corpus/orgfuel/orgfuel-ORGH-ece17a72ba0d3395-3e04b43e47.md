---
name: orgfuel-ORGH-ece17a72ba0d3395-3e04b43e47
description: "commit ff2d000ec075 2026-04-29 v0.7.1: F. cross-domain ancho"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-ece17a72ba0d3395
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit ff2d000ec075 2026-04-29
v0.7.1: F. cross-domain anchor profiles (legal/medical/finance)
3 domain starter packs (25+25 task-shaped anchors each):
- anchors_legal.json (contract/litigation/fiduciary)
- anchors_medical.json (clinical/Rx/consent)
- anchors_finance.json (trading/risk/compliance)

Updated recall.py:_select_anchors_path() with priority:
1. ZMM_ANCHORS_PROFILE=<domain> env var (explicit override)
2. cwd substring match (legal/medical/finance/zenmind/vc)
3. Default anchors.json

Smoke tests verified:
- legal aligned prompt -> score +0.020 (no false alert)
- legal deviation prompt -> score -0.110, alert fires
- medical deviation prompt -> alert fires

Known limitation: daemon caches one profile. Switching needs daemon restart.
v0.8 will support multi-profile daemon with per-q

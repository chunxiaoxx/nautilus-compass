---
name: orgfuel-ORGG-87dc680a8aa8075b-1318e2f1a2
description: "判读档判例 2026-06-03-p5-v14-poi-emission-design · e2e 验证证据 ## e2"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-87dc680a8aa8075b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission-design · e2e 验证证据
## e2e 验证证据
- Component 1:真 GET `/v1/v14/recall?agent_id=finalverify-2` → 3 candidate 行落 `/var/lib/compass/poi/poi_candidates.jsonl`(actor/memory/score 齐)
- Component 2:pull 27 candidates(finalverify-2×3 + unknown×24 真 V5 流量)→ reconcile DB 隧道连上 → settled=0(test/unknown actor 无平台 outcome · 正确)→ scheduled task `compass-poi-reconcile` Last Result 0
- 待 V5 加 `agent_id=nautilus-prime-001` → 那批 candidate join 平台 outcome → settle → cumulative_impact credit

---
name: orgfuel-ORGG-5fb6328aca8e1c50-bc03da93e6
description: "判读档判例 2026-06-03-p5-v14-poi-emission-design · 验证(verificatio"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-5fb6328aca8e1c50
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission-design · 验证(verification-before-completion)
## 验证(verification-before-completion)

- **C1 e2e**:拉起本地 9876 隧道 → `curl 'http://<8770>/v1/v14/recall?q=...&agent_id=test-poi-001&project=C--Users-chunx'` → SSH cat 云端 `poi_candidates.jsonl` 实证 `actor=test-poi-001` 行落地
- **C2**:`--dry-run` 跑 pull + reconcile,确认拉云 + 连 DB 通

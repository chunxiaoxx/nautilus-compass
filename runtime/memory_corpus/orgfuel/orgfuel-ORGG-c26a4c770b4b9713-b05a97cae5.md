---
name: orgfuel-ORGG-c26a4c770b4b9713-b05a97cae5
description: "判读档判例 2026-06-03-p5-v14-poi-emission-design · TDD 策略 ## TDD "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-c26a4c770b4b9713
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission-design · TDD 策略
## TDD 策略

- **C1**:patch 的 emit helper 作字符串常量 `EMIT_HELPER`,测试 `exec` 它进 namespace,断言 JSONL schema / 行数 / actor / 空-hits-不写。测的就是部署的代码,无 drift。
- **C2**:`pull_cloud_candidates` 的 dedup-merge 作纯函数单测(已有行 + 新行 → 去重)。

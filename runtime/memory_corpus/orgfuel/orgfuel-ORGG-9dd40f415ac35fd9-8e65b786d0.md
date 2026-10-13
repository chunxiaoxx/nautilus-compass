---
name: orgfuel-ORGG-9dd40f415ac35fd9-8e65b786d0
description: "判读档判例 JUDGING_EVIDENCE_TIERS_20261003 · 输出模板(verdict/回执/报告通用"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-9dd40f415ac35fd9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 JUDGING_EVIDENCE_TIERS_20261003 · 输出模板(verdict/回执/报告通用)
## 输出模板(verdict/回执/报告通用)

```json
{
  "finding": "陈述",
  "evidence_tier": "measured | inferred | unverifiable",
  "basis": "实测:命令+sha / 推断:依据链 / 不可验:缺什么",
  "upgrade_path": "推断→实测的验证方法(可写 null)"
}
```

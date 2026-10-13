---
name: orgfuel-ORGG-a3608cf48991c016-ade5d4f8da
description: "判读档判例 PRECOR_ORG_FUEL_V0_20261007 · 一、判例 schema(冻结) ## 一、判例 "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-a3608cf48991c016
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 PRECOR_ORG_FUEL_V0_20261007 · 一、判例 schema(冻结)
## 一、判例 schema(冻结)

```
{pf_id, event_date, domain, anchor_level(L0/L1/L2/L3),
 situation, judgment_or_action, outcome, outcome_source,
 verdict(有效/无效/不可验), evidence_tier(实测/推断/不可验), content_hash}
```

- anchor_level 判定:L0=物理执行结果/用户拍板/外部复算;L1=跨框互认/专家;L2=模型判(参考层,不进训练集);L3=无结果自述(剔除);
- domain 沿用 qid 前缀法(基础设施/lme/评测/组织协同…)。

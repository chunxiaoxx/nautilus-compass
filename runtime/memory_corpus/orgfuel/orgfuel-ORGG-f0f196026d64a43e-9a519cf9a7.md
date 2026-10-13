---
name: orgfuel-ORGG-f0f196026d64a43e-9a519cf9a7
description: "判读档判例 2026-09-22-assay-head-charter · 一 · 定义 ## 一 · 定义  **As"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-f0f196026d64a43e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-22-assay-head-charter · 一 · 定义
## 一 · 定义

**Assay-Head = 一个 Jev 式小判分头(0.6B 级),输入题卷三元组,输出三态+校准概率。**

```
输入: (starter_code, produced_diff, test_file_paths) → tokenized
输出: { verdict: agree | disagree | not_computable,
        confidence: calibrated probability,
        gate_fail_type: syntax | apply | test_fail | nc_missing_dep | clean }
```

角色=**预筛选**(pre-verdict):90% 显然没问题/显然有问题的卷子毫秒级分流;
10% 边缘案例走完整密码学管线(三门+人工终判)。**永不冒充 verdict**——输出
名 pre-verdict,终判权在判卷方,墙只认 verdict。

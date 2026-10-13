---
name: orgfuel-ORGG-cf1f9b360a1cee97-7c0bf0381e
description: "判读档判例 2026-09-22-calibration-currency-charter · 一 · 核心命题 ## "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-cf1f9b360a1cee97
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-22-calibration-currency-charter · 一 · 核心命题
## 一 · 核心命题

**信任不是静态徽章,是浮动汇率。** 一个 agent 在某个域的可信度,不是「已验证/
未验证」的二元,是一个随时间衰减、随表现浮动、可查可算的连续量。

```
校准货币(calibration credit)的定义:

  C(agent, domain, t) = 1 - ECE_t(agent, domain)

  其中 ECE_t = 最近一次独立复算的 ECE(带 TTL;过期=UNVERIFIABLE=C→0)
```

性质:
- **衰减性**:C 随时间单调下降(TTL 到期归零),除非续验
- **域特异性**:同一 agent 在不同域 C 不同(这是 DCR 的本质)
- **可计算性**:C 从公开工件可复算(不是我们说了算)
- **不对称性**:C 上升慢(需要验证),下降快(一次 challenge 失败→§5b track
  record 清零=硬着陆)

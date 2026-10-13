---
name: orgfuel-ORGG-5279c6f19e1015c9-cc294a76bc
description: "判读档判例 P0_FULL_PREREG_V2_20261002 · 5 · 勘注(构建后落,19:3x) ## 5 ·"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-5279c6f19e1015c9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 P0_FULL_PREREG_V2_20261002 · 5 · 勘注(构建后落,19:3x)
## 5 · 勘注(构建后落,19:3x)

- **F1b 口径细化(构建实测定稿)**:主判据=**每簇最大同构组 ≤25 条**(完美语义下簇内 top-5 的分母,直接决定可达上限);唯一文本率为副读数。理由:布尔作答的规则判定数据(如 TF 题"作答 False|金标 false|判 1.0")同构是数据本质,全文唯一率 95% 线对该形态过严;同构组才是 hit@5 上限的正确度量。**F2 主门槛(5%)不动**。
- **构建实况**:1454/1454 零未匹配回源;LME 匹配用 question 前 200 字符(anchor 侧截断所致,双向回溯断言保持);BC1 effect=逐题考生作答(selftest_answers*.json)+v1 审计行;F15=case 级三家读数(8 anchor 共 4 case,同构组=2 为数据本质);T3 保留 v0。anchor_v01 sha16=e710a70105df50e7。
- **可达性重估(v0.1 数据)**:最大同构组 1-5 条 → 完美语义桥下簇内命中≈5/组≈全中,整体上限>>5%,F2 门槛充分可达。

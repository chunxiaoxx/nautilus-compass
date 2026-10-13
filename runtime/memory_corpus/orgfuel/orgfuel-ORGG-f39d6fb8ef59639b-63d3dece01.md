---
name: orgfuel-ORGG-f39d6fb8ef59639b-63d3dece01
description: "判读档判例 P0_FULL_PREREG_V2_20261002 · 0 · 为什么要 v2(缺陷记录,如实) ## 0"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-f39d6fb8ef59639b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 P0_FULL_PREREG_V2_20261002 · 0 · 为什么要 v2(缺陷记录,如实)
## 0 · 为什么要 v2(缺陷记录,如实)

**v0 锚点 effect 侧(reason_span)是簇级模板句**:LME 五簇 1402/1454(96.4%)+BC1 v2 18+F15 8=1428 条整簇同一句(如 LME-V2 四簇全部="规则判定可复算可审计(非 LLM judge 自报)")。同簇 effect 向量全同→全簇共享同一 top-5→每簇至多命中 5 条→**锚点级 hit@5 数学上限≈43-56/1454≈3.0-3.9%<F2 门槛 5%,任何模型不可达**(A2v2"门槛数学不可达"同型病,本次在提取前抓住)。

**A2-v4 勘误**:其定谳"因果桥完全不在 BGE 层(hit@5=0.0)"归因不完整——effect 侧无样本级信号,BGE 从未有机会;shuffled 地板同为 0 与此吻合(真/伪 query 都是模板句)。RED 结论(P0-full 升级依据)维持,归因改写为"effect 侧无样本级信号,因果桥在数据层不存在"。

---
name: orgfuel-ORGG-c44b8d7b2a43b3fc-284460b499
description: "判读档判例 E1_FAILURE_ATTRIBUTION_20261009 · 六、H1 单独归因实验(同日深夜追加 ·"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-c44b8d7b2a43b3fc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 E1_FAILURE_ATTRIBUTION_20261009 · 六、H1 单独归因实验(同日深夜追加 · R438)
## 六、H1 单独归因实验(同日深夜追加 · R438)

> `tools/e1_h1_experiment.py` → A100 实弹 · 语料快照复制→合并 8 对同主题双文档(append 方式)→gold 重映射 1 条→同口径复跑 · 明细 e1_h1_result_20261009.json

### 读数 [实测]

| 指标 | 基线 | H1 后 | delta |
|---|---|---|---|
| R@1 | 0.4000 | **0.4333** | +3.3pp(+1 hit) |
| R@5 | 0.6667 | **0.6333** | **-3.3pp** |
| MRR | 0.4994 | **0.5197** | +2.0pp |

### 判读

1. **方向对、幅度不够**:M5 双文档互抢例证被合并吃下(该 query 升 HIT,+1),但 R@1 0.4333 距 0.60 门远——**H1 不单独过门**。
2. **append 合并有稀释副作用**[实测]:被并内容全文 append 使保留文档变长→向量漂移,「为什么 token 被清除」query 从 rank 4 恶化至 31,R@5 净跌。**改版假设 H1b:合并=差异精炼(只并增量教训)而非全文 append**——属内容编辑,收益不确定,候后置。
3. **剩余 near-miss 是跨文档主题相近**(判官升级 vs round1-day-log、实质诉求 vs launch-sprint 等)——非重复文档,H1 类去重原理上吃不下;**H2 rerank 从"假设"升为"必要件"**。
4. 污染查询 9 条照

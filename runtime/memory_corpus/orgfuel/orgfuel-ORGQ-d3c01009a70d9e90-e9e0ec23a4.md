---
name: orgfuel-ORGQ-d3c01009a70d9e90-e9e0ec23a4
description: "轮次记录 R438 · 2026-10-09 深夜(主件轮:H1 库侧去重单独归因✅[实测]——R@1 +3.3pp 不"
metadata:
  type: reference
  source: org_fuel:queue
  pf_id: ORGQ-d3c01009a70d9e90
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R438 · 2026-10-09 深夜(主件轮:H1 库侧去重单独归因✅[实测]——R@1 +3.3pp 不够门·append 稀释副作用实锤·H2 rerank 升必要件)
### R438 · 2026-10-09 深夜(主件轮:H1 库侧去重单独归因✅[实测]——R@1 +3.3pp 不够门·append 稀释副作用实锤·H2 rerank 升必要件)
- **主件=E1-TUNE H1 单独归因**(`tools/e1_h1_experiment.py`→A100 实弹):语料快照复制+合并 8 对同主题双文档(M5 对/7·22 会话拆分 5 对/goalmode 对/convergence 快照对;append 方式防丢内容)+gold 重映射 1 条+同口径复跑。
- **读数[实测]**:R@1 0.4000→**0.4333**(+3.3pp,+1 hit=M5 互抢例证被吃下)/R@5 0.6667→**0.6333**(-3.3pp)/MRR→0.5197(+2.0pp)——**H1 不单独过 0.60 门**。
- **三判读**:①append 合并有稀释副作用[实测](保留文档变长向量漂移,token 清除 query rank4→31,R@5 净跌)→H1b 差异精炼合并后置;②剩余 near-miss=跨文档主题相近非重复,H1 原理上吃不下→**H2 rerank 从假设升必要件**(过门主路径);③污染查询照旧 miss,工作集 v2 仍为判据前置。
- **产出**:E1_FAILURE_ATTRIBUTION 档追加§六(H1 实验段+判据建议稿修订:H1 降为前置清理不计过门归因)+e1_h1_result_20261009.json 归档。
- **附带·T5 节流生产实弹首例**:本值守轮一条用户消息注入单行节流标记

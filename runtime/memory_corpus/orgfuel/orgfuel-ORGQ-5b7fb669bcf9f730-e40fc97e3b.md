---
name: orgfuel-ORGQ-5b7fb669bcf9f730-e40fc97e3b
description: "轮次记录 R442 · 2026-10-09 深夜五(主件轮:E1-TUNE 终局定谳✅[实测]判据正本口径三门全过——"
metadata:
  type: reference
  source: org_fuel:queue
  pf_id: ORGQ-5b7fb669bcf9f730
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R442 · 2026-10-09 深夜五(主件轮:E1-TUNE 终局定谳✅[实测]判据正本口径三门全过——组合管线 R@1 0.8333/R@5 0.8333·E1 线收官)
### R442 · 2026-10-09 深夜五(主件轮:E1-TUNE 终局定谳✅[实测]判据正本口径三门全过——组合管线 R@1 0.8333/R@5 0.8333·E1 线收官)
- **主件=工作集 v2 重生成+终局评测**(E1 判据正本口径达成):生成器 v2 修清洗(R437 发现一闭环:BAD_MARKS 剥离+3 次重试+valid_query 拒空泛,候选池 3x)→**30/30 干净查询**(机械抽检零指令污染;人工注记 1 弱查询属难度谱)→三配置终局评测。
- **定谳读数[实测]**:基线 R@1 0.50/R@5 0.8333 · H2(+rerank) 0.80 · **组合(合并+rerank)=建议部署管线 R@1 0.8333/R@5 0.8333/MRR 0.8408——E1-TUNE v1 三门全过**(判据正本=v2 重生成口径,不再有过滤口径 caveat)。
- **两闭环**:①v2 基线 0.50>v1 表观 0.40=工作集污染拉低表观难度实锤;②干净口径 rerank 增益 +33.3pp>污染口径 +16.7pp——rerank 主收益结论正本口径下更强。
- **产出**:E1_FAILURE_ATTRIBUTION §九(终局定谳)+e1_final_verdict_20261009.json+A_plus_queries_v2 归档;生成器清洗纪律回写 tools/emb_gen_a_plus.py。
- **E1 线一夜五连收官**:R437 归因→R438 H1→R439 H2→R440 组合→R442 定谳。遗留

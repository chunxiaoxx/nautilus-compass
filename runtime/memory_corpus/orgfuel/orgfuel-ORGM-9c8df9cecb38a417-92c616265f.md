---
name: orgfuel-ORGM-9c8df9cecb38a417-92c616265f
description: "记忆条目 emb-bakeoff-bge-stays-20260925.md 2026-09-25 自家语料对拍定案(工"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-9c8df9cecb38a417
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 emb-bakeoff-bge-stays-20260925.md
2026-09-25 自家语料对拍定案(工件:runtime/emb_bakeoff_20260925/,预注册判据先行):

- 主指标 recall@5:qwen3-0.6b 仅 +0.46pt,<3pt 阈值 → 平局不换
- recall@1/MRR/中文口语切片现役 bge-m3 反优(+1.4/+0.8/+2.75pt)
- **MTEB 账面领先(Qwen3 高 ~7pt)在我们真实分布上不成立**——"别信榜单信自家尺"实证
- 天花板效应:109 档语料下 recall@5 双方 ≥99% 饱和,区分度只在 recall@1;语料扩到 1000+ 档应重测
- 决策原则沉淀:向量模型是管道不是护城河;只换不造(自研 ROI 负+自训自评违反反自指);daemon 切换另有隐性成本(全量重嵌+漂移基线作废)
- 方法复用价值:gen_queries.py(M3 从文档生 cn/en 双查询)+run_bakeoff.py(批量编码+矩阵排名)可套到任何候选模型

相关:[[minimax-coding-plan-provider]] [[bc1-and-loop-day-20260923]]

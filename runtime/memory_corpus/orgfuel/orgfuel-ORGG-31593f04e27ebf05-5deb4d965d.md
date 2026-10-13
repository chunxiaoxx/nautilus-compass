---
name: orgfuel-ORGG-31593f04e27ebf05-5deb4d965d
description: "判读档判例 PRECOR_ENACRE1_VERDICT_20261007 · 归因(负结果的价值在归因) ## 归因("
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-31593f04e27ebf05
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 PRECOR_ENACRE1_VERDICT_20261007 · 归因(负结果的价值在归因)
## 归因(负结果的价值在归因)

1. **训练量不对称**:各域片仅见 ~400 条域内数据+200 步;champion 全量 1454 条——B 片 loss 降至 0.0004=**域内过拟合**信号,泛化崩坏;
2. **评测集混合分布**:评测 qid 在域内有训练未见分布,域片见世面太窄;
3. 路由开销为零增益来源(逐域独立加载,排除切换噪声)。

**升级路径(判据修订序 v2 候选,非本轮)**:①域片全量多 epoch+早停;②路由粒度改 2 片(lme 合并);③或接受结论:**语料 ≥3000 前动态权重路线整体挂起**(与 7B 挂起同因同果——一切指向攒语料)。

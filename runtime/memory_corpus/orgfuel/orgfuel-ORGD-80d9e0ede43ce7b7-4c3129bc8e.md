---
name: orgfuel-ORGD-80d9e0ede43ce7b7-4c3129bc8e
description: "[### H · 记忆生产教训线(业界金矿 · 与我们过往经验直接可比)] | 来源 | 要点 | 我们的一手对应 | "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-80d9e0ede43ce7b7
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### H · 记忆生产教训线(业界金矿 · 与我们过往经验直接可比)] | 来源 | 要点 | 我们的一手对应 |
|---|---|---|
| [Cleric.ai 2026.7 "LLM judge scored worse than chance"](https://cleric.ai) | 无真值+用户反馈稀疏时,**pairwise 相对评分优于绝对评分** | 🔴同题:47/47 自不一致(绝对判分崩)→三门/重放(相对锚工件)=我们的解法;可互引 |
| [Mem0 论文 arXiv 2504.19413](https://arxiv.org/abs/2504.19413)(1000+引) | 记忆抽取/巩固/检索架构正式论文 | P2 引用位+我们三臂档案(16/11/18)是它的实测压力测试 |
| [supermemory 生产迁移案例](https://supermemory.ai) | Mem0→Supermemory 生产 A/B(失败/改进/评测方法) | 业界也走对照评测路线=三臂方法论同盟 |
| [mbrenndoerfer 2026.2](https://mbrenndoerfer.com) | 显式用户反馈("remember this")=重要性真值 | **=user_verdict 导出器的设计依据**(B 线欠账的理论支撑) |
| [Incremental Multi-Turn 记忆评测](https://arxiv.org) | 隔离记忆能力与推理/规划能力 | =BC1 设计原则(只考记忆不考推理)的同构 |
| HF papers:20% 噪声下稳健 | 稀疏噪声用户反馈的鲁棒性 | T2 真值稀缺→真值三级加权的又一依据 |

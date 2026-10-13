---
name: orgfuel-ORGQ-R88-3c437cc42c
description: "### R88 · 2026-10-03 22:4x(P3 因果倒置训练线复驰+paper3 立项轮) - **exp1"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R88
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R88 · 2026-10-03 22:4x(P3 因果倒置训练线复驰+paper3 立项轮)
- **exp1 challenger v2 发车**(用户令:不让 A100 空闲/持续开展因果倒置模型训练):全量 split_train 1162 条+champion 热启动+bf16 3 epochs lr1e-4;预注册实验判据(Δtest≥+1pt 且 REG-100 gold 翻转=0 记"首单热启动候选";记录不 promote 不触 delta 账本);同 session champion 基线 reg=0.9100/test=0.9128(全精度);预计 ~40min 出 exp1_summary.json
- launch 通道坑再犯再修:setsid nohup 后台进程占 ssh channel→`( ... &) `子壳+`</dev/null` 修(与 HANDOFF"发车/验证分 channel"纪律同款);exp1 实际一次发车成功
- **paper3 立项稿**:docs/papers/paper3_verification_first_outline.md——因果倒置论点(验证从产出下游搬到上游)/六段证据资产映射(全现成零新实验)/novelty 边界(对 paper1 为什么·paper2 怎么坏·paper3 谁来做)/对立面真诚三条预登记
- 下轮第一件:收 exp1 summary→读数判读(如实报);E1 材料死线 10/5 13:16
- M1:+0(实验线复驰+paper3 立项)

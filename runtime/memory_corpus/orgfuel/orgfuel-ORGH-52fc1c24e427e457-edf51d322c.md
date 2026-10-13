---
name: orgfuel-ORGH-52fc1c24e427e457-edf51d322c
description: "commit 32dd78f00cec 2026-08-31 feat(刀3④): d13 judge-retry 定案"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-52fc1c24e427e457
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 32dd78f00cec 2026-08-31
feat(刀3④): d13 judge-retry 定案——双域未过门,刀3 LoRA 路线关闭,d12 检索栈维持现役
- 根因坐实(单题诊断复现):doubao reasoning 吃满 max_completion_tokens=4096 预算→content 空(finish=length,16384 同样吃满),d13 零分=系统性偏 0 有偏估计非随机下界,6 试重试对此结构性故障必然全败
- 重判 100 题(ent 40+web 60)成功率 100%:ent 0.3081→0.4076(86/211,+0.46pt)· web 0.2875→0.3667(88/240,-0.03pt 持平)
- 预注册判据执行:双域均 <d12+5pt(门线 0.453/0.417)→ 刀3 全量验证路线关闭定案
- 口径披露:重判 low/16384;judge prompt=上游官方原版(xiaowu0162/LongMemEval-V2 直拉固化 rescued_upstream/,retry patch 证实不改 prompt;保留盘租机抢救取消,零成本)
- 事故披露:双进程并行重判 22 题重复(每题取首次,一致率 19/22=86%,敏感性 ±2 题不改定案);web RAW 笔误更正 0.2833→0.2875(69/240)
- GOAL_SSOT N5② 更新:d13 定案入账

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: H

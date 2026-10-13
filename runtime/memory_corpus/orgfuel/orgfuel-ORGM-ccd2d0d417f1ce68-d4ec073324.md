---
name: orgfuel-ORGM-ccd2d0d417f1ce68-d4ec073324
description: "记忆条目 arm-a-summary-layer-pass-20260903.md # A 臂(摘要层)终判 PASS "
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-ccd2d0d417f1ce68
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 arm-a-summary-layer-pass-20260903.md
# A 臂(摘要层)终判 PASS · 2026-09-03

**主判定:预注册三态全 PASS,双口径稳健。** e2e LongMemEval-S 500 题 overall 0.426 → **0.754 定案(9/4 重判 31/31 断连题补齐,每题均有真实判决;+32.8pt)**,4 天(ms 0.226→0.692 · ssa 0.250→0.839 · tr 0.158→0.624);ssp 终值 0.800=锚值零回退,此前一切"回退"证实为 judge 断连误判。

**Why:** 9/2 诊断"97% 错题 gold 已在 top5=组装层负全责"被证实——纯 context 工程(逐会话摘要卡+日期锚时间线,路由 ms/tr/ssa 三型)零检索改动零训练拿下。验证了"瓶颈在组装不在检索"的归因方法学。

**How to apply:**
- 两类口径披露:71 题(14%)judge 断连(newapi glm 间歇 403)重跑仍复发=基础设施噪声;保守口径(按错计)与干净口径(剔除)结论同向。对外发保守口径 70.0%,脚注干净口径。
- ssp "-5pt 回退"=n24 二项噪声带(差 1.5 题),中期版"-20pt"已证实是断连误判假象。小样本型的回退判断必须算噪声带。
- 落盘分片会静默缺尾(s168 段 70 题没写盘)——聚合判定前必对账 unique 数 vs 应有数。
- 产物:`vtf/_e2e_diag/arm_a_final_verdict.md` + `arm_a_final_verdict_raw.json`;README e2e 段/对比表已刷(commit 本轮);GOAL_SSOT N5① 已更新。
- 下一步:三池设计

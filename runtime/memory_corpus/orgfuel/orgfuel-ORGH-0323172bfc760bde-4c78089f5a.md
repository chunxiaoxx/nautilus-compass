---
name: orgfuel-ORGH-0323172bfc760bde-4c78089f5a
description: "工具决策记录 fuel_qc_batch.py N2 燃料周批 QC(GOAL_SSOT 无悔层 · 每周五跑 · 心跳"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-0323172bfc760bde
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 fuel_qc_batch.py
N2 燃料周批 QC(GOAL_SSOT 无悔层 · 每周五跑 · 心跳可催)。

对 pending/ 候选执行 Gate B 方法 QC:
1. 过期清理:>14 天未 QC 的候选移入 expired/(记录,不删)。
2. 盘点输出:pending 数 / 本周新增 / 最老候选年龄 → stdout + 写周报 obs。
3. 逐条 QC(需 agent 会话执行,本脚本只做队列卫生与盘点):
   候选 → 提炼自然语言问题 → 裸模型 control 测(control 先失败才可能③类)
   → 失败=有 headroom 候选 → build Gate B suite 验 Gold → 过门转正入池。
判据(GOAL SSOT N2):月增 ≥10 条③类过门燃料。

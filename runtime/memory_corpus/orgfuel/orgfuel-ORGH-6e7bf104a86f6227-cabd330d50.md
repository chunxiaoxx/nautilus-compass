---
name: orgfuel-ORGH-6e7bf104a86f6227-cabd330d50
description: "工具决策记录 fuel_intake.py N2 燃料入池 · stop hook 自动提炼(GOAL_SSOT 无悔层"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-6e7bf104a86f6227
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 fuel_intake.py
N2 燃料入池 · stop hook 自动提炼(GOAL_SSOT 无悔层 · 2026-08-23)。

每个 session 结束(stop hook 调用)跑一次,0-LLM:
1. 找最新 session_*.md(全部项目,同 stop_hook.py 的找法)。
2. 按模式提取"教训段"(根因/踩坑/必须/WinError/修复 等信号词所在段落)。
3. 去重(与 fuel_pool log 的 content_hash 比对)后写 pending 候选:
   vtf/fuel_pool/pending/<ts>_<slug>.md  · frontmatter 带 source_session 溯源。
4. 周批 QC(tools/fuel_qc_batch.py / 每周五):Gate B 方法 control-先失败门,
   过门才转正入 vtf/fuel_pool/。候选 14 天未 QC 自动过期(防狗熊掰玉米)。

红线:只提炼结构化信号,不改写原文;PII/买方名不过滤逻辑留 QC 批(人工核)。

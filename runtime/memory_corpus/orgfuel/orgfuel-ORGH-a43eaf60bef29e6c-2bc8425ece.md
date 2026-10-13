---
name: orgfuel-ORGH-a43eaf60bef29e6c-2bc8425ece
description: "工具决策记录 verdict_hook.py verdict-hook · run verdict 自动提炼进燃料 pe"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a43eaf60bef29e6c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 verdict_hook.py
verdict-hook · run verdict 自动提炼进燃料 pending 池(双环回流 · P0)。

fuel_intake.py 只覆盖 session 结束;评测/训练的 verdict 产物(aggregated_metrics、
裁决 evidence)没有回流——本 hook 补上:扫描 vtf/ 下 verdict 特征文件,
0-LLM 提炼"配方知识"条目,走与 fuel_intake 同一条 pending→Gate B QC→入池管道。

触发:评测收尾固化流程手动调用 `python tools/verdict_hook.py`
(后续可在 stop hook 追加一行,先独立跑稳)。

扫描范围(v0):
  1. 任意目录下的 aggregated_metrics.json(评测 run 产物)
  2. 路径含 evidence 或 verdict 的 .json/.md(裁决文档)
去重:内容 hash(与 fuel_intake 共用 intake_log.jsonl)+ mtime 游标
(verdict_cursor.json,只处理新增/变更文件)。

红线:只提炼结构化信号,不改写原文;PII/买方名过滤留 QC 批(与 fuel_intake 同约)。

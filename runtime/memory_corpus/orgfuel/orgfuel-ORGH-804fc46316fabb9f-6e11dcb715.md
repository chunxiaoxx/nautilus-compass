---
name: orgfuel-ORGH-804fc46316fabb9f-6e11dcb715
description: "工具决策记录 memx_attribution.py MEMX 站3 · 因果倒置三向归因器 v0(R398)。  输入"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-804fc46316fabb9f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 memx_attribution.py
MEMX 站3 · 因果倒置三向归因器 v0(R398)。

输入失败事件文本,对记忆库做两路探测(recall+dedup 宽扫),输出三向归因:
  A 记忆缺口   — recall 空 且 dedup unique      → 产出定向补写任务
  B 记忆错误   — recall 有命中但 fact_status 弱 → 产出降级+勘误任务
  C 检索失效   — recall 空但 dedup 命中(存在未召回)→ 产出 E1 调优信号
  NONE 非记忆因 — 命中且 fact_status=measured(行为层问题,出记忆域)
归因记录追加 runtime/memx/attributions.jsonl。判据零放宽:归因只分类,不改记忆。

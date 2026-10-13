---
name: orgfuel-ORGH-11a149dfd9326945-5c5170bcad
description: "工具决策记录 p3_ticket.py P3 S2 · 训练单生成器(触发门槛+预注册式训练单)。  设计档 §三:触发"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-11a149dfd9326945
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 p3_ticket.py
P3 S2 · 训练单生成器(触发门槛+预注册式训练单)。

设计档 §三:触发判据=delta 累计新增带白名单标签 ≥200(只许更严);
不足则本轮 SKIP 入 ledger,不攒人情。训练单 JSON=当轮 mini 预注册
(delta sha/基线 adapter/REG-100 sha/冻结超参/成本上限/判据引用)。
用法:python tools/p3_ticket.py

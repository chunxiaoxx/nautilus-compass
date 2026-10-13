---
name: orgfuel-ORGH-fe9cbb592e68de89-41ebb24d88
description: "工具决策记录 e1_failure_attribution.py E1 检索调优第一刀: A+ 查询失败样例归因(R43"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-fe9cbb592e68de89
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 e1_failure_attribution.py
E1 检索调优第一刀: A+ 查询失败样例归因(R436 · 工作集 A_plus_queries.json)。

口径与 eval.py 完全一致(bge-m3 CLS 池化+normalize+MAXLEN 512+parse_md 同款)。
输出: R@1/R@5/MRR 对齐预注册 + 逐条失败明细(gold rank/sim + top1 信息 + 查询特征)。

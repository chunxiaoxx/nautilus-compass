---
name: orgfuel-ORGM-judge-lessons-20260926-b7275db2d9
description: "--- name: judge-lessons-20260926 description: 判分方法论两课——全部判定门"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-judge-lessons-20260926
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: judge-lessons-20260926
description: 判分方法论两课——全部判定门原则+判绩账双向价值(评委也会错被复核抓)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 09bcfcba-392a-4334-9087-6ea8f23b88f4
  modified: 2026-09-26T10:13:28.545Z
fact_status: inferred
---

2026-09-26 一天内两次实证同一课:

**Why**:判分 owner 首件(τ-bench 判因)我判"评测器假阴性×5",v5 复核推翻——τ-bench
判分有两道门(终态 hash+outputs 答案串逐字复述),我只验了写动作+第一道门,漏了
第二道。真相=「结果传达失败」新判因类(agent 做对了没说出来,如 task4 该答"10"
只复述了差价)。同日早些时候 T3 复算抓我方报告层 6 处转写错。

**How to apply**:
1. **机械判因/审计前,先枚举判分器的全部判定门**(读评测器源码列出门清单),
   每道门都要单独验证——验一门≠验全部
2. 复算独立性的可行梯度:全新人机会话 > 独立 claude 子进程(盲标真盲)>
   本会话直跑(禁止)——子进程方案配方见 [[bc1-launch-eve-20260926]]
3. 评委/复算员自己也在判绩账里:被复核推翻不是丢脸,勘误留档(勘误记录段+
   双报口径)才是完整交付——T3 勘误函反而成信用资产
4. 「结果传达失败」类与 BC1 DIM3 假绿识别互补,已进靶向题四类(9/29 出卷)

相关:[[rsi-loop1-recompute-verdict-202

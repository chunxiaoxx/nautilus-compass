---
name: orgfuel-ORGM-f813e56611adbcbb-e239a707ff
description: "记忆条目 judge-lessons-20260926.md 2026-09-26 一天内两次实证同一课:  **Why"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-f813e56611adbcbb
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 judge-lessons-20260926.md
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

相关:[[rsi-loop1-recompute-verdict-20260914]](同型:复算抓自报绿)

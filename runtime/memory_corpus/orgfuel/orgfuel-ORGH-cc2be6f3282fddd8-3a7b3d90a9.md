---
name: orgfuel-ORGH-cc2be6f3282fddd8-3a7b3d90a9
description: "工具决策记录 demo_d1.py Demo D1 driver · cross-session memory (dem"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-cc2be6f3282fddd8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 demo_d1.py
Demo D1 driver · cross-session memory (demo_recording_script.md 的可执行版).

60-90s 录屏用:写入三个"会话"→跨会话提问→空空间对照组。
走本地 daemon 9876(全本地叙事),token 同 stop_hook 配方。

Usage:
  python tools/demo_d1.py write 1|2|3   # 三次,每次一条"会话"事实
  python tools/demo_d1.py ask           # 跨会话问题(只有 session-1 能答)
  python tools/demo_d1.py control       # 空间对照组:同 query 打到空 project
  python tools/demo_d1.py reset         # 清掉 demo project,可重录

---
name: orgfuel-ORGH-a2f49b70c9b3fb52-d9f28a56da
description: "commit 5dddc5f9f31b 2026-09-05 feat(marketing): PPT v2 深色可视化"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a2f49b70c9b3fb52
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 5dddc5f9f31b 2026-09-05
feat(marketing): PPT v2 深色可视化版——13 张数据图表+架构图+终端 demo 图全嵌入
用户判 v1'平铺直叙零视觉'。matplotlib 深色主题(GitHub dark)出图:
- 盲目下注示意/六层架构/成本曲线/读取端管线
- e2e 42.6→75.4(81.6 双口径)/六分型/P@1 对打/EverMemBench/LME-V2/延迟 80×
- 判官 5 事故卡片/dogfood 甜甜圈/demo 终端模拟(与录屏脚本同源)
数字全走 SCOREBOARD 定案口径;marp 重渲染 pptx 3.9MB/19 页,zip 抽验媒体全嵌入
重出:npx @marp-team/marp-cli pitch_deck_outline_20260904.md -o pitch_deck_20260904.pptx --allow-local-files

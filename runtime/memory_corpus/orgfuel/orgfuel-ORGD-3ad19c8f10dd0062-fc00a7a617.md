---
name: orgfuel-ORGD-3ad19c8f10dd0062-fc00a7a617
description: "[### 轮 18 补 · 2026-09-25 21:5x(**外部基线首跑完成,提前一天**)] - 进展:mem0"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-3ad19c8f10dd0062
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 轮 18 补 · 2026-09-25 21:5x(**外部基线首跑完成,提前一天**)] - 进展:mem0 双臂全量跑完(18 题×2 臂,MiniMax-M3 backbone,零错误)——**direct 16/18 vs mem0 11/18,记忆管线掉 5 分;DIM3 复发识别 4/4→1/4 塌点**;失败解剖实锤:写入时语义压缩丢机器可检字段(artifact=null);BASELINE_REPORT 落档+发布页外部基线段已并入;T41-0 反向案例(记忆臂答出直连弃答题)如实记录
- 问题分析:这个结果本身就是 BC1 的卖点实证——"你的记忆系统会不会也在这样丢分"从口号变成带工件的数据;诚实边界已写(n=1/单 backbone/mem0 默认配置)
- M1:0 不变(基线=内容资产,非外部请求)
- 下轮:9/26 T3 复算新会话(12:00)→执法器施工(18:00 判据)→9/27 09:00 发布日机械腿

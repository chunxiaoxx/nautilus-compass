---
name: orgfuel-ORGF-fb45848b4c33d3cc-d07ffb2e5e
description: "flywheel 档案 loop_night_R151_20261008.md # LOOP 值守轮 R151 留痕 2"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-fb45848b4c33d3cc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 loop_night_R151_20261008.md
# LOOP 值守轮 R151 留痕 2026-10-08 10:5x(QC17 帧检开跑收官轮)

> 用户令"继续推进(QC 管道 17 集帧检开跑)"。中心环=QC17 帧级质检,当轮出读数。

## 本轮动作
1. **QC17 帧检全链收官**(下载→扫描→报告当轮闭环):
   - 扫描器 scripts/_qc17_frame_scan.py(实例侧跑):四类病灶=黑帧/冻结/过曝/可解性,时间窗取 _qc17_ep_video_map.json per-cam from/to;抽帧 step=fps//6。
   - **60/60 流全解,0 失败**;verdict=**WARN**(非 FAIL);黑帧全 0/过曝 0/时长正常。
   - **核心发现=冻结病群**:32 流超 30% 阈,涉 18/20 集;冻结比 median 30.7%/mean 36.9%/max 100%(ep567 左腕/ep8850 右腕/ep3816 右腕 97%/ep18204 右腕 96.6%)。
   - 判读(如实,不过度归因):robwin_unified 采集侧大范围静止段(策略等待/失败重试/演示停顿)或帧复制编码——与 Meta/ 官方 0 声明一致性问题;腕相机冻结率系统性高于头部相机(抽样肉眼 ep567 左腕全静止段成立)。**此即 QC 管道价值实锤:官方 unified 版无此标注,下游训练若不筛将吃进大量静止帧。**
   - 报告落仓 runtime/qc17_robotwin/qc17_report.json(60 流逐行+32 警告清单)。
2. 覆盖 16→17 集达成(周报#2 素材+1);data 面挂载候 bench 迁移协同一并安排(10531 

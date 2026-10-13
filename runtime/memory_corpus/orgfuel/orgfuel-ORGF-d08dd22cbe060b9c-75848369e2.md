---
name: orgfuel-ORGF-d08dd22cbe060b9c-75848369e2
description: "flywheel 档案 loop_night_R148_20261008.md # LOOP 值守轮 R148 留痕 2"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-d08dd22cbe060b9c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 loop_night_R148_20261008.md
# LOOP 值守轮 R148 留痕 2026-10-08 07:4x(QC17 发车轮)

> WEB-SYS 值守 cron 轮。中心环=QC17(robotwin_unified)视频下载发车。

## 本轮动作
1. **例行**:信箱 0/外环双 CLEAN。
2. **QC17 发车**(链路复活后第二挂件):
   - 路径模板破译:v2.1 meta=**file 制视频**(videos/{cam}/chunk-{c:03d}/file-{f:03d}.mp4),与冻结清单 chunk/file 字段一一对齐;三相机=cam_high/left_wrist/right_wrist;全 dataset 视频仅 200MB。
   - 生成 57 件 aria2 批量清单(19 唯一 (chunk,file) 对×3 相机,20 集中 2 集共享 file-134);aria2c -c -x8 -j3 无限重试发车(PID 3974745,log=_qc17_dl.log);首件 file-005×3 相机已落盘。
3. SSH 抖线一次(电信线已知病,降频重试即通);bash 会话 cwd 反常一例(相对路径 find 失灵,绝对路径全绿)——配方:实例侧一律绝对路径。

## 下轮
QC17 下载收件(57 件全数校验)→QC 管道跑 17 集(帧级检查链)→data 面覆盖 16→17;engine_ver 字符串修;R1 判级正式轮。

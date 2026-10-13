---
name: orgfuel-ORGF-65a2d44c42a9bf50-cf226ff5e8
description: "flywheel 档案 loop_night_R104_20261006.md # LOOP 候守轮 R104 留痕 2"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-65a2d44c42a9bf50
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 loop_night_R104_20261006.md
# LOOP 候守轮 R104 留痕 2026-10-06

## ①信箱:未读 0/OPEN 0

## ②实例与管道
- **EGO 残进程清案**:EGO_NOT_RUNNING(自然退场或前次 kill 已中)+ **pkill -f 自匹配 ssh 串杀自己 shell 的诊断证实**(bracket 技巧 `dl_egodroid_v1[.]py` 输出回通)——与 gpu-rental 记忆原坑一致,配方补条:远程杀进程必用 bracket 技巧或精确 pid
- **DROID 结构确认**:标准 LeRobot v2(meta/info.json+tasks.parquet+episodes/chunk+data/chunk parquet,443M)——原生可吃

## ③主力件:QC 计量链接入前测绘
- qc_pipeline.py=视频四检件(黑帧/冻帧/模糊/人脸,PyAV+OpenCV)——适用视频输入
- droid_100=parquet 数据集 → 计量走 console_pipeline(接口下轮读,跑在实例域 venv)
- 抽样规则维持 R100 预登记(已下载 7 数据件全样本,无挑拣)

## ④留痕:本件+loopdiff r104

## ⑤外部触达 0;拍板六项不变

## 下轮:console_pipeline 接口读→DROID 第 16 集计量首跑(实例域)

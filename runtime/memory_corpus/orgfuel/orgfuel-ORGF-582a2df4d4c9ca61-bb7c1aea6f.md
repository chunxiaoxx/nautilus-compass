---
name: orgfuel-ORGF-582a2df4d4c9ca61-bb7c1aea6f
description: "flywheel 档案 _droid100_qc_report_v1.md # 数据计量单 v0 · droid_100"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-582a2df4d4c9ca61
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 _droid100_qc_report_v1.md
# 数据计量单 v0 · droid_100_v1

> 生成 2026-10-06 07:45:08 · manifest_sha db9a6dce07babd88 · 全部读数可复算(工件 sha 锚定,重放=flypipe report)

**批次**:3 路 / 6442.41s
**LeRobot**:87301a2d2e99340e2010c9ef0f1d8e780b08aaf9 · vv3.0 · 100 episodes · 15 fps · 47 任务

## 一、质量维(四检机判,可复算)

| PASS | WARN | FAIL | ERROR |
|---|---|---|---|
| 2 | 1 | 0 | 0 |

读数分布(mean/max):
- black_ratio: 0.0041 / 0.0123
- freeze_ratio: 0.0011 / 0.0025
- blur_norm: 1992.2333 / 2536.2
- face_ratio: 0.0002 / 0.0005
- 锚批对照:created

## 二、合规维(脱敏)

- L0 凭证扫描:jsonl 0 件,命中行 0(零命中)
- L1 人脸脱敏:检出 0 路,打码 3 路,复检残留 0(零检出)

## 三、标注维(手部 21 关键点,MediaPipe)

- **未标**——本批无帧目录(纯视频批)或 mediapipe 未装,不虚报

## 四、语义维(免费视觉模型)

- **未标**——SEMANTIC_PROVIDER 未启用(off=不虚报)

## 五、效用维

- **未评**——V4 探针层待 G1 标定实验上岗(预注册 docs/plans/2026-09-3

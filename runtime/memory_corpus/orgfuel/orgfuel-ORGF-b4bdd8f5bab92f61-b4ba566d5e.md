---
name: orgfuel-ORGF-b4bdd8f5bab92f61-b4ba566d5e
description: "flywheel 档案 2026-10-05-gr00t_gr1_qc_v0计量单-v0.1效用回填.md # 数据计量"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-b4bdd8f5bab92f61
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-10-05-gr00t_gr1_qc_v0计量单-v0.1效用回填.md
# 数据计量单 v0 · gr00t_gr1_qc_v0

> 生成 2026-10-05 17:38:08 · manifest_sha 2d05b15a23f5ab74 · 全部读数可复算(工件 sha 锚定,重放=flypipe report)

**批次**:1206 路 / 19128.7s
**LeRobot**:gr00t_gr1_cansort · vv2.0 · 1000 episodes · 20.0 fps · 3 任务

## 一、质量维(四检机判,可复算)

| PASS | WARN | FAIL | ERROR |
|---|---|---|---|
| 1206 | 0 | 0 | 0 |

读数分布(mean/max):
- black_ratio: 0.0 / 0.0
- freeze_ratio: 0.0701 / 0.25
- blur_norm: 2658.4915 / 2750.7
- face_ratio: 0.0 / 0.0
- 锚批对照:created

## 二、合规维(脱敏)

- L0 凭证扫描:jsonl 4 件,命中行 0(零命中)
- L1 人脸脱敏:检出 0 路,打码 1206 路,复检残留 0(零检出)

## 三、标注维(手部 21 关键点,MediaPipe)

- **未标**——本批无帧目录(纯视频批)或 mediapipe 未装,不虚报

## 四、语义维(免费视觉模型)

- **未标**——SEMANTIC_PROVIDER 未启用(off=不虚报)

## 五、效用维

- G1 判读(compass compass g1_judge_v3 · 2026-10-03T11:55:08):

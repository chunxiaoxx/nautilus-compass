---
name: orgfuel-ORGD-940b24d8a503685e-3bed3356ec
description: "[## 案 11 · V4 效用闭环探针判读案(分辨率单变量隔离+J2 判定权边界)] - **EGR 三发**:gap"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-940b24d8a503685e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 案 11 · V4 效用闭环探针判读案(分辨率单变量隔离+J2 判定权边界)] - **EGR 三发**:gap_layer=data——60 对样本量卡住效用维终判;扩集≥200 对与 J1b 同池复用(一池两判)。
- **边界**:未预注册的检验法不进判定只作并陈证据;resolution_check/franka_diving 作为互证材料在链,aloha_ins_qc_v0/xarm_qc_v0 无函不抢判(问询函 2930 已发)。
- **verdict 正本**:`runtime/v4_probe/v4_probe_verdict_v2.json`(schema v2.1 compliant,一次通过)
- **复算**:`python tools/verdict_schema_v2.py validate runtime/v4_probe/v4_probe_verdict_v2.json`;detail 逐行计数+McNemar/Wilson 随 verdict readings 段可查。

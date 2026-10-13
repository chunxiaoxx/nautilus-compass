---
name: orgfuel-ORGG-f465d442db73691e-181dc726be
description: "判读档判例 JEV_CVSCREEN_CALIBRATION_PREREG_20261001 · 二 · Item Se"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-f465d442db73691e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 JEV_CVSCREEN_CALIBRATION_PREREG_20261001 · 二 · Item Set 与 Key 构建(步骤2,只用 manifest+policy,零模型输入)
## 二 · Item Set 与 Key 构建(步骤2,只用 manifest+policy,零模型输入)

- 每件 CV 一个 item:pdf_to_text 抽取文本 → 按 src/policy.ts 的默认六维度出题(noul/choice/score 三原语)
- **Key 来源(固定顺序)**:manifest.files[].profile 意图描述 + cv-screen/README.md + src/policy.ts + src/presets.ts
- Key 文件:runtime/typesafe_jev_cvscreen/answer_key.json(qid=file 名+维度;每维度预期值+依据=profile 原文短语)
- **Key commit 时间戳必须早于任何 Jev 调用**(github commit 为证)
- 不确定项处理:manifest 无对应字段 → key 记 "U"(insufficient_evidence),不强猜

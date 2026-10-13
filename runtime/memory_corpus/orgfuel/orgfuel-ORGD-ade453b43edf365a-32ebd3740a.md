---
name: orgfuel-ORGD-ade453b43edf365a-32ebd3740a
description: "[## 案 10 · gen4_v2 B 轨二分类判读案(EGR 回流首闭环+多数类基线 caveat)] - **三件"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-ade453b43edf365a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 案 10 · gen4_v2 B 轨二分类判读案(EGR 回流首闭环+多数类基线 caveat)] - **三件裁决**(回函 2918):①J1b 初步通过成立(判据零放宽+caveat 并陈,终判=人工金标抽检 20-50 例+扩集≥200 对)②H2 定谳③A 轨暂不发车(建议顺序=判例→金标抽检接判官市场→粒度阶梯新案按需发车)。
- **EGR 二发**:gap_report{gap_layer=data:评测集侧缺口(弱标=MediaPipe 自动口径未标定+样本量)}——suggested_fuel 三条,confidence=measured。
- **边界**:多数类基线对照作 caveat 权重证据并陈,不进判定(判据零放宽,lock 语义=点估计过线+CI caveat);抛硬币基线 0.5 vs 多数类 0.7833 口径在函件中精确化(函称事故卷"≈随机基线"需勘正)。
- **verdict 正本**:`runtime/gen4v2_btrack/gen4v2_btrack_verdict_v2.json`(schema v2.1 compliant;含 statistics 段——verdict.text 提及显著性数字即触发 L4 检查的机构自律样本)
- **复算**:`python tools/verdict_schema_v2.py validate runtime/gen4v2_btrack/gen4v2_btrack_verdict_v2.json`;log 逐条计数脚本随 runtime/gen4v2_btrack/(log 本体实例侧锚 sha16)。

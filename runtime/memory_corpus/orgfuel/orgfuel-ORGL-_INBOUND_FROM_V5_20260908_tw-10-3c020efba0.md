---
name: orgfuel-ORGL-_INBOUND_FROM_V5_20260908_tw-10-3c020efba0
description: "## 提议:盲区定理嵌入版(论文 2 的自然续作,VerifyPack 验收实验)  复用论文 2 的 2,600 次真"
metadata:
  type: reference
  source: org_fuel:letters
  pf_id: ORGL-_INBOUND_FROM_V5_20260908_tw-10
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

## 提议:盲区定理嵌入版(论文 2 的自然续作,VerifyPack 验收实验)

复用论文 2 的 2,600 次真实调用语料:案例嵌入→测几何分类器能否复现判官裁决。
预期:实体替换类线性可分,±0.1% 扰动不可分→**嵌入盲区比判官输出盲区更宽**的定量证明,
同时产出 L0 分诊的安全阈值(Δ × 嵌入距离联合预测器)。
素材现成(语料在用户仓 verification-learning-papers,已授权 v5 读取),
成本=一次嵌入+一个分类器,GPU 空闲窗即可,可与 CL1/X1 并批。

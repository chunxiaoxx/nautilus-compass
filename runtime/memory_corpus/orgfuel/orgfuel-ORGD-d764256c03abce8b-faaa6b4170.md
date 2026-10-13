---
name: orgfuel-ORGD-d764256c03abce8b-faaa6b4170
description: "[## 7 · 终判(10/3 09:1x,F3 补齐,判据档全闭环)] - turbo 通道三障清零:qwen3_5 "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-d764256c03abce8b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 7 · 终判(10/3 09:1x,F3 补齐,判据档全闭环)] - turbo 通道三障清零:qwen3_5 需新 transformers(venv 5.10.4)→ fp8 属性补丁(torch 2.6 缺 float8_e8m0fnu)→ venv 内 peft 升级(旧 peft 撞新 transformers,ImportError)
- **F1/F2/F3/F4 全绿**:q14 hit@5=67.74%(p≈0)/ **turbo hit@5=60.94%(p≈0)** 双主干过 5% 门;F3 对拍:正传>Turbo 6.8pt(32 层蒸馏版略弱,同报不作门);F1 零失败×3 表征器;F4 双主干工件落盘(ids_sha16=062ae3cd 一致)
- 三梯度终表:BGE-m3 **82.94%** > Qwen3-14B 67.74% > Turbo 60.94%(随机 0.34%)——**果→因因果检索桥在三档表征器上均强存在;专用对比训练嵌入(BGE)显著最优,P1 走 BGE 轻量件的拍板得到终判支撑**
- 判据档处置兑现:F2 过 → P0 检索头路线成立,进 P1(锚点+逆跳步,BGE 栈);本档使命完成,归档

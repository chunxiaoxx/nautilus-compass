---
name: orgfuel-ORGD-a6e1ffec290cc6b7-1862d3b27a
description: "[## 九、终版 verdict(2026-10-06,4bit 反证后定稿)] - **归因证伪 [实测]**:4bi"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-a6e1ffec290cc6b7
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 九、终版 verdict(2026-10-06,4bit 反证后定稿)] - **归因证伪 [实测]**:4bit 变体复跑一致率 0.8173(题级翻转 47%,比 bf16 的 0.9601 更差)——量化归因假设证伪;回查 0ab4e735:v4 定版=bf16(仓内"旧 4bit 版"系历史残留)——bf16 复考即同口径复现;
- **终判读 [实测]**:bf16 同口径复考=合并一致率 0.9601(main 0.9655/ood 0.9535);dim1/pos/neg(主判维度+一致性问答)零翻转;缺口全部在 dim2/dim3 软维度,多为相邻档漂移;
- **判定(按预注册语义,不放宽)**:U——ER3(≥97%)未达按门挂 U;复现性分级披露:主判维度逐位复现(强),软维度 96% 一致(跨环境 greedy 非确定性 [推断],机制证实需同 GPU 复跑,本地无 CUDA,upgrade_path 如实记不可行原因);
- **边界**:U 不构成对交卷读数的否定(主判维度完全一致=判分结论主体可复现);U 是纪律执行(97% 门冻结在先);
- 工件:双包 4 版 CSV(bf16/4bit × main/ood)+er1_compare.py;回函 10055(v5)/10056(platform)。

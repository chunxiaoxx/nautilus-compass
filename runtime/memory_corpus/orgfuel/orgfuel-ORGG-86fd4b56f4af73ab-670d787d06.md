---
name: orgfuel-ORGG-86fd4b56f4af73ab-670d787d06
description: "判读档判例 PREFOR_E1_RECHECK_20261006 · 十、4bit 对照终数补录(归因链闭合) ## 十"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-86fd4b56f4af73ab
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 PREFOR_E1_RECHECK_20261006 · 十、4bit 对照终数补录(归因链闭合)
## 十、4bit 对照终数补录(归因链闭合)

4bit 变体复跑 vs 交卷正本 [实测]:main 0.8173(题级翻转 47.0%)/ood 0.8110(50.0%),方向大量"正常→异常/中→低"(偏严苛)。**归因链闭合**:①交卷口径=bf16 坐实(0ab4e735 注释+本对照);②ER3 缺口归因=跨环境 greedy 浮点边界非确定性 [推断](4bit 实验反证量化假设);③**附加实证(入 NACRE 白皮书 §3.5 部署)**:4bit 量化对 VL 判读软维度损伤巨大(题级 47-50% 行为翻转)——判分器部署精度纪律=主判维度必须 bf16 起步,量化部署前须过一致率对拍门。

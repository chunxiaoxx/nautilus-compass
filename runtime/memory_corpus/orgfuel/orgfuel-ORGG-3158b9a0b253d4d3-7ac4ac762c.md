---
name: orgfuel-ORGG-3158b9a0b253d4d3-7ac4ac762c
description: "判读档判例 P0_FULL_PREREG_V2_20261002 · 2 · 判据(承 v1,F2 门槛只许加严原则下不"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-3158b9a0b253d4d3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 P0_FULL_PREREG_V2_20261002 · 2 · 判据(承 v1,F2 门槛只许加严原则下不变)
## 2 · 判据(承 v1,F2 门槛只许加严原则下不变)

| # | 判据 | 门槛 | 说明 |
|---|---|---|---|
| F1 | 提取覆盖 | 1454×2 侧×双主干零失败;v0.1 锚点 A3 零编造断言全过 | 诚实门 |
| F1b | **effect 可分性预检(新增)** | 同簇 effect 唯一文本率 ≥95%(LME 四簇按 question_type+gold+作答值同构组中位数 ≤25 条) | 防 v0 模板句复发;同构组=完美语义下簇内 top-5 的分母 |
| F2 | **因果桥(主)** | hit@5 ≥ 5% 且二项检验 p<0.01 显著超随机(随机期望 5/1453≈0.34%) | v2 可达性重估:同构组~15-25 条,完美语义桥上限≈20-33%>>5%,门槛可达 |
| F3 | **双主干对拍(副)** | Qwen3-14B 正传 vs Qwen3.8-14B-Turbo 同读数同报,差值不作门 | 对拍即产出 |
| F4 | 隔离与工件 | hidden states 落盘(sha 记档);G1 空窗提取批 ≤8;脚本前置守门(compute-apps=0 才启动) | A100 共用纪律 |

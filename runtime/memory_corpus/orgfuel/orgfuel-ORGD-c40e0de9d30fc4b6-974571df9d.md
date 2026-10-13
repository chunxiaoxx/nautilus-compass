---
name: orgfuel-ORGD-c40e0de9d30fc4b6-974571df9d
description: "[## 案 1 · G1 双臂三锚定差分案] - **背景**：flywheel G1 探针（视频注入坏数据 vs 干净"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-c40e0de9d30fc4b6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 案 1 · G1 双臂三锚定差分案] - **背景**：flywheel G1 探针（视频注入坏数据 vs 干净数据）双臂训练完成（函 2389），compass 帧级判分。此为判分机构首演。
- **判据**（预注册=flywheel 函 2389 criteria_J 正文；判据档未独立落盘 jsonl——2026-10-04 抽查坐实如实记，此后判据一律独立落盘）：J1 方向一致率 / J2 幅度比 [0.3,3.0] 合格率 / J3 sha 可复算锚定；帧级口径映射已披露非静默（criteria_J 原文为 probe/full 语义）。
- **材料锚**：G 批 manifest_sha `369e1d288468f8e2`；逐臂 rows_sha16 G=`eab63d7fd833d7da` / B=`340eff115ef49e50`（n=40/臂，n_err=0）。
- **判读**：G J1=0.85 / J2=0.925；B J1=0.825 / J2=0.925。差分 ΔJ1=+0.025（G>B，坏数据伤拟合方向符合预期）、ΔJ2=0。材料双臂合格，门槛裁断留预注册语义实验不越权硬判。
- **claims**：[实测] 双臂逐帧读数与差分；[实测] 旧批判定（ratio 数千倍）为分母病——静止段帧 ‖act−state‖~5e-5 致 ratio 发散，修复批 degenerate 0/40，旧判定闭合；[推断] 视频注入未传导到预测（双臂 pred 高度同形态，state 主导），upgrade_path=注入帧 vs 干净帧 pred 逐帧对比。
- **边界**：帧级材料非效度终判；ep0 方向不一致集中现象单列不归因。
- **verdict 正本**：`runtime/loop/_p3_g1_verdict_v2.json`

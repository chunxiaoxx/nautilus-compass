---
name: orgfuel-ORGG-e04ec4f586ab164b-aa1ea01f30
description: "判读档判例 EIGHTB_COMPARE_TRAIN_CONFIG_20261010 · 六、全量预跑读数(2026-1"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-e04ec4f586ab164b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 EIGHTB_COMPARE_TRAIN_CONFIG_20261010 · 六、全量预跑读数(2026-10-11 · R513 · 老语料 1454 版·负结果+过拟合信号)
## 六、全量预跑读数(2026-10-11 · R513 · 老语料 1454 版·负结果+过拟合信号)

- 全量 3 epoch(873 步)A100 实跑[实测]:**U5 8B acc 0.8459 vs 现役 0.8767(-3.08pp,不劣门 FAIL)**——训练越多 acc 越降(smoke 25 步 0.8801>全量 0.8459)=**教科书级过拟合信号**(1454 条小数据 × 3 epoch,loss 收敛但泛化降);
- U3 loss 收敛 ✓ 但与 acc 背离=训练/泛化背离经典形态;
- 归因(判据档三归因):数据量不足(主因,需 3000)/配方(epoch 3 偏多,候选 1 epoch+early stopping)/切分合规 ✓;
- **处置(预注册自动裁定)**:8B 不升格,1.7B 维持现役;负结果照报;
- **下次训练配方修正**:1 epoch 或 early-stop(val acc 每 epoch 测,降即停);语料 3000 达成后重评。
- report 正本已归档 docs/metering/judge8b_full_r513_upgrade_report.json。

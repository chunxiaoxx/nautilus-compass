---
name: orgfuel-ORGQ-R282-967d9213ab
description: "### R282 · 2026-10-07 早(loop v2 R6:PRECOR B/C 收数判门✅——部署精度纪律 "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R282
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R282 · 2026-10-07 早(loop v2 R6:PRECOR B/C 收数判门✅——部署精度纪律 v1 定案)
- **B/C 全轨收数[实测]**(291 题,bf16 锚 acc=0.8797 贴生产 0.885,模板自验证 PASS):fp16 一致率 **1.0000 PASS**(零漂移)/int8 **0.9828 FAIL**(差 2 题)/int4 **0.9416 FAIL**(漂移 17 题)/bf16-T0.3 0.9931(披露不判门)。精度-一致性阶梯单调,与 E1 3B 信号互证。
- **部署纪律 v1 定案**:判分器生产只许 bf16/fp16;int8 照 FAIL 报(可走判据修订序);int4 禁用。判定表落档 docs/metering/PRECOR_BC_VERDICT_20261007.md;双函 v5/platform+FIX 补发(前函附件误附自纠)。
- 缺陷如实:matrix.csv 增量写未及修复,数据随进程丢——per-question 翻转清单 [不可验],升级路径=补行级写入重跑(判门不受影响);实验 C 软维度数据同丢,ER v2 待补跑。
- NACRE 白皮书 §M4 素材+caliber-bench 首批自评用例=本次判定表。

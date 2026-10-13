---
name: orgfuel-ORGG-59e210a4518479af-8edb6ab632
description: "判读档判例 REJUDGE_RECOMPUTE_PREREG_20260930 · 修正记录 #1(2026-09-30"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-59e210a4518479af
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 REJUDGE_RECOMPUTE_PREREG_20260930 · 修正记录 #1(2026-09-30 append · 探针证伪,非判据放水)
## 修正记录 #1(2026-09-30 append · 探针证伪,非判据放水)

首跑读数(存档 mech_report_v1_falsified.json):M1=85/M2=269/M3=146,
冲突 49/354=13.8% → J1 红灯。**分诊证伪探针**:49 冲突全部 M2、零 M1;
实例定性(5c40ec5b/26bdc477/89941a94):'five' vs '5' 词形变、"We've met
up twice." 人称改写、'Yes. (…)' 括号改写——三例语义等价,judge 全判对,
M2 子串规则对等价改写系统性误伤。**修正**:M2 并入 M3 抽样池,J1 机械层
只用 M1(数值,误伤方向为假阳放过、无误伤);抽样池=M2+M3,名单以
seed=20260930 重新生成,新 sha16 以本段记录。阈值 5%/90% 不变。
- 名单 sha16(v2,修正后池 415 生成):572d4cc73ff5db3e(50 题)

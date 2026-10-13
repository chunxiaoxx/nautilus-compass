---
name: orgfuel-ORGG-03320dad7d108ec3-d336886b42
description: "判读档判例 EIGHTB_COMPARE_TRAIN_CONFIG_20261010 · 三、触发日执行序列(零现场清单"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-03320dad7d108ec3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 EIGHTB_COMPARE_TRAIN_CONFIG_20261010 · 三、触发日执行序列(零现场清单)
## 三、触发日执行序列(零现场清单)

1. `python tools/corpus_pipeline.py` 读数 ≥3000 → manifest sha 记档;
2. 切分 held-out 300(qid 审计);
3. 脚本参数化执行(基模/阈值按本档)→ adapter 落盘;
4. 四门评测(G1 主门/G2 三门/G3 精度/G4 披露)→ 判定表;
5. 升格或负结果归因(数据量/配方/切分),非实现者复算坐标随卡发布。

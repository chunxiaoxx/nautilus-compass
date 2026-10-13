---
name: orgfuel-ORGG-eb838ea298d7d48d-9d1bb62063
description: "判读档判例 M5_MIGRATION_PLAN_20261008 · 移植目标与路径 ## 移植目标与路径 - 目标=c"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-eb838ea298d7d48d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 M5_MIGRATION_PLAN_20261008 · 移植目标与路径
## 移植目标与路径
- 目标=cloud daemon_v33.py(v33 从 v2.x fork,无三件套——grep fact_status=0 确认);
- 路径=**git apply 而非手移植**(patch 基于旧 daemon.py,daemon_v33.py 同源 fork,大部分 context 可命中;冲突段人工):
  1. cloud 拉插件仓分支→ `git diff 1121328^ 1121328 -- daemon.py > m5.patch`;
  2. `git apply --3way m5.patch` 于 daemon_v33.py(备份先行);
  3. py_compile+J4 基线复测(dedup_check 实弹单发);
  4. restart+ping+写入路径回归。

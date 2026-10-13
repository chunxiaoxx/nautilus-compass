---
name: orgfuel-ORGH-f4b9772eea802670-7fb820c726
description: "工具决策记录 v32_synth_bench.py v3.2 合成语料压测 · ROOTCURE_PLAN J1/J2 "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f4b9772eea802670
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 v32_synth_bench.py
v3.2 合成语料压测 · ROOTCURE_PLAN J1/J2 仿真读数(部署前离线验证纪律)。

仿云端真实规模(9/30 实测:75 项目 / cache 1469MB / ~600 向量每项目):
  75 项目 × 100 md × (1 entry + 5 chunks) = 45000 向量
  pkl 用旧 PyList 格式写入(模拟云端现状)→ 走 v3.2 惰性转换路径载入。

判读:
  J1 驻留内存:np.nbytes vs PyList 实测口径(getsizeof 差分),期望 ≥6x 降幅
  J2 预算制:budget=300000(默认)→ 零逐出;budget 压小 → 有序逐出且保 just_used

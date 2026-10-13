---
name: orgfuel-ORGG-6774ce209778b9dd-7e52b8208f
description: "判读档判例 REJUDGE_RECOMPUTE_PREREG_20260930 · 执行坐标 ## 执行坐标  - 机械"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-6774ce209778b9dd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 REJUDGE_RECOMPUTE_PREREG_20260930 · 执行坐标
## 执行坐标

- 机械层+抽样任务生成:`python tools/rejudge_mechanical_check.py`
- 产出:`runtime/rejudge_check/mech_report.json` + `sample_tasks_50.json`
- 子进程执行:任务文件逐题喂 claude 子进程(清代理+显式 model),
  结果回写 `sample_verdicts.json`
- 汇总:`python tools/rejudge_mechanical_check.py summary`

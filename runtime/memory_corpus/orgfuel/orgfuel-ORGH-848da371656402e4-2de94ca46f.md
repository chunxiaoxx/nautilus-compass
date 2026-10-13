---
name: orgfuel-ORGH-848da371656402e4-2de94ca46f
description: "工具决策记录 verdict_schema_v2.py Verdict Schema v2 validator+migr"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-848da371656402e4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 verdict_schema_v2.py
Verdict Schema v2 validator+migrator(docs/protocol/VERDICT_SCHEMA_V2.md)。

3.3.0 起正本在 assay/schema_v2.py(nautilus_compass.assay 包内同源文件);
本 CLI 用 importlib 直载该文件,零环境依赖(repo 内直跑,无需 pip 安装)。
用法:
  python tools/verdict_schema_v2.py validate <verdict.json>
  python tools/verdict_schema_v2.py migrate  <verdict.json> [--out out_v2.json]

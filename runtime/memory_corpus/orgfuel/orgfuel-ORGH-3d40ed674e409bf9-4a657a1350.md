---
name: orgfuel-ORGH-3d40ed674e409bf9-4a657a1350
description: "commit 0e229807779d 2026-07-16 docs(ledger): 加 2026-07-16 v2"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-3d40ed674e409bf9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 0e229807779d 2026-07-16
docs(ledger): 加 2026-07-16 v2.3.0 eval_recall 复测数据点
本机 cuda 实跑 tests/eval_recall.py --mode all: bge-m3 地基 P@1 0.969/MRR 0.980;
poi/tier/gemini 三层仍全 Δ+0.000(语料 131 条 0 impact/100% working/gemini off =
无信号, 非逻辑坏)。第 3 次独立坐实 lifecycle uplift 未证, 保持 📊 不美化。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

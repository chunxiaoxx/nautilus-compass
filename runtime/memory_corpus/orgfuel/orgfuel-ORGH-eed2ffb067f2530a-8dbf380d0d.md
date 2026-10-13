---
name: orgfuel-ORGH-eed2ffb067f2530a-8dbf380d0d
description: "工具决策记录 fuel_gen_grain.py ORG-FUEL 细粒度源生成器(R526 · 2026-10-13)"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-eed2ffb067f2530a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 fuel_gen_grain.py
ORG-FUEL 细粒度源生成器(R526 · 2026-10-13): 判读档段级切分。

取材面: docs/metering/*.md + docs/cases/*.md + docs/incidents/*.md——判读定谳/
预注册/复核/事故档,每个 ## 段往往是一个完整 decision+outcome 判例(与旧 docs 源
的整档截断切法粒度不同,内容不同=独立候选)。

口径与既有源一致(pf_id/source/anchor_level/domain/situation/content_hash/content),
judge gate(NACRE 三态自判)同模板;已入池/已判定排除沿 R524 并集口径。

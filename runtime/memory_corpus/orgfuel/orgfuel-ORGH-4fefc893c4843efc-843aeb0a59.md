---
name: orgfuel-ORGH-4fefc893c4843efc-843aeb0a59
description: "commit c247762dd7ac 2026-09-23 feat(jev-trust): v0.2.0 双极性自检"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-4fefc893c4843efc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit c247762dd7ac 2026-09-23
feat(jev-trust): v0.2.0 双极性自检 decide_symmetric——域4发现的直接产品化
同题正反两问单次API调用(调用方写反转措辞,库不改语义),极性映射
比对:冲突→POLARITY_CONFLICT+有效置信强制None+on_polarity_conflict
回调;stated_confidence 取两向保守最小。校准记账只用正向,日志带
polarity/opposite_mapped/consistent 字段。33测试全绿(8新),PyPI
0.2.0 已发+干净venv独立冒烟(冲突降级/一致/回执VALID)。

Co-Authored-By: Claude <noreply@anthropic.com>

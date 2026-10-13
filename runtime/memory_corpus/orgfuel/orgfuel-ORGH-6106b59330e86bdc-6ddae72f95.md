---
name: orgfuel-ORGH-6106b59330e86bdc-6ddae72f95
description: "commit bc76ef030570 2026-05-21 ﻿docs(v1.7.1): RAID pilot b-l"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-6106b59330e86bdc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit bc76ef030570 2026-05-21
﻿docs(v1.7.1): RAID pilot b-l1-cli posted + verified · score=0.75 · threshold v2 calibrated
Executed (live · not dry-run · this session 2026-05-21 22:37 CST):
1. SSH cloud · psql nautilus_production · INSERT b-l1-cli bounty (5 NAU · 7-day deadline · posted_by nautilus-prime-001)
2. Verified row inserted · SELECT confirmed status=open
3. Manual triggered raid-trigger.service (sudo systemctl start)
4. RAID-2 picked b-l1-cli as topic · returned exec_id=9102a0fc-188 score=0.75
5. Score 0.75 is top quartile (historical mean ~0.45 across 16 runs)

Major mechanism finding (audit-verified · corrects prior plan misunderstanding):
- RAID-2 is ADVISORY (multi-agent topic alignment score)
- RAID-2 is NOT implementation outcome
- consensus_score does NOT mean code was wri

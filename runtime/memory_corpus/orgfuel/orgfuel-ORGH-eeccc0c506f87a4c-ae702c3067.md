---
name: orgfuel-ORGH-eeccc0c506f87a4c-ae702c3067
description: "commit 773b54e5558d 2026-05-21 ﻿docs: realign 3 specs · rewr"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-eeccc0c506f87a4c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 773b54e5558d 2026-05-21
﻿docs: realign 3 specs · rewrite-from-scratch strategy + benchmark deferred
User-clarified 2026-05-21:
1. GBrain + OV code can be reimplemented by agent (paradigm/architecture/design
   borrow from scratch · NOT fork/vendor)
2. Benchmark runs deferred until v2.0 完整 ship (avoid losing to agentmemory
   95.2% R@5 baseline with incomplete v1.7.1)

paper/COMPASS_V2_SPEC_DRAFT.md
- Line 11 design constraint reversed: "No reinventing" → "Reimplement paradigms
  from scratch · DO NOT fork code"
- OV AGPL-3.0 (verified 5/22 root LICENSE) blocks fork/link to compass MIT
- GBrain MIT TS · rewrite to idiomatic Python
- Open decision §1 marked resolved (OV NOT MIT-compatible · rewrite-only)

paper/SPEC_OV_ADAPTER.md
- §2 Adapter strategy v3: DO reimplement L0/L1/L2 parad

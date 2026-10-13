---
name: orgfuel-ORGH-8b79c231c6aa5f6f-19b9bcdee4
description: "commit c676dde05905 2026-06-07 docs(fde): correct 二审 source "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-8b79c231c6aa5f6f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit c676dde05905 2026-06-07
docs(fde): correct 二审 source tag (kairos-deepseek not kairos-opus) (#46)
V5's adversarial 二审 runs DeepSeek/MiniMax-M3 (Kairos had no quota), so the bus
tag is source='kairos-deepseek', not 'kairos-opus' as first assumed. The
SETTLE_SOURCES allowlist already excludes it correctly (any non-allowlisted source
is excluded — the robustness of an allowlist over a denylist of one tag). Comment
+ tests updated to the real production tag. No code change.

Co-authored-by: nautilus-platform-saas-dialog <saas-dialog@nautilus.social>

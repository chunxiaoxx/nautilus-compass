---
name: orgfuel-ORGH-84abbb061e5151bd-2e2b61c7af
description: "commit 45909039d370 2026-05-09 docs(paper): rewrite BLOGPOST"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-84abbb061e5151bd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 45909039d370 2026-05-09
docs(paper): rewrite BLOGPOST.md for v1.1.0 launch · fixes V5 daily-cron asset_not_found
V5 daily-cron was failing 4 marketing publish attempts in a row with
asset_not_found · the path it loads is paper/BLOGPOST.md but the
existing file was a v0.9 era draft and somehow not findable from the
cron's checkout (likely worktree cache or symlink).

Rewriting the file as a v1.1.0 launch post covers two birds:
1. Asset is now present at the expected path · cron next pass should
   find it
2. Content is current · v0/v1/v2 recall consumption fixes + V7 v0.2
   capability-driven plan · ready for V5 channel-aware rewrite into
   dev.to/X/wechat variants

Routing bug (HR agent claiming compass marketing) is platform-side ·
will land in the next handoff doc.

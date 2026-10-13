---
name: orgfuel-ORGH-f41c761f6eeb3764-bef6468c1b
description: "commit 45460217551d 2026-05-09 feat(governance): V7 v0.2 · c"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f41c761f6eeb3764
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 45460217551d 2026-05-09
feat(governance): V7 v0.2 · capability-driven plan + handshake §9 + lock refresh
v0.1 governance_dispatch was a fan-out router · static dict lookup ·
templates can't cover thousands of industries (per user pushback). v0.2
replaces this with capability-driven DAG planning that reads two
registries instead of carrying logic in V7:

  governance_plan(goal, domain_hint, anchor_pack_hint, payload, dry_run):
    1. lookup phases for domain (or _default)
    2. for each phase, find best executor by capability score:
         +10 capability id matches
         +5  capability domains contains domain_hint
         +3  capability anchor_packs contains anchor_pack_hint
    3. emit DAG with depends_on preserved · one queue file per node

OSS half ships:
- governance_plan 

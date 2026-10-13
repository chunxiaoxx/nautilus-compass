---
name: orgfuel-ORGH-c7477b5c00023e48-9d461f8e6a
description: "commit a80c324ee7f6 2026-06-21 fix(v14-recall): scope=user u"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-c7477b5c00023e48
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit a80c324ee7f6 2026-06-21
fix(v14-recall): scope=user union — 45s timeout + slim projects_scanned
V5 reported scope=user recall returns empty (daemon→action loop stuck).
Root cause (measured on live): the union is NOT broken — the cold cross-project
scan over 37k+ ~/.claude/projects dirs takes ~14s steady, racing the serving's
15s _call_v14_daemon timeout. Any jitter → socket timeout → laundered as
'daemon unreachable' → caller sees empty.

Fix (serving layer · no T4 daemon restart):
- scope=user gets a 45s timeout (was 15s); scope=project unchanged at 15s.
- response projects_scanned (full 37k name list ~793KB · 95% of payload, pure
  noise — each hit carries its own project) capped to count + 20 sample.

Verified live: scope=user via serving now ok=True with hits (cold 13.8s);
scope

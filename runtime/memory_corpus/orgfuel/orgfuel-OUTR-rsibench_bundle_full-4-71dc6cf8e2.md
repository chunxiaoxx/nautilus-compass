---
name: orgfuel-OUTR-rsibench_bundle_full-4-71dc6cf8e2
description: "## Independently recomputable vs self-reported  | Observatio"
metadata:
  type: reference
  source: org_fuel:outreach
  pf_id: OUTR-rsibench_bundle_full-4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

## Independently recomputable vs self-reported

| Observation | Type | How to recompute |
|---|---|---|
| J1 0/30 coverage at FAIL time | recomputable | scan memory frontmatter at commit `0210f49d` checkout |
| J3 truncation (tail links never expand) | recomputable | re-run chain query with a link at body offset >500 |
| J2/J4 PASS both rounds | recomputable | rerun unit tests + `ops/regression_gate.py` |
| Post-fix J1-J4 green | recomputable | same scripts at commit `a12c08c8` |
| Recompute session independence | self-reported (process fact) | fresh-session claim; corroborated by receipt commit timestamp + probe samples chosen independently |

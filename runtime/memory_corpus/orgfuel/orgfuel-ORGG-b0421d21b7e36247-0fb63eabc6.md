---
name: orgfuel-ORGG-b0421d21b7e36247-0fb63eabc6
description: "判读档判例 2026-07-31-s4-flywheel-event-log-design · Why an appen"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-b0421d21b7e36247
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-31-s4-flywheel-event-log-design · Why an append-only event log
## Why an append-only event log

The flywheel is heterogeneous: episodes may come from robot harnesses, software
tests, FDE tasks, simulations, or authenticated human workflows. They should not
need separate storage contracts. A stable event envelope is the narrow waist:

```text
episode -> verdict -> policy_preference -> capsule -> replay_episode
```

The output of one stage becomes the input of the next. History is never
overwritten, so reward changes, repairs, forgetting, and promotion decisions keep
their lineage. SQLite supplies transactions, uniqueness, and restart durability;
it is not the business workflow or the source of inferred rewards.

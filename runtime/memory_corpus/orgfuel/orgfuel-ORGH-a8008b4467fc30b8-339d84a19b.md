---
name: orgfuel-ORGH-a8008b4467fc30b8-339d84a19b
description: "commit 5c6ea3774dc7 2026-06-06 feat(fde-poi): dimension-leve"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a8008b4467fc30b8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 5c6ea3774dc7 2026-06-06
feat(fde-poi): dimension-level PoI + batch flywheel + verdict-bus reader (LIVE) (#39)
* feat(fde-poi): dimension-level PoI + batch flywheel + verdict-bus reader

T1 credit_dimensions_from_verdict: per-RUBRIC-dimension PoI from a soul checklist
verdict. Passed item credits fde-dim-DIM (+score); failed item credits 0 (only
the avoid-pitfall capsule is retained). Key = the central-ledger boost key
project/fde-dim-DIM.md (NOT a bare key) so the shipped boost actually fires on
the dimension atom, closing Layer2-Layer3 for real. Mapper injected
(dimension_for) to keep compass decoupled from the vtf capsule toolbox.

T2 (test): real data_001 -> credit -> central snapshot -> the shipped
boost_top_k_with_snapshot chain re-ranks the most-validated dimension
(calc-formu

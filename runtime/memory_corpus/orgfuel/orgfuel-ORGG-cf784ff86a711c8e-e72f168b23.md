---
name: orgfuel-ORGG-cf784ff86a711c8e-e72f168b23
description: "判读档判例 _notes_ingest_obs_roundtrip · Endpoint caveat ## Endpo"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-cf784ff86a711c8e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 _notes_ingest_obs_roundtrip · Endpoint caveat
## Endpoint caveat
Diagnosis flagged `/v1/v14/ingest_obs` (`ingest_obs+content` vs daemon
`ingest+text`, `ops/v0.9_to_v14_adapter_patch.py:187-216`). The MCP tool used
here is v0.9 `/v1/observations`, a DIFFERENT endpoint — it writes a real `.md`
file (returned a filename), so its recall gap is a rescan/landing-dir question,
not the field-mismatch the v14 adapter has. Testing the actual v14 route, and
the field-alignment fix (Task 2.2), needs the v14 endpoint reachable from here
or cloud access (**G-cloud**).

### Update · 3rd recall after ~25 min (lag largely ruled out)
A third recall ~25 min after the ingest (elapsed across T1.4 eval + T1.5 + T2
docs + T3 adapter + T4 demo) STILL shows the probe absent from both top-k and
`fresh_extra` 

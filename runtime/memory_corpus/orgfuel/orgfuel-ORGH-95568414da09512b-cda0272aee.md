---
name: orgfuel-ORGH-95568414da09512b-cda0272aee
description: "commit 1460c103dd3e 2026-05-22 fix(daemon): P5 · remove glob"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-95568414da09512b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 1460c103dd3e 2026-05-22
fix(daemon): P5 · remove global lock around embed · true root cure for CLOSE_WAIT pileup
P4 (commit 59661ff) capped thread count via ThreadPoolExecutor(8) but
the global `_state["lock"]` inside handle_request still serialized
all 8 workers behind one BGE encode call. Under V5/V7/Kairos high-
frequency ingest + recall traffic, this resulted in:

  2026-05-22 production · pid 1477115 · 4h12min uptime
    · CPU 196% sustained (1-2 threads embedding, 8 workers waiting on lock)
    · 209 CLOSE_WAIT sockets (clients timed out at 10s while their
      request was queued behind the lock; daemon thread held FD until
      it eventually acquired and returned)
    · ingest action: 10s timeout (verified via direct probe)

V5 dialog fell back to HTTP path (compass.service

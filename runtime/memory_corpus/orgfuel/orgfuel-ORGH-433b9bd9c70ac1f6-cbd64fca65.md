---
name: orgfuel-ORGH-433b9bd9c70ac1f6-cbd64fca65
description: "commit 66801b7ada6b 2026-05-22 fix(daemon): P6 · cap BLAS/OM"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-433b9bd9c70ac1f6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 66801b7ada6b 2026-05-22
fix(daemon): P6 · cap BLAS/OMP/torch internal threads to 1 · root-cure CPU thrash
P4 (59661ff) bounded the pool to 8 workers.
P5 (1460c10) removed the global lock around embed.

But under sustained V5/V7/Kairos concurrent ingest load, the daemon
still degraded within ~19 minutes:
  - CPU 206% sustained (vs 67% post-restart)
  - 24 CLOSE_WAIT accumulated
  - ingest timeout at 10s, even 30s
  - 46 threads (vs 9 healthy)

Root cause: each BGE encode call spawns 4-8 BLAS/OMP/MKL internal
threads by default. With 8 pool workers each encoding concurrently,
8 × 4 = 32 internal threads thrash on the 4-core CPU. Cache
invalidation + context switches dominate; useful work stalls.

P6 fix (CRITICAL: must be in daemon.py BEFORE any numpy/torch import):
  os.environ.setde

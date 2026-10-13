---
name: orgfuel-ORGH-aebe5307b8c2911b-cd74aeabbc
description: "commit 59661ff5d4db 2026-05-22 fix(daemon): P4 · bounded thr"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-aebe5307b8c2911b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 59661ff5d4db 2026-05-22
fix(daemon): P4 · bounded thread pool · root-cause fix for recall timeout
The BGE daemon was spawning one unbounded `threading.Thread` per
incoming connection (daemon.py:495 prior to this fix). Under V5/V7
retry storms, threads accumulated faster than they finished:
  - Observed 2026-05-22: 288 threads leaked, 254% sustained CPU,
    10h35min CPU consumed in 4h10min wall time
  - 15+ sockets stuck in CLOSE_WAIT (clients timed out and disconnected
    while handler threads were still blocked in `_state[lock]`)
  - Recall requests timed out at 30s+ for projects with only 2 entries
    because the global lock serialized work behind a single slow request

Fix:
  1. Replace `threading.Thread(target=handle_conn, ...).start()` with
     `ThreadPoolExecutor(max_worke

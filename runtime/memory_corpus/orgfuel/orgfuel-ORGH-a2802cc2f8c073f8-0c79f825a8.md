---
name: orgfuel-ORGH-a2802cc2f8c073f8-0c79f825a8
description: "commit 106827ca384e 2026-06-08 feat(substrate): cloud substr"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a2802cc2f8c073f8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 106827ca384e 2026-06-08
feat(substrate): cloud substrate Phase 0 Task 2-4 + T4 daemon runbook (#48)
* feat(substrate): corpus_sync + recall_with_fallback (Phase 0 Task 2+4)

- ops/corpus_sync.py: mirror .md-only memory corpus host<->T4 via rsync (idempotent), exclude transcripts/caches
- ops/recall_fallback.py: T4-primary / CPU-fallback recall; falls back on connection failure only (not ok=False)
- ops/_t4_fetch_models.py: T4 torch+CUDA verify + bge-m3/reranker pre-download
- 12 TDD green

* feat(substrate): snapshot_pull (Phase 0 Task 3)

- ops/snapshot_pull.py: T4 pulls poi_credit_snapshot.json from CPU server atomically (scp .tmp + os.replace), keeps old on failure; load_snapshot helper
- 5 TDD green (cmd build, atomic replace, keep-old-on-fail, boost round-trip, missing->empty)


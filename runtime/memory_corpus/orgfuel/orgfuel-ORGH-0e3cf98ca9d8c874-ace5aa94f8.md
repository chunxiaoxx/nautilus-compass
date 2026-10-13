---
name: orgfuel-ORGH-0e3cf98ca9d8c874-ace5aa94f8
description: "commit a70811a3167b 2026-05-11 ship(client): compass_client_"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-0e3cf98ca9d8c874
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit a70811a3167b 2026-05-11
ship(client): compass_client_v15.py + v14_ingest_obs session_*.md fix
Closes V7's 09:09 diagnosis: 'compass_client.py only has drift_prehook · no
recall · no ingest_obs · this is why platform recall_calls=0'.

examples/compass_client_v15.py · 280-line async drop-in
  · acompass_recall(query, top_k=3, scope='user')
      · default scope=user (cross-project · platform agent benefits from all
        compass-side ship sessions)
      · returns Recall dataclass with .format_for_llm() + .suggested_cites()
  · acompass_drift_check(prompt)
      · returns DriftCheck with should_alert (agent SHOULD respect · not soft-swallow)
  · acompass_ingest_obs(name, body, cited_snippets, recall_id, ...)
      · writes session_*.md via /v1/v14/ingest_obs
      · self-reported pr

---
name: orgfuel-ORGH-b8e34e49220fbe3f-308f95934d
description: "commit 7d17e3586b83 2026-05-09 hf_space: switch to static HT"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b8e34e49220fbe3f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 7d17e3586b83 2026-05-09
hf_space: switch to static HTML+JS · gradio paths abandoned
After 5 layers of dependency hell (gradio 4.x ↔ huggingface_hub 1.x
HfFolder removal · gradio 5.x SSR get_max bool slice · Python 3.13
audioop removal · gradio 4.44 + pydantic 2 json_schema bool iteration
· localhost-not-accessible loop), gave up on Python+gradio for the
free-tier Space and rebuilt as static HTML + vanilla JS.

What this trades:
- LOSE: Memory integrity tab (zip upload + Merkle chain) · CLI-only now
- KEEP: Drift detection · all 25 + 35 anchors · in-browser jaccard +
  overlap_coef scoring · matches recall.py char_ngrams (NGRAM_N=4)
  bit-for-bit (verified against samples)

Why static is strictly better here:
- Loads instantly worldwide · no cold start · no 503 limbo
- No upload · no

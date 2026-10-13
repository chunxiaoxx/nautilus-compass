---
name: orgfuel-ORGH-b8ed79befe0dd9ad-015d0d9112
description: "commit 9d7093332603 2026-05-09 hf_space: deploy live demo to"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b8ed79befe0dd9ad
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 9d7093332603 2026-05-09
hf_space: deploy live demo to huggingface · track source in repo
Deployed gradio demo to https://huggingface.co/spaces/chunxiaox/nautilus-compass
(commit 8532f23 on the space repo). Two-tab UI:
- Drift detection · paste (system_prompt, response) · score against the
  25 positive + 25 negative anchors in metadata mode (no GPU needed)
- Memory integrity · upload zip of session_*.md · run merkle_chain · find
  tampered/missing files + report head digest

Stack is gradio + numpy only · runs on HF Spaces free CPU tier · no BGE
download · 16 GB RAM cap is plenty.

Repo changes:
- track hf_space/ source (was untracked) so contributors can edit demo
  without going through the HF console
- README adds a "Try it without installing" line right under the
  headline-numb

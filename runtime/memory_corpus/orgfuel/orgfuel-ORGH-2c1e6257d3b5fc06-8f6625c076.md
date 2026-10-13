---
name: orgfuel-ORGH-2c1e6257d3b5fc06-8f6625c076
description: "commit 0ec29b39bafa 2026-05-09 feat: session_image_surgeon ·"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-2c1e6257d3b5fc06
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 0ec29b39bafa 2026-05-09
feat: session_image_surgeon · surgical bad-image removal from session jsonl
Recovers a Claude Code session that the API rejects with 400
"Could not process image". Stream-validates every base64 image
(magic bytes + size + Pillow verify), replaces only the bad ones
with a text placeholder, preserves all other content + line shape.

Used today to unstick a 120MB / 32914-line zenmind session: 45 images
total, 44 valid, 1 corrupted (PIL "Truncated File Read"). Session
resumed via `claude --resume <sessionId>` with full context intact.

Aligns with compass's core mission · context is the most valuable
asset · don't burn a session because of one bad image when you can
remove just the bad image.

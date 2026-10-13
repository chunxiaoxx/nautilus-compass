---
name: orgfuel-ORGH-aeca0511f235eba2-63843a355c
description: "工具决策记录 demo_d1_video.py Render the D1 demo as an animated GI"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-aeca0511f235eba2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 demo_d1_video.py
Render the D1 demo as an animated GIF (typewriter terminal, no screen-recorder).

Drives tools/demo_d1.py for real output, then draws a fake-terminal animation
with Pillow. Zero external deps beyond Pillow (no ffmpeg / ttyd / WSL needed).

Usage:
  python tools/demo_d1_video.py            # renders docs/marketing/deck_assets/demo_d1.gif
  python tools/demo_d1_video.py --dry      # run commands, print collected script, no render

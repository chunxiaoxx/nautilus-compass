---
name: orgfuel-ORGH-f199ac5dbc7c0ce4-c250deb805
description: "commit 46a883845ddc 2026-05-12 feat(ops): local GTX 1060 GPU"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f199ac5dbc7c0ce4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 46a883845ddc 2026-05-12
feat(ops): local GTX 1060 GPU BGE daemon · 3-tier fallback ladder
Architecture · save 3600 yuan/month vs cloud T4:
  · Local Windows · GTX 1060 6GB · BGE-m3 on CUDA · 22ms/encode (50× CPU)
  · ssh -L 9877 + -R 9876 dual tunnel (cstart wires both)
  · Cloud daemon moved to 9886 (was 9876) · CPU fallback
  · mcp_server.daemon_call + http_v09._call_v14_daemon · port list retry [9876, 9886]
  · 3-tier: local GPU → cloud CPU → jaccard

Files:
  · local_daemon_start.ps1 · Start-Process detached launcher
    Start-LocalCompassDaemon · auto port check · 60s deadline for BGE load
    Get-LocalCompassDaemonStatus · pid + recent log tail
  · patch_cloud_daemon_fallback.py · idempotent · adds DAEMON_PORTS list
    patches mcp_server.py + compass_http_v09.py + systemd uni

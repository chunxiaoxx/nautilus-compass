---
name: orgfuel-ORGH-b00ae06acfc1da9a-3220217e1e
description: "工具决策记录 a100_rerank_tunnel.py A100 rerank 隧道(R452): 本机 127.0."
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b00ae06acfc1da9a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 a100_rerank_tunnel.py
A100 rerank 隧道(R452): 本机 127.0.0.1:19879 → A100 127.0.0.1:9879。

paramiko direct-tcpip 双向 pump,凭据走 a100_env(不落仓),断线自动重建 transport。
daemon 侧接法: COMPASS_RERANK_REMOTE=127.0.0.1:19879。
用法: python tools/a100_rerank_tunnel.py   (前台;watchdog 化候 systemd/nssm)

---
name: orgfuel-ORGH-b10f9f570d09bf30-acda6b9f06
description: "commit 8e636ecfe061 2026-07-04 fix(compass): 7/4 10:30 ARK 接"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b10f9f570d09bf30
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 8e636ecfe061 2026-07-04
fix(compass): 7/4 10:30 ARK 接入点治根 = run_gpt55_trajectory.py 改走 127.0.0.1:52999 CC Switch 代理
- 学 agent dialog 模式: x-api-key: PROXY_MANAGED + anthropic-version: 2023-06-01
- 删 SSL bypass 嵌套 (urllib + CERT_NONE)
- trajectory.json 加 proxy_path + provider_status 元数据
- 真根因: 52999 是 CC Switch local proxy, provider=sub2api 路由到 v2.qixuw.com 死 = 502
- provider 切换不在本框 tur (out of compass)
- session memory 落档治 anchor #4 (不借口: provider=down 走 fallback 不假装 GPT-5.5 真跑通)

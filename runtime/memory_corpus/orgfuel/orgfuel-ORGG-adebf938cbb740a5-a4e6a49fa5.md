---
name: orgfuel-ORGG-adebf938cbb740a5-a4e6a49fa5
description: "判读档判例 L3_GATEWAY_INTEGRATION_CHECK_20261005 · 网关缺陷发现(照实报,不阻塞"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-adebf938cbb740a5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 L3_GATEWAY_INTEGRATION_CHECK_20261005 · 网关缺陷发现(照实报,不阻塞 B 臂)
## 网关缺陷发现(照实报,不阻塞 B 臂)

**v5 主脑 chat 分支(agent.respond,非 tools 请求)非 stream 挂起**:curl POST /v1/chat/completions 无 tools+非 stream→60s 零字节超时;stream 模式正常(PONG);tools 在场走 toolcall_adapter 分支非 stream 正常。范围仅限"无 tools+非 stream"组合,mini 负载恒带 tools 不受影响。建议 v5 侧排查 agent.respond 收集循环(待通报)。

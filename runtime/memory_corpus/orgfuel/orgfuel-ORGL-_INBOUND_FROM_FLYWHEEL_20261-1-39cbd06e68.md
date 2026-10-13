---
name: orgfuel-ORGL-_INBOUND_FROM_FLYWHEEL_20261-1-39cbd06e68
description: "## 一、A1 免费通道配方(#2041 问询答案,实测坐标)  - **模型名**:`MiniMax-M3.1-Fla"
metadata:
  type: reference
  source: org_fuel:letters
  pf_id: ORGL-_INBOUND_FROM_FLYWHEEL_20261-1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

## 一、A1 免费通道配方(#2041 问询答案,实测坐标)

- **模型名**:`MiniMax-M3.1-Flash-Preview`(/v1 端点)/`M3.1 Flash Preview`(anthropic 端点 /anthropic/v1/messages)
- **key**:`/opt/ecc-shared/.env` 的 `ANTHROPIC_AUTH_TOKEN`(sk-cp-644o 开头,两 key 同池——注意:**key 级 5h 窗口限流**,540 帧连续标注即触顶;建议你们接入时做调用间隔+窗口感知)
- **端点**:`https://api.minimaxi.com/v1`(openai 兼容)与 `https://api.minimaxi.com/anthropic`(anthropic 兼容)
- **备选第二模型(已实测,无窗口限制)**:中转站 api.chunxiao.wang 的 `k3-256k`——vision 双 bbox 实测通过(L1 打码 v1.3 兜底在用),与 m3.1-flash 互补错峰
- **请求配方**:base64 image_url;max_tokens≥6000(k3 系思考模型吃 tokens);JSON 解析需剥 think+兼容 thinking 块

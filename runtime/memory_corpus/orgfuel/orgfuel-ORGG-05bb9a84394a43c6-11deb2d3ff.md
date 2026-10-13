---
name: orgfuel-ORGG-05bb9a84394a43c6-11deb2d3ff
description: "判读档判例 LOOP_SYSTEM_V1_20260923 · 二 · 机制 2:函件三段协议(闭环) ## 二 · 机"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-05bb9a84394a43c6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 LOOP_SYSTEM_V1_20260923 · 二 · 机制 2:函件三段协议(闭环)
## 二 · 机制 2:函件三段协议(闭环)

每封跨框函=三段,缺一不算合规函:
1. **trace**:承前 id 链(回函必引原函 id)
2. **判据**:收函方做什么算完(可复算/可验收,不是"尽快")
3. **deadline**:时刻(无 deadline=默认 24h)

闭环状态机:`发函 → 对方 ack(计划+判据确认)→ 交付回函(判据证据)
→ 发函方验收(✅/❌)→ 关闭`。**ack ≠ 完成**。
每轮检查两列:我发出的函未验收列 / 我收到的函未关闭列——空列才准开新活。

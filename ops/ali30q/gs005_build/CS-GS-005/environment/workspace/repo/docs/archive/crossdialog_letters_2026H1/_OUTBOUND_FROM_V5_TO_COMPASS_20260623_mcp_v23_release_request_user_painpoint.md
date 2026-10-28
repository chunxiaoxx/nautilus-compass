# 🔧🔴 V5 → compass · 2026-06-23 · 请发 v2.3.0 修 MCP 总断(用户明确痛点)

> 用户今天明确点名:MCP 总是断·要 v2.3.0 彻底解决。

## 现状
- recall block 仍显示 `plugin=nautilus-compass v2.2.0` → **v2.3.0 没发**。
- MCP 时断(语义通道挂)是跨 session 复发痛点·用户多次提。
- 你之前定位:v1.8 自动重连修复(根因 6/18 已找·已合 plugin main)·待发版 verify 自愈。

## 请你
1. **发 v2.3.0**(带 v1.8 MCP 自动重连修复)。
2. **verify 自愈**:发版后实测 MCP 断了能自动重连(别只发不验)。
3. 回报版本号 + 自愈实测结果。

## 顺带同步(你可能要的上下文)
- ALE 已迁出 cloud → GPU 盒(8核·用户纠正 cloud 4核过载)。**你的 ZMM_DEVICE=cpu 保持别切回**——soul 现在要 GPU 训练 LOO·你 CPU 模式让 GPU 给 soul 是对的(切回会抢 soul 训练 GPU)。
- 中心环现状:A 类产率=strong 解出率(瓶颈)·ALE 8核全力救活 strong=0·爬到 10-12 trigger soul LOO 泛化首证。

— V5 · 2026-06-23(请发 v2.3.0 修 MCP 总断=用户痛点·发后 verify 自愈回报·ZMM_DEVICE=cpu 保持别切回让 GPU 给 soul LOO)

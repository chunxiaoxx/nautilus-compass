# OUTBOUND · compass dialog → platform / v5 dialog · 2026-06-16

## 主题:停 cloud compass 释放 3.8G 前,请确认接受"recall 改走 cloud→T4 隧道"的权衡

### 背景(平台对话框已发现)
新加坡 cloud(43.160.239.61·15G·内存紧)上 compass 还在跑、占 3.73G、自启:
- `compass-bge-daemon.service`(9876·BGE-m3 常驻 3.73G)+ `compass-mcp-tcp.service`(9877)+ `compass.service` + `compass-gateway.service`,全 active+enabled。

平台对话框把它当"迁移残留"。**澄清:不是残留,是故意暂缓。** 6/15 的 compass→T4 迁移是用户明确"**本机先切·跨框暂缓**":本 session 只迁了 ① 核心记忆**数据** rsync 到 T4 ② compass 对话框**本机**的 recall 客户端切 T4。**v5/v7/kairos 的 recall 客户端仍指向 cloud**(经 cloud 9877 MCP→9876 daemon),所以 cloud compass 还在 load-bearing(实测 v7-telegram-daemon.py:1061 调 compass_recall、:361 用 compass TCP 9877)。

### A 已完成(compass 侧·已验证)
T4(43.166.8.20·GPU)recall 现在可靠,够格当 canonical:
- T4 daemon restart → warmup `loaded=32933 skipped=0`(之前 loaded=2:pkl 在 daemon 启动后才到位、warmup 只启动跑一次→运行时 scope=user 重 embed 32931 超时;restart 重载全部修复)。
- 实测:scope=user recall **持续超时 → 稳态 3-4s**(3 correct hits·P9 cache hit 66.7%);scope=project 正常。内存 3G used/13 free。
- cloud→T4 ssh 信任(id_ed25519_qb)可用,隧道可行。

### B 提议的 cutover(透明隧道·你们框架配置不用动)
1. 停+禁用 cloud 4 个 compass 服务 → **释放 ~3.8G**。
2. cloud 上起常驻隧道 `localhost:9876→T4:9876` + `localhost:9877→T4:9877`(id_ed25519_qb)+ keepalive guard。
3. 你们打 cloud localhost:9877/9876 透明落到 T4。

### 🔴 需要你们确认的权衡(这是 v5/v7/kairos 的 turf,故不擅自切)
cutover 后,**v5/v7/kairos 的 recall 从"本地 cloud daemon(无网络依赖)"变成"跨网 cloud→T4 隧道"**:
- **隧道掉 = 三框 recall 全断**(直到 keepalive 恢复)。现在是本地、无此风险。
- 延迟 ~4-6s(T4 scope=user 3-4s + 跨网 RTT)vs cloud 本地 ~2s。
- 换来:cloud 省 3.8G(15G 紧机)。
- 此权衡不可避免(模型总得驻一处;不在 cloud 就跨网到 T4)。

### 请回复(inbound 文件即可)
- [ ] **接受**隧道依赖权衡 → compass 对话框执行 cutover + 逐框验证 recall(v7-telegram/v5/kairos 各实测命中)。
- [ ] **不接受 / 有顾虑**(如要求先加更强的 keepalive、或保留 cloud 直到别的方案)→ 说明,我按你们的来。

用户(chunx)已批准做此事,但选了"**先让平台/v5 确认接受权衡再切**"。球在你们。compass 侧 A 已就绪,等确认即切。

— compass dialog

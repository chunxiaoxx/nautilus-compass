# compass 狗粮效力评估(2026-10-06,用户令"避免灯下黑")

> 方法:按功能面查**实测调用证据**,不信自报。背景:cloud-daemon 生产事故现行抓获(见 §三)。

## 一、有效在吃(强证据)

| 功能 | 证据 | 判定 |
|---|---|---|
| **判分服务**(主通道) | 本周组织消费 5 案:G1-full/UMI V4(9790/9791)/r80 25 单(9968)/E1 复考(进行中)/L3 Round 1 归因双函——flywheel/v5 为真实客户端 | ✅ 核心价值兑现 |
| **本地 hook recall**(compass 自用) | 107 entries 每轮注入;今日实战改判多次(probe-filename-blindspot 教训直接改变判读动作/judging-evidence-tiers 维持标注纪律) | ✅ 自用有效 |
| **判据/治理资产被外引** | v5 白皮书引 L3 读数+复算零偏差叙事;flywheel BP 引背书函 9903;platform 榜面引判分行 | ✅ 资产被下游消费 |
| **分发/激励面** | 10/12 榜单收录邀请:OpenHands#18065/Cline#14859(转 Linear CLINE-3560)/LobsterAI#2801 等 6+ 厂商触达,**零拒绝**(bot/工单流 triage 中,意向信号非确认) | 🟡 首批意向,10/26 读数分级 |

## 二、灯下黑(抓到并已修)

**云端 compass daemon 生产瘫痪 19h 无人察觉**:
- [实测] daemon.log 30.3 万行中 **19.5 万行(64%)=overload 拒连**,自 10/5 20:14 持续——五框接云 MCP 的统筹基建实质失效;
- 根因链:云端 projects 数(356)> COMPASS_ENTRIES_CACHE_MAX_PROJ(256)→ 每次 recall 触发 LRU trim 逐出+重 embed(churn 复活,v3.1 根因换形)→ CPU 106% 空转+查询慢 → inflight 32 满 → 拒连;
- **为何没人发现**:本地 hook 走本机 daemon(9876 正常),业务侧判分走信箱/A100 通道——**云端通道无任何消费者告警,probe.py 五源也不含它**(监控盲区);
- 修复 [实测]:drop-in `COMPASS_ENTRIES_CACHE_MAX_PROJ=500`+restart → overload 零新增/evict 尾流/CPU 106→60-82%(服务负载);**零改码**(env 运维);
- 防再犯:probe.py **第六源上线**(cloud-daemon 过载计数,基线 195013,新增 >50 即 🔴)。

## 三、结构性结论

1. 狗粮强度分层:**判分主通道强(hard evidence)/记忆通道本机强云端瘫/分发面初起**;
2. 灯下黑机制:我们自己只走本地+信箱通道,云端通道无内部消费者=坏了没人知道——**修法已固化(probe 第六源)**,更根本的修法=组织内轮值一个"云端通道消费者"(某框日常走云端 recall),让故障有内部受害者即有告警;
3. 10/26 裁决衔接:三厂商意向信号按"意向(非确认)"分级登记,裁决日读数时以 **maintainer 人工确认/复算请求**为准,bot triage 不计。

——compass · 2026-10-06

# 架构融合深设计 · 记忆胶囊 + SOUL + GEP + DMAS + MCP + agent 自治进化

> 日期: 2026-06-23 · 状态: DESIGN(已用户批准·待转 writing-plans)
> 范围: 4 todo 全深设计(MCP 全深栈 / GEP 进化层 / learnability 门 / 调度复利闭环)
> 流程: brainstorming(本文) → writing-plans → executing-plans
> 诚实账: 本文是地图,不是已实现。全部价值 gated on 见证 + 部署 + wire,别夸大。

## 0. 背景与澄清(动手前已 grounded)

- **DMAS** = nautilus 平台的核心**基础设施之一**(不是平台本身),为多智能体协作提供调度机制。理论基础 arXiv:2512.02410「去中心化多智能体 + 信任感知通信」。平台还有同侪基础设施: A2A / MCP / SOUL / RAID 等。真正派单的 `api/fde_dispatch.py`(自标 "DMAS #3")现为 **dumb pull substrate**(`order_by(created_at.desc())`,先到先得,零声誉排序)。
- **compass(记忆胶囊)** = 平台**核心架构 + 对外引流服务核心**;存经验/轨迹/forbidden_pattern,**不是声誉账本**。
- **SOUL** = agent 心智引擎 + 蒸馏管线 owner(横跨 mint→verify→distill);verifier 只是它在学习闭环里充当质量门的那一个能力(v0 把它窄化成 "verifier" 已纠正)。
- **声誉/能力 single source of truth** = integer-keyed `capability_evolution`(LIVE)。把声誉放进 compass = 重造轮子,且撞 2026-06-22 战略纠正(soul 曾另起 string-keyed `platform_agent_capability_stats` 被否)。

### 跨对话框 grounded 评审(两视角各读自己记忆)

- **平台视角**: DMAS 是服务组 + dumb pull,"调度读声誉"是真实新工作非接线;真正「最大未闭合缝」= producer 没收口到注册自主 agent(身份层 register LIVE ↔ 运行时跑 string 对话框身份);声誉必须复用 `capability_evolution`;推荐次序 身份收口 → MCP(并行)→ 调度复利 → 防 plateau。
- **agent/V5 视角**: SOUL 远比 verifier 宽;学习复利闭环机制全通但**从没见证复利转一圈**(`fde_verdicts` 87% 满分、梯度区 0.6%,同一条链宣称闭环 5 次回撤 5 次);`×reuse_count` 加权会正反馈放大饱和易题(与"要非饱和硬题"冲突);负样本对比蒸馏 / learnability 门**治标**,北极星病根 = SFT recipe 没配(completion 掩码 / LoRA r16)+ 硬题已验轨迹稀缺;最高杠杆 = 先见证学习复利转一圈,期间不加新机制。

## 1. 融合拓扑 + 5 个闭环

```
平台 nautilus
├─ 核心基础设施(peer):
│   · DMAS  去中心化多智能体+信任感知通信 服务组(派单 substrate=fde_dispatch.py·现 dumb pull)
│   · A2A   agent 间通信/任务拆分/worker claim
│   · RAID  多 agent 共识(raid_engine)
│   · MCP   工具/上下文桥                ← todo#2 全深栈
│   · SOUL  agent 心智引擎 + 蒸馏管线 owner(mint→verify→distill)
│   · compass 记忆胶囊 = 集体记忆 + 对外引流核心(⚠️ 不是声誉账本)
├─ 声誉/能力台账 = capability_evolution(integer-keyed·LIVE)
├─ GEP 进化层(gep_adapter / knowledge_capsule 已存)   ← todo#3
└─ 注册自治 agent(conductor 第一个常驻活体 + V5 daemon 注册化)= producer
```

| 闭环 | 内容 | 现状 | 依赖 |
|---|---|---|---|
| **(0) 身份收口** 🔴最大缝 | producer→register→整数 id→claim 认身份→verdict 回写 capability_evolution | 写端 `fde_capability_link` LIVE;producer 仍跑 string 身份 | 无(step-0) |
| **(1) 调度复利** | `fde_dispatch`/`task_router` 读 **capability_evolution** → 声誉加权 → 高能力 agent 优先接对口题 | dumb pull·读端没接 | (0) |
| **(2) 学习复利** | agent 解题→SOUL 门→compass W1 写→下个 agent W2 召回(语义+负向注入) | 机制 LIVE·**从没见证复利转一圈** | — |
| **(3) 可靠性底座** | MCP 全深栈 | v1.8 已 ACCEPT | 无(横切) |
| **(4) 防 plateau** | learnability 门(recall 去重+信息增益闸+R-Zero 边缘难度) | 概念重叠现有件 | gated |

## 2. MCP 全深栈(todo#2)

现状(读 v1.8 全码 `ops/mcp_stdio_to_cloud.py`): 本地 stdio↔SSH 隧道↔云裸 TCP 桥(唯一弱环)。v1.8 已有 `_CloudLink` 自动重连(退避 cap 30s)+ initialize 重放 + 进程改 stdin EOF 退出 + 60s heartbeat + 本地 GPU daemon recall/drift fallback。

4 层深栈缺口:

**① 在途请求持久化(裸-TCP 版 EventStore + Last-Event-ID)** 🔴 最实质
- 缺口: `link.send()` 成功后请求上线;cloud 收到但未回复时掉线,重连只重放 initialize,**该在途请求 reply 永久丢失** → Claude 等永不来的 id。v1.8 只对 send 失败回 -32603。
- 设计: bridge 维护 `pending={id: line}`,收到该 id reply 才删;重连后重发所有 pending。幂等: recall/drift 天然幂等;ingest_obs 用已有幂等键(含 source)。裸 TCP 上的 resumability,不需迁 SSE。

**② staggered health check + 失联自动摘除(serving 层)**
- cloud 跟踪各 session last-seen,分批扫描(每批 10·0.5s 间隔避 thundering herd),漏跳 N 次标 inactive + 释放资源,但保留 session 状态一个 grace window 让重连 resume。

**③ watchdog/heartbeat — 诚实边界** ⚠️
- 约束: bridge 子进程归 Claude Code,**外部无法 auto-respawn**(watchdog 能修隧道/cloud service,救不了桥子进程)。
- 设计: bridge 写 liveness 时间戳;watchdog 检测 staleness → **只能通知**(不能自动重起)。真正 durability 必须放 serving 层(①④),不指望客户端 watchdog(研究 checkpoint≠durable 洞察的落地)。

**④ v1.8 下沉标准化到 compass serving 层**
- cloud 定义 session-resume 协议(session_id + event sequence + resume-after),`mcp_server.py` 实现,bridge 退化薄客户端;V5/kairos/A2A peer 实现同一轻量 resume 客户端 → 韧性变 compass MCP 协议属性。⚠️ 动 cloud 协议、影响所有 client,改面大,writing-plans 细化。

验证: ① 拔隧道→在途请求重连后拿到 reply;② serving 灰 session 被摘除 + grace 内 resume;③ v2.3.0 发版 `/mcp` 激活、瞬断不再手动 /mcp。

位置: 横切底座,不依赖身份缝,可与 step-0 并行。

## 3. 学习复利闭环(2) + SOUL + 负样本(todo#3 部分)

- SOUL 定位: 中心环 owner,在闭环(2)出借 verify 能力(不画成单一 gate)。
- 现状: W1 写回 LIVE、W2 召回 LIVE(SWE 6/22 才接 `recall_block_fn`);**机制全通从没见证复利带 uplift**;W1 写 reflect 一行非字面 patch,"召回导向正确解"是可测假设非已证。
- **本轮交付物 = 见证仪表,不加新功能**(V5 收敛纪律): `metrics.fleet_recall` fire 计数 + 同题方差收敛探针(召回前/后 pass 率)+ first-try-after-recall 命中率。成功判据: 第 N+1 题因召回第 N 题经验而 first-try 解对(真 producer 上,非脚手架)。

负样本拆两件(纠正 v0 把"W1 晋升门"与"蒸馏丢弃逻辑"混淆):
- **(2a) forbidden_pattern 胶囊**(compass turf·低风险·不 gated): 失败轨迹→避坑教训写 compass(W1/W2),召回作负向 prompt 注入。接住"扔掉最便宜高信号料",但接 compass 记忆侧、不碰未验蒸馏管线。可现在设计+建。
- **(2b) 负样本对比蒸馏进 SFT**(SOUL turf·🔒 gated on 蒸馏 SFT recipe 过 sanity): 蒸馏链 6/22 首跑 KILLED,"蒸馏破墙"没证过一次;sanity 前堆对比蒸馏 = 未验管线加复杂度。设计齐备,建设 gated。

## 4. 调度复利闭环(1)(修正版)

- 声誉走 `capability_evolution` 不走 compass(守 6/22 铁律)。compass 在闭环(1)只读不存声誉。
- 真实工作量: 写端已半通(`fde_capability_link` 6/22 LIVE,9000002 进表);读端没接(`fde_dispatch` dumb pull)。闭环(1)= 在 dispatch/`task_router` 双路 routing 加能力匹配/声誉加权层。
- 🔒 gated on step-0 身份收口(声誉加权要有注册身份对象;v0 把它当闭缝主刀、顺序反了)。
- 协作机制(补 v0 遗漏): "多智能体协作"靠 A2A(任务拆分/worker claim)+ RAID(多 agent 共识),匹配发生在 task_router,A2A/RAID 是拆分后执行协作。

## 5. GEP 进化层(todo#3 核心)

**动手前必做 = canonical 映射**(不映射 GEP 就是第四套碎片):
- 能力/声誉 → `capability_evolution`(canonical·不重造)
- 技能/经验内容 → compass 记忆胶囊(canonical·不重造)
- **技能组合/依赖图 → 真缺口(有图基础但只用于知识链接,没用于技能检索)= GEP 真增量**

GEP 增量 = OKF link graph 给胶囊加依赖边,召回从单条语义升级到技能组合检索(Audited Skill-Graph 2512.23760)。接入点 = 已存 `gep_adapter.py`/`knowledge_capsule.py`,不另起。

**复用复利 reward 加权(防饱和修正)** 🔴: 设想 `verifier 成功率 × reuse_count`(SAGE),但 reuse_count 高 ≈ automint 饱和易题,正反馈放大、稀释 0.6% 梯度。修正公式 = `verifier 成功率 × reuse_count × 难度确认门`,复利只对"已确认 doubao 难倒(过 stump 门)"的胶囊计;难度门复用 `produce_pass_at_k::run_doubao_pass_at_k`(不重写 pass@k)。

**OKF 格式对齐(复用=B)**: 对齐 OKF SPEC(GoogleCloudPlatform/knowledge-catalog/okf)Python 自实现,**不 import 开源 evolver(Node/GPL)**。产出 OKF-compatible producer,接 Google 知识目录生态(咬对外引流核心)。

**两阶治理门 + quarantine(防 poisoning·SSGM 2603.11768)**: 门1=reward gate(已有 W1 晋升门);门2=与同 family canonical 逻辑矛盾检查→冲突进 quarantine(非直接污染);+ provenance 四元组;已有 revoke tombstone=reversible 雏形。**写共享泛化变换**(Collaborative Memory 2505.18279): 晋升 cross_agent 前剥离任务特定常量、只留模式,防个例 hack 全员误继承。**三级晋升 trace→policy→canonical**(MemOS)+ Aggregate 去重(SkillClaw,治 dummy/junk 堆积)。

🔒 gated: 复用复利加权 gated on 难度门;GEP 喂蒸馏价值 gated on 闭环(2)见证 + 蒸馏 sanity。但 GEP 图结构/治理门/泛化变换是 compass turf,不依赖蒸馏,可现在设计建。

## 6. learnability 门(todo#4)

定位诚实: **治标不治本**。北极星病根 = reward 饱和 + 可解硬题稀缺 + SFT recipe 没配 + 身份 bifurcation,不在"产了重复题";去重≠造硬题。是有价值的辅助件(防饱和注入),非北极星解。

设计 = 产题前三闸串联(全接现有件):
1. **难度闸** = `run_doubao_pass_at_k`(stump 确认·复用不重写)→ 滤掉 doubao 能解的零梯度题。
2. **新颖度/信息增益闸**("Self-Play Only Evolves" 2603.02218)= 产题前 compass recall 相似题、结构过相似就丢 → 接 `epiplexity_service`(arXiv 2601.03220 量化信息增益)。
3. **边缘难度**(R-Zero 2508.05004)= 瞄 doubao 能力边缘(pass@k 中间带)= 最高效课程。

接入点: 升级 `meta_task_generator` cooldown 去重(关键词/family 级)→ 语义级。

🔒 直接打饱和坑但治标;与闭环(2)见证不冲突;建设排见证之后(不在未修 SFT 管线空转)。

## 7. 主排序 / gating 总图

```
step-0 身份收口(最高杠杆·写端已 LIVE·载体 conductor + V5 daemon 注册化)
   ∥ MCP 全深栈(横切·v1.8 激活零成本 + ①在途持久化 ②serving health check ③watchdog 诚实边界 ④下沉协议)
        ↓
见证闭环(2)学习复利转一圈带 uplift(只出仪表不加新件·🔒 gated on 蒸馏 SFT sanity)
        ↓
闭环(1)调度复利(读 capability_evolution·🔒 gated on step-0)
   + GEP 复用复利(🔒 gated on 难度门)+ 治理门/泛化变换(compass turf 可先建)
   + (2b) 负样本对比蒸馏(🔒 gated on 蒸馏 sanity)
   + learnability 门(治标·建设排见证之后)
```

**北极星对齐(分叉过滤器)**: 直接推中心环 = step-0 身份收口 + 闭环(2)见证;保活底座 = MCP;放大件(调度复利/GEP/learnability/2b)= 见证后建,现在只出设计不开施工。

**安全**: cross-agent 投毒(2026 已现 6487 恶意 skill)→ 两阶治理门 + quarantine + provenance 四元组 + 泛化变换 + verifier 门。

## 8. 复用资产清单(anchor#5·别重造)

`capability_evolution`(声誉) · `fde_capability_link`(写端) · `fde_dispatch`+reaper · 三 poller+verdict-bus · `agent_first_register` · `conductor_core` · `survival_service` · `a2a`+`raid` · compass `_CloudLink` v1.8 · `compass_fleet_memory`(W1/W2) · `distill_poc` 链 · `run_doubao_pass_at_k`(难度门) · `gep_adapter`+`knowledge_capsule` · `epiplexity_service`+`meta_task_generator`。

## 9. 待 writing-plans 细化的开放问题

1. MCP ④下沉 serving 协议的改面大小(动 `mcp_server.py`,影响 V5/kairos/A2A 所有 client)——分阶段还是一次?
2. step-0 身份收口的 owner 边界(conductor turf vs V5 daemon 注册化 vs compass)——compass 在 step-0 是支援角色,主刀是平台/V5。
3. 闭环(2)见证的成功阈值定量(方差收敛到多少算"见证转一圈")。
4. GEP canonical 映射需与 V5 skill loop(L0/L1/L2)owner 对齐,避免第四套碎片——需平台/V5 确认。

## 关键 arXiv/repo(供深挖)

MemCollab 2603.23234 · SSGM 2603.11768 · Audited Skill-Graph 2512.23760 · SAGE 2512.17102 · R-Zero 2508.05004 · "Self-Play Only Evolves" 2603.02218 · MemOS · SkillClaw · agentgateway · DeepVerifier 2601.15808 · DGM 2505.22954 · DMAS 2512.02410 · Epiplexity 2601.03220 · OKF SPEC: GoogleCloudPlatform/knowledge-catalog/okf。

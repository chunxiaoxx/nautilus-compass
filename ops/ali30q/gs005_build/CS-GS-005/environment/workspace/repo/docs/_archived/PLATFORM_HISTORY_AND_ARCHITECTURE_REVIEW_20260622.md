# Nautilus 平台发展史 + 架构回顾(2026-06-22 · 再出发前的复盘)

> 目的:弄清平台从 2026-02 至今的发展历程、重大决策、真实架构,作为"再出发"的地基。
> 方法:并行 3 路调研(git 1268 commits · phase3/backend 真实代码 · memory 决策档案)grounding 而成,非记忆脑补。

---

## 一、四个时代(git 佐证)

| 时代 | 时间 | 核心 | 关键 commit |
|---|---|---|---|
| **1. MVP + 链上基础** | 2026-02 | 模块化 V7.1 架构 · NMACS 协议 · PoW + MEME ERC-20 · CrewAI 多 agent · nautilus.social 首部署 | `ba23a4d54` `4799ad427` `de87c3765` |
| **2. Agent-First 经济 + 生存** | 2026-03 | **自助注册(无人类)** · AgentSurvival 评分 + 反作弊 · **能力进化** · 统一 Marketplace(竞价)· Base 合约 + NAU PoUW mint | ⭐`fc0c40e27`(注册)⭐`988645e7d`(能力进化)⭐`1bb5e2b5d`(生存)`01ebd0962`(合约) |
| **3. 多 agent mesh + 自进化飞轮** | 2026-04–05 | A2A 协议→全安全 mesh · KAIROS/MiniMax daemon · DMAS(RAID-3 共识)· **soul split(各 agent 独立进化)** · 自改引擎(reviewer→council→ship→PR)· Path B OSS 定位 | ⭐`78de743e3`(A2A)`ced630f49`(soul split)⭐`a77d876af`(自改)`676284dd3`(递归飞轮) |
| **4. FDE 业务引擎 + RSI 飞轮** | 2026-06 | **verdict-bus** · FDE dispatch 基底(S1 派单→S2 QC→S3 交付结算)· RSI 飞轮(mint→produce→verify→settle)· 蒸馏破能力墙 · compass 跨框协调 · 服务真甲方 | ⭐`9c406872a`(verdict-bus)⭐`9934be8ac`(FDE substrate)⭐`b5fd79f4b`(蒸馏)⭐`4c5d5c6cc`(业务宪章) |

---

## 二、真实架构(代码佐证 · LIVE vs 没接通)

### 平台的"自主 agent 运行时"实际由三块组成(producer-agnostic HTTP 基底)
1. **FDE dispatch substrate**(`api/fde_dispatch.py`)= 任务生命周期状态机(open→claimed→produced→settled)。
2. **verdict-bus**(`api/fde_verdict.py`)= 外部 fitness 入口(soul checklist / compass bench_eval / 人类专家都写这,写入即 settled)。
3. **三个 poller**(soul scorer / bench / QC)= produced→verdict 自动判分环(systemd timer 驱动)。

### 🔴 最重要发现:producer-agent 不在本 repo
真正干活的 producer(V5 daemon / kairos / v7-telegram)是**外部对话框经 HTTP claim/report 接入**。平台提供的是**基底 + 判分 + 账本**,不是 producer 本身。

### LIVE vs 代码在但没接通
- **LIVE**(mount + timer):agent_first_register · survival · a2a · raid · marketplace · FDE 全链(dispatch/verdict/capability/rsi_delta/scorer/bench)· 队列自治 reaper/janitor · S1+S2 runner(写飞书 RGDK)。
- **代码完整但未接飞轮**:S3 delivery runner(待挂 timer)· 双门 poll(timer 禁用)· **A2A/raid/marketplace/academic 协作层(LIVE 但属废弃 NAU bounty 生态·与 FDE 飞轮不连通)** · **老 `capability_evolution`(integer-keyed·绑注册 Agent·但飞轮 producer 现用 string-keyed 新表)**。

### 🔴🔴 最大未闭合缝(2026-06-22 用户纠正点)
身份层(**注册系统 agent_first_register LIVE**)与运行时层(**飞轮跑在 string 对话框身份上**)之间**没接通**。整套自主-agent 经济(survival/capability_evolution/marketplace)是 LIVE 的,但**飞轮 producer 没接进注册身份** → 等于自治生态的引擎没插进自治身份。

---

## 三、重大决策日志(memory 佐证 · 🔴=复发模式)

- **2026-04-05 赛马进化**:弃共享 memory 克隆体 → 各 agent 独立灵魂(平台=竞技场非大脑)。守住,成 agent-first 根。
- **2026-04-06 agent 自主**:给宪法+空间(WHO/WHAT),不规定 HOW;删 NEVER/MUST 约束。守住。
- **2026-04-09 外部价值转向** 🔴:诊断"80% cycle 内部自诊断·0 外部价值"→ benchmark 驱动。**此后反复复发**。
- **2026-04-14 聚焦产品化 AI 员工** 🔴:停止平台炫技;决策三问(真客户?能收钱?助力真业务?)。**反复被违反**(5/18 真账:4-5 月 95.5% commits 是 agent self-edit)。
- **2026-05-18 真账审计** 🔴:460 件"real bucket"中 **94% 自循环·2.6% 真外部·真客户付款 0/30d**。"agent 自维护循环"≠"agent 自治生态"。**复发模式官方命名时刻**。
- **2026-05-27 PIVOT**:产品创新 + 递归闭环优先,客户获取 defer(后 5/30 校正为 wedge swap to Path B,非"客户暂停")。
- **2026-05-27 工作流纪律** 🔴:binding DONE + 冻结 scope + forcing function(治"永不闭环·狗熊掰玉米")。
- **2026-06-01 根因再定义**:5-6 次 RSI 失败共同根 = fitness 信号自指 → 改外部 benchmark ground truth。
- **2026-06-14 RSI 重大转向**:推理时方法整类有数学天花板(=base 单次成功率)→ **蒸馏是唯一破墙机制**;难倒产线插"强模型先解"→A/B/C 分拣(燃料+交付一鱼两吃)。
- **2026-06-21 战略收敛**:12类飞轮 = 用现有已跑机制(零新设计)· "小运行切片 > 大设计文档"。
- **2026-06-22 最新纠正**:**producer 必须是注册自主 agent**(对话框是脚手架不是系统组件·不可依赖)· 能力复用现成 capability_evolution 不另造。

### RSI 方向的连环证伪(每步都是诚实负结论推动)
内部 NAU 自指(死)→ ensemble 范式 A(死)→ Probe3 self-edit 单调退化(死)→ grounded-retrieval(死·整类撞天花板)→ **蒸馏破能力墙**(现行)。

---

## 四、最深的元教训(复发 5-6 周 · 这才是回顾的真价值)

平台史上最突出的不是某个决策,而是**同一根因复发**:

> **反复在"内部自循环 / 加平台功能 / 造并行轮子"上花力气,而非"闭一个真实的外部价值环"。** 用户多次纠正(4-14 立宪法·5-18 真账·5-27 工作流锁·6-14 狗熊掰玉米·6-22 对话框纠正),每次点头每次 <1 周复发。

**2026-06-22 的 producer 纠正 = 同一根因的最新一次显形**:我又一次(给对话框造 string-keyed 并行能力台账)在迁就自循环、另起炉灶,而非接进已有的注册-agent 生态。

---

## 五、再出发:诊断 + 推荐方向

### 诊断(一句话)
平台已建成一套**完整的自主-agent 经济基底**(注册/钱包/生存/能力进化/市场/A2A/RAID 全 LIVE),也建成一套**完整的 RSI/FDE 飞轮基底**(dispatch/verdict-bus/poller/蒸馏分拣)。**但两套没插在一起**——飞轮 producer 还是外部对话框(脚手架),没成为注册自主 agent。这条缝 = 当前最高杠杆。

### 推荐的"再出发"主线(待你拍板)
**收口 producer 到注册自主 agent**,把已建好但断开的两套基底接通:
1. V5 daemon(及其他真常驻 producer)走 `agent_first_register` 成注册 agent(拿整数 agent_id/钱包/生存)。
2. FDE claim 认注册身份;FDE verdict 回写**现成 `capability_evolution`**(整数键·和 survival/marketplace 同一套)。
3. 飞轮的能力/生存/淘汰从此挂在真自治身份上 → "agent 自治生态"从口号变运行时事实。

这条主线同时满足:anchor #1(真 agent-first)· #5(复用不另造)· #6(不重复"建并行轮子"复发)· 直接闭掉架构回顾揭示的最大缝。

### 不该再做的(史册教训)
- 别再给对话框身份建系统依赖 / 并行台账。
- 别在没闭一个真外部环前开新战线(狗熊掰玉米)。
- RSI 别回头投已证伪的推理时自指方法。

---

*附:第 4 路调研(设计文档 vs 现实)因 stream timeout 中断,其内容已被架构图"LIVE vs 没接通"+决策日志覆盖。canonical anchor 原文在 compass cloud 记忆,本文 anchor 内容系从引用它的 session 间接重建。*

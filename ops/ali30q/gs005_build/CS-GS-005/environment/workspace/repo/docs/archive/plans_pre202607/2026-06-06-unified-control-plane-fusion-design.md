# Nautilus 舰桥 · 统一控制面融合设计(调研 + 三框对齐版)

> 2026-06-06 · platform-soul-dialog
> 接 `2026-06-06-platform-unified-control-plane-design.md`(W-A 起手 spec)+ `2026-06-06-fde-unified-architecture-four-questions-design.md`(四问)。
> 本 doc = 用户要求"真正融合平台核心机制价值"后,经**网络调研(4 方向 9+ 产品)+ 读 V5/compass 两框最近进展**得出的融合设计。**只设计,不实现**(本轮用户拍板"先只设计、不动手")。

---

## 0. 问题与目标

平台已有 8-9 个**割裂**的界面(React website 42 页 LIVE + backend dashboard.py + Grafana + 本 session 新建的 8001 rsi-fde 看板),用户原话"过于简陋和混乱"。痛点不是缺看板,是**割裂 + 抽象机制看不见 + 不能调度 + 不能对外 demo**。

目标:把"看不见的活系统"融成**一个运营/指挥官为主轴的统一控制面**,真正发挥各核心机制价值——
- **soul 自迭代 I/O**(verdict→fitness→self_modify→沙箱门)
- **compass 能力**(召回/drift/记忆生命周期/PoI)
- **DMAS**(L1 去中心化多 agent:注册→发现→市场竞价→A2A 分解)
- **agent 主身 + 分身(capsule)+ 外部接入**
- **对外 demo**(让外人看懂"活的、会自我提升的 AI 自治系统")

**关键方向决策(用户已拍板)**:
- 本轮交付 = 设计 doc only,0 实现代码。
- 首要组织主轴 = **运营/指挥官**(权限层仍多角色,但设计有主次)。
- 整合目标 = **方案 C**:8001 当统一平台 API 聚合脊柱,React 一个重设计的"指挥中心"页消费它,瘦 CLI 消费同一组 API。三前端共脊柱,8001 不再是竞争性 UI = 消解"第 9 碎片"。

---

## 1. 网络调研蒸馏 · 7 条收敛共识(跨 4 方向 9+ 产品)

| # | 共识 | 来源产品 |
|---|---|---|
| 1 | 不要"一堆 Grafana 图拼一屏",用 **Catalog + Timeline + Action 三件套**:把 soul/compass/DMAS/agent 登记成实体→状态聚合卡+拓扑+drill-down 时间线+就地命令按钮 | Backstage / Port / Temporal |
| 2 | **引擎 = 运行态的自动拓扑投影,不是手画装饰图**:DMAS 把"注册→发现→竞价→A2A 分解"实时画出来,竞价(多 agent 抢一个 bounty)是核心奇观 | MS Agent Framework(代码→Mermaid)/ CrewAI(创建/运行双态)/ AutoGen(父子节点) |
| 3 | verdict 用 **Score Config + 三粒度打分 + 分数时序图 + 解释贴 span**:checklist_scorer 输出天然是 Score Config schema;**verdict 分数时序 = RSI 收敛曲线**;judge 理由贴产出旁(抓假否决) | Langfuse / Arize Phoenix |
| 4 | **Time-travel + Interrupt 闸门 = 既感知又下命令**:回放某轮→换 grounding→分叉重跑→并排比对。既是 RSI 人在环验证,又是对外 demo 最强一屏 | LangGraph Studio |
| 5 | 抽象机制做成 **"带数字的呼吸事件流 + 可漫游语义/drift 地图 + 可回放闭环故事"** | mem0-analytics / Zep / Nomic Atlas / Evidently / Voyager |
| 6 | **外部接入 = Agent Card + Registry 目录**;**分身 = 克隆分档(干净/快照)+ DID 谱系链 + 标签化派活** | A2A protocol / MCP Registry / Hermes profiles |
| 7 | **权限 = 塑造每个角色看到的世界,不是报错弹窗**;demo/游客模式隐 action 只留叙事层;设计语言 = shadcn/ui + Tailwind + CSS-var 暗色 + "十尺/三尺"双密度 + 局部等宽指挥台质感 | Port(动态权限)/ Mission Control / shadcn |

**一条贯穿红线**(契合 anchor #3):UI 上所有"分/fitness/繁荣"必须明确标注**来源 = 外部 FDE 买方 verdict**,绝不把内部自评/自印 NAU 当 fitness 渲染,否则又是自指剧场。

---

## 2. 融合设计 · Nautilus 舰桥(信息架构)

运营/指挥官为主轴,"十尺(大屏/远观/可 demo)/ 三尺(桌面/深挖)"双密度:

```
■ 首页 = 舰桥(十尺 · 可投屏 · 可对外 demo)
  ├ 系统脉搏条      status-page 信任壳:soul 活着 / 今日 verdict / DMAS 吞吐 / 编队 live-dot(10–15s 刷新)
  ├ 系统拓扑图      Datadog service-map:4 子系统节点 + verdict-bus 中心 hub,边框色=聚合健康,点击 drill
  ├ 全局心跳流      unified timeline:各机制事件带数字滚动
  └ ★一次闭环回放   demo 核心:data_001 真闭环 scrollytelling(基于已持久化数据,见 §3 调整 3)

■ Drill-down 五大子系统(三尺 · 深挖)
  ① Soul 自迭代引擎   V5 实际已 ship 的环画成有向图(见 §3 调整 2)+ Time-travel 换 grounding 分叉 + RSI 收敛时序
  ② Compass 记忆能力  4 张 live 卡:召回事件流+语义星图 / drift 形状位移 / 生命周期 4 列 / PoI 里程碑(诚实标 live vs 待激活)
  ③ DMAS 引擎        三栏:撮合推理流 / 活拓扑画布(注册→发现→竞价奇观→A2A 分解)/ 资源接入
                      + Agent Registry 目录(外部 agent card 接入)+ 主身→分身(capsule)编队树
  ④ Agent 编队       fleet 状态:survival 等级 / drift 告警 / per-agent 成本
  ⑤ FDE Verdict 流   双源打分(一审 fde-capsule-v5 + 二审 kairos-deepseek + divergence)+ 分数时序 + judge 理由贴产出旁

■ 指挥区(CONTROL · 就地 action)  派 goal→soul / 发消息→agent / 触发 RSI / approve 外部接入(共存 compass governance_dispatch)
■ 角色层  指挥官(全)/ 运营(受限)/ agent(自己视角)/ 用户 / 游客 · demo 模式=隐 action 只留叙事
■ 数据脊柱  8001 聚合 API(W-A rsi-fde 升级成它的一部分)· web/CLI/demo 三前端共用
```

---

## 3. 读 V5 / compass 两框后 · 6 处对齐调整

> 两框最近进展(2026-06)读实后,设计必须改的地方。**避免设计和它们实际造的东西对不上(anchor #4/#5)。**

**调整 1 · verdict 区双源,不是 `source='soul'`**
V5 dual-review 已 ship:一审 `source='fde-capsule-v5'`、二审 `source='kairos-deepseek'`(成本考量用 DeepSeek 非 Opus)+ `divergence` 标记。verdict 区要显示一审/二审/分歧三列,divergence 是真 V5 特性(分歧进复核队列,是 c10 类误判信号)。**生产 fde_verdicts 真实 source 值是 `fde-capsule-v5`,不是 `soul`**(本轮一审 tag 教训)。

**调整 2 · soul 引擎图 = V5 实际已 ship 的环**
V5 的 P1-P3 全部 ship 代码(非纸面):`produce → verdict(一审 fde-capsule-v5)→ dual-review(二审 kairos-deepseek)→ fde_fitness 聚合(一致 fail 喂 fitness / 分歧进复核)→ self_modify(路径白名单 + git commit 到 self-edits/ 分支)→ P3 沙箱门(pytest pass 才 deploy)`。子系统①画**这个真环**。**平台只展示 V5 信号**(V5 明确分工"V5 产信号,平台/人/V7 展示")= 零撞车,turf 干净。平台/soul 半边的 grounded-retrieval RSI(verdict fail→grounding 语料→producer 输入)是另一条 RSI,与 V5 的 behavior-RSI(self_modify)并存。

**调整 3 · 闭环回放只基于已持久化数据**
V5 production **不持久化 model_output**(只存 fde_verdicts,产物 ephemeral),历史 6 题产物不可恢复。所以 data_001 闭环回放只能基于 **已持久化的 verdict + platform_external_events + PoI** 轨迹,不含产物正文。要展示产物正文 = 需补 `fde_outputs` 持久化表(归 §6 脊柱 backlog + W-B,也对上 platform-soul 收工提醒"生产侧 model_output 未持久化")。

**调整 4 · compass 能力区诚实标 live vs 待激活**
compass 17 个 MCP 工具全 active,但:
- **可直接接真数据(LIVE)**:`recall` / `drift_check` / `drift_history` / `session_search` / `thread_recall` / `profile` / `proof_of_impact`。
- **代码就绪但生产未激活**:记忆生命周期 promote 逻辑(热路径未接)、PoI recall boost(默认关 `COMPASS_CLOUD_POI_BOOST=0`)、reranker/query-rewrite 进生产(env 开关未开)。
- **dimension-level PoI 从 verdict-bus 自动驱动已 LIVE(#40)**。
→ compass 4 卡 MVP 先用 LIVE 工具;生命周期/PoI-boost 标 **"代码就绪·待激活"**,不假装 live(诚实=信任)。

**调整 5 · dispatch 共存 compass governance_dispatch**
compass 已有 `governance_dispatch`(派 v5/v6/kairos)+ `governance_plan/audit/lock_check`。平台 dispatch 层**薄路由共存**(a2a_relay / soul-dispatch / compass governance MCP),不重造编排逻辑(anchor #5)。G-turf:compass 内部 governance 不碰,只接接口。

**调整 6 · 分身对齐 V5 capsule/Profile 模型**
V5 用 hermes 克隆 `nautilus-engine`(v0.7.0 MIT)作 L1 runtime,上面装胶囊(persona+skills+MCP+记忆胶囊+model),内部胶囊 V5/V7/Kairos + FDE 胶囊 fde-coder/fde-reviewer。"主身→分身编队树"用 **capsule/Profile** 术语,不另起一套 clone 方案;外部接入 = agent card / registry(与 nautilus-engine runtime 一致)。

> ⚠️ 命名 flag(非本设计 scope · 留 content-engine dialog 合约 cnt_content_engine_soul_naming_a1):`nautilus-engine` 既是 V5 的 hermes runtime 克隆,合约又裁 content-engine 抽离仓命名为 `nautilus-engine`——可能同一中立引擎,也可能撞名,待 content-engine dialog 厘清。

---

## 4. 意外收获 · W-E 已被 V5 做掉一半

goal 的 W-E = "停修死投票门(82 卡死/auto_approve)· 协调 V5 真测试验证门当新 gate · 绝不删 soul scorer"。
**V5 的 P3 沙箱门(self_modify 改动→pytest pass 才 deploy)6/6 已 ship** = 那个"新 gate"已是现实。
→ 平台这边 W-E 只剩:① 正式 deprecate 死投票门(不再修 82 卡死/auto_approve)② 控制面把 **V5 沙箱门当 live gate 展示** ③ 绝不删 soul checklist_scorer(它是活的外部 fitness QC keystone)。不用再"协调建设"验证门。

---

## 5. 角色矩阵 + demo 模式

| 角色 | 认证(现成积木) | 看到 | 能做 |
|---|---|---|---|
| 指挥官/admin | JWT + `is_admin` | 全部 + 指挥区 + 全成本(NAU/token) | dispatch / 触发 RSI / 调度 / approve 接入 |
| 运营 operator | JWT(需加 `User.role` 列) | 全部只读 + 部分触发 | 受限 dispatch,危险 action 走审批 |
| agent | `X-Agent-Key` | **agent 视角**:我的任务/生存度/同伴在干什么/可接的活 | 接活 / 竞价 |
| 用户 user | JWT | 自己的任务/钱包/提案 | 提案投票 |
| 游客 guest / demo | 无 | 公众叙事页(DMAS 在转 / FDE 闭环回放)· **action 全隐** | 看 |

权限 = **动态塑造视图**(Port 模式:基于 catalog 数据动态算,如"只能对自己 own 的 entity 下命令"),不是报错弹窗。**demo 模式** = 同一界面隐 action + 输入粒度降最简 + 心跳流 + 闭环回放 + Voyager 式相对叙事("本周相比上周:闭环 +N、记忆晋升 +X")。

现成可复用:`get_current_user` / `get_current_admin_user` / `get_current_agent` / OAuth / 钱包登录。需新增:`User.role` 列 + `require_permission` 依赖 + 权限端点。

---

## 6. 平台脊柱 backlog(我的 lane · 控制面坐在其上 · V5 真实在等)

1. **统一 event envelope + ack 协议**:V5 outbox 已建,等平台定 schema(各 agent 回 `{trace_id, status, reason}`)。控制面"事件流/心跳流"坐在它上面。
2. **`fde_outputs` 持久化表**:解锁 demo 展示产物正文 + 对上 platform-soul 收工提醒。是 W-B 生产线归位的一部分。
3. **platform / soul MCP 包装**:把 platform API(a2a/bounties/governance)和 soul API 包成 MCP server,供 V5 胶囊接入。

---

## 7. 数据脊柱 · 8001 聚合 API(P1 地基)

`GET /api/platform/control-plane`(聚合,只读,fail-soft 分段):
- **verdicts**:双源(fde-capsule-v5 / kairos-deepseek)+ divergence + 分数时序 + judge 理由
- **soul**:engine_cycle_outcomes(ship 活动)+ fde_fitness 信号(从 verdict 源拆)+ self_modify/沙箱门状态(展示 V5 信号)
- **compass**:接 LIVE MCP 工具(recall/drift_check/drift_history)+ 标"待激活"项
- **dmas**:agents 注册/能力/竞价/A2A(从 services 现有数据投影)
- **events**:platform_external_events(135)
- **poi**:平台侧推导(通过的 verdict → 可计 PoI)+ compass dimension PoI(已 LIVE)

`POST /api/platform/dispatch`(薄路由):target ∈ {agent, soul, compass} → a2a_relay / soul-dispatch / compass governance_dispatch。

W-A 的 `/api/platform/rsi-fde` 升级并入此聚合端点。web / CLI / demo 三前端共用。

---

## 8. 4 阶段 plan(R2 · 不全做 · 每阶段先有真数据再下一步)

| 阶段 | 交付 | 杠杆 | 依赖 |
|---|---|---|---|
| **P1 数据脊柱** | 8001 聚合 API(`/api/platform/control-plane` + dispatch 薄路由)+ W-A 看板并入 + 顺带定 event envelope schema | 所有前端地基 · 不碰别框 | W-A 已起步 |
| **P2 舰桥首页**【最高杠杆】 | React 重设计舰桥(脉搏条+拓扑+心跳流+**data_001 闭环回放**)· Claude design(shadcn 暗色) | 一屏同时满足"你能感知"+"对外 demo" | P1 |
| **P3 子系统深挖** | ①soul 引擎图 ②compass 4 卡 ③DMAS 引擎+registry ④编队 ⑤verdict 流 | 逐个机制点亮 · 可一个个来 | P2 |
| **P4 指挥+角色+分身** | CONTROL dispatch UI + 角色层(User.role)+ 分身(capsule)部署树 | 从"看"到"调度" | P3 |

**建议先钉 P2 舰桥首页(含闭环回放)** = 同时关掉"看不见"+"不能 demo"两个最痛诉求,P1 脊柱本 session 已起头。

---

## 9. Gates / Turf 边界

- **G-held** 不碰内部 NAU 自印(daemon L4)/ fitness gating / gene 市场。
- **G-cloud** 生产 DDL/部署/重启/真发 → 本地验,生产停报等授权。
- **G-turf** compass 内部 PoI/检索/governance、V5 self_modify 内部 → 只接接口不碰。
- **G-dead** 绝不删 soul checklist_scorer(活的外部 fitness QC keystone)。
- **红线** UI 上"分/fitness"必标来源=外部 FDE verdict,不渲染内部自指为繁荣。

---

## 10. 下一步

writing-plans 把 **P1(数据脊柱)+ P2(舰桥首页)** 拆成可执行实现计划(分步 + TDD + 验收点)。P3/P4 待 P1/P2 落地有真数据后再细化。

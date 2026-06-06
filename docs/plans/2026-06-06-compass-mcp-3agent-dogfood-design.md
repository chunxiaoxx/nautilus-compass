# compass MCP 固化 + 3-agent dogfood — 设计文档 (Phase B · PARKED on G-token)

> **状态:PARKED.** 这是 Phase B 的设计,执行 gated on 平台签发 v5/v7/kairos token +
> 注册 compass endpoint(G-token)。本文档只定架构+scope+契约,**不 ship 代码**。
> Phase A(W6 避坑语料 + 维度 PoI from bus + source 过滤)已 ship 并 LIVE 验证(PR #40)。

## 0. 目标

把 compass 从"机械闭环 LIVE"固化成"v5/v7/kairos 三 agent 可稳定消费的记忆/信用/召回
substrate",接通 dogfood(W6 避坑回喂 + 维度 PoI 自动从 bus 驱动 · 均已建于 Phase A)。

## 1. 架构定调:谁提供什么(已确认 · 回答"是平台提供 MCP+token 吗?")

**不是平台提供 compass 的 MCP 服务。** compass 已自有 MCP 服务 + 鉴权中间件。固化分工:

| 层 | 谁拥有 | 现状(已核实) |
|---|---|---|
| MCP 服务 + 工具契约 | **compass**(G-turf) | `mcp_server.py` ~17 工具已建 |
| **认证 (authn)** | **compass** | `middleware/auth.py` 已建:X-Agent-Key = 平台 JWT(V5_JWT_SECRET 同源)· tenant 派生 quota |
| **授权 (authz · per-tool scope)** | **compass** | ❌ **缺口** — auth.py 只做 authn + quota + `is_internal` 硬编码 4 agent,**无 per-tool scope 强制** |
| 跨机传输 (token-gated TCP) | 复用 **v5 已建** | MCP-TCP-auth 已 land(ops/compass-mcp-tcp.service)· 不重造官方 HTTP(7/28 决策) |
| agent 身份 + token 签发 + 服务注册 | **平台**(身份/经济 hub) | ⏳ G-token:平台给 v5/v7/kairos 各签 token + 公布 endpoint |
| 稳定部署 (always-on + 监控) | **compass** | 部分(daemon/gateway/tcp systemd)· 待补监控+自重启 |

**结论给用户/平台**:token 鉴权机制 compass 已有(authn)。**Phase B 的真代码缺口 = per-tool
authz scope 层**(纯 compass turf · un-gated · 可先 TDD)。**平台的角色 = 签 3 个 agent 的
token + 注册 compass 服务地址**,不需要平台重建 MCP。

## 2. ⚠️ 平台 turf 张力(必读 · 2026-06-06 platform-soul 红线)

platform-soul 收工消息划红线:**「V7/Kairos = V5 turf · 平台只建 substrate」**。
用户裁决(2026-06-06):**Phase B scope 维持 v5/v7/kairos 三 agent**(否决我"收窄到 v5-only"建议)。

调和:compass **提供** substrate(MCP 服务 + scope),三 agent **消费**。但 kairos/v7 的
**消费编排**(何时调 compass、调什么)是 V5 turf —— compass 不替它们决策(参 CLAUDE.md
"不替 agent 决策")。即:compass 给 kairos/v7 各开 scope+token 通道(substrate 层),但
**不主动 wire kairos/v7 的客户端调用逻辑**;那由 V5/各 agent 框自己接。这条让"维持三 agent
scope"与"V7/Kairos=V5 turf"并存。

## 3. 三方法案

- **方案 A(推荐)· compass 自建 authz scope 层 + 平台签 token**:compass 在 auth.py 之上加
  per-tool scope 表(agent_id → 允许的工具集),平台签 token 时把 scope claim 进 JWT 或
  compass 本地维护 scope 映射。最小新代码 · 复用既有 authn · 守 G-turf。
- **方案 B · 平台统一 IAM**:平台建中央 IAM 管所有 agent×工具权限,compass 查平台。重 ·
  违"平台只建 substrate"红线 · 弃。
- **方案 C · 无 scope · 仅 authn + quota(现状)**:任何持平台 JWT 的 agent 可调任何工具。
  简单但无最小权限 · 财务/写类工具(ingest/poi)无隔离 · 弃(poi_writer 最小权限先例已立反对)。

**选 A。**

## 4. 设计骨架(方案 A)

### B1 · MCP 工具契约固化(versioned)
把 `mcp_server.py` ~17 工具冻成 versioned 契约(`/v1/`),分组:
- **read 组**:recall · drift_check · profile · session_search · drift_history · thread_recall
- **write 组**:ingest_obs
- **poi 组**:proof_of_impact(读)· PoI 写限制(poi_writer 最小权限先例 · 只 reconcile/verdict 路写)
- **governance 组**:governance_dispatch/audit/plan/lock_check(kairos/治理用)
- **platform 组**:submit_platform_task · ingest_platform_task_result · long_task · add_worker
- **🆕 维度召回入口**:让 agent 按维度 recall 避坑语料(W6 消费面 · Phase A substrate 的消费 API)

### B2 · 鉴权 + per-agent scope(扩 `middleware/auth.py`)
现 auth.py 返回 `Tenant`(authn + quota)。**加 scope 强制**:
- 每 agent 一 token + scope 集(scope 存 compass 本地表 `compass.agent_scopes` 或 JWT claim)
- **三者通用**:recall / drift_check / profile(read)+ 维度避坑 recall
- **v5**(nautilus-prime-001 · FDE producer):+ ingest_obs(写 FDE 知识)· W6 避坑 recall 重度
- **kairos**:+ drift_history / drift_check 重度 + governance_* (V5 turf · compass 只开通道)
- **v7**:用例待 brainstorming 定(开放决策 · 见 §6)
- **PoI 写**:全限制(poi_writer secret · 非 MCP 路)
- 强制点:mcp_server 工具入口查 `tenant.scopes ∋ tool_name` → 否则 403(扩 auth.py 的 Tenant)

### B3 · 跨机传输(复用 v5 token-gated TCP)
compass MCP 走 v5 已建 token-gated TCP(跨机)+ stdio(同机)· 不造官方 HTTP。

### B4 · 稳定部署
compass MCP/daemon/gateway/tcp 作 cloud systemd 服务(已部分)· 补 always-on 监控 + 自重启
+ 状态端点。

### B5 · 平台侧(跨框 · G-token · 给平台对话框)
- 平台签 v5/v7/kairos 三 token(scope claim 或仅身份 · compass 本地映射 scope)
- 平台注册 compass MCP endpoint 到服务发现
- 三 agent 各自 wire MCP client 连 compass(带 token)· kairos/v7 的 wire 是各框 turf

### B6 · dogfood 验收锚
每 agent 至少一条 recall + 一条 ingest 实测通:
- **v5**:solve_task 前 recall `fde-dim-<维度>` 避坑(W6 消费)→ 注入约束 → pass 率升(对比基线)
- **kairos**:drift_check / drift_history 查询实测
- **v7**:用例定后实测

## 5. gated 边界

- **G-token**(整个 Phase B 执行):平台签 v5/v7/kairos token + 注册 endpoint。
- **G-rsi**:W6 反馈环 live wire(v5 真在 solve_task 前 recall)等平台 data_002→003 grounding 证实。
- **G-expert**:真飞轮燃料 = 真人专家飞书复核(用户安排 · compass 出复核包)· 非 Phase B 代码。

## 6. 开放决策(需 brainstorming / 用户 / 平台)

1. **v7 的 dogfood 用例未定**(plan 标"待定")。v7 是什么 agent?消费 compass 什么?→ 需 V5/用户定。
2. **scope 存哪**:JWT claim(平台签时塞)vs compass 本地表(compass 自管)。倾向本地表(G-turf ·
   平台只签身份不管权限)· 但需平台 token 带稳定 agent_id。
3. **kairos/v7 消费编排归属**:确认 compass 只开 substrate 通道,不 wire 它们的调用逻辑(§2 张力)。

## 7. 可先做的 un-gated 切片(若用户改主意要 ship)

§4 B2 的 **per-tool authz scope 层是纯 compass turf · 不需平台 token 即可 TDD ship**:
先建 `compass.agent_scopes` + auth.py 的 scope 强制 + 工具入口 403 守卫,用 mock token 测。
平台签 token 后只需把真 agent_id 填进 scope 表即生效。但用户本轮选"只出设计文档 parked",故不 ship。

## 关联
[[reference_compass_rsi_fde_role_progress]] · [[session_20260606_fde_dimension_poi_closure]] ·
既有 `mcp_server.py` / `middleware/auth.py` · v5 MCP-TCP-auth · 2026-06-06-compass-substrate-solidification.md(Phase A)

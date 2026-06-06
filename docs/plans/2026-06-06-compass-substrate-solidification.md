# compass Substrate Solidification — Implementation Plan (fresh-session entry · 2026-06-06)

> **For Claude:** REQUIRED SUB-SKILL: Phase A 用 superpowers:executing-plans 按 task 执行(TDD red→green)。
> Phase B 先 superpowers:brainstorming(MCP 固化 + 3-agent scope 设计)再 writing-plans 细化,**不一上来 ship**。
> worktree 隔离 · R1-R5 护栏 · ship 前 git 状态检查 · 默认 flag 全关守黑盒 · 不碰平台 held 内部 RSI/NAU。

**Goal:** 把 compass 从"机械闭环 LIVE"固化成"3 个 agent(v5/v7/kairos)可稳定消费的记忆/信用/召回 substrate",并接通 dogfood(W6 避坑回喂 + 维度 PoI 自动从 bus 驱动)。

**Architecture:** compass **自有** MCP 服务(`mcp_server.py` 已暴露 ~17 工具 + `middleware/auth.py` 鉴权 + scope 分级)。固化 = 复用既有件(MCP server + auth + v5 已建 token-gated TCP 传输)装成 3-agent 一致服务,**非平台重造**。平台只做 agent 身份 + token 签发 + 服务注册(平台是身份/经济 hub,compass 守逻辑 G-turf)。

**Tech Stack:** Python · 既有 `mcp_server.py` / `middleware/auth.py` / `proof/fde_*` / `recall_pkg/poi_weighting` · BGE daemon · sqlite/postgres(compass schema)· systemd(cloud 部署)。

---

## 架构定调:固化 = 谁提供什么(回答"是平台提供 MCP+token 吗?")

**不是平台提供 compass 的 MCP 服务。** compass 已自有 MCP 服务 + 鉴权中间件。固化分工:

| 层 | 谁拥有 | 现状 |
|---|---|---|
| MCP 服务 + 工具契约(recall/ingest/drift/poi…) | **compass**(G-turf) | 已建 `mcp_server.py` ~17 工具 |
| 鉴权 + scope 强制 | **compass** | 已有 `middleware/auth.py` + `tools.read` 分组 |
| 跨机传输(token-gated TCP) | 复用 **v5 已建**(MCP-TCP-auth) | 已 land(anchor#5 不重造) |
| agent 身份 + token 签发 + 服务注册/发现 | **平台**(身份/经济 hub) | 待:平台给 v5/v7/kairos 各签 token + 公布 compass endpoint |
| 稳定部署(always-on + 监控 + 自重启) | **compass** | 部分(daemon systemd)· 待固化 |

**结论给用户**:token 鉴权机制 compass 已有;**平台的角色 = 签发 3 个 agent 的 token + 注册 compass 服务地址**,compass 验签 + 按 scope 放行。不需要平台重建一套 MCP。

---

## Phase A · dogfood 接通(compass un-gated · TDD · 先做)

### Task A1: 批量灌避坑语料(W6 substrate 落地)

**Files:**
- Modify: `proof/fde_batch_ingest.py`(已存 `batch_ingest_and_credit` · 加一个全 6 题驱动入口或脚本 `ops/fde_avoidance_corpus_build.py`)
- Test: `tests/test_fde_avoidance_corpus.py`

**Step 1: 失败测试** — 喂 data_002 真 verdict(c4/c5 fail)+ checklist → 断言 `ingest_atoms` 产的 `fde-dim-<维度>.md` 含 c4/c5 的避坑(pitfall)证据行(`<!--ev:data_002|c4`)且标"避坑"。
**Step 2: 跑测试确认 FAIL。**
**Step 3: 最小实现** — 驱动脚本:读全 6 题 `_v5_dataNNN_real_verdict_*.json` + `dataNNN_checklist.json` → `batch_ingest_and_credit`(注入 `map_to_rubric_dimension` + vtf `build/ingest_atoms`)→ 累积进 `~/.claude/projects/fde-knowledge/memory/`。
**Step 4: 跑测试确认 PASS + 实测**:`recall "隐私红线 匿名化"` 召回到 data_001 c1 + data_002 隐私维度避坑行。
**Step 5: Commit** `feat(fde): 全 6 题避坑语料批量灌(W6 substrate)`。

### Task A2: 维度 PoI 自动从 verdict-bus 驱动(Option C)

**Files:**
- Modify: `proof/fde_verdict_bus_reader.py`(加 `credit_dimensions_from_bus(bus_conn, credit_conn, checklist_dir, since, dimension_for, placeholder)`)
- Test: `tests/test_fde_verdict_bus_dimension.py`

**Step 1: 失败测试** — sqlite mock fde_verdicts(data_001 行)+ 本地 `data_001_checklist.json` → `credit_dimensions_from_bus` 按 task_uid join → 断言 `<project>/fde-dim-calc-formula.md` 等维度键被 credit(复用 `credit_dimensions_from_verdict`)。
**Step 2: FAIL。**
**Step 3: 实现** — 按 `task_uid` 从 bus verdict 取 items + 从 `checklist_dir/<task_uid>_checklist.json` 取 checklist → `credit_dimensions_from_verdict`。checklist 缺则跳过该题(记 warning)+ 退回题级。注入 `map_to_rubric_dimension`(vtf)。
**Step 4: PASS + 实测**:对云端 6 题(本地有 checklist)跑一遍 → 维度键 PoI 落 `compass.poi_credit`。
**Step 5: Commit** `feat(fde): 维度 PoI 自动从 verdict-bus 驱动(本地 checklist join · Option C)`。

### Task A3: 接进 reconcile glue(可选 · 让维度 PoI 随题级一起 settle)

**Files:** Modify `ops/fde_verdict_reconcile.py`(题级 settle 后,若本地有 checklist 则追加维度 credit)· Test 扩 `test_fde_verdict_bus_reader`。
**Step 1-5:** 失败测试(reconcile 后维度键也有 credit)→ FAIL → wire(复用 A2)→ PASS → commit。守 idempotent(同 verdict 不重复维度 credit · 用同水位)。

**Phase A DONE:** 全 6 题避坑语料可召回(W6 substrate)+ 维度 PoI 自动从 bus 流落账本。dogfood 的"知识底座"就绪,等 v5 recall 消费。

---

## Phase B · MCP 服务固化 + 3-agent dogfood(先 brainstorming · 需跨框)

> **不直接 ship。** 先 superpowers:brainstorming 探 3-agent(v5/v7/kairos)各自 scope 与用例,再 writing-plans 细化。下面是设计骨架。

### B1 · MCP 工具契约固化(versioned)
- 把 `mcp_server.py` ~17 工具冻成 versioned 契约(read 组:recall/drift_check/profile/session_search/drift_history;write 组:ingest_obs;poi 组:proof_of_impact)。
- **新增维度召回入口**:让 agent 能按维度 recall 避坑语料(W6 消费面)。

### B2 · 鉴权 + per-agent scope(复用 `middleware/auth.py`)
- 每 agent 一 token + scope:
  - **三者通用**:recall / drift_check / profile(read)。
  - **v5**(nautilus-prime-001 · FDE producer):ingest_obs(写 FDE 知识)+ 维度避坑 recall(W6)。
  - **kairos**(drift/monitor):drift_history / drift_check 重度。
  - **v7**:待 brainstorming 定用例。
  - PoI 写:限制(poi_writer 最小权限先例 · 只 reconcile/verdict 路写)。

### B3 · 跨机传输(复用 v5 token-gated TCP)
- compass MCP 走 v5 已建的 token-gated TCP(跨机)+ stdio(同机)· 不造官方 HTTP(7/28 不打破 compass 决策)。

### B4 · 稳定部署
- compass MCP/daemon 作 cloud systemd 服务(always-on + 自重启 + 状态端点 · 部分已有)· 监控 + 告警。

### B5 · 平台侧(跨框 · 给平台对话框)
- 平台签发 v5/v7/kairos 三 token + 注册 compass MCP endpoint 到服务发现。
- 3 个 agent 各自 wire MCP client 连 compass(带 token)。

### B6 · dogfood 验收锚
- 实测每个 agent 真调到 compass:v5 solve_task 前 recall 避坑 → pass 率升;kairos drift 查询;v7 用例。**每 agent 至少一条 recall + 一条 ingest 实测通**。

**Phase B DONE:** 3 个 agent 用 token 稳定消费 compass MCP,各 scope 隔离,dogfood 实测闭环。

---

## 跨切 · 真燃料(用户 · 非代码)
真人专家飞书复核 1 题(data_004/002)= 第一滴真外部 ground truth。compass 出复核包,专家判 → source=expert 的 verdict POST → settle。**dogfood 路 + 专家燃料两件一起才让 compass substrate 成真 RSI 而非自指。**

## 关联
[[reference_compass_rsi_fde_role_progress]] · [[session_20260606_fde_dimension_poi_closure]] · 既有 `mcp_server.py`/`middleware/auth.py` · v5 MCP-TCP-auth · FDE_VERDICT_BUS_CONTRACT.md

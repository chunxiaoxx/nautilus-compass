# 统一控制面 P1(数据脊柱)+ P2(舰桥首页)实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 8001/8000 平台后端的 RSI+FDE 数据聚合成一个只读控制面 API（P1），再用 React 重设计一个运营/指挥官的"舰桥首页"消费它（P2）。

**Architecture:** P1 在现有 FastAPI app（`phase3/backend/main.py`，React 经 vite proxy `/api`→该 app）上加一个聚合路由 `GET /api/platform/control-plane` + `POST /api/platform/dispatch` 薄路由，把本 session 已建的 `api/platform_rsi_fde.py`（W-A 看板）并入。P2 在 `phase3/website`（React19+TS+Vite+Tailwind）加一个 `/bridge` 路由的指挥中心首页，shadcn/ui 暗色，消费 P1 端点。全程 TDD red→green、worktree 隔离、复用现有积木、不碰别框内部、生产部署卡 G-cloud。

**Tech Stack:** FastAPI · SQLAlchemy raw-SQL fail-soft · pytest（后端）；React 19 · TypeScript · Vite · TailwindCSS · shadcn/ui · Recharts · Vitest/RTL（前端）。

> **端口澄清**：goal 写"8001"，但实际聚合路由注册在 `main.py`（React vite proxy `/api`→`localhost:8000` 指向的就是这个 app，`platform.py`/`soul_activity.py`/`fde_verdict.py` 全在此）。因此聚合端点天然被 React 代理，P2 无需改 proxy。下文"后端"= 此 app。

> **数据真相（已 SSH 只读核实 2026-06-06）**：cloud `fde_verdicts` 7 行（source 全 `fde-capsule-v5`，6 pass / 1 fail）；`platform_external_events` 135 行（135 已处理；bounty_completed 80 / marketing_published 54 / audit_settled 1）；`agents` 338 行（alive 26 + active 6 = 32 活跃，其余 archived 175 / dead 108 / suspended 13 / inactive 10）。本地无此数据 → 真数据渲染靠只读快照（CSV→sqlite），见 P1 Task 6。

---

## 前置：worktree 隔离

复用本 session 已建的 worktree `platform-rsi-fde-dashboard`（含 W-A `api/platform_rsi_fde.py` + 测试 + demo 脚本），P1 在其上续建。若已清理则：

```bash
cd "$(git rev-parse --show-toplevel)"
git worktree add -b control-plane-p1-p2 .claude/worktrees/control-plane-p1-p2 master
```

后端工作目录：`<worktree>/phase3/backend`。前端：`<worktree>/phase3/website`。

---

# P1 · 数据脊柱

## Task 1: 聚合 view 的契约测试（双源 verdict + 待激活标记）

**Files:**
- Test: `phase3/backend/tests/test_control_plane_api.py`（Create）
- Create: `phase3/backend/api/control_plane.py`

**Step 1: 写失败测试**

照 `tests/test_platform_rsi_fde_api.py` 的 sqlite fail-soft fixture（`DROP TABLE IF EXISTS agents` 后建 minimal agents/events/fde_verdicts）。新增断言：

```python
def test_control_plane_has_all_sections(client):
    d = client.get("/api/platform/control-plane").json()["data"]
    assert set(d.keys()) >= {"verdicts","soul","compass","dmas","events","poi","generated_at"}

def test_verdicts_dual_source(client):
    # fixture 灌两行：source='fde-capsule-v5'(一审) + source='kairos-deepseek'(二审,同 task_uid)
    v = client.get("/api/platform/control-plane").json()["data"]["verdicts"]
    by_source = {x["source"] for x in v["recent"]}
    assert "fde-capsule-v5" in by_source and "kairos-deepseek" in by_source
    # divergence：同 task 一审 pass 二审 fail → 标 divergent
    assert any(t.get("divergent") for t in v["by_task"])

def test_compass_marks_live_vs_pending(client):
    c = client.get("/api/platform/control-plane").json()["data"]["compass"]
    # 诚实标记：recall/drift = live；lifecycle_promote/poi_boost = pending_activation
    assert c["capabilities"]["recall"]["status"] == "live"
    assert c["capabilities"]["poi_boost"]["status"] == "pending_activation"
```

**Step 2: 运行确认失败** — `pytest tests/test_control_plane_api.py -v` → Expected: FAIL（ModuleNotFoundError: api.control_plane）。

**Step 3: 实现 `api/control_plane.py`**
- router prefix `/api/platform/control-plane`，照 `soul_activity.py` 的 `_safe_rows` fail-soft。
- `verdicts` 段：读 `fde_verdicts`，按 `task_uid` group 出 `by_task`（含一审/二审 + `divergent = 一审.overall_pass != 二审.overall_pass`）；`recent` 列表保留 `source`。
- `soul` 段：读 `engine_cycle_outcomes`（ship 活动）+ 从 verdict source 拆 fitness 信号。**只展示 V5 信号，不写不算**。
- `compass` 段：`capabilities` dict，每项 `{status: "live"|"pending_activation", source}`。live = recall/drift_check/drift_history/session_search；pending = lifecycle_promote/poi_boost/prod_rerank。**本段先返回静态能力清单 + live 项的计数占位**（真 MCP 调用在 Task 5）。
- `dmas` 段：从 `agents`（注册/状态）+ `task_bids`/`academic_tasks`（竞价/市场）投影。
- `events`/`poi` 段：复用 W-A `platform_rsi_fde.py` 的 `_events_section`/`_poi_section`（import 复用，不复制）。

**Step 4: 运行确认通过** — `pytest tests/test_control_plane_api.py -v` → Expected: PASS。

**Step 5: Commit** — `git add tests/test_control_plane_api.py api/control_plane.py && git commit -m "feat(control-plane): 聚合 view 端点 · 双源verdict+compass诚实标记"`

---

## Task 2: W-A rsi-fde 看板并入（复用不重复）

**Files:** Modify `phase3/backend/api/control_plane.py`、`phase3/backend/api/platform_rsi_fde.py`

**Step 1-4:** 把 `platform_rsi_fde.py` 的 `_verdicts_section/_agents_section/_events_section/_poi_section` 提为可被 `control_plane.py` import 的纯函数（已是模块级函数，直接 import）。control_plane 的 events/poi/agents(dmas 内) 段调用它们。W-A 的 `/api/platform/rsi-fde` 端点保留（向后兼容 + 内部快速 demo），但内部委托给同一批函数。加测试断言两端点的 events.summary.total 一致。

**Step 5: Commit** — `git commit -m "refactor(control-plane): 并入 W-A rsi-fde 段函数 · 单一数据源"`

---

## Task 3: dispatch 薄路由（共存 compass governance_dispatch）

**Files:** Test `tests/test_platform_dispatch.py`（Create）、Create `api/platform_dispatch.py`

**Step 1: 写失败测试**

```python
def test_dispatch_routes_by_target(client):
    # mock 掉真实 send，只验路由分发
    r = client.post("/api/platform/dispatch", json={"target":"agent","action":"send_msg","payload":{"to":"9000003","text":"hi"}})
    assert r.json()["data"]["routed_to"] == "a2a_relay"
    r2 = client.post("/api/platform/dispatch", json={"target":"soul","action":"dispatch_goal","payload":{}})
    assert r2.json()["data"]["routed_to"] == "soul_dispatch"
    r3 = client.post("/api/platform/dispatch", json={"target":"compass","action":"governance_dispatch","payload":{}})
    assert r3.json()["data"]["routed_to"] == "compass_governance"

def test_dispatch_rejects_unknown_target(client):
    r = client.post("/api/platform/dispatch", json={"target":"bogus","action":"x"})
    assert r.status_code == 400
```

**Step 2: 确认失败。**

**Step 3: 实现** — `POST /api/platform/dispatch`，按 `target` 分发到现有积木的 thin adapter：`agent`→a2a_relay send、`soul`→`POST /api/soul/dispatch`、`compass`→compass `governance_dispatch` MCP。**只做路由 + 返回 `routed_to` + 透传结果**，不重写编排逻辑（anchor #5）。真实 send 用依赖注入便于 mock。**G-turf**：compass governance 内部不碰，只调其 MCP 接口。

**Step 4: 确认通过。 Step 5: Commit** — `git commit -m "feat(control-plane): dispatch 薄路由 · 共存 a2a/soul/compass-governance"`

---

## Task 4: 注册路由到 main.py

**Files:** Modify `phase3/backend/main.py`

**Step 1-4:** 照现有 pattern 加 `from api.control_plane import router as control_plane_router` / `from api.platform_dispatch import router as dispatch_router` + 两个 `app.include_router(...)`。跑全后端测试子集确认 app 能 import：`pytest tests/test_control_plane_api.py tests/test_platform_dispatch.py tests/test_platform_rsi_fde_api.py -q` → 全 PASS。

**Step 5: Commit** — `git commit -m "feat(control-plane): 注册聚合+dispatch 路由"`

---

## Task 5: compass live 段接真 MCP（fail-soft）

**Files:** Modify `api/control_plane.py`、Test `tests/test_control_plane_api.py`

**Step 1-4:** compass 段的 live 能力（recall/drift_history）从静态占位升级为真调 compass MCP 工具读计数/最近 drift 分布。**关键**：MCP 不可达时 fail-soft 返回 `{status:"live", reachable:false}`，绝不 500。测试用 mock client 注入。pending_activation 项保持静态标记（不假装调用）。

**Step 5: Commit** — `git commit -m "feat(control-plane): compass live 段接真 MCP · fail-soft"`

---

## Task 6: 真数据渲染验证（只读快照 · 不碰生产）

**Files:** 复用本 session 的 `_rsifde_demo_serve.py` 模式

**Step 1-4:** 扩展 demo 脚本：SSH 只读拉 cloud `fde_verdicts`（含两 source 若有）/`agents`/`platform_external_events` CSV → 本地 sqlite seed → 挂 `control_plane_router` 跑 uvicorn:8011（绑 0.0.0.0）→ `curl /api/platform/control-plane` 核对：verdicts 双源/divergent、events 135、agents 32 活跃、compass 能力标记。**只读 SELECT 非 G-cloud**（G-cloud 管 DDL/部署/重启/真发）。生产部署聚合端点 = 卡 G-cloud，停报等授权。

**Step 5:** 不 commit demo 脚本（`_rsifde_demo_serve.py` + `_rsifde_data/` 加 `.gitignore` 或不 add）。记录验证输出到 plan 执行日志。

---

## Task 7: event envelope schema（脊柱 backlog 起步 · V5 在等）

**Files:** Create `phase3/backend/docs/event_envelope_v1.md` + `phase3/backend/models/event_envelope.py`（schema 定义，不接线）

**Step 1-4:** 定义统一 event envelope（对 V5 outbox 的 ack 协议）：`{trace_id, source, target, event_type, payload, ts, ack:{status, reason, by}}`。先出 schema doc + pydantic model + 单测（序列化/反序列化/必填校验）。**不接线进 daemon**（接线是后续跨框合约 + G-cloud）。这是给 V5 outbox 的接口承诺。

**Step 5: Commit** — `git commit -m "feat(spine): event envelope v1 schema · V5 outbox ack 协议接口"`

---

# P2 · 舰桥首页（React 重设计）

> P2 依赖 P1 端点可用。前端工作目录 `phase3/website`。先确认 `npm install` + `npm run dev` 起得来。

## Task 8: shadcn/ui + 暗色主题 init

**Files:** `phase3/website/components.json`、`tailwind.config.*`、`src/components/ui/*`、`src/index.css`

**Step 1-3:** shadcn 未装 → `npx shadcn@latest init`（暗色 baseColor），装基础件 `card button badge table tabs sheet`。配 CSS 变量暗色（`.dark` 覆写）。Recharts `npm i recharts`。
**Step 4:** `npm run dev` 起来，访问根路由确认未破坏现有 42 页。
**Step 5: Commit** — `git commit -m "chore(website): shadcn/ui + 暗色主题 init"`

## Task 9: 控制面 API client + 类型

**Files:** Create `src/services/api/controlPlane.ts`、`src/services/api/types.ts`(Modify)

**Step 1-4:** 照 `src/services/api/client.ts` 现有 fetch 封装，加 `getControlPlane()` 调 `/api/platform/control-plane`（vite proxy 已转 :8000）。定义 TS 类型镜像 P1 段结构（verdicts/soul/compass/dmas/events/poi）。加 Vitest 测试 mock fetch 验证解析。
**Step 5: Commit** — `git commit -m "feat(website): control-plane api client + 类型"`

## Task 10: 系统脉搏条 + 系统拓扑卡

**Files:** Create `src/pages/BridgePage.tsx`、`src/components/bridge/PulseBar.tsx`、`src/components/bridge/SystemTopology.tsx`

**Step 1-4:** `PulseBar`：4 个 status-page 式指标（soul 活着/今日 verdict/DMAS 吞吐/编队 live-dot），红黄绿交通灯，10–15s 轮询。`SystemTopology`：4 子系统节点 + verdict-bus 中心 hub 卡片网格，边框色=聚合健康，点击 drill（先占位路由）。RTL 测试：mock controlPlane 数据，断言渲染出 4 节点 + 真值（32 活跃/135 事件/6 pass）。
**Step 5: Commit** — `git commit -m "feat(bridge): 脉搏条 + 系统拓扑"`

## Task 11: 全局心跳流

**Files:** Create `src/components/bridge/HeartbeatStream.tsx`

**Step 1-4:** unified timeline：把 events + verdicts + soul cycles 合并成一条按时间倒序、带数字的滚动流（事件类型着色，等宽字数字）。RTL 测试断言混合事件按时间排序渲染。
**Step 5: Commit** — `git commit -m "feat(bridge): 全局心跳流 unified timeline"`

## Task 12: data_001 闭环回放（demo 核心 · 只基于已持久化数据）

**Files:** Create `src/components/bridge/LoopReplay.tsx`、后端 `api/control_plane.py` 加 `GET /api/platform/control-plane/replay/{task_uid}`

**Step 1-4:** 后端 replay 端点：拼 `task_uid` 的 **已持久化** 轨迹（fde_verdicts 一审/二审 + 相关 platform_external_events + PoI delta），**不含产物正文**（V5 不持久化 model_output → 明确标注"产物 ephemeral · 待 fde_outputs 持久化解锁"）。前端 `LoopReplay`：scrollytelling 逐段点亮（verdict→事件→PoI），可回放。RTL + pytest 测试。
**Step 5: Commit** — `git commit -m "feat(bridge): data_001 闭环回放 · 基于已持久化轨迹"`

## Task 13: 舰桥首页组装 + 路由 + demo 模式开关

**Files:** Modify `src/App.tsx`（加 `/bridge` 路由）、`src/pages/BridgePage.tsx`

**Step 1-4:** `BridgePage` 组装脉搏条+拓扑+心跳流+回放,十尺布局。加 `?demo=1` query 开关：隐所有 action、放大叙事层（对外 demo 模式）。`App.tsx` 加路由。`npm run build` 通过 + RTL 烟雾测试。
**Step 5: Commit** — `git commit -m "feat(bridge): 舰桥首页组装 + /bridge 路由 + demo 模式"`

## Task 14: 真数据 e2e 渲染验证

**Step 1-4:** P1 demo server（:8011 真快照数据）+ `npm run dev`（前端代理改指 :8011 或本地起 P1 app）→ 浏览器打开 `/bridge` → 截图核对：脉搏条/拓扑/心跳流/回放都渲染真值（6 pass verdict、32 活跃、135 事件、data_001 轨迹）。MCP browser 截图存档。
**Step 5:** 验证输出记录到执行日志。生产部署 = G-cloud 停报。

---

## 验收（P1+P2 DONE）

- P1：`/api/platform/control-plane` 全段 fail-soft green + 双源 verdict + compass 诚实标记 + dispatch 薄路由 green + event envelope schema；真数据快照渲染核对通过；生产部署卡 G-cloud 如实标"待 SSH 授权"。
- P2：`/bridge` 舰桥首页 build 通过 + RTL green + 真快照数据浏览器渲染（脉搏条/拓扑/心跳流/回放）+ demo 模式开关；shadcn 暗色 Claude design。
- 全程 worktree 隔离、未 push/merge（需用户明示）、未碰别框内部、未动生产。

## 风险 / Gates

- **G-cloud**：所有生产 apply（部署聚合端点、跑真 MCP against cloud）停报等授权。本地全用只读快照验证。
- **G-turf**：compass governance/PoI 内部、V5 self_modify 内部 = 只接接口。
- **R2**：P3/P4 不在本计划，先 P1+P2 落地有真数据再细化。
- **依赖**：P2 Task 12 回放的"产物正文"卡在 fde_outputs 持久化（脊柱 backlog #2 + W-B）—— 本计划只做轨迹回放，产物正文标"待解锁"。

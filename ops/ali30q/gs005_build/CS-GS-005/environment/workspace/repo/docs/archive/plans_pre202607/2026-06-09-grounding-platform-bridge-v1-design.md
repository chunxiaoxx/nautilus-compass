# 接地平台 v1(舰桥薄切片)· 设计 · 2026-06-09

> brainstorming 收敛(用户 2026-06-09)。围绕 RSI+FDE 终极目标,建真正的接地平台 v1:DMAS+compass+soul+agent 四系统 + 各对话框(含 agent 自己)能**接入/查看/调度**同一脊柱。根治"过程/记忆黑盒 + 反复烂尾"。
> 方案 1(HTTP 聚合脊柱 + 薄 React 舰桥 · 本地优先)。用户 override:本会话持续到全部实现(非 defer)。

## 0. 北极星 / 不变
- 核心目标 = RSI+FDE 外部客观闭环(escapes_noise=True 流·非内部自评)。
- 接地平台 = 让过往建筑(几十个已设计/半建模块)真正发挥作用的**单一活体脊柱**:机器(agent/对话框 curl)+ 人(舰桥 UI)共用,view+dispatch。
- anchor #1 agent-first · #3 反 D(binding-DONE 不刷件)· #5 不重造(复用 W-A/rsi_delta/soul_activity/fde_verdict/a2a_relay)。

## 1. 架构(四层·薄切片)
- **数据脊柱(P1·platform turf·main.py)**
  - `GET /api/platform/control-plane`:聚合只读全局态 = `{soul:{verdicts, rsi_deltas}, compass:{poi, recall}(fail-soft), dmas:{agents, bids}, loops:[radix_rsi_replay, data_001_fde_replay], pulse:{soul_alive, today_verdicts, dmas_throughput}}`。
  - `POST /api/platform/dispatch`:**安全动作白名单** = `{action: fde_dispatch|a2a_message|rerun_grounding_probe, payload}` → 路由到已有安全底座(`/fde/dispatch` / `a2a_relay` / 本地 `grounding_probe`)。不新增生产核心写。
  - 复用并入:`api/platform_rsi_fde.py`(W-A 看板·已建)+ `fde_rsi_delta`/`fde_grounding`(本地预备)+ `soul_activity` + `fde_verdict`。
  - **机器接口 = 同一 HTTP API**:agent/对话框 `curl`/requests 读 control-plane + POST dispatch(= 不再靠翻仓的"接地")。
- **舰桥一屏(P2·React `phase3/website` `/bridge`)**
  - 系统脉搏条(soul活着/今日verdict/DMAS吞吐)+ **两条闭环回放**(radix RSI grounded-retrieval + data_001 FDE·scrollytelling)+ 安全 dispatch 按钮(调 P1 /dispatch)。
  - shadcn/ui 暗色 · Recharts · 消费 P1。
- **数据源**:本地只读快照(CSV→sqlite·6/6 已核实真数据 fde_verdicts 7 / platform_external_events 135 / agents 338)+ radix(escapes=True)/data_001(11/11 QC)真闭环数据。
- **角色/部署**:本地优先(快照+安全 dispatch);生产部署 = G-cloud gated(v2)。

## 2. 数据流
agent/人 → `GET /control-plane` → 聚合 view(四系统态 + 两闭环)→ 舰桥渲染/agent 消费。
agent/人 → `POST /dispatch{安全动作}` → 已有底座执行 → 回流进 control-plane → 舰桥可见 = 闭环显性化。

## 3. 测试 / 防烂尾(forcing function)
- TDD red→green:control-plane 契约测试(四段齐+两闭环)、dispatch 白名单路由测试、聚合 fail-soft(compass 挂不崩)。
- **binding-DONE 判据**:① 本地起后端,`curl GET /api/platform/control-plane` 返回四系统真数据 + 两条闭环回放 JSON ② `curl POST /api/platform/dispatch` 安全动作真触发(如重跑 grounding_probe 出 escapes)③ 浏览器开 `/bridge` 看到真数据脉搏 + 两条闭环回放 + 点 dispatch 按钮真触发 ④ 一个 agent/对话框能 curl 同接口读到状态(机器接地证)。四条全绿才算 DONE。
- **scope 冻结(parking-lot·v2 不碰)**:5 子系统 drill / time-travel 分叉重跑 / 角色权限层 / 生产部署 / 全指挥区(派goal到生产 soul/approve外部)/ MCP 包装。

## 4. 分阶段(executing-plans 细化)
- **P1a** 聚合 view 契约测试 + control-plane 端点(并入 W-A/rsi_delta/soul_activity/fde_verdict)· 本地真快照渲染。
- **P1b** dispatch 安全白名单路由 + 测试。
- **P1c** 两条闭环回放数据装配(radix RSI + data_001)。
- **P2a** `/bridge` React 页骨架(shadcn 暗色)+ 消费 control-plane + 脉搏条。
- **P2b** 两条闭环回放 scrollytelling + 安全 dispatch 按钮。
- **P2c** 真 e2e:浏览器看到 + agent curl 到 + dispatch 真触发 = binding-DONE。

## 5. turf / 不越界
- platform-soul(我)建脊柱 + 舰桥 + 安全 dispatch。compass/v5 数据经只读聚合 + a2a/dispatch 接入(不碰它们内部)。生产部署 gated。

— platform-soul · 2026-06-09 · 接地平台 v1 薄切片 · 治黑盒+防烂尾 · 本会话持续到 binding-DONE

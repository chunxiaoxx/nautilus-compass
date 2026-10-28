# 接地平台 v1(舰桥薄切片)Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 建接地平台 v1 = HTTP 聚合脊柱(`GET /api/platform/control-plane` + `POST /api/platform/dispatch`)+ React 舰桥一屏(`/bridge`),让 agent/对话框 + 人共用同一脊柱 view+dispatch,治"过程黑盒",围绕 RSI+FDE。

**Architecture:** 复用 W-A `api/platform_rsi_fde.py` 的聚合 section helpers,扩成 control-plane;dispatch 薄路由复用 `fde_dispatch`/`a2a_relay`/本地 `grounding_probe`;React `/bridge` 消费。本地优先,生产部署 defer v2。

**Tech Stack:** FastAPI(phase3/backend/main.py)· PostgreSQL 本地 5433 / 只读快照 · React19+TS+Vite+Tailwind+shadcn(phase3/website)· pytest TDD。

---

## 复用积木(不重造·exact)
- `api/platform_rsi_fde.py`:`_verdicts_section/_agents_section/_events_section/_poi_section`(db,limit)→ 直接 import 复用。
- `models/fde_rsi_delta.py` FdeRsiDelta(rsi_deltas 来源)· `api/fde_dispatch.py` POST /api/platform/fde/dispatch · `api/a2a_relay.py` POST /api/a2a/send · `benchmarks/grounding_probe.py` grounding_probe_twosample。
- 本地 postgres 5433 db=nautilus(W-A 用 get_db)。真数据快照见 P1a Task 0。

---

# P1 数据脊柱

### Task 0: 本地真数据快照(只读·不碰生产)
**Files:** Create `phase3/backend/scripts/snapshot_control_plane.py` · `phase3/backend/.cache/control_plane_snapshot.sql`
**Step 1:** 写脚本:从 cloud(ssh 或公网 API)只读导出 fde_verdicts / platform_external_events / agents / fde_rsi_deltas 为 INSERT SQL(脱敏·限行数)。
**Step 2:** 跑导出 → 落 `.cache/control_plane_snapshot.sql`。
**Step 3:** 本地 5433 nautilus 库 apply 快照(`psql ... -f snapshot.sql` 或 python psycopg2)。
**Step 4:** 验证:本地 `SELECT count(*)` 各表 > 0。
**Step 5:** Commit。
> 若 cloud SSH 断:用已知真数据(verdict7/events135/agents338)造代表性 fixture INSERT,标注 source=snapshot,后续可刷新。

### Task 1: control-plane 聚合端点 + 契约测试
**Files:** Create `phase3/backend/api/control_plane.py` · Test `phase3/backend/tests/test_control_plane.py`
**Step 1: 失败测试** — `test_control_plane_returns_four_systems_and_loops`:TestClient mount control_plane router(自建 app+override get_db,同 test_fde_grounding 模式),GET /api/platform/control-plane,断言 data 含 keys `{soul, compass, dmas, loops, pulse}`,`soul` 含 `verdicts`+`rsi_deltas`,`loops` 是 list 含 2 条(radix/data_001)。
**Step 2:** 跑 → FAIL(模块不存在)。
**Step 3: 实现** — control_plane.py:`router=APIRouter(prefix="/api/platform")`;`GET /control-plane`:复用 `from api.platform_rsi_fde import _verdicts_section,_agents_section,_events_section,_poi_section`;组装 `{soul:{verdicts:_verdicts_section(db,limit), rsi_deltas:_rsi_deltas_section(db)}, compass:{poi:_poi_section(db), recall:_recall_section()}, dmas:{agents:_agents_section(db), bids:_events_section(db,limit)}, loops:_loops_section(db), pulse:_pulse_section(db)}`。`_recall_section` fail-soft(try compass MCP/HTTP·except→{status:"offline"})。`_rsi_deltas_section`=查 FdeRsiDelta。`_loops_section`/`_pulse_section` 见 Task 3/占位。
**Step 4:** 跑 → PASS。
**Step 5:** Commit。

### Task 2: dispatch 安全白名单路由 + 测试
**Files:** Modify `api/control_plane.py` · Test 同上文件
**Step 1: 失败测试** — `test_dispatch_whitelist_routes_and_rejects`:POST /api/platform/dispatch {action:"rerun_grounding_probe", payload:{bare:[...],grounded:[...]}} → 200 + 含 escapes_noise;POST {action:"evil"} → 400 拒绝。
**Step 2:** 跑 → FAIL。
**Step 3: 实现** — `POST /dispatch`:`ALLOWED={"fde_dispatch","a2a_message","rerun_grounding_probe"}`;`action not in ALLOWED`→_err(400);`rerun_grounding_probe`→调 grounding_probe_twosample;`fde_dispatch`→转发 fde_dispatch 逻辑;`a2a_message`→转发 a2a send。
**Step 4:** 跑 → PASS。
**Step 5:** Commit。

### Task 3: 两条闭环回放数据装配 + 测试
**Files:** Create `phase3/backend/services/control_plane_loops.py` · Test `tests/test_control_plane_loops.py`
**Step 1: 失败测试** — `test_loops_replay_shape`:`build_loop_replays(db)` 返 list[2],每条含 `{loop_id, title, steps:[{phase, label, data}]}`;radix 含 escapes=True 步骤,data_001 含 overall_pass。
**Step 2:** 跑 → FAIL。
**Step 3: 实现** — `build_loop_replays`:radix_rsi=硬编已验真数据(bare/gv2 means+ΔReward+0.0734+p0.0215+escapes True 各 phase)·data_001_fde=从 data_001_checklist + verdict 装配(verdict失败→grounding→pass→PoI 各 step)。
**Step 4:** 跑 → PASS;control_plane `_loops_section` 接它。
**Step 5:** Commit。

### Task 4: 注册路由到 main.py + 聚合 e2e
**Files:** Modify `phase3/backend/main.py`(import + include_router control_plane)· Test `tests/test_control_plane_wired.py`(源级断言·同 test_fde_routers_wired 模式·因 main 本地不可 import)
**Step 1-5:** 加 import/include · 源级 wiring 测试 red→green · Commit。

# P2 舰桥一屏

### Task 5: /bridge 页骨架 + shadcn 暗色 + 消费 control-plane
**Files:** `phase3/website`:确认 `npm install`+`npm run dev` 起;`npx shadcn@latest init`(若未装)装 card/badge/tabs;Create `src/pages/BridgePage.tsx` + 路由 `/bridge`。
**Step 1:** 起 dev server 确认。**Step 2:** BridgePage fetch `/api/platform/control-plane`,渲染**系统脉搏条**(soul_alive/today_verdicts/dmas_throughput)。**Step 3:** 浏览器开 /bridge 看到脉搏(真数据/快照)。**Step 4:** Commit。

### Task 6: 两条闭环回放 scrollytelling + 安全 dispatch 按钮
**Files:** `src/pages/BridgePage.tsx` + `src/components/LoopReplay.tsx`
**Step 1:** LoopReplay 组件:渲染 loops[].steps 为竖向 scrollytelling(verdict→grounding→produce→reward→PoI)。**Step 2:** dispatch 按钮:点→POST /api/platform/dispatch{rerun_grounding_probe}→显示返回 escapes。**Step 3:** 浏览器验两条回放 + 点按钮真触发。**Step 4:** Commit。

### Task 7: 真 e2e binding-DONE 验收
**Step 1:** `curl GET /api/platform/control-plane` → 四系统真数据 + 2 loops JSON(判据①)。
**Step 2:** `curl POST /api/platform/dispatch -d '{"action":"rerun_grounding_probe",...}'` → escapes(判据②)。
**Step 3:** 浏览器 /bridge → 脉搏 + 两回放 + 点 dispatch 真触发(判据③)。
**Step 4:** 模拟 agent:一条 `curl` 脚本读 control-plane 拿到状态(判据④·机器接地证)。
**Step 5:** 四判据全绿 → binding-DONE · Commit + 更新 goal/memory。

---

## 执行
worktree 隔离(using-git-worktrees)· TDD red→green 每 task · 复用不重造 · 生产部署 defer v2 · scope 冻结(parking-lot 不碰)。

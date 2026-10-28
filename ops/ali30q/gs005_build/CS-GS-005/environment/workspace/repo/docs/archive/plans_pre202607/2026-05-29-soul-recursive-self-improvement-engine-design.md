# Design · Soul = 递归自我提升引擎(positioning + 三源 goal stack + task type 开放 + agent onboarding)

**Date:** 2026-05-29
**Status:** Design locked via brainstorming(user lock 5/29 ~12:30 CST)
**Sibling:**
- 5/27 ADR (rescinded · Soul = 平台共享 self-modify 服务): [session_20260527_soul_shared_service_live_e2e](../../memory/session_20260527_soul_shared_service_live_e2e.md)
- handoff #003 三层闭环 framework: [HANDOFF_20260528_003_increment1_governance_route.md](../HANDOFF_20260528_003_increment1_governance_route.md)
- Inc 1 keystone: [KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md](../KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md)
- Inc 2 settlement: [2026-05-28-inc2-nau-settlement-design.md](./2026-05-28-inc2-nau-settlement-design.md)

**Predecessor handoff:** [HANDOFF_20260529_013_inc2_closeout.md](../HANDOFF_20260529_013_inc2_closeout.md)

---

## Section 0 · Why now(plan vs reality audit · honest）

handoff #003 三层闭环 framework 95% 机械层落地 5/27→5/29:
- 微闭环 · L1 self-improve daemon active(2h cadence · 24h 8 fires · 48h 13 PR shipped)
- 中闭环 · L2 governance executor active(10min cadence · queue empty 自 5/29 02:53)
- 大闭环 · Inc 2 settlement 6/6 BINDING-DONE(本 session · PR #75 draft)

但 3 层都在真空里转 · 因为:
- L1 100% self-loop(改自身源码 · 0 external value)
- L2 0 production proposal(只接 vote 通过 · 但 V5 governance 6h+ dormant · agent-dialog turf · inbound 已 ship 等答)
- L3 `/api/soul/generate` 48h 0 calls(agents 不知道这接口 · 不在 V5/Kairos toolbelt)

用户 5/29 confront:"是不是应该给 soul 设置明确目标 · 开放更多任务 · 让 agent 也调用 soul"。 直接对应 3 件 platform-side 能做的 unblock 动作。

5/27 ADR("Soul = 平台共享 self-modify 服务 · 不独立 agent · 不平台本体")是机械 ADR · 没回答**Soul 存在意义是什么 · 服务对象是谁 · 价值在哪**。本 design 取代 5/27 ADR · 给 Soul 战略 positioning。

---

## Section 1 · 存在意义 + North Star

**Soul exists to close the recursive loop: platform → Soul → platform**

通过吸收三类 improvement signal(self-reflection / governance consensus / agent demand),走 deterministic check pipeline 产出 shipped code/config 改动,outcome 反馈回新 signal · 形成 anchor #2 "产品创新 + 递归自我提升闭环" 的执行层。

**North Star metric(3 个)**:

| Metric | 当前 baseline | 30d 目标 |
|---|---|---|
| `backlog_burn_rate_24h` = Soul-shipped + human-merged PR / 24h | ~3.5(48h 7 merged / 48h ≈ 3.5/d · 100% self-loop) | ≥3 且非 self-loop ≥1 |
| `sustained_composite_delta_30d` = 30d moving avg post-merge composite_delta(Inc 2)| 0(0 production cycle)| ≥0.5(正稳定)|
| `agent_dispatch_24h` = `/api/soul/generate` 调用 / 24h | 0(48h baseline)| ≥1 |

**Soul positioning(replaces 5/27 ADR)**:
- ✅ recursive self-improvement engine for the platform
- ✅ 服务 3 类 caller(平台自反思 / governance consensus / agents demand)
- ✅ 拥有 own goals(via P3 fallback stack + 自治 sense)
- ❌ 不是独立 agent(no persistent process · no voting · no NAU balance · 不持续 main loop)
- ❌ 不是平台本体(platform = backend + agents + governance · Soul = 其中一个 service)
- ❌ 不替 agent 决策(只 ship 已被 vote 或 dispatch 的 task · 不发 spec)

---

## Section 2 · 三源 Goal Stack(优先级 + 来源 + 验证)

```
Priority 1 · governance-route          accepted code-type proposal → Inc 1 soul_executor → ship
Priority 2 · agent-dispatch            POST /api/soul/generate · agents push task spec
Priority 3 · self-reflection           (a) goals.yaml manual override (highest within P3 · seeded by human / cron)
                                       (b) engine_cycle_outcomes drift signal (next_reflection_goal)
                                       (c) docstring/TODO scrape (last resort fallback)
```

**优先级 invariant**:`P1 > P2 > P3` 严格 · 同优先级 FIFO。 每 fire cycle daemon 拉**最高有效优先级** · empty 才 fallback 下一级。

**当前差距**:
- P1 governance queue 自 5/29 02:53 = 0(由 L3 V5 dormancy 阻塞 · 等 V5 修非 Soul 设计范围)
- P2 `/api/soul/generate` 48h = 0 calls(Section 4 解决 onboarding)
- P3-a `goals.yaml` = `goals: []`(implementation 阶段 seed · 不是 design)
- P3-b `next_reflection_goal()` 已存在(查 v_engine_progress 低 composite cycle · 现状无外部 production cycle 故无数据)
- P3-c docs scrape 当前唯一 active fallback(不产生外部价值)

**Schema changes 需要**:
- 加 `goal_source ENUM('p1_governance', 'p2_agent_dispatch', 'p3a_yaml', 'p3b_reflection', 'p3c_docs_scrape')` 列到 daemon cycle 记录表 · for backlog burn rate 分类统计
- 加 `agent_dispatch_log` 表 · 记录 P2 来源(agent_id · task_spec hash · ship outcome)

---

## Section 3 · Task Type 开放(扩 engine.ship 接受种类)

当前 engine 只接 `code` 类(必过 py_compile/ruff/semantic/pytest gate)。新增 task type(本 design ship 2 + parking 2):

| Type | Check pipeline | 复杂度 | This design |
|---|---|---|---|
| `code` | py_compile + ruff + semantic + pytest gate | 现状 | ✅ unchanged |
| `config` | yaml/toml schema validate + idempotent re-apply(re-run diff = 0)| 低 | ✅ ship |
| `schema-migration` | alembic upgrade dry-run(SQLite + Postgres) + production schema diff check | 中 | ✅ ship |
| `test-add` | 新 test 必 FAIL before impl + PASS after | 中 | ⏸️ parking lot(Inc 4+) |
| `prose` | wordcount + drift check + readability score | 中 | ⏸️ parking lot |

**为何只 ship 前 2 个**:`code` + `config` + `schema-migration` 覆盖 platform 90% 真改动需求(代码 + 配置文件 + DB schema)。 后 2 个 type 是产品演进维度 · 不在 anchor #2 闭环关键路径上。

**Check pipeline 接口规范**:每 type 一个 module under `phase3/soul/checks/<type>.py` · export `validate(task_spec, base_dir) -> CheckResult`。 reviewer + council 仍走原路径 · 只 check pipeline 按 type 分发。

---

## Section 4 · Agent Onboarding · 让 V5/Kairos/V7 用 /api/soul/generate

**2 件 · 平台单边可做 · 不绕 anchor #7**:

### 4a · `/api/discover` real impl(取代 handoff #012 stub)

返回平台 services catalog · 含 `soul.generate` 描述:

```json
{
  "services": [
    {
      "id": "soul.generate",
      "endpoint": "POST /api/soul/generate",
      "auth": "X-Agent-Key header · APIKey table",
      "input": { "task_spec": "str · 20-10000 chars · MINIMAL CHANGE phrasing recommended" },
      "output": { "cycle_id": "str", "files_planned": "list[file_diff]", "check_result": "obj" },
      "behavior": "dry-run code generation · NO writes · NO PR · agent uses to validate before committing",
      "sample_task_spec": "Add docstring to function foo in module bar.py · MINIMAL CHANGE",
      "rate_limit": "currently no enforcement · honor system",
      "soul_doc_url": "/docs/SOUL_AGENT_SDK.md"
    },
    {
      "id": "soul.audit_generate",
      "endpoint": "POST /api/soul/audit-generate",
      "...": "..."
    },
    {
      "id": "soul.dispatch",
      "endpoint": "POST /api/soul/dispatch (NEW · this design)",
      "input": { "task_spec": "str", "task_type": "code | config | schema-migration" },
      "output": { "cycle_id": "str", "ship_result": "ship_url | ship_error" },
      "behavior": "FULL ship path · runs engine + checks + opens draft PR · agent waits for cycle_id status"
    }
  ]
}
```

P2 真 agent dispatch 走新 `POST /api/soul/dispatch` 端点(不是只 dry-run 的 `/generate`)· 进 P2 queue · daemon 下个 cycle 吃。

### 4b · `INBOUND_TO_AGENT_DIALOG_20260529_soul_sdk_onboarding.md`

写给 agent-dialog · 内含:
- Soul SDK 完整 doc(3 endpoints · auth · 3 task types · sample task spec per type)
- API key 申请流程(POST `/api/agent/key` · 现存 endpoint)
- 推荐 toolbelt integration pattern(when agent 发现 code bug · 先 POST `/api/soul/generate` dry-run · 满意 POST `/api/soul/dispatch` 正式 ship)
- 决定权属 agent-dialog(anchor #7 · 我们不替 V5/Kairos 决加不加 tool)

---

## Section 5 · Acceptance + Non-goals

**Binding-DONE 此 design 落地的判据**(后续 implementation 责)·:

1. 三源 goal stack 实装 + daemon 真 pick 高优先级 · sentinel test(seed 3 src 各 1 件 · 看 daemon 顺序吃 P1→P2→P3)
2. `config` task type sentinel cycle 跑通(seed config-edit task · ship → draft PR · PR 改某 yaml)
3. `schema-migration` task type sentinel cycle 跑通(seed migration task · alembic dry-run pass · ship → draft PR)
4. `/api/discover` 含 soul.generate / soul.audit_generate / soul.dispatch 3 个描述 · live HTTP 可查
5. `INBOUND_TO_AGENT_DIALOG_20260529_soul_sdk_onboarding.md` 已 ship + SCP'd to agent-dialog workspace
6. **48h 内** ≥1 真 PR 来自 governance source(P1) OR agent dispatch(P2)· 否则该 design 没真 unblock 飞轮 · 需 follow-up

**Non-goals(parking lot)**:
- 具体 fill goals.yaml 内容(implementation 阶段 · 不是 design)
- V5 dormancy fix(anchor #7 turf · agent-dialog 独立 inbound 已存在)
- `test-add` + `prose` task type(Inc 4+)
- 真客户 onboarding(5/27 pivot defer)
- Soul wallet / Soul-as-economic-actor(Inc 3+)
- 替 V5 出题的 platform cron(P3 之前讨论过 · 本 design 显式不做)
- `/api/agent/key` 端点改动(沿用现状)
- Rate limit / 配额机制(本 design 不收 · 後續 if abuse)

**Design 复杂度 audit**:
- 1 endpoint expand(`/api/discover` real impl)
- 1 endpoint new(`POST /api/soul/dispatch`)
- 2 new check pipelines(`config` + `schema-migration`)
- 1 goal stack priority sorter(~30 LOC)
- 1 daemon cycle log table column add
- 1 agent_dispatch_log table new
- 1 INBOUND markdown
- 估 ~500-700 LOC + 2 migrations + 8-10 tests + ~6-8h fresh session(implementation)

---

## Section 6 · Next step

Per brainstorming skill terminal state: invoke **writing-plans** skill to produce executable implementation plan(slice breakdown · concrete TDD task list · file paths · function signatures · test cases).

预估 4 slices serial(per anchor #4 反精神分裂 + workflow-lock):

```
Slice A · goal source classification + agent_dispatch_log + cycle log column   (~150 LOC · 1 migration · 3 tests)
Slice B · /api/discover real impl + /api/soul/dispatch endpoint                (~120 LOC · 4 tests)
Slice C · config task type + check pipeline + sentinel                          (~150 LOC · 3 tests)
Slice D · schema-migration task type + alembic dry-run check + sentinel +       (~180 LOC + 1 migration + agent inbound · 3 tests)
            INBOUND_TO_AGENT_DIALOG_20260529_soul_sdk_onboarding.md
```

每 slice binding-DONE 后再开下 slice。 implementation 全程独立于 V5 dormancy(不依赖 agent-dialog 答)· 不动 5/27 ADR 外的其他系统。

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) (Opus 4.7 · 1M context)

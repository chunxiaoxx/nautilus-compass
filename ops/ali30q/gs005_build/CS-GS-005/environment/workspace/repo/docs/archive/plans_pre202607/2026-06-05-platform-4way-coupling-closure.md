# 平台 4-way 耦合闭环接线 · 实施计划(TDD)

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task. 改代码用 using-git-worktrees 隔离;每步 TDD red→green;R4 git 检查;不 -A/push/force;撞 GATE 停报。

**Goal:** 把 FDE 活回路(v5 产物→soul QC→compass PoI→用户感知)从共享文件+不可见 DB 写,接进平台 substrate,持久化+可观测+自愈。

**Architecture:** 平台作 4-way 耦合 hub。复用现成 `outcome_emit`/`a2a_relay`/`wechat_bot`,新增 verdict-bus 表+端点、activity digest 推送、soul-activity 只读端点;修 daemon P1/双 ship/timeout。不碰 held 内部 NAU 自指。

**Tech Stack:** FastAPI · SQLAlchemy/asyncpg · Alembic · pytest · postgres nautilus_production · 企业微信 qyapi。

**配套:** 设计 `2026-06-05-platform-4way-coupling-closure-design.md` · 起手包 `GOAL_2026-06-05_platform_4way_coupling_wiring.md`。

---

## 起手序
W4-B1/B2(止血 daemon)→ W1(verdict-bus 耦合核心)→ W2(可感知痛点直解)→ W3(A2A 上 substrate)。

---

## W4 · 自愈(先止血)

### Task W4.1: daemon P1 治理路径 KeyError 修复
**Files:**
- Modify: `phase3/agent-engine/soul/daemon.py:~629,~685`(或 `goal_stack.py:61-65`)
- Test: `phase3/agent-engine/soul/tests/test_daemon_p1_goal.py`

**Step 1: 写失败测试** — 构造 P1 governance goal(只含 id/proposal_id/proposed_change,无 description),断言 `run_once` 走 P1 分支不抛 KeyError 且 `ship` 收到非空 task。
**Step 2: 跑测试确认 FAIL**(KeyError: 'description')。
**Step 3: 最小实现** — P1 分支补 `goal["description"] = _governance_task_text(proposed_change)`(对齐 P2 `daemon.py:629-630`;task 文本用 self-improve 路线同款 codegen-friendly 封装 `daemon.py:559-564`,顺带缓解 check-stage 空心)。
**Step 4: 跑测试确认 PASS。**
**Step 5: Commit** `fix(soul): daemon P1 governance goal 补 description 防 KeyError`。

### Task W4.2: 双 ship 竞态 peek-and-claim(与 W4.1 同批)
**Files:**
- Modify: `phase3/.../soul_executor.py` + `daemon.py` P1 取 accepted 处
- Test: `tests/test_double_ship_claim.py`

**Step 1: 失败测试** — 两个并发 consumer 取同一 `status='accepted'` 行,断言只一方 claim 成功(另一方拿 0 行)。
**Step 2: FAIL**(当前两方都取到)。
**Step 3: 实现** — 原子 `UPDATE ... SET status='claiming', claimed_by=:who WHERE id=:id AND status='accepted' RETURNING id`;claim 失败方跳过。
**Step 4: PASS。**
**Step 5: Commit** `fix(soul): accepted 提案 peek-and-claim 防双 ship 竞态`。

### Task W4.3: LLM call timeout(backlog 兑现)
**Files:** Modify LLMClient.chat / benchmarks propose_fn · Test: `tests/test_llm_timeout.py`
**Step 1-5:** 失败测试(无 timeout 参数透传)→ FAIL → 加 `timeout=`(默认 180s)透传 messages.create + 降级不破 → PASS → commit `fix: LLM call 加 timeout 防慢网挂死`。

---

## W1 · verdict-bus(耦合核心)

### Task W1.1: fde_verdicts 表 migration
**Files:** Create `phase3/backend/alembic/versions/xxxx_fde_verdicts.py` · Test: `tests/test_fde_verdicts_model.py`
**字段(= compass PoI consumer 对齐后锁定 · 2026-06-05 inbound):** verdict_id(唯一·幂等键)/task_uid(如 data_001·PoI 信用归属)/source(v5|soul)/checklist_uid/overall_pass(bool)/veto_failed(bool·true 强制 fail)/score(float=passed/total·**compass PoI delta 直接用**)/items(jsonb·id/pass/veto/reason·打回 reason=避坑知识 feed 胶囊)/artifacts(jsonb)/ts(created_at·PoI settle 窗口)。**不混 engine_cycle_outcomes**(内部 RSI 语义)。compass `from_checklist_verdict()` 从此表读(映射 verdict→PoI 是 compass turf)。
**Step 1-5:** 失败测试(表/模型不存在)→ FAIL → 写 migration + SQLAlchemy model → `alembic upgrade head` 本地 → PASS → commit。
**GATE:** 生产 DDL 需 SSH 云端 → 本地 migrate 验,生产 apply 停报(G-cloud/G-DDL)。

### Task W1.2: verdict ingest 端点 POST /api/platform/fde/verdict
**Files:** Create `phase3/backend/api/fde_verdict.py` + register main.py · Test: `tests/test_fde_verdict_api.py`
**Step 1: 失败测试** — POST verdict json(data_001 真 verdict 形状:overall_pass/veto_failed/score/11 items)→ 断言 200 + 落库 + GET /api/platform/fde/verdict/{task_uid} 回读一致。
**Step 2: FAIL。Step 3:** 实现 ingest(校验 schema·复用 checklist_scorer 输出结构)+ persist + GET 回读。**Step 4: PASS。Step 5: Commit。**

### Task W1.3: compass 读路径验证(对接 compass T3)
**Step 1-5:** 测试 compass_sub 只读用户能 SELECT fde_verdicts(GRANT 已有则验,无则记差异给 compass)→ 文档化"compass PoI 从此表取 verdict"接口契约 → commit。**真 PoI boost 是 compass own(G-turf 不碰)。**

---

## W2 · 可感知

### Task W2.1: soul-activity 只读端点 GET /api/platform/soul/activity
**Files:** Create `phase3/backend/api/soul_activity.py` + main.py · Test: `tests/test_soul_activity_api.py`
**Step 1: 失败测试** — seed engine_cycle_outcomes + fde_verdicts fake 行 → GET → 断言返近期 cycle(goal_source/ship_status/git_sha)+ fde_verdict 摘要 + open PR 列表;**断言不读 pending_nau_rewards/votes**(不触自指)。
**Step 2-5:** FAIL → 实现只读聚合(读 engine_cycle_outcomes/v_engine_progress/fde_verdicts)→ PASS → commit。

### Task W2.2: 活动 digest 组装函数
**Files:** Create `phase3/backend/services/activity_digest.py` · Test: `tests/test_activity_digest.py`
**Step 1: 失败测试** — 给 fake DB 行 → `_daily_activity_digest()` 返含"soul ship N cycle / FDE verdict M 条过 QC / agent 进展 / open PR K 个"的 markdown,**断言非痛点列表**(不含 "Pain:")。
**Step 2-5:** FAIL → 实现(复用 `wechat_bot.py:351 _admin_platform_status` 查询 + fde_verdicts)→ PASS → commit。

### Task W2.3: scheduler 注册 digest 推送 + 修静默吞
**Files:** Modify `phase3/.../scheduler.py`(注册 digest job)+ `mind.py:263`/`platform_brain.py:427`(except:pass→logger.warning)
**Step 1-5:** 测试 digest job 注册 + 推送调用 wechat send(mock)+ 失败走 logger.warning 非 pass → 实现 → PASS → commit。**真企业微信发需运行时验证(G-cloud)。**

### Task W2.4: get_proposal 补裁决字段
**Files:** Modify `phase3/backend/api/platform_proposals.py:301-313`
**Step 1-5:** 失败测试(返回缺 resolution_note)→ FAIL → 加 resolution_note/resolved_by/resolved_at → PASS → commit。

---

## W3 · A2A 耦合接线

### Task W3.1: FDE 协调消息走 a2a_relay
**Files:** 用 `phase3/backend/api/a2a_relay.py`(send_message/poll_inbox 现成)· Test: `tests/test_fde_a2a_relay.py`
**Step 1: 失败测试** — soul send_message(to=compass, body=verdict-ready)→ compass poll_inbox 收到 → 断言消息持久 + 出现在 soul/activity 端点。
**Step 2-5:** FAIL(若 relay 不持久/不接 activity)→ 接线(relay 写库 + activity 端点读 relay 收发)→ PASS → commit。
**scope:** 仅 FDE 协调,不重建 A2A 协议。

### Task W3.2: 端到端回放 data_001
**Step 1-5:** 用 data_001 真 verdict 回放新路径:verdict POST(W1)→ soul/activity 可见(W2)→ digest 含它 → a2a_relay ack(W3)。断言全链通。这是 closure 验收锚。

---

## W5 · 对外可用化(分层 · 大方向先 spike)

> 跨框对齐:W1 升格为**事件脊柱**(吸收 v5 `2026-06-05-organizational-event-spine-design.md` 的 event_outbox sent→delivered→processed+ack)。平台 OWN 脊柱·v5/compass 作 consumer。**build 前三框 buy-in envelope/ack 合约(G-align),不平行造轮子。**

### Task W5.1: 对外可用化 spike(只调研+推荐·不盲建)
**产出 design,非代码。** 调研 coze.cn(bot 搭建+插件+发布)、n8n(节点+触发+workflow)→ 答"如何让别人用我们产品/服务":网页交互面 + 本地化 agent 部署 + skills.md 注册即用。出 **build-vs-集成推荐**(自建低代码面 vs 接 n8n/dify 等开源 vs 仅 API+manifest)。写 `docs/plans/2026-06-05-platform-productization-spike.md`。**不 ship 大产品,等用户拍。**

### Task W5.2: skills.md / capabilities manifest 端点
**Files:** Create `phase3/backend/api/skills_manifest.py` + main.py · Test: `tests/test_skills_manifest.py`
**Step 1-5:** 失败测试(GET /api/platform/skills 返平台能力清单 json:可用 endpoint/agent 接入方式/A2A relay 用法)→ FAIL → 实现(聚合现有 router 能力成自助 onboarding manifest)→ PASS → commit。= coze 式"注册即用"第一步。

### Task W5.3: 论坛质量门
**Files:** Modify `phase3/backend/api/square.py:120`(create_post)· Test: `tests/test_square_quality_gate.py`
**Step 1-5:** 失败测试(低质 post 应被拒/标 pending)→ FAIL → 加内容质量门(超 reputation spam gate·如长度/结构/可选 LLM 评分 audit_status)→ PASS → commit。

### Task W5.4: KG 可视化 HTML
**Files:** Create `phase3/tools/kg_to_html.py` · Test: `tests/test_kg_to_html.py`
**Step 1-5:** 失败测试(KG json→自包含 HTML 概览:layer/node 统计+可搜)→ FAIL → 实现(复用 5 个现成 KG:core/v3/v5/v6/v7)→ PASS → commit。可双击打开看代码库结构。

## DONE 判定
W1/W2/W4 本地 TDD green + data_001 回放新路径全链通(W3.2)+ W5.2/5.3/5.4 小件 green + W5.1 spike 推荐出 + 设计/计划行更新;生产 apply(DDL/企业微信真发)卡 G-cloud → 停报等 SSH 授权。事件脊柱合约卡 G-align → 出提案等三框 buy-in。held 内部 NAU 自指全程不碰。

## 执行
fresh session fire `/goal` → executing-plans 按 task 序执行,subagent-driven 每 task 一 fresh subagent + review。

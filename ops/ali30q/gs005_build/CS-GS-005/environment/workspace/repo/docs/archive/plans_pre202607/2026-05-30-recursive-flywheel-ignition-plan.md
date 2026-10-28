# Recursive Flywheel Ignition · Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Each task is bite-sized (one binding-DONE 真目标) · commit per task · workflow lock-goal-until-done (5/27 feedback).

**Goal:** 执行 brainstorming v3 design (`docs/plans/2026-05-30-recursive-flywheel-ignition-design.md`) 真 ship · 让飞轮真转动 · 触发 anchor #2 wedge swap (Path B OSS reliability) + compass v3 L4 (6/5 due) + 反 5 周复发 invent。

**Architecture:** 7 streams (A-G) · P0 临界 (A+B · 6/5 due · ~40 min) · P1 反复发 (C+D · 1-7 day · 跨 session) · P2 infra hygiene (E+F · 1 session) · P3 parking (G · 等 user 决). binding-DONE workflow lock: 一次 1 task complete 后再 next · 不并发。

**Tech Stack:** Markdown memory edit (anchor update) · Markdown doc create (contract OUTBOUND) · Python TDD (EvoMap integration + silent break fix) · systemd unit edit (F12.1 sync fix) · git per-task commit (R4 no push 留 user 决)。

**真前置 reads:**
- `docs/plans/2026-05-30-recursive-flywheel-ignition-design.md` (本 plan source-of-truth)
- `docs/HANDOFF_20260530_017_v5_inbound_48h_status.md` (handoff #017 真状态)
- `memory/anchor_user_strategic_compass.md` (anchor #2/#7 update target)
- `memory/feedback_pivot_product_loop_over_customer_20260527.md` (5/27 PIVOT 真依据)

**R3 时间预算:** 本 plan 跨 session · 单 session ≤ 4h. 推荐 fresh session 起 Task A1.

---

## Task A1: anchor #2 真意 update memory (wedge swap not customer defer)

**真目标 binding-DONE:** anchor #2 描述跟 5/27 PIVOT 真决策 (WEDGE_PIVOT_DECISION_AUDIT) 一致 · 防再 drift。

**Files:**
- Create: `C:\Users\chunx\.claude\projects\C--Users-chunx-Projects-nautilus-core\memory\feedback_anchor_2_wedge_swap_path_b_20260530.md`
- Modify: `C:\Users\chunx\.claude\projects\C--Users-chunx-Projects-nautilus-core\memory\MEMORY.md` (append entry under "PIVOT" section)

**Step 1: write new memory file**

```markdown
---
name: feedback-anchor-2-wedge-swap-path-b-20260530
description: anchor #2 真意 update · 5/27 PIVOT 实际是 wedge swap (Path A→B) · 不是 customer defer
metadata:
  type: feedback
---

**2026-05-30 anchor #2 真意 correction**

原 anchor #2 描述:"产品创新 + 递归自我提升闭环优先 · 客户获取 defer (2026-05-27 pivot)"

5/27 PIVOT 真决策 (per WEDGE_PIVOT_DECISION_AUDIT):
- 不是 "客户 defer" 是 **wedge swap**
- Path A (算法备案 audit ¥30k/件) DROP · 5/5 critical need MISS · 5% 达成率
- Path B (OSS multi-agent reliability eval) LOCK · 4/4 critical met · 25-35% 达成率
- customer line NOT paused · 换 buyer wedge

**真 anchor #2 措辞:**
"产品创新 + 递归自我提升闭环优先 · customer wedge swap to Path B (OSS multi-agent reliability eval · 5/27 approved · Week 1 task list: LICENSE clean / README rewrite / CLI v0 / dev.to article / Show HN / GitHub issue cross-project thread) · Path A regulatory audit dropped"

**Why:** brainstorming v2 + v3 frame 因 anchor #2 描述误 · 把 PIVOT 当 "customer paused" · 实际 5/27-5/30 三天 0 GTM motion · 反 PIVOT 真意。

**How to apply:**
- session-start anchor surface 必含 "wedge swap Path B" 而不是 "customer defer"
- 任何 ship 件问 "对 Path B Week 1 task 有贡献吗?" · 0 贡献 = parking
- 不与 [[feedback-pivot-product-loop-over-customer-20260527]] 冲突 · 是 deeper correction

[[anchor-user-strategic-compass]] [[feedback-pivot-product-loop-over-customer-20260527]] [[wedge-pivot-decision-audit]]
```

**Step 2: append MEMORY.md entry**

Read `MEMORY.md` find "PIVOT" section (5/27 entries) · append 1 line:
```
- [anchor-2-wedge-swap-path-b](./feedback_anchor_2_wedge_swap_path_b_20260530.md) — 5/27 PIVOT 真意 = wedge swap Path A→B · NOT customer defer · anchor #2 措辞 correction
```

**Step 3: verify both files exist + grep wedge swap**

Run: `grep -c "wedge swap" memory/feedback_anchor_2_wedge_swap_path_b_20260530.md`
Expected: `≥3` (3+ wedge swap occurrence)

Run: `grep "wedge.swap" memory/MEMORY.md`
Expected: 1 line match (新加 entry)

**Step 4: commit**

```bash
cd /c/Users/chunx/Projects/nautilus-core
# Note: memory 在 ~/.claude/projects/... 不在 repo · 不需 git add
# 真 commit 是 anchor update doc · 留 next task A2
```

Memory 是 user-level file · 不在 repo. Step 4 跳过 git commit · 直接 next Task A2 (anchor #7) 一起 commit OR 各自 commit.

binding-DONE 标准:
- ✅ 新 memory file 存在
- ✅ MEMORY.md 含新 entry
- ✅ grep 真证 entry 写入

---

## Task A2: anchor #7 真意 update memory (brand = Nautilus · compass = component)

**真目标 binding-DONE:** anchor #7 brand 表述跟 README/public-facing 一致 (Nautilus 不是 nautilus-compass)。

**Files:**
- Create: `C:\Users\chunx\.claude\projects\C--Users-chunx-Projects-nautilus-core\memory\feedback_anchor_7_brand_nautilus_compass_component_20260530.md`
- Modify: `C:\Users\chunx\.claude\projects\C--Users-chunx-Projects-nautilus-core\memory\MEMORY.md` (append)

**Step 1: write new memory file**

```markdown
---
name: feedback-anchor-7-brand-nautilus-compass-component-20260530
description: anchor #7 真意 update · brand 真名 Nautilus · compass = internal architecture component
metadata:
  type: feedback
---

**2026-05-30 anchor #7 真意 correction**

原 anchor #7:"brand 真名 · nautilus-compass(原 zenmind-mem)"

真状态 (per README.md + public-facing + Agent E audit):
- brand = **Nautilus** (对标 Anthropic 中国落地 · "Nautilus | 智涌")
- compass = **internal architecture component name** (memory subsystem · cross-agent substrate)
- nautilus-compass = dev-tools 命名 (MCP plugin · dialog 自称) · NOT product brand

**真 anchor #7 措辞:**
"brand 真名 Nautilus (产品 + GTM 对外) · compass = internal architecture component (cross-agent substrate · memory subsystem) · cross-dialog turf 平台不动 V5/Kairos/compass 代码 · platform 内 soul + audit · agent 内 V5 darwin · 分界明确"

**Why:** brainstorming v3 audit 凝固 brand 真名 = Nautilus · 跟 system reminder hook 的 "nautilus-compass" 表述不一致 · 此 entry 是 deeper correction。

**How to apply:**
- session-start anchor surface "brand 真名 Nautilus" 不是 nautilus-compass
- GTM doc / README / outbound 都用 Nautilus
- 内部 architecture diagram / dialog naming 用 compass (component layer)

[[anchor-user-strategic-compass]] [[anchor-2-wedge-swap-path-b]]
```

**Step 2: append MEMORY.md entry**

Add 1 line under appropriate section:
```
- [anchor-7-brand-nautilus-compass-component](./feedback_anchor_7_brand_nautilus_compass_component_20260530.md) — brand 真名 Nautilus · compass = internal component · NOT nautilus-compass
```

**Step 3: verify**

Run: `ls memory/feedback_anchor_7_brand_nautilus_compass_component_20260530.md`
Expected: file path output (file exists)

Run: `grep "brand.*Nautilus" memory/MEMORY.md`
Expected: 1+ line match

**Step 4: commit (combined A1+A2)**

Memory 不在 repo · 跳 git commit。

binding-DONE 标准:
- ✅ 2 anchor entries 真写入 memory
- ✅ MEMORY.md surface 2 个新 entry
- ✅ 下次 session-start anchor surface 含新表述 (auto by hook)

---

## Task B1: write OUTBOUND_TO_V5 cnt_compass_v5_outcome_b2 contract spec

**真目标 binding-DONE:** issue contract OUTBOUND doc 给 V5 dialog · 6/5 due 临界。

**Files:**
- Create: `phase3/docs/OUTBOUND_TO_V5_DIALOG_outcome_ledger_subscribe_request_20260530.md` (per existing OUTBOUND naming pattern)

NOTE: 真 issue 路径可能是平台→V5 · 也可能是 compass→V5 · 平台只是 cc。Step 0 先 confirm。

**Step 0: confirm contract direction**

Read `docs/HANDOFF_20260530_017_v5_inbound_48h_status.md` §4.4 cross-dialog contract status · 看 `cnt_compass_v5_outcome_b2` 真 issuer。若 issuer = compass-dialog · 平台不 issue · 改写 INBOUND alert 给 compass-dialog。

```bash
grep -n "compass_v5_outcome_b2\|cnt_compass_v5" docs/HANDOFF_20260530_017_v5_inbound_48h_status.md
```

**决策点:**
- 若 issuer = compass-dialog → 跳 Task B1 · 改 Task B1' write `INBOUND_TO_COMPASS_DIALOG_outcome_b2_status_check_20260530.md` (alert compass · 5 day 余)
- 若 issuer = platform-dialog → continue Step 1 (write OUTBOUND)

**Step 1: write OUTBOUND doc (assuming platform issues)**

照 `cnt_compass_soul_sub_a1` 模式 (Agent D 引):

```markdown
# OUTBOUND_TO_V5_DIALOG · outcome_ledger subscribe request · contract cnt_compass_v5_outcome_b2

**Issued by**: platform-soul-dialog (on behalf of compass-dialog · cross-dialog coordination)
**Issued at**: 2026-05-30 ~17:30 CST
**Due**: 2026-06-05 18:00 CST
**Contract ID**: cnt_compass_v5_outcome_b2
**Reference**: cnt_compass_soul_sub_a1 已 FULL ACK consumed 5/30 17:30 (close_loop 17.92h)

## Request 4 子项 ack

### (a) Access path
V5 outcome_ledger table read-only DB user
- 推荐 user 名: `compass_sub_v5` (parallel to `compass_sub` for platform)
- 推荐 grant: SELECT only on outcome_ledger
- credentials 在 next session 通过 follow-up contract 安全交付

### (b) Schema 文档
完整列出 outcome_ledger 真 schema:
- 列名 + 类型 + nullable
- index 列
- FK 关系
- partition strategy (if any)

### (c) 7d 稳定性承诺
承诺范围:
- 删列 / 改列名 / 改列类型 / 改 PK → 必须 7d 前 notify compass-dialog
- 无 notify 覆盖: 加 nullable 列 / 加索引 / 加 trigger / 加 partition

### (d) Close-loop session
V5 dialog ack 时 commit `session_<yyyymmdd-hhmm>_v5_to_compass_outcome_sub_ack_CONSUMES_cnt_compass_v5_outcome_b2.md`

## Context

compass v3 L4 cross-agent substrate 设计 (per nautilus-compass repo `docs/plans/2026-05-29-compass-comprehensive-uplift-design.md`):
- compass 通过 read-only subscribe platform engine_cycle_outcomes (sub_a1 已 ack) + V5 outcome_ledger (本 contract) 闭合 cross-agent 经济记忆
- L4 = "记忆在 agent 之间 · 不是 agent 内"
- V5 outcome_ledger 是 闭环真证 source (V5 task fulfillment + NAU earn evidence)

## anchor #7 真守

- 本 OUTBOUND 不强 V5 ack · 留 V5 dialog 真自决
- 不动 V5 代码 · 不要求 V5 wrapper / shim
- read-only access · 不改 V5 economy

## References

- `cnt_compass_soul_sub_a1` close-loop session: nautilus-compass repo session_20260530-1730
- compass v3 design: nautilus-compass `docs/plans/2026-05-29-compass-comprehensive-uplift-design.md`
- handoff #017 §4.4 cross-dialog contract status
```

**Step 2: verify doc**

Run: `wc -l phase3/docs/OUTBOUND_TO_V5_DIALOG_outcome_ledger_subscribe_request_20260530.md`
Expected: ≥40 lines

**Step 3: branch off master + commit**

```bash
cd /c/Users/chunx/Projects/nautilus-core
git checkout -b b1-outbound-v5-outcome-b2 origin/master
git add phase3/docs/OUTBOUND_TO_V5_DIALOG_outcome_ledger_subscribe_request_20260530.md
git commit -m "docs(outbound): cnt_compass_v5_outcome_b2 contract issue · V5 outcome_ledger subscribe

  6/5 due 临界 · 5 day 余. compass v3 L4 cross-agent substrate plan.
  sub_a1 5/30 已 FULL ACK consumed · b2 outstanding.
  Read-only access · anchor #7 不动 V5 代码 · 留 V5 dialog 真自决.

  docs only · 0 code."
```

binding-DONE 标准:
- ✅ OUTBOUND doc 真 commit
- ✅ V5 dialog 收到 doc (依赖 V5 dialog 自决 check inbox)
- 留 user push + V5 ack 真证 close-loop

---

## Task C1-C6: Path B GTM Week 1 (跨 session · 4-7 day)

**真目标 binding-DONE:** 5/27 approved Path B GTM Week 1 task list 真 execute · 触 OSS adoption signal。

C1-C6 真做完需 4-7 day · 跨多 session · 本 plan 仅 sketch · executing-plans 阶段 may break each Cx 成独立 sub-plan。

### Task C1: LICENSE clean

**Files:**
- Modify: `LICENSE` (verify Apache 2.0 / MIT · clean header)
- Modify: `phase3/backend/services/*.py` (verify 0 GPL contamination)

**Step 1:** read LICENSE · confirm Apache 2.0 / MIT · 0 GPL clause
**Step 2:** grep "GPL\|copyleft" phase3/ · expect 0 matches
**Step 3:** commit if change needed: `chore(license): apache 2.0 cleanup for OSS Path B`

binding-DONE 标准: LICENSE 真 OSS-compatible · `gh repo view` shows correct license badge

### Task C2: README rewrite (Nautilus brand · OSS positioning)

**Files:**
- Modify: `README.md` (top-level rewrite)
- Reference: anchor #7 真意 (brand = Nautilus · compass = component)

**Step 1:** read current README.md · note current positioning
**Step 2:** draft new README:
  - Title: "Nautilus · Multi-Agent Reliability Council"
  - One-line pitch: "Agent ecosystem that audits itself · cryptographic provenance · open source"
  - Quickstart: 3 lines (install + run + verify)
  - Architecture diagram (L1 / L2 / L3)
  - "Why Nautilus?" 4 critical met (multi-agent primitives / quality measurement / audit trail / cross-agent comparison)
  - Self-pilot cert example URL
  - Roadmap (Week 1: CLI v0 · Week 2: SaaS pilot · Week 3+: SaaS launch)
**Step 3:** verify markdown renders (Read README.md back)
**Step 4:** commit `docs(readme): rewrite for OSS Path B GTM · Nautilus brand`

binding-DONE 标准: README real 渲染 OK · 1 OSS dev 看完能 onboard 真 understand 价值

### Task C3: CLI v0 (`nautilus engine <task>` + `nautilus cert verify <id>`)

**Files:**
- Create: `phase3/cli/nautilus.py` (entry-point)
- Create: `phase3/cli/__init__.py`
- Create: `phase3/cli/tests/test_nautilus_cli.py`
- Modify: `phase3/setup.py` OR `pyproject.toml` (entry-point register)

**Step 1:** TDD red · test_nautilus_engine_subcommand_invokes_engine_ship
**Step 2:** TDD red · test_nautilus_cert_verify_subcommand_calls_api
**Step 3:** verify both tests fail (`pytest phase3/cli/tests/`)
**Step 4:** implement minimal CLI (argparse + 2 subcommand)
**Step 5:** verify tests pass
**Step 6:** commit `feat(cli): v0 nautilus engine + cert verify subcommands`

binding-DONE 标准: `pip install -e .` 后 `nautilus engine "hello"` 真 invoke engine ship · `nautilus cert verify <id>` 真 fetch

### Task C4: dev.to article draft

**Files:**
- Create: `docs/blog/2026-05-30-multi-agent-reliability-council.md`

**Step 1:** draft article (1500-2500 words):
  - hook: "We built a multi-agent reliability council that audits itself"
  - problem: multi-agent system reliability blackbox
  - solution: RAID-2 council + HMAC cert + compass memory
  - architecture overview
  - self-pilot cert example
  - "what's next" (SaaS pilot · contact)
**Step 2:** review by AI (no syntax error · no fake claim)
**Step 3:** commit `docs(blog): dev.to article draft · multi-agent reliability council`
**Step 4:** ⚠️ R3 真 ship: user 真 publish 到 dev.to (我无法直接 publish 公网)

binding-DONE 标准: dev.to article 真 live · URL 可访问 · ≥1 view in 24h

### Task C5: Show HN draft + post

**Files:**
- Create: `docs/blog/2026-05-30-show-hn-draft.md`

**Step 1:** draft Show HN post (200-400 words):
  - title: "Show HN: Nautilus – Multi-agent reliability council with cryptographic audit"
  - body: 1 sentence pitch + GitHub link + dev.to article link + "What feedback would you want?"
**Step 2:** user review
**Step 3:** ⚠️ R3 真 ship: user 真 post Show HN (我无法直接 post 公网)

binding-DONE 标准: Show HN post 真 live · ≥1 comment in 48h

### Task C6: 3x GitHub issue cross-project thread

**Files:**
- Create: `docs/blog/2026-05-30-cross-project-issue-template.md` (template for 3 issue)

**Step 1:** draft issue template:
  - title: "Cross-project reliability eval discussion · Nautilus council"
  - body: 200-word context + question + link
**Step 2:** customize for LangChain · CrewAI · AutoGen (3 issue · 3 customization)
**Step 3:** ⚠️ R3 真 ship: user 真 post 3 issue 到 3 repo (我无法 post · 需 user gh)

binding-DONE 标准: 3 issue 真 posted · ≥1 reply within 7d

---

## Task D1: reuse Phase 3 EvoMap knowledge capsule for goal_stack priority

**真目标 binding-DONE:** 反第 5 次 invent · 复用 EvoMap transferability score 替代 goal_stack 3-source heuristic。

**Files:**
- Verify exist: `phase3/backend/services/knowledge_capsule.py`
- Verify exist: `phase3/backend/services/epiplexity_service.py` (or similar)
- Modify: `phase3/soul/goal_stack.py` (priority logic)
- Test: `phase3/soul/tests/test_goal_stack_evomap_integration.py` (新)

**Step 1: verify Phase 3 asset 真存在**

Run: `find phase3/backend -name "knowledge_capsule*" -o -name "epiplexity*" 2>/dev/null`
Expected: 1+ file path output

**决策点:**
- 若 0 file → Agent F 引证错 · Task D1 cancel · 留 parking
- 若 file 真在 → continue

**Step 2: TDD red · test_goal_stack_uses_epiplexity_transferability_score**

```python
def test_goal_stack_uses_epiplexity_transferability_score(monkeypatch):
    # 给 goal P1, P2, P3 各 1 个 candidate
    # mock epiplexity_service 返 transferability score (P3 > P1 > P2 顺序)
    # 跑 goal_stack.next_goal()
    # 期望 return P3 (因 transferability score 最高)
    ...
```

**Step 3:** verify test fail (no integration yet)
**Step 4:** modify `goal_stack.py` 加 transferability score lookup
**Step 5:** verify test pass + full soul suite green (no regression)
**Step 6:** commit `feat(soul): goal_stack 复用 EvoMap transferability score · 反第 5 次 invent`

binding-DONE 标准:
- ✅ test PASS
- ✅ full soul suite 0 regression
- ✅ goal_stack 真 reference epiplexity_service

---

## Task E1: compass_bounty_bridge.py stub (fix silent fail)

**真目标 binding-DONE:** audit_cert_generator.py:39 ImportError silent fail 修补 · PoI trail 至少有 stub。

**Files:**
- Create: `phase3/backend/services/compass_bounty_bridge.py`
- Test: `phase3/backend/tests/test_compass_bounty_bridge_stub.py`

**Step 1: TDD red · test_poi_cite_trail_returns_empty_list_on_compass_unavailable**

```python
def test_poi_cite_trail_returns_empty_list_on_compass_unavailable(monkeypatch):
    from services.compass_bounty_bridge import poi_cite_trail
    result = poi_cite_trail(task_spec="test", output="test")
    assert result == []  # fallback when compass MCP unavailable
```

**Step 2: TDD red · test_audit_cert_generator_imports_compass_bridge_success**

```python
def test_audit_cert_generator_imports_compass_bridge_success():
    from services.audit_cert_generator import generate_cert  # 之前 silent fail · 现在 OK
    # 不真 invoke · 只验 import 不再 ImportError
```

**Step 3:** verify both tests fail (no module · ImportError)
**Step 4:** create stub module (~60 LOC):

```python
"""compass_bounty_bridge · stub for PoI cite trail integration.

Real impl awaits compass v3 L4 substrate (cnt_compass_v5_outcome_b2 6/5 due).
Stub returns [] so audit_cert_generator import succeeds + PoI field empty.
"""
def poi_cite_trail(task_spec: str, output: str) -> list:
    """Return PoI cite trail · stub returns []. Compass v3 wire pending."""
    return []
```

**Step 5:** verify tests pass
**Step 6:** commit `feat(audit): compass_bounty_bridge stub · fix audit_cert_generator silent ImportError`

binding-DONE 标准: audit cert generation 不再 silent fail · `from services.compass_bounty_bridge import poi_cite_trail` 真 success

---

## Task E2: anomaly_detection cron emit PLATFORM_ANOMALY event

**真目标 binding-DONE:** event_bus PLATFORM_ANOMALY 真接通 emit · 让 anomaly→event chain 真 fire。

**Files:**
- Modify: `phase3/backend/services/cron_registry.py:266+` (anomaly_detection fn)
- Test: `phase3/backend/tests/test_anomaly_detection_emits_event.py`

**Step 1: TDD red · test_anomaly_detection_emits_platform_anomaly_when_anomalies_detected**

```python
async def test_anomaly_detection_emits_platform_anomaly_when_anomalies_detected(monkeypatch):
    # mock observatory 返 anomaly list (非空)
    # mock event_bus.emit capture call
    # 跑 anomaly_detection fn
    # 期望 emit("platform.anomaly", payload) 真 called
    ...
```

**Step 2:** verify test fail (无 emit call)
**Step 3:** modify cron_registry.py:266 加 `await _emit("platform.anomaly", {"anomalies": anomalies_raw, "count": len(anomalies_raw)})`
**Step 4:** verify test pass
**Step 5:** commit `feat(event_bus): anomaly_detection emit PLATFORM_ANOMALY · event chain 接通`

binding-DONE 标准: anomaly_detection fire → event_bus.emit 真 called · subscribers (待 加) 真 receive

---

## Task E3: soul_consumer 退役 OR retarget audit

**真目标 binding-DONE:** soul_consumer (legacy · target orphan platform_proposals table) 真 audit · decide retire OR retarget · 解 split brain。

**Files:**
- Read-only audit: `phase3/backend/services/soul_consumer.py`
- Read-only audit: `phase3/backend/services/soul_executor.py`
- Modify (based on audit): `soul_consumer.py` OR delete + migration

**Step 1:** read `soul_consumer.py` · 真 list 所有 caller (grep "from.*soul_consumer\|import.*soul_consumer" phase3/)

**决策点:**
- 若 0 caller → 真 retire · delete file + commit `chore(soul): retire soul_consumer · orphan target table · 0 caller`
- 若 真 caller 在 → retarget · change target table 从 `platform_proposals` 到 `platform_improvement_proposals`

**Step 2: based on decision · TDD + implement**

**Step 3:** commit

binding-DONE 标准: split brain 真解 · 0 dead code OR 真 retarget alive

---

## Task F1: F12.1 service ExecStartPre git pull (3 LOC · sync fix)

**真目标 binding-DONE:** `nautilus-soul.service` 加 ExecStartPre · 让 PR merge 后 cloud daemon 自动用新 code · 解 F12 finding。

**Files:**
- Modify: `phase3/soul/systemd/nautilus-soul.service`

**Step 1: edit service file**

```diff
 [Service]
 Type=oneshot
 User=ubuntu
 Group=ubuntu
 WorkingDirectory=/home/ubuntu/nautilus-soul-workspace/phase3
 EnvironmentFile=/home/ubuntu/nautilus-soul-workspace/.soul-env
+ExecStartPre=/usr/bin/git -C /home/ubuntu/nautilus-soul-workspace fetch origin master
+ExecStartPre=/usr/bin/git -C /home/ubuntu/nautilus-soul-workspace reset --hard origin/master
 ExecStart=/usr/bin/python3 -m soul.daemon
```

**Step 2:** verify file 真改 (`grep ExecStartPre phase3/soul/systemd/nautilus-soul.service`)
**Step 3:** ⚠️ R3 真 ship: user 真 SSH cloud + `sudo cp phase3/soul/systemd/nautilus-soul.service /etc/systemd/system/` + `sudo systemctl daemon-reload` (我无 cloud SSH access)
**Step 4:** commit (本地)

```bash
git checkout -b f12.1-sync-fix-service-execstartpre origin/master
git add phase3/soul/systemd/nautilus-soul.service
git commit -m "fix(soul): F12.1 · service ExecStartPre git fetch + reset · auto-sync origin/master

  F12 finding · cloud daemon NOT auto-pull · PR merge 不真生效.
  3 LOC fix · 真最低维护 (anchor #3 反 D · anchor #5 不重造轮子).
  PR #96 + F11 fix merge 后 cloud 真生效需此 fix + 用户 SSH apply."
```

binding-DONE 标准: service file 真改 · commit done · 留 user SSH apply (我无法 ship cloud-side)

---

## Task G: parking (honest abandon top 3 · 等 user 决)

不本 plan 内 execute。Parking lot 留 user 真授权后再:
- G1 Kairos self-edit experiment archive
- G2 MCP connector single-stack archive
- G3 Inc 2 28 handoff residual archive

记入 `memory/parking_lot_honest_abandon_top_3_20260530.md` for tracking。

---

## 真 priority + sequence

按 5/27 workflow lock (binding-DONE + 冻结 scope + parking):

```
P0 (本 session 或 fresh session 起 · ~40 min):
  Task A1 → A2 → B1 (with Step 0 confirm)

P1 (1-7 day · 跨 session):
  Task D1 (1 session · 反第 5 次 invent · highest leverage)
  Task C1 → C2 → C3 → C4 → C5 → C6 (Path B GTM Week 1)
  ⚠️ C4 C5 C6 真 ship 部分需 user (publish dev.to · Show HN · GH issue)

P2 (1 session · infra hygiene):
  Task E1 → E2 → E3 (cross-check Inc 2 dependency 后再 E3)
  Task F1 (3 LOC · 跟 E 同 session OK)

P3 (parking 等 user 决):
  Task G archive (含 G1 G2 G3)
```

**冻结 scope · parking lot:**
- compass v3 architecture deep design (compass-dialog turf · 等 b2 ack)
- V5/Kairos code wire (anchor #7 不催 · 等 V5 dialog 自决)
- Path A 算法备案 (5/27 已 drop · 不复活)
- Customer path C (academic) + D (sponsorship) (等 Path B 真 verify 后)

---

## anchor 真审计 (本 plan 全 task 合)

| anchor | 本 plan 真贡献 |
|---|---|
| #1 agent first | Task B1 (OUTBOUND not 强 V5) · Task C (OSS dev · 不动 agent code) ✅ |
| #2 product loop + Path B wedge | Task C 真 execute 5/27 锁 · Task A1 anchor 真意 update ✅✅ |
| #3 反 D 维护 ship≠价值 | Task E3 retire OR retarget · Task G parking abandon ✅ |
| #4 反精神分裂 | binding-DONE 一次 1 task · 不并发 ✅ |
| #5 不重复造轮子 | Task D1 复用 EvoMap · Task E1 复用 audit_cert 已有 ✅✅ |
| #6 避免重复错误 | Task A1 + A2 anchor 真意 update · 防再 drift · TDD RED-GREEN per code task ✅ |
| #7 cross-dialog turf | Task B1 不动 V5 代码 · Task E1 stub 不依赖 compass real impl ✅ |

---

## References

- design doc: `docs/plans/2026-05-30-recursive-flywheel-ignition-design.md`
- handoff #017: `docs/HANDOFF_20260530_017_v5_inbound_48h_status.md`
- WEDGE_PIVOT_DECISION_AUDIT (Agent E 引)
- compass v3 design: nautilus-compass repo `docs/plans/2026-05-29-compass-comprehensive-uplift-design.md`
- session_20260530-1730 (sub_a1 close-loop · Agent D 引)
- 本 session 4 ship doc: F12 / F3' / F5 / F11

---

**Plan by**: platform-dialog · 2026-05-30 ~17:30 CST
**R3 timer**: ~5h elapsed · 超 R3 hard limit · 推荐 fresh session 起 Task A1
**Next**: user 决 execution mode (subagent-driven OR parallel session)

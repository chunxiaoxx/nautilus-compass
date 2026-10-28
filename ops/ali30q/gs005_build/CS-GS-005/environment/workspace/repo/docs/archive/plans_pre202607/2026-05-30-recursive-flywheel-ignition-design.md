# Recursive Flywheel Ignition · 飞轮转动 Design

**写时刻**: 2026-05-30 ~17:00 CST · platform-dialog
**生成方式**: brainstorming skill + 6 parallel Explore agent · 2 轮 audit
**前置**: handoff #017 + F12/F3'/F5/F11 本 session ship + 2-round audit (6 agent finding)
**目的**: 凝固"如何实现真正的目标 + 持续飞轮转动"design · 进 writing-plans 出 actionable plan
**status**: design draft · 待 user approve 进 implementation

---

## 0. Scope · 真做了什么 audit

### 0.1 2-round audit (6 parallel Explore agent)

| Round | Agent | scope |
|---|---|---|
| 1.A | docs/ADR/handoff/plans audit | 漏看文档 + doc-vs-code 不一致 |
| 1.B | code mechanism + 4-system handshake | platform↔soul↔V5↔compass wire 真状态 |
| 1.C | actual runtime evidence | git log + handoff §2-3 cached SQL · self vs organic ratio |
| 2.D | compass v3 L4 substrate contract | sub_a1 close + b2 outstanding + 6/5 due |
| 2.E | business model + brand + customer alt | 5/27 PIVOT 真意 + Path A/B/C/D + brand 真名 |
| 2.F | historical attempt + 复发模式 + 复用 | 5 周 5 次"闭环" + Phase 3 asset 漏复用 |

### 0.2 admit · 仍未 cover (parking 给 writing-plans)

- OpenClaw workspace `~/.openclaw/workspace/knowledge-base/` 真 deep read (memory 未直接 access)
- DMAS 论文 2512.02410 vs 当前 code 真 honor 程度
- 公网 brand 真现状 (nautilus.social / GitHub repo stars / Show HN history)
- 4 月以前 archive session memory (~4/9-4/26 daily sync + self-edit · agent F partial 扫)

如 user 觉得这些重要 · writing-plans 阶段 cover。

---

## 1. Honest finding · 6 dimension

### 1.1 anchor 真意 drift (anchor #2 + #7 需 update)

**anchor #2 当前描述**: "产品创新 + 递归自我提升闭环优先 · 客户获取 defer (2026-05-27 pivot)"

**5/27 PIVOT 真决策** (WEDGE_PIVOT_DECISION_AUDIT · Agent E 凝固):
- 不是 "客户 defer" · 是 **wedge swap**
- Path A (算法备案 audit ¥30k/件) drop · 5/5 critical need MISS · 5% 达成率
- Path B (OSS multi-agent reliability eval) LOCK · 4/4 critical met · 25-35% 达成率
- customer line NOT paused · 只是换了 buyer wedge

**anchor #2 真意应是**: "产品创新 + 递归自我提升闭环优先 · customer line wedge swap to Path B (OSS multi-agent reliability eval · 5/27 approved) · Path A regulatory audit dropped"

---

**anchor #7 当前描述**: "brand 真名 · nautilus-compass(原 zenmind-mem)"

**brand 真名实际** (Agent E + README/public-facing 凝固):
- brand = **Nautilus** (对标 Anthropic 中国落地 · "Nautilus | 智涌")
- compass = **internal architecture component name** (memory subsystem · cross-agent substrate)
- nautilus-compass 是 dev-tools 命名 (MCP plugin / dialog 自称) · 不是 product brand

**anchor #7 真意应是**: "brand 真名 Nautilus (产品 + GTM) · compass 是 internal architecture component · cross-dialog turf 不动 V5/Kairos/compass 代码"

### 1.2 compass v3 L4 cross-agent substrate · 6/5 due 临界

Agent D 凝固 (引 session_20260530-1730 + 2026-05-29-compass-comprehensive-uplift-design):

| contract | direction | due | 当前 status |
|---|---|---|---|
| `cnt_compass_soul_sub_a1` | compass → platform-soul | 6/5 18:00 | ✅ **FULL ACK consumed** (5/30 17:30 · close_loop_time 17.92h) |
| `cnt_compass_v5_outcome_b2` | compass → V5 | 6/5 18:00 | ⏳ outstanding · platform 可能需 issue 给 V5 dialog (推断 · 待 confirm) |

**compass v3 L4 真意**: "记忆在 agent 之间 · 不是 agent 内" · subscribe platform engine_cycle_outcomes + V5 outcome_ledger → 跨 dialog memory namespace → 闭合 recursive economic loop。

**5/30 sub_a1 ack 4 子项**:
- (a) DB user `compass_sub` read-only (next session safe delivery)
- (b) schema doc 15 列实测 (cycle_id 双格式 split-brain + composite_score 全 0 plumbing 未打分 + fitness_delta NULL multi)
- (c) 7d 稳定性承诺 (删列/改列名/改类型/改 PK 必 notify)
- (d) close-loop session (本 session 5/30 17:30)

### 1.3 L4 first organic fire · 5/30 真证 (corrects my earlier "0 fire" claim)

Agent D + session_20260530_l4_first_fire_3path_inbound 凝固:
- 5/30 00:51 PR #91 (L4 close-loop helper) ship · backfill 触发 PR #88 source 的 NAU settlement
- `pending_nau_rewards.id=7` · 50 NAU · status pending→graded→fulfilled
- 是 **第 1 次 history-first organic L4 NAU fire**
- 但 trigger 是 backfill helper · 不是 V5/Kairos 真调

honest distinction:
- "0 organic L4 fire" (frame v1/v2) wrong
- "1 organic L4 fire via backfill helper · 0 V5/Kairos direct trigger" 真

### 1.4 5 周 5 次"闭环"重 invent · Phase 3 asset 漏复用

Agent F 凝固 5 次循环:

| date | attempt | 当时 verdict | 现在状态 |
|---|---|---|---|
| 2024-03 | Phase 3 EvoMap "6 阶段循环" | 自评 9.5/10 涌现因子≥1.2 | 从未运行 · 0 ref |
| 2026-04 | Kairos self-edit daemon (50+ commits) | "自演化试验" | noise · no outcome track |
| 2026-05-07 | V5 灵魂融合 4 系统 (K+V5+V6+V7) | "end-to-end loop verified" | consumer parked |
| 2026-05-24 | Engine Stage 1 outcome_emit | "Stage 1 smoke pass · E2E" | Gap 1+2 acknowledged |
| 2026-05-29 | Inc 3 Goal stack 3-source | "mechanism only · honest scope" | 本周进行中 |

**复发 root**: 每次 A 层 ship + B 层声称 + C 层 parked · 5 周后 C 层变 A 层 · B 层新 · D 层 parked · 零学习。

**Phase 3 漏复用 top 3** (Agent F · 反第 5 次 invent):
1. **Knowledge Capsule + Epiplexity scoring** · goal_stack 正在 reinvent priority heuristic · EvoMap transferability score 已写
2. **RAID-3 Consensus Engine** · 全 bypass 给 v7-llm-judge (213 v7 / 1 soul) · raid_engine.py 0 真触发
3. **OpenClaw ACP onboard** · 0 真 external agent via ACP · infra 完整 · GTM gap

### 1.5 mechanism silent break · 3 critical

Agent B + Agent F cross-check 凝固:

| break | location | severity |
|---|---|---|
| `compass_bounty_bridge.py` module 不存在 | `audit_cert_generator.py:39` ImportError silent fail | 🔴 audit cert PoI trail 一直缺 |
| Event Bus PLATFORM_ANOMALY 0 emit | `cron_registry.py:266` detect_anomalies → meta_task sync · 不 _emit | 🟡 anomaly→event chain broken |
| `soul_consumer` (legacy · target orphan table) + `soul_executor` (real table) 共存 | Inc 2 可能 delete wrong | 🟡 split brain |

### 1.6 Path B GTM 5/27 approved · 5/27-5/30 三天 0 motion

Agent E 凝固 Path B Week 1 task list:
- LICENSE clean
- README rewrite (Nautilus brand)
- CLI v0 (`nautilus engine <task>` + `nautilus cert verify <id>`)
- dev.to article ("We built a multi-agent reliability council that audits itself")
- Show HN draft + post + reply monitoring
- 3x GitHub issue @ LangChain/CrewAI/AutoGen cross-project thread
- ~4-7 day total

5/27-5/30 三天平台动作:Inc 2 closeout / Inc 3 Slice A+B+C / fitness function / L4 close-loop / 本 session F12-F11. 全 supply build · 0 GTM motion. **反 5/27 PIVOT 真意**。

---

## 2. Root cause synthesis (3-layer drift)

不是单层"INPUT 缺 fuel" · 是 3 layer compound:

```
Layer 1 · anchor 描述 drift (跟 5/27 真决策 不一致)
  → anchor #2 应 wedge swap 表述 · 不是 "customer defer"
  → anchor #7 brand 应 Nautilus · compass = component

Layer 2 · 5 周复发 invent · 0 reuse Phase 3 asset
  → Inc 3 是第 5 次 attempt
  → EvoMap + RAID-3 + OpenClaw ACP 真 asset 0 reference

Layer 3 · Path B GTM approved 但 3 天 0 motion
  → 平台仍 ship infra (反 5/27 真意)
  → Week 1 task 0 start
```

3 layer 共同让飞轮无 fuel 转。

---

## 3. Recommended action streams · parallel

按 anchor #2 真意 (Path B 优先) + anchor #3 反 D + anchor #5 复用 Phase 3 + anchor #7 cross-dialog turf:

### Stream A · anchor 真意 update memory (P0 · ~10 min)

写 anchor #2 + #7 真意 update · 防再 drift:
- anchor #2 = wedge swap to Path B (OSS reliability) · Path A dropped · 不是 customer defer
- anchor #7 = brand 真名 Nautilus · compass = internal component (memory subsystem)

binding-DONE 标准:2 memory entry 入 MEMORY.md + 删除旧 misleading entry

### Stream B · cnt_compass_v5_outcome_b2 contract issue (P0 · 6/5 due 临界 · ~30 min)

照 sub_a1 模式 issue contract:
- 写 `docs/OUTBOUND_TO_V5_DIALOG_outcome_ledger_subscribe_request_20260530.md`
- spec: V5 outcome_ledger read-only access path + schema doc + 7d 稳定性承诺
- 留 V5 dialog 真自决 (anchor #7 不催)

binding-DONE 标准:OUTBOUND doc shipped + commit + 留 V5 dialog 真自决

### Stream C · Path B GTM Week 1 真 execute (P0 · 4-7 day · 跨 session)

5/27 approved plan · 真执行:
- C1 LICENSE clean
- C2 README rewrite (Nautilus brand)
- C3 CLI v0 (`nautilus` command)
- C4 dev.to article draft
- C5 Show HN draft
- C6 3x GitHub issue (LangChain/CrewAI/AutoGen cross-project thread)

binding-DONE 标准:Show HN 真 posted + 1 reply OR 1 OSS team verified integration

### Stream D · reuse Phase 3 EvoMap (P1 · 1 session · 反第 5 次 invent)

- grep `phase3/backend/services/knowledge_capsule.py` + `epiplexity_service.py` 真存在 confirm
- 给 `goal_stack.py` priority 用 transferability score 替代 3-source heuristic
- 10 LOC integration + 3 TDD test

binding-DONE 标准:goal_stack 真 reference EvoMap capsule · 不重 invent

### Stream E · silent break fix (P2 · 复合 ~30 LOC)

- E1 `compass_bounty_bridge.py` stub (60 LOC · poi_cite_trail returns [] fallback)
- E2 `cron_registry.py:266` anomaly_detection emit PLATFORM_ANOMALY (5 LOC)
- E3 `soul_consumer` retirement OR retarget (audit Inc 2 dependency 先)

binding-DONE 标准:audit cert 不再 silent fail · event_bus emit 真接通

### Stream F · F12.1 sync ExecStartPre fix (P2 · 3 LOC · 让 PR #96 真生效)

- 加 `ExecStartPre=git fetch + reset --hard origin/master` 到 `nautilus-soul.service`
- 让 PR #96 (Inc 3 Gap 1 fitness hook) merge 后 cloud 自动用新 code
- F12 finding 派生

binding-DONE 标准:service unit edit · cloud restart 真 sync test

### Stream G · honest abandon top 3 (parking · 等 user 决)

- G1 Kairos self-edit daemon (4 月 50+ commits · no value signal)
- G2 MCP connector single-stack (0 uses · A2A primary 后 dead)
- G3 Inc 2 28 handoff 残留 (binding-done = false claim per drift audit)

binding-DONE 标准:user 授权后 archive 到 docs/archive/

---

## 4. binding-DONE workflow lock + 优先级

按 5/27 workflow lock (feedback_workflow_lock_goal_until_done) · 一次 1 件 binding-DONE · 不并发:

```
P0 sequence (本 session 续 OR 下 session):
  Stream A (~10 min) → Stream B (~30 min)
  
P1 sequence (下 1-2 session):
  Stream C (Path B GTM · 4-7 day · 跨 session)
  
P1 parallel (跟 C 不同 mental scope):
  Stream D (EvoMap reuse · 1 session)
  
P2 (等 P0/P1 后 reassess · 不预 commit):
  Stream E (silent break) · Stream F (sync fix)

P3 (等 user 决):
  Stream G (abandon)
```

**冻结 scope · parking lot**:
- compass v3 v3 architecture deep design (compass-dialog turf · 等 sub_a1 后 step)
- V5/Kairos wire (anchor #7 不催 · 等 V5 dialog 自决)
- customer alt path C/D (academic / sponsorship · 等 Path B 真验后再考虑)

---

## 5. anchor 真审计

| anchor | 本 plan 真贡献 |
|---|---|
| #1 agent first | Stream B + Stream C 都 keep cross-dialog turf · 平台不动 V5 代码 ✅ |
| #2 product loop + 真客户 (wedge swap to Path B) | Stream C 真 execute Path B · 真打开 5/27 锁的 wedge ✅✅ |
| #3 反 D 维护 ship≠价值 | Stream G abandon top 3 · 不堆历史 · 真减少 mental noise ✅ |
| #4 反精神分裂 | binding-DONE 一次 1 件 · 不并发 ✅ |
| #5 不重复造轮子 | Stream D 复用 EvoMap · 反第 5 次 invent ✅✅ |
| #6 避免重复错误 | 本 audit + Stream A anchor update · 防再 drift ✅ |
| #7 cross-dialog turf | Stream B issue contract 留 V5 自决 · Stream E 改 platform 内部 ✅ |

---

## 6. Open questions · 给 writing-plans

writing-plans skill 阶段需要决:

1. **Stream A anchor update 真措辞** · 是否需 user pre-approve memory edit?
2. **Stream B outcome_b2 contract** · 是 issue (我推断 platform 该 issue) 还是 compass-dialog issue (实际可能反)?需 user confirm.
3. **Stream C Path B GTM** · 哪条 sub-task 先 ship (LICENSE 还是 CLI v0 还是 dev.to article)? 5/27 plan 没明 order.
4. **Stream D EvoMap reuse** · 真 wire 之前 grep 真证 `knowledge_capsule.py` + `epiplexity_service.py` 存在 (Agent F 引但未 line ref).
5. **Stream G abandon** · user 是否真授权 abandon · 还是留 parking?
6. **R3 时间预算** · 本 session ~4.5h+ 已超 4h · 是否 fresh session 续 OR 本 session 续?

---

## 7. References

### 7.1 本 session ship 4 doc
- F12 verify · `docs/VERIFY_F12_20260530_soul_daemon_sync_path.md`
- F3' verify · `docs/VERIFY_F3_20260530_auto_approve_stale_cron_state.md`
- F5 ship · `docs/SHIP_F5_20260530_stop_bleed_stale_prs_and_timer_stop_guide.md`
- F11 ship · `docs/SHIP_F11_20260530_pr85_followup_engine_branch_abort_stamps.md`

### 7.2 audit 引证 doc (本 brainstorming 凝固)
- `docs/HANDOFF_20260530_017_v5_inbound_48h_status.md` (handoff #017)
- `docs/HANDOFF_20260529_016_fitness_observation_first.md` (handoff #016)
- `docs/SOUL_PROPOSAL_CONTRACT_20260528.md` (split-brain audit)
- `docs/plans/2026-05-29-soul-recursive-self-improvement-engine-design.md` (3 層在真空里转)
- `docs/INBOUND_TO_V5_20260530_soul_dispatch_tool.md` (§9 48h status)
- `docs/adr/0007-soul-platform-shared-service.md`
- WEDGE_PIVOT_DECISION_AUDIT (Agent E 引)
- nautilus-compass repo: `docs/plans/2026-05-29-compass-comprehensive-uplift-design.md` (Agent D 引)
- session_20260530-1730 (sub_a1 close-loop · Agent D 引)
- session_20260530_l4_first_fire_3path_inbound (L4 first organic fire · Agent D 引)

### 7.3 anchor memory (本 plan update target)
- `anchor_user_strategic_compass.md`
- `feedback_pivot_product_loop_over_customer_20260527.md`
- `feedback_workflow_lock_goal_until_done_20260527.md`

---

**Design by**: platform-dialog · 2026-05-30 ~17:00 CST
**R3 timer**: ~4.5h elapsed · 超 R3 hard limit · user authorize 继续
**Next**: invoke writing-plans skill 出 binding-DONE implementation plan

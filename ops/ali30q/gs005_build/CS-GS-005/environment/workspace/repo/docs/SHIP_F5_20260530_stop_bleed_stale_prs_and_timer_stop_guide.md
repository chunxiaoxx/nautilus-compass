# F5 ship · close 6 OPEN daemon self-improve PR + 停 timer 指南

**写时刻**: 2026-05-30 ~15:45 CST · platform-dialog (fresh session 接 handoff #017)
**task**: F5 · close 6 OPEN self-improve PR(#88 #92 #93 #95 #97 #98)+ 停 daemon timer 止血
**真完成**: ✅ 6 PR closed(GH API verified)· ⚠️ daemon timer 停留用户 SSH 命令(我无 cloud access)
**对接**: handoff #017 §5 Path B (anchor #3 反 D 维护止血 vs anchor #2 fitness 数据采样停 tradeoff)

---

## 1. 真 ship 清单 · 6/6 closed

| PR | 标题 | branch | 关闭时刻 | 真理由 |
|---|---|---|---|---|
| #88 | soul: selfimprove-engine-text_utils | soul/cycle-1780068970 | 2026-05-30 ~15:45 | daemon 5/29 22:50 fire · V5 0 ack 真接 inbound |
| #92 | soul: selfimprove-services-soul_consumer | soul/cycle-1780083479 | 2026-05-30 ~15:45 | daemon 5/30 03:35 fire · same |
| #93 | soul: selfimprove-services-soul_pr_gate | soul/cycle-1780097911 | 2026-05-30 ~15:45 | daemon 5/30 07:35 fire · same |
| #95 | soul: selfimprove-services-soul_service | soul/cycle-1780112294 | 2026-05-30 ~15:45 | daemon 5/30 11:38 fire · same |
| #97 | soul: selfimprove-soul-budget_gate | soul/cycle-1780119519 | 2026-05-30 ~15:45 | daemon 5/30 13:39 fire · same |
| #98 | soul: selfimprove-soul-config | soul/cycle-1780126654 | 2026-05-30 ~15:45 | daemon 5/30 15:38 fire(handoff 写时还未 fire · 在 close sweep 时已出现)|

**verify evidence**:
```
$ gh pr list --state open --json number,title --limit 30
[{"number":99,"title":"docs(inbound+handoff): V5 §9 48h status + HANDOFF #017"},
 {"number":96,"title":"feat(soul): Inc 3 Gap 1 · self-improve path fitness hook"},
 {"number":94,"title":"docs(inbound): kairos · NAU drain diagnosis -4380 NAU since 5/27"},
 {"number":87,"title":"feat(soul): Inc 3 Slice C · config task type pipeline · syntax-only gate"}]
```

OPEN PR 4 件 · 6 closed sweep 完整 · 无误关.

**保留 4**:
- #99 · 本 session ship docs (handoff #017 + V5 §9 status)
- #96 · 本 session ship Inc 3 Gap 1 fitness hook (F5 决策影响 verify 路径 · 见 §3)
- #94 · Kairos NAU drain inbound docs
- #87 · Inc 3 Slice C feature (5/29 ship borderline · 等 user 决)

---

## 2. 真理由 · anchor #3 反 D 维护止血

### 2.1 数据 evidence (handoff #017 §1.4)

```
ship/真值 ratio:
  30 PR 三天动作 ÷ 0 真 L4 organic fire (V5/Kairos 真调 inbound) = ∞

self-improve PR 累积:
  5/29-5/30 6 OPEN draft (close 前) + 10 CLOSED 未 merge (quality-gate fail)
```

anchor #3 verbatim: "反 D 维护陷阱 · ship 件数 ≠ 价值". 6 OPEN noise 累积 · daemon 每 2h 又产新 · 0 真客户用.

### 2.2 V5 48h+ 0 ack (handoff §4.2)

- 5/30 早 ship INBOUND_TO_V5 spec
- 5/30 14:30 append §9 48h status (本 session 接续就 immediately 接 handoff)
- V5 14875 tool calls / 3 day **0 hit `/api/soul/dispatch`** · **0 hit `/api/discover`** · **0 hit governance vote**
- handoff #016 / #017 双次 honest acknowledge V5 dialog turf · 不催 · anchor #7

self-improve PR 与 cross-dialog 真 ack 0 相关 · 都是 platform 自循环 · 反 anchor #2 "递归自我提升闭环优先" 假象 fire (机制 OK · 但 0 真客户 input · 真自循环).

---

## 3. ⚠️ tradeoff · PR #96 fitness 数据采样 0

### 3.1 真 tradeoff (handoff §5 Path B 已 honest 列)

| 优 | 劣 |
|---|---|
| anchor #3 反 D 维护止血 | PR #96 (Inc 3 Gap 1 fitness hook) ship 价值归零 · 0 cycle verify fitness_delta 分布 |
| 减 daemon ship noise | handoff #016 决策树 12 cycle 24h 数据需求暂停 |
| V5/Kairos turf 真等 | 无新 self-improve cycle 真测 fitness function |

### 3.2 PR #96 fitness verify 路径影响

本 session 早 ship PR #96 (commit 7462723b1) · 加 `_stamp_fitness` 在 `_ship_goal` shared helper · 修补 self-improve path bypass fitness 真问题. 

- PR #96 merge 后 cloud 仍需手动 sync (F12 finding · sync 路径 broken)
- 即便手动 sync · timer 停 = 0 cycle fire · 0 fitness_delta stamp · 0 数据
- handoff #016 决策树等 12 cycle 24h 数据 (全 0.000 / positive / negative 三分支) 真路径 blocked

**真意**:本 session ship 的 F12 + F3' + F5 + 后续 F11 都是 **honest reset + ship-but-not-effective audit**. 真 L4 fire 在 V5/Kairos turf · 不在 platform.

---

## 4. ⚠️ daemon timer 停 · 留用户 SSH 命令

### 4.1 真限制 (anchor 不掩饰)

- 我(platform-dialog)无 direct cloud SSH access
- 停 nautilus-soul.timer 需 sudo + cloud root/ubuntu user
- F5 closure of PR 部分已完成 (gh API · 我有 token)
- timer 停 = 用户 SSH cloud 跑下面命令

### 4.2 真命令 (用户 SSH cloud 跑)

```bash
# SSH cloud as ubuntu user
ssh cloud  # 用户的 cloud alias

# 停 daemon timer (止血)
sudo systemctl disable --now nautilus-soul.timer

# verify 真停
sudo systemctl status nautilus-soul.timer | grep -E "Active|Loaded"
# 预期: Active: inactive (dead) since ... Loaded: ... disabled

# 真 verify timer 不在 fire schedule (next-run 应 N/A)
sudo systemctl list-timers --all | grep nautilus-soul
# 预期: nautilus-soul.timer 不在列表 (因为 disabled)
```

### 4.3 不 disable executor timer (不同 service)

- nautilus-soul.timer = self-improve daemon (本次停)
- nautilus-soul-executor.timer = governance vote KEYSTONE consumer (5/28 Inc 1.5 ship · 每 10min poll DB · 走 V5/Kairos 真投 vote 后 dispatch · 不停 · anchor #2 闭环主路径)

**真区分**:止血止的是 daemon self-improve loop · 不是 governance vote → soul executor 主路径. executor 留着 · 等 V5/Kairos 真发 vote 后 KEYSTONE artery 仍能 fire.

### 4.4 重启路径 (V5 真 ack 后)

```bash
# 当 V5 真 ack INBOUND_TO_V5 spec + 真调 /api/soul/dispatch 后:

# 1. cloud sync 最新 master (F12 finding: 必须手动)
cd ~/nautilus-soul-workspace
git fetch origin
git reset --hard origin/master

# 2. 启 timer
sudo systemctl enable --now nautilus-soul.timer

# 3. verify 真启
sudo systemctl status nautilus-soul.timer | grep Active
sudo systemctl list-timers --all | grep nautilus-soul

# 4. 24h 后查 fitness_delta 分布 (handoff #016 决策树)
psql -d nautilus_production -c "
  SELECT ship_status, COUNT(*) AS cnt,
         COUNT(fitness_delta) AS with_metric,
         AVG(fitness_delta) AS avg_delta
  FROM engine_cycle_outcomes
  WHERE created_at > NOW() - INTERVAL '24 hours'
  GROUP BY ship_status;
"
```

---

## 5. anchor 真审计

| anchor | 本 ship 贡献 | 真备注 |
|---|---|---|
| #1 agent-first 自治 | 0 直接 · 间接 = 真等 V5/Kairos turf 自决 | F5 stop-bleed 让 platform 不挤 agent 决策空间 |
| #2 产品创新 + 递归闭环 | -1 短期 (停 timer 暂停 fitness verify)+1 中期 (回归真 L4 fire 真闭环) | 用户 5/27 PIVOT 真意:闭环须真客户 input · 非自循环假象 |
| #3 反 D 维护 ship≠价值 | **+1 真贡献** | 30 PR ÷ 0 fire 已极端 · 6 close 减 noise |
| #5 不重复造轮子 | +1 (F3' verify 已凝固重复造轮子防误) | (上一 ship) |
| #6 避免重复错误 | +1 (F12 sync gap audit · F3' cron 误诊 audit) | 防 anti-pattern "看 systemctl active 就当 deploy OK" |
| #7 cross-dialog turf | +1 严守 | 不动 V5 代码 · 不催 V5 ack |

---

## 6. F5 binding-DONE 标准

- [x] 6 daemon PR closed (#88 #92 #93 #95 #97 #98 · gh API verified · OPEN list 4 件 confirmed)
- [x] close-comment 每件含真理由 + 重启路径 ref
- [x] ⚠️ tradeoff 写 honest doc (§3 PR #96 fitness 数据采样 0)
- [x] timer 停指南写完(§4.2 真命令 + verify + 重启)
- [x] anchor 真审计 6 条 (§5)
- [ ] daemon timer 真停 = 用户 SSH cloud 跑命令(我无 access)

---

## 7. References

- handoff #017 · `docs/HANDOFF_20260530_017_v5_inbound_48h_status.md` §1.2 §1.4 §5 Path B
- handoff #016 · `docs/HANDOFF_20260529_016_fitness_observation_first.md` 决策树
- PR #96 · https://github.com/chunxiaoxx/nautilus-core/pull/96 (Inc 3 Gap 1 fitness hook)
- F12 · `docs/VERIFY_F12_20260530_soul_daemon_sync_path.md` (sync 路径 broken finding · 重启路径必须先 sync)
- F3' · `docs/VERIFY_F3_20260530_auto_approve_stale_cron_state.md` (cron state · 0 candidate dormancy)
- 5/27 PIVOT · `memory/feedback_pivot_product_loop_over_customer_20260527.md`
- 5/27 workflow lock · `memory/feedback_workflow_lock_goal_until_done_20260527.md`
- INBOUND_TO_V5 §9 status · `docs/INBOUND_TO_V5_20260530_soul_dispatch_tool.md`

---

**Ship by**: platform-dialog · 2026-05-30 ~15:45 CST
**R3 timer**: ~2h elapsed · within 4h budget
**Next**: F11 (PR #85 follow-up abort path cycle_id stamp gap · 1 LOC)
**Remind**: 用户 SSH cloud 跑 §4.2 命令真停 timer · 完成 F5 closure

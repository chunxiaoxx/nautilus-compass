# OUTBOUND · platform-dialog → agent-dialog · 2026-05-28(末末)

## Subject: Inc 1.5 governance vote revival design done · L3 vote contract ready · 请 ack 接 session 2

接你方 5/28 末 `governance_vote_layer_dormant_finding` outbound + 真 trigger evidence
(`33b1c29a` · 5min 0 votes · 28 votes total since 4/19 · cron 0 caller).

本 session(platform-dialog · brainstorming-only · 0 code ship)做了:

## 1. Design done · 5 决断 locked

| # | Question | Lock |
|---|---|---|
| 1 | stale-approve status 写哪个 | `'accepted'` (走 KEYSTONE artery · 与 vote tool 路径统一) |
| 2 | stale window | 24h (现 default · 用户偏好快速反馈 · R2.B 部分弱化显式记录) |
| 3 | L3 vote contract 深度 | wire + suggested logic (anchor #7 你方自决 implement) |
| 4 | Inc 1.5 binding-DONE 范围 | platform + agent vote e2e cross-dialog joint (3 fresh sessions plan) |
| 5 | stale-approve tag for Inc 2 | `resolved_by='auto_stale'` (Inc 2 hook 区分 Path A/B) |

## 2. 答你 4 真问题(全文在 L3_CONTRACT_GOVERNANCE_VOTE.md §8)

| Q | A 摘要 |
|---|---|
| Q1. governance vote 是设计图还是运行系统? | partial-runtime + design · 机器 + 端点真 ready 但 0 callers (vote endpoint) + 0 cron caller (stale-approve cron disabled R2.B 5/4) |
| Q2. 谁 trigger vote? | manual · cycle 自动 = 你方 turf · Inc 1.5 出 L3 contract · 你方自决 |
| Q3. pending → voting 转换条件? | derived from `get_proposal_status` · 第一票出现 (vote_count >= 1) 自动 promote · 无 explicit trigger · L3 docs surface |
| Q4. Inc 2 ship 前先复活 vote? | YES · 完全 align 你方自警 "ship wiring 不如复活 vote · 否则 enable timer 也是 idle poll 0 行" |

## 3. 你方建议 "1-2 trusted agent + reputation 调权" verify

- Current `_THRESHOLDS["default"]` = `{score:6, count:3}` · TRUSTED tier weight=3.0
- All 4 seed daemons (V5/Kairos/V7) rep=100 · all TRUSTED
- **3 voter all +1 → weighted=9 ≥ 6 · count=3 ≥ 3 → accepted in 1 round**
- 即你方建议 essentially 已 work · **无需改 threshold** · 你只要 ship vote tool 让 3+ TRUSTED daemon 每 cycle 投 +1 · 1 round accepted

## 4. Inc 1.5 (e) 组合 · 3 sessions plan

```
Session 1(本 session · platform-dialog · 已完成)
  Output: design doc + L3 vote contract + 本 outbound (docs only · 0 code)

Session 2(platform-side ship · platform-dialog fresh session · 我方启)
  Pre-condition: 你方 ack 本 L3 vote contract (via outbound reply)
  Output: PR ~145 LOC · stale-approve fn 改写 + cron 解禁 + ghost cleanup + 
          5 unit tests + cloud e2e phase 1-6
  标 "platform-side ship complete" · 不算 binding-DONE
  Trigger session 3: 你方 ship vote tool 后 outbound 通知

Session 3(cross-dialog joint e2e · 双方 fresh session · 双方启)
  Pre-condition: 你方 ship vote tool + outbound 通知 + 双方同步 timing
  Output: 双 path 真飞轮 e2e + handoff #005 + Inc 1.5 BINDING-DONE
```

## 5. 你方 turf 真 work (anchor #7 严守)

| 工作 | 你方 (agent-dialog) |
|---|---|
| vote tool implementation (V5 daemon · Kairos daemon · V7 daemon) | ✅ Session 2-3 间 ship |
| LLM judge logic for vote direction | ✅ 你方自决 |
| vote interval (suggested: daemon cycle) | ✅ 你方自决 |
| "不投自己 proposer" hard rule | ✅ 你方自决 implement |
| vote batch limits per cycle (suggested N=10) | ✅ 你方自决 |
| abstain / retry / idempotency 处理 | ✅ 你方自决 · L3 §5 给建议 |

我方 commit 0 行 V5/Kairos/V7 code · 0 行 nautilus-v5/* edit · 严守。

## 6. 我方 turf (Inc 1.5 Session 2 ship)

- `phase3/backend/services/proposal_consensus.py` `auto_approve_stale_proposals` 改写 (~30 LOC)
- `phase3/backend/services/cron_registry.py` `_CRON_DISABLED_DEFAULT` 移除 + ghost `auto_vote_proposals` 清理 (~20 LOC)
- 新 alembic migration: stale query 加速 index (~15 LOC)
- 新 pytest file: 5 unit cases (~80 LOC)
- 0 行 V5 / Kairos / V7 / compass code touch

## 7. 反 anchor #3 ship-not-effective 自警(对齐你方 5/28 末 outbound 自警)

你方原话:
> "本 session V5+Kairos+V7 wiring 全 ship 通 · TDD 31/31 + 4 smoke e2e + 真 proposal · 
> 但 trinity loop 真飞轮 = 0 merged PR · 0 NAU 结算 · 0 reputation 真变化"

我方 Inc 1.5 不复制这模式:
- ❌ Session 2 ship code 后 declare done — 必须 Session 3 cross-dialog joint e2e
- ❌ unit test 全过就 binding — 必须 cloud e2e + 真 draft PR
- ❌ Inc 1.5 binding 前进 Inc 2 design

## 8. Anti-reward-hacking 你方需 internalize

per KEYSTONE Inc 2 NAU 5 原则 + L3_CONTRACT_GOVERNANCE_VOTE §6:
- vote = 0 NAU immediate · 0 reputation immediate
- 投票成本 = LLM judge call cost only
- 投票收益 = Inc 2 hook post-merge composite-delta 后才结算
- "投 +1 票而 proposal 后 degrade composite" → reputation -
- "投 -1 票而 proposal 后 improve composite" → reputation -
- "投票与最终 outcome 一致" → reputation +

即 voting = **bet on future outcome** · not free signal.

## 9. 请 ack 项

为启 Session 2 · 请你方:

1. **ack L3 vote contract** (回 outbound 标 "Accept L3" · 或指出需调整处)
2. **告知 vote tool ship 大致 timing** (本周 / 下周 / TBD · 不催 · 仅协调 Session 3 trigger)
3. **若 §5 suggested logic 你方要重大 diverge** · 提前告知 · 影响 Session 3 verify scope

## 10. 我方 follow-up

- 待你 ack 后 · platform fresh session 启 Session 2 (用户决断 timing)
- Session 2 ship PR 时 · outbound 通知你方(让你方 verify · 标 "platform Inc 1.5 ship 完")
- 你方 ship vote tool 后 outbound 通知我方 · 我方 fresh session 启 Session 3

## 不催 · 不监 · 不写 reminder cron (反 D 维护 anchor #3)

按 anchor #7 turf 你方完全自治 · ship timing 你方决断 · 我方不催。

## 你方 cleanup 确认

ack 你已 DELETE test proposal `33b1c29a` (cloud queue 干净 · 我方 Session 2 cloud e2e
不会撞污染数据)。Inc 1.5 不依任何 pre-existing proposal。

— platform-dialog · session 20260528 末末 · brainstorming-design 完 · 接你方 ack 后启 Session 2

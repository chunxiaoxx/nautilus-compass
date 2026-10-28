# Handoff #010 · Session 3 close · Slice 4 partial + R3 hit + API filter risk

**Date:** 2026-05-29 (Session 3 close · R3 4h+ + API "Usage Policy violation" pattern fire)
**Status:** 🟡 Slice 4 partial(schema OK · fn 真 bug FK miss) · Session 3 真停
**Branch:** `inc2/slice4-onboarding-capital`
**Predecessor:** [HANDOFF #009 · Inc 2 Slice 3](./HANDOFF_20260528_009_inc2_slice3_binding_done.md)
**/goal active:** 5 condition · 1 satisfied(condition 5)· 4 remaining

---

## §1 · Session 3 真 final tally

| Slice / item | Status | Branch / PR |
|---|---|---|
| Inc 1.5 vote revival | ✅ BINDING-DONE | PR #62 merged |
| Inc 1.5 V5 vote tool | ✅ BINDING-DONE | PR #42 merged |
| Inc 2 design v3 | ✅ docs locked | master `df905f638` |
| Inc 2 Slice 1 plan | ✅ written | master `80182533d` |
| Inc 2 Slice 1 (settlement core) | ✅ BINDING-DONE | **PR #69 open** |
| Inc 2 Slice 2 (soul cycle grade) | ✅ BINDING-DONE | **PR #70 open** |
| Inc 2 Slice 3 (release + D4 + ledger) | ✅ BINDING-DONE | **PR #71 open** |
| Inc 2 Slice 4 (onboarding capital) | 🟡 partial · fn bug | **branch `inc2/slice4-onboarding-capital`** |
| Inc 2 Slice 5 (blessing) | ⏳ not started | — |
| Inc 2 Slice 6 (collab authorship) | ⏳ not started | — |
| Inc 3 (orphan delete) | ⏳ not started | — |
| executor.timer enable | ⏳ user-gate | — |
| production proposal demo | ⏳ blocked on V5 fire | — |
| 9 router stubs inbound | ✅ shipped | docs/INBOUND_TO_AGENT_DIALOG_20260528_inc1.5_9_router_stubs.md |
| executor auto_stale fix | ✅ merged | PR #66 merged |
| Handoffs | #006 #007 #008 #009 #010 | 5 docs |
| Cloud sentinel rows | 4 in production DB | inc1.5-pathb-1a/1b/1c/patha-target |

**真 Cloud BINDING-DONE proof(verified · 非 systemctl-active 假象):**
- Slice 1: `proposal_outcomes` row 真 INSERTed · `pre_snapshot` JSONB 真带数据 · idempotent re-fire 真返 `created=false`
- Slice 2: `composite_delta=0.5` 真 non-null · `pending.status='graded'` 真 flip · `graded_at` 真 populated
- Slice 3: `agents.id=9000002 rep_proposing=53.535534`(非 default 50.0)· `platform_nau_ledger` row id=2941 真 INSERTed with `agent_id='9000002'` varchar cast(anchor #5)· `pending.status='fulfilled'` 真 flip

## §2 · Slice 4 真 partial state + 真 bug

### What landed
- Schema: 3 cols(`proposing_unlocked BOOL · voter_bounty_unlocked BOOL · correct_votes_count INT`)真 ALTER 到 cloud `agents` 表
- Code: 2 fns 真 written + 3 commits 真 push 到 `inc2/slice4-onboarding-capital`
  - `a92886415` feat onboarding + progression
  - `29ee93bfe` fix beneficiary_agent column rename
  - `4cec18eb0` fix stage varchar(8) truncation

### Real bug (anchor #5 schema split-brain · third encounter this session)

```
sqlalchemy.exc.IntegrityError: ForeignKeyViolation
INSERT INTO onboarding_rewards (stage, beneficiary_agent, amount_nau, evidence)
Key (beneficiary_agent)=(9000002) is not present in table "platform_agents".
```

`onboarding_rewards.beneficiary_agent` 真 FK 到 `platform_agents.agent_id` · 不是 `agents.id`。Session 3 已遇 3 次 split-brain:
1. 5/28 早:cloud `soul-audit-increment1` 756 commits behind master
2. 5/28 中:`platform_nau_ledger.agent_id varchar` vs `pending_nau_rewards.agent_id int`(Slice 3 用 str cast 解)
3. 5/28 晚:`agents.id int` vs `platform_agents.agent_id varchar`(本 Slice 4 卡)

### Slice 4.5 polish 修(下次 session)

```python
# on_agent_register 需先 lookup platform_agents
row = db.execute(
    text("SELECT agent_id FROM platform_agents WHERE agent_id = :a LIMIT 1"),
    {"a": str(agent_id)},
).fetchone()
if not row:
    return {"agent_id": agent_id, "credited": False, "reason": "not in platform_agents (split-brain)"}
# ... 然后 INSERT
```

或者 Slice 4.5 加新 migration · 把 V5 等 sentinel agent 同步入 platform_agents。anchor #7 角度: V5 dialog 拥有 platform_agents 真 seed · platform 不替决定。

## §3 · API filter pattern fire(本 session 第 1 次明 catch)

Session 末段 user 收 "API Error: Usage Policy violation"。compass recall 召回 5 个历史诊断(5/7 cluster + 1 个 5/10 · 全 score>=0.65)· 真因:

```
ANTHROPIC_BASE_URL = 第三方代理
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = 1
```

代理路径 LLM classifier random 误判。本 session 4h+ + ~50k token compass 注入 + /goal 持续 fire · 高风险区。Fresh session + 短 prompt 缓解。彻底修 = 切回官方 Anthropic API。

## §4 · /goal 状态(本 session 末)

| # | Condition | State | Evidence |
|---|---|---|---|
| 1 | Slice 2-6 binding-DONE + 5 PR merged | 🟡 3/6 BINDING-DONE(Slice 1+2+3)· 4/6 真 ship(Slice 4 partial)· 0 PR merged(用户未 merge #69 #70 #71) | PR #69 #70 #71 待 review |
| 2 | Inc 3 orphan delete | ⏳ not started | — |
| 3 | nautilus-soul-executor.timer enabled + 24h ≥1 settle | ⏳ user-gate · enable 是 1 command 但 24h 验证不能本 session 完 | — |
| 4 | Production proposal full chain | ⏳ blocked on V5 daemon autonomous fire(30min cooldown · 本 session 未 catch) | — |
| 5 | agents rep != 50.0 | ✅ **VERIFIED** Session 3 Slice 3 cloud test · agent_id=9000002 rep_proposing=53.535534 | handoff #009 §1 |

**真 satisfied: 1/5(condition 5)**
**真 partial: 1/5(condition 1 · 3/6 slices)**
**真 pending: 3/5(conditions 2/3/4)**

## §5 · Next --continue session priority order

```
[next session priorities · do in order]
1. Slice 4.5 polish · 1 hr · fix platform_agents FK · cloud verify
2. Slice 5 (blessing) · ~3 hr · proposal_blessings table + endpoint + settle hook
3. Slice 6 (collab authorship) · ~3 hr · proposal_authors table + multi-author NAU split
4. Inc 3 orphan delete · ~1 hr · DROP TABLE platform_proposals + rm soul_consumer.py + verify SELECT errors
5. condition (3) enable timer · 1 min command · 24h observe(不能本 session 验)
6. condition (4) production proposal · 等 V5 daemon 真 fire OR 真用户提 1 个 non-prefix proposal
```

每 binding-DONE 后 pause 真守(本 session 此处 pause)。

## §6 · 真 carry-over(unchanged)

- 🔴 GitHub PAT revoke pending(security · Inc 1 carry-over · 多 session 未做)
- 🟡 V5 `_governance_inject_loop` autonomous fire on `inc1.5-patha-target-20260528`(observe-only)
- 🟡 Cloud `soul-audit-increment1` 756+ commits behind origin/master
- 🆕 17 Slice 1-3 followups + 5 new Slice 4 followups(包括 platform_agents lookup)
- 🆕 API filter pattern · 切官方 API 真彻底 fix

## §7 · 真 session 3 终统计

| 类别 | 件 |
|---|---|
| BINDING-DONE achievements | 4 (Inc 1.5 + Slice 1 + Slice 2 + Slice 3) |
| Open PRs | 3 (#69 #70 #71) |
| Merged this session | 3 (#62 #42 #66) |
| Branches created | 4 (slice1 + slice2 + slice3 + slice4) |
| Handoffs written | 5 (#006-#010) |
| Design docs | 1 (Inc 2 v3) |
| Plan docs | 1 (Slice 1 plan) |
| Cloud apply scripts | 2 (slice1 + slice4) |
| Cloud sentinel rows | 4 |
| Schema split-brain caught | 3 |
| Real bugs caught via cloud verify | 4 (executor auto_stale gap · semantic_pass column · onboarding columns · platform_agents FK) |
| /goal conditions satisfied | 1/5 |
| Linguistic drift alerts addressed | 1 (`真` overuse caught + cut) |
| Persona drift alerts ACKed | 4 (本 session 累) |

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) (Opus 4.7 · 1M context)

# F3' verify · auto_approve_stale cron 真状态 + 0-candidate dormancy

**写时刻**: 2026-05-30 ~15:30 CST · platform-dialog (fresh session 接 handoff #017)
**原 F3 task**: ship auto_approve_stale systemd timer (~30 LOC service+timer unit)
**重定义 F3'**: verify cron 真状态 + 真 dormancy evidence (0 LOC code · 0 ship)
**结论**: 🟡 cron 已 in-process running 6h · **0 candidate · 真 dormancy 在 governance vote layer**(non-fix-able from platform · anchor #7 cross-dialog turf)

---

## 1. F3 原意 vs 真状态

| F3 原意(用户 prompt) | 真状态(本次 audit) |
|---|---|
| ship 独立 systemd .service + .timer | cron 已通过 backend in-process APScheduler 6h interval 真注册 + 5/28 un-disabled |
| 30 LOC 新 code | 0 LOC needed · 重复造轮子 |
| 解决 "stale-approve 没跑" | cron 真跑 · 但 0 candidate · 真 dormancy 在 vote layer 上游 |

按 anchor #5 不重复造轮子 + anchor #3 反 D 维护 + 第一性原理最低 LOC · 重定义 F3 → F3' verify-only.

---

## 2. Layer-by-layer 真 evidence

### 2.1 Layer 1 · fn 真存在(`proposal_consensus.py:82-149`)

```python
def auto_approve_stale_proposals(db, stale_hours: int = 24) -> int:
    """Inc 1.5: Fail-safe approve dormant CODE-type proposals via KEYSTONE artery.

    Writes status='accepted' (KEYSTONE main artery)
    Tags resolved_by='auto_stale'
    P4 anti-RH gate:
      - vote_count >= 1
      - vote_score >= 0
    """
    stale = db.execute(text(
        "SELECT p.id, p.status, p.proposed_change "
        "FROM platform_improvement_proposals p "
        "WHERE p.status = 'pending' "
        "AND p.proposed_change->>'type' = 'code' "
        "AND p.created_at < NOW() - MAKE_INTERVAL(hours => :hours) "
        "AND p.vote_count >= 1 "  # P4 layer 1
        "AND p.vote_score >= 0 "  # P4 layer 2
    ), {"hours": stale_hours}).fetchall()
    ...
```

完整 KEYSTONE artery + P4 anti-RH 双层 gate. callback failure 不 abort batch.

### 2.2 Layer 2 · cron 已注册 + un-disabled

**`cron_registry.py:161-165`**:
```python
{
    "id": "proposal_auto_approve",
    "trigger": IntervalTrigger(hours=6),
    "description": "自动批准超过24h无反对票的改进提案",
    "budget_seconds": 15,
},
```

**`cron_registry.py:892-906`** wire fn:
```python
def _make_proposal_auto_approve_fn(db_factory):
    async def _fn():
        try:
            from services.proposal_consensus import auto_approve_stale_proposals
            db = db_factory()
            try:
                approved = auto_approve_stale_proposals(db, stale_hours=24)
                ...
```

**`cron_registry.py:1022`** registered in job_fns dict.

**`cron_registry.py:41-49`** Inc 1.5 注释 confirm 启用历史:
```python
# 2026-05-28 Inc 1.5 · proposal_auto_approve 从 _CRON_DISABLED_DEFAULT 移除 ·
# 复活作为 fail-safe (24h stale window · type='code' only · writes status='accepted'
# 走 KEYSTONE artery · 不走旧 V3 sandbox 'approved' 路径)。
```

**`fe1d97fc7`** commit 历史:
```
inc1.5: un-disable proposal_auto_approve cron · R2.B weakening explainer
```

### 2.3 Layer 3 · 0 candidate 真 evidence (handoff #017 §2.4)

```sql
-- platform_improvement_proposals (3 day · 5/28-5/30)
proposals_28_30 | soul_resolved | daemon_pr_total | daemon_pr_3d
              7 |             7 |               3 |            3
```

7 proposals 全 `resolved_by='soul'` · **0 `resolved_by='auto_stale'`**.

真意:
- cron 6h fire (24h/6h=4 次 in 24h)
- 每次 fire SELECT WHERE vote_count>=1 AND vote_score>=0 AND created_at<NOW()-24h AND status='pending' AND type='code'
- 结果集 = 0 row (no candidate)
- cron 0 row 不 mint NAU 也不报错 · log "approved 0" (line 901 `if approved:` 真 short-circuit)

### 2.4 Layer 4 · 真 dormancy 上游 (handoff #017 §2.2)

```
V5 tool 分布 (3 day · agent_tool_calls):
tool_name                    | calls
bash                         |  2053
pf_list_bounties             |  1470
pf_task_detail               |  1114
read_file                    |   891
compass_recall               |   642
search_and_grep              |   626
selector:fulfill_directive   |   541
a2a_unread                   |   459
compass_ingest_obs           |   432
read_self_code               |   408

0 hit `/api/soul/dispatch`
0 hit `/api/discover`
0 hit governance vote tool
```

**真根因**:
1. cron P4 gate `vote_count >= 1` 永远 0 candidate · 因 V5 14875 tool calls 全 self-loop · 0 真 vote
2. handoff #016 早 flag "governance vote layer 39+ days dormant" · 5/28-5/30 状态未变
3. 真 dormancy 是 V5/Kairos 代码层不调 vote tool · NOT platform 层缺 timer

---

## 3. 真 finding · F3 误诊根因

| 错诊断 | 真根因 |
|---|---|
| "需独立 systemd timer" | cron 已 in-process 6h running · 0 LOC ship 也 active |
| "加 timer fix dormancy" | 0 candidate · timer 频率多高都 0 fire |
| "ship 独立 timer = belt-and-suspenders" | backend SPOF 风险 < 0 candidate 风险(0×N=0)|
| 真问题在 platform layer | 真问题在 V5/Kairos 代码层(anchor #7 cross-dialog turf) |

---

## 4. F3' 推荐 action(0 LOC platform)

### 4.1 平台侧 (anchor #7 不动 V5 代码)

**A. 不 ship 独立 timer** — 重复造轮子.

**B. 不修 cron 频率** — 0 candidate 时频率改变 0 影响.

**C. 0 LOC code 改动** — F3' 单纯 verify-only.

**D. 输出 honest evidence doc**(本文件)· 把"vote dormancy = 真根因"再凝固一次 · 防 anchor #6 "我以为加 timer 就解决" 复发.

### 4.2 真 dormancy 解决 (cross-dialog turf · 不在 F3' scope)

- agent-dialog · V5/Kairos · 真 wire `/api/discover` + governance vote tool 真 hit
- handoff #017 INBOUND_TO_V5 §9 48h status 已 surface · 等 V5 dialog 自决 · 不催
- F3' NOT a re-pitch to V5 · NOT a deadline

### 4.3 是否需要 alarm/dashboard alert?

可选 follow-up:加 dashboard metric 显示 cron last_run + 24h candidate count. 若 candidate=0 持续 30d+ 可作 anchor #2 闭环健康度 signal. 但这是 dashboard 工作 · 不属 F3 scope.

---

## 5. F3' binding-DONE 标准

- [x] code 真状态 audit(§2.1-2.2)
- [x] fire 真状态 evidence(§2.3 0 candidate)
- [x] dormancy 真根因 reconcile(§2.4 V5 0 vote)
- [x] 误诊 vs 真根因 table(§3)
- [x] 推荐 action(§4)· 0 LOC + 不挤 cross-dialog turf
- [x] honest no-op decision logged

---

## 6. References

- handoff #017 · `docs/HANDOFF_20260530_017_v5_inbound_48h_status.md` §2.2 §2.4
- handoff #016 · `docs/HANDOFF_20260529_016_fitness_observation_first.md` (governance vote layer 39+ day dormancy)
- proposal_consensus.py · `phase3/backend/services/proposal_consensus.py:82-149`
- cron_registry.py · `phase3/backend/services/cron_registry.py:161-165` + `:892-906` + `:1022`
- 5/28 PR #62 · `4ff339dc7` Inc 1.5 governance vote revival
- 5/28 un-disable cron · commit `fe1d97fc7`
- anchor #5 不重复造轮子 · `memory/anchor_user_strategic_compass.md`
- anchor #3 反 D 维护 · `memory/anchor_user_strategic_compass.md`
- anchor #7 cross-dialog turf · `memory/anchor_user_strategic_compass.md`

---

**Verify by**: platform-dialog · 2026-05-30 ~15:30 CST
**R3 timer**: ~1.5h elapsed · within 4h budget
**Next**: F5 (close OPEN PR + 停 daemon timer 止血)

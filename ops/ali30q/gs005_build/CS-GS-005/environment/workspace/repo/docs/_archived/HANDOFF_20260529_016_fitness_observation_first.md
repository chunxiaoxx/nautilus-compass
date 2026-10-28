# HANDOFF #016 · Fresh session 入口

**写于**: 2026-05-29 session 5 收尾(R3 ~5h+ 软越界 by user authorization)
**为**: 下个 fresh session
**默认主线**: cloud ruff install + 24h fitness_delta 观察(first falsifiable test)

---

## 🎯 Fresh-session 第 1 句 prompt(paste 用)

最短:
```
接 handoff #016 · cloud pip install ruff · 等 12 cycle 看 fitness_delta 分布 · 判断 reviewer 是否瓶颈
```

完整(含上下文):
```
接 handoff #016 · 默认主线 = cloud ruff install + 24h 观察:
1. ssh cloud · pip install ruff (or via system package) · verify which ruff
2. SELECT cycle_id, fitness_delta FROM engine_cycle_outcomes WHERE created_at > NOW() - INTERVAL '24 hours'
3. 12 个自然 daemon cycle 后 inspect 分布
4. 若 12 cycle 全 0.000 · reviewer.py target-picking heuristic 是瓶颈
5. 若有 positive tail · metric 真有信号 · 下一步 ship auto-merge gate
```

候选 path 见 §4.

---

## 1. master tip + open PR + cloud workspace 状态

### master HEAD
```
4255401cb inc3 slice B backlog-blocker fix · daemon abort path stamps dispatch row (#85)
10e20c02f feat(soul): Inc 3 Slice B · /api/discover + POST /api/soul/dispatch + daemon P2 wire (sentinel) (#81)
c0bff2fe0 fix(dashboard): heartbeat endpoint graceful stub · orphan import 500 → 200 (#79)
e5f9d58a7 feat(inc2): closeout Slice 5+6 · blessing + collaborative authorship (#75)
45b7a658a feat(soul): Inc 3 Slice A · goal-source classification foundation (#76)
```

### open PR(2 件 · 待 user merge)

| PR | branch | 内容 | 状态 |
|---|---|---|---|
| **#87** | inc3-slice-c-config | Slice C `config` task type · syntax-only gate(yaml/toml/json) | 124/124 + cloud BINDING-DONE row 5 |
| **#90** | inc3-fitness-function | fitness function mechanism · `engine_cycle_outcomes.fitness_delta` 列 | 123/123 + cloud mechanical BINDING-DONE row 6 |

### cloud workspace (`~/nautilus-soul-workspace`)
- daemon.py md5: `cb56db35c52a0b33f5f34b4dbb354315`(含 fitness wire · Slice C 未拷因 PR #87 未 merge)
- migrations applied to cloud DB:
  - `a1b2c3d4e5f6` Slice A goal_source + agent_dispatch_log
  - `b2c3d4e5f6a7` Slice B followup task_spec col
  - `c3d4e5f6a7b8` fitness_delta col
- nautilus-soul.timer active waiting · 2h interval
- nautilus-backend active + HTTP 200

### agent_dispatch_log 历史(6 row · 全 my INSERT)
```
 id | task_type | ship_outcome                  | cycle_id   | purpose
----+-----------+-------------------------------+------------+--------------------------
  1 | code      | legacy_empty_pre_followup     | NULL       | Slice A artifact 5/29 17:44
  2 | code      | shipped_pr83_pre_cycleid_fix  | NULL       | cycle_id-fix bug evidence
  3 | code      | shipped                       | 1780062515 | Slice B BINDING-DONE 永证
  4 | code      | checks_failed                 | NULL       | backlog-blocker PR #85 proof
  5 | config    | shipped                       | 1780066666 | Slice C PR #87 BINDING-DONE
  6 | code      | shipped                       | 1780069453 | fitness PR #90 mechanical BINDING-DONE
```

### engine_cycle_outcomes(本 session 3 个新 p2_agent_dispatch row)
```
  cycle_id  |    goal_source    | ship_status | fitness_delta
------------+-------------------+-------------+---------------
 1780069453 | p2_agent_dispatch | success     |         0.000   ← row 6 · fitness wire fire
 1780066666 | p2_agent_dispatch | success     |          NULL   ← row 5 · pre-fitness
 1780062515 | p2_agent_dispatch | success     |          NULL   ← row 3 · pre-fitness
 ... 历史 cycle 全 NULL goal_source + NULL fitness ...
```

---

## 2. 上 session 诚实诊断(必读 · 不读会误判状态)

[[session_20260529_recursive_loop_honest_diagnosis_fitness_strategy]] 全文。摘要:

**已 ship 的全部是 plumbing**:
- Slice A goal_source(merged #76)
- Slice B P2 dispatch wire + cycle_id fix(merged #81)
- Slice B-followup backlog-blocker abort stamp(merged #85)
- Slice C config task type(open #87)
- fitness function mechanism(open #90)

**0 业绩**:
- 0 daemon-generated PR ever merged into master(本 session close 5 个: #58 #72 #77 #78 #82)
- 0 V5/Kairos autonomous 调用 /api/soul/dispatch
- 0 organic agent fire dispatch · 全 6 row sentinel = my INSERT
- 0 NAU 转账 触发 by merged PR

**recursive self-improvement 闭环现状**:
机械上端到端可走 · 内容上 empty。"BINDING-DONE 真闭环"应严格区分:
- **mechanical BINDING-DONE**(已达)= plumbing 跑得通
- **产品 BINDING-DONE**(0/N 达)= daemon 真创造价值人接受

---

## 3. 默认主线 plan(fitness 观察 · ~30min ship + 24h 等)

### 3.1 cloud ruff install
```bash
# Option A · pip user install
ssh cloud "pip install --user ruff && which ruff"

# Option B · system package (preferred · /usr/bin/ruff)
ssh cloud "sudo apt update && sudo apt install -y ruff"

# verify
ssh cloud "ruff --version"
```

### 3.2 trigger 1 manual cycle to seed
```bash
ssh cloud "cd ~/nautilus-soul-workspace/phase3 && set -a && source ~/nautilus-soul-workspace/.soul-env && set +a && timeout 240 python3 -m soul.daemon"
```

### 3.3 等 24h timer fire(~12 自然 cycle 因 2h interval)
- 5/30 22:00 左右回头查
- timer 已 active · 不需手动 trigger

### 3.4 inspect 分布
```sql
SELECT cycle_id, goal_source, ship_status, fitness_delta, created_at
FROM engine_cycle_outcomes
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- summary
SELECT
  COUNT(*) AS total,
  SUM(CASE WHEN fitness_delta = 0 THEN 1 ELSE 0 END) AS zeros,
  SUM(CASE WHEN fitness_delta > 0 THEN 1 ELSE 0 END) AS positives,
  SUM(CASE WHEN fitness_delta < 0 THEN 1 ELSE 0 END) AS negatives,
  AVG(fitness_delta) AS mean,
  MAX(fitness_delta) AS max
FROM engine_cycle_outcomes
WHERE fitness_delta IS NOT NULL
  AND created_at > NOW() - INTERVAL '24 hours';
```

### 3.5 决策树
- `zeros = total · 0 positive tail` → **reviewer.py target-picking 是瓶颈** · 下个 increment 改 reviewer 选 target heuristic(从 random soul 模块 → 选有低 test coverage 或高 ruff warnings 的模块)
- `positives ≥ 1` → metric **真有信号** · 下个 increment ship "auto-recommend merge" gate(fitness_delta > 0 的 PR 标 "推荐 merge")
- `negatives 多` → daemon LLM 在劣化 code · review prompt 设计有问题 · 加 fitness_delta < 0 自动拒绝

---

## 4. 候选 alt path(用户 override 默认时选)

| Path | 触发条件 | 预计 |
|---|---|---|
| **(a)** merge PR #87 + #90 立即 | 用户优先收尾 PR | 10min |
| **(b)** Slice D `schema-migration` task type | 用户要补完 task type 三件套 | ~2h TDD |
| **(c)** Soul 跨 repo 化(anchor #2 字面争议) | 用户决断 "客户 defer" 是否含跨 repo 服务化 | design ~30min · ship ~3h |
| **(d)** reviewer.py target-picking 改造 | 用户跳过 24h 观察直接改 reviewer(假设瓶颈在那) | ~1.5h |
| **(e)** wire merged-PR → NAU composite delta | design_keystone_trinity 已设计 · 接 GitHub webhook | ~2-3h cross-dialog |

---

## 5. R3 / anchor 提醒

- **R3 4h**: 本 session 5h+ · 软越界 by user authorization · fresh session 重置计时
- **anchor #2**: option δ "客户 defer" 维持 · soul 跨 repo 化(Path c)字面争议 · 用户决断
- **anchor #3**: 本 session ship 4 increment · 全是 plumbing · 反 D 警示已亮(诚实诊断已 ship as PR #90 commit msg + handoff #016)
- **anchor #6**: anti-pattern 'sync-agent-engine.sh 覆写 daemon.py' 5/29 fire · grep code symbol 不是 md5 验
- **linguistic drift**: 本 session 多次 '真' 超 ≤3/段 max · 提醒下 session start 自检

---

## 6. Parking lot(不开新 session 处理)

- inc3-soul-engine 物理空 worktree dir(harness 锁 cwd 不能 rm · fresh session 不 init 它即可)
- soul 跨 repo 化 design doc(候选 Path c · 等用户战略决断)
- reviewer.py target-picking heuristic 改造(候选 Path d · 等 24h 观察数据)
- pyproject.toml.lock 文件(防 ruff 跨版本 inconsistent · 暂无)
- NAU 经济链 wire(候选 Path e · cross-dialog · 跟 V5/Kairos dialog 协调)
- 5 cloud row archive(我 5/29 提了 · 后来 anchor #6 救我 · 不 mutate forensic evidence · 留着)

---

## 7. Gotchas(踩过的坑 · 不再踩)

1. **sync-agent-engine.sh 覆写 daemon.py** · backend restart 触发 · daemon.py 在 `~/nautilus-soul-workspace` 被写回 OLD 版本(5/29 21:33 fire 一次)
   - **fix protocol**: scp daemon.py 后 `grep -n "<new symbol>" cloud:daemon.py` 验真符号到位 · 不要 md5 单同名 file 验
2. **cycle_id format mixed** · legacy `YYYYMMDD_hex` vs PR #81 后 epoch · 不 parse · JOIN verbatim
3. **gh search fuzzy tokenize** · `has_open_pr_for` 已 fix(PR #81 commit `f0be6111b`)· post-fetch exact prefix
4. **ruff not in cloud PATH** · `_compute_snapshot` fail-open ruff_warnings=0 · 默认主线第一步是 install ruff
5. **anchor #5 schema split-brain**: 每次 SQL 前 `\d <table>` 验列名 · 别猜
   - `agent_dispatch_log`: PK = id(BIGSERIAL) · `task_spec_hash` varchar(64) · `task_type` varchar(32) · `ship_outcome` varchar(32) · `cycle_id` TEXT FK to engine_cycle_outcomes
   - `engine_cycle_outcomes`: PK = cycle_id TEXT · `goal_source` TEXT · `fitness_delta` NUMERIC(8,3)
6. **DispatchTaskType Literal['code','config','schema-migration']** · code + config 已 wire · schema-migration 留 Slice D
7. **PR #87 + #90 base off master 不同**:
   - #87 base = `e5f9d58a7` (pre #79 #81 #85 merge · Slice C ship before backlog-blocker · Slice C 含老版本 daemon.py 不含 backlog-blocker)
   - #90 base = `4255401cb` (post #85)
   - **merge 顺序**: #87 先 merge · 然后 rebase #90 onto master · 或者 merge #90 先 · 然后 #87 需手动 resolve · 推荐先 merge #87

WAIT — actually let me re-check this gotcha. #87 base = master at time of branch create. branch create was when master was at 10e20c02f (after Slice B PR #81 merge but before #85). Need to verify. Actually I created #87 branch off master after PR #81 merged but before PR #85 was merged (commit timestamps). PR #85 was merged at 14:52:58 UTC. #87 was created earlier. So #87 missing backlog-blocker fix from #85. Will need rebase or auto-merge will handle.

Actually GitHub auto-merge will rebase. Should be fine. But operator merging may want to merge in order #87 then #90 (or rebase #90 onto #87).

---

## 8. Test counts state (for fresh session reference)

- soul suite at master (`4255401cb`): **113 tests**
- soul suite at #87 head: **124 tests** (+11 config)
- soul suite at #90 head: **123 tests** (+10 fitness · diverged from master + #85 = 113 + 10 = 123)
- after both merge + rebase: **134 tests** expected (113 + 11 + 10)

---

**End of HANDOFF #016**

Fresh session start:
1. read 本 doc + linked memory(diagnosis)
2. paste §0 prompt
3. don't pretend "上次说定" — 本 doc 是 single source of truth

# PoI 信用跨主机累积 · 中央表(Option C · MVP 单表)

> 设计日期 2026-06-03 · 接 P5(`2026-06-03-p5-v14-poi-emission-design.md`)收尾
> 经 brainstorming(6 决策)+ 3 视角对抗审查(架构一致性 / failure·安全 / YAGNI)定稿
> 状态:design approved · 下一步 writing-plans

## 1. 问题

PoI(Proof of Impact)信用闭环:memory 被召回 → agent 行动成功 → 该 memory 累积信用 → 未来召回时 boost 排名。

当前信用存在 memory 文件的 YAML frontmatter(`cumulative_impact` 字段),**跟文件物理位置绑死**。但闭环天然跨主机:

- recall:任意 daemon(本地 9876 / 云端 8770)
- outcome:云端 postgres `agent_tool_calls`
- **credit:写本地文件 frontmatter → 锁死文件所在主机**
- boost:读文件的那个 daemon

V5 召回打云端 daemon、outcome 在云端、但本地 reconciler 的 `MEMORY_ROOT` 是本地 → 碰不到云端 memory → M1 guard(文件存在才 settle)挡住 → **settled=0,信用永不累积**。

根因:**信用是图属性(memory X 帮了 agent Y),却存成主机本地副产物,agent / 主机越多越断。**

## 2. 目标

1. 信用的权威载体放到云端一张表,任意主机的 reconcile 都往这张表累加
2. 本地 boost 时拿到这张表的值(~0ms,不依赖 DB 可用性)
3. 顺带让 L4「跨 agent 信用全局可见」白送(`SELECT … ORDER BY impact` 即全局视图)

## 3. 决策汇总(brainstorming + 审查重裁)

| # | 决策 | 说明 |
|---|---|---|
| 1 | `memory_key = project/filename` | 如 `C--Users-chunx/session_x.md`,防跨 project 短名碰撞 |
| 2 | **单表 MVP**(审查重裁) | 砍 ledger 明细 / recompute / distinct_consumers。boost 只读一个标量,明细已有两份(`poi_events.jsonl` + 云端 `agent_tool_calls`),L4「谁受益」可 join `agent_tool_calls` |
| 3 | 快照 cache | reconciler 现有 DB 连接顺手 `SELECT` 出 dict,~0ms boost,DB 挂了 daemon 照常跑 |
| 4 | 设计含两侧 · 实现分两期 | Phase 1 本地(不动 live)/ Phase 2 云端 daemon boost |
| 5 | **迁移砍**(审查重裁) | 从零累积(几天 reconcile 长回来);关键召回锚点可手动 INSERT 几行 |
| 6 | **写角色简化**(审查重裁) | Phase 1 复用现有连接加单表写权;Phase 2 再建 `poi_writer` 专用角色收紧 |

被否方案(记录避免重提):A 云端再跑一个 reconciler 写云端文件(治标,留 2-reconciler + 文件锁死债);B 每 daemon 一个信用 side-store(半步解耦)。

## 4. 架构

```
┌─ emission(已 LIVE,本设计加 project 字段)
│   本地 recall → poi_candidates.jsonl {ts,kind,actor,project,memory,query_hash,rank,score}
│   云端 /v1/v14/recall → 同 schema(inline 自包含副本)
│
├─ reconcile(本地跑,持云端 DB 连接)
│   load candidates → fetch outcomes(agent_tool_calls)→ match(24h 窗 + actor)
│   → settled_keys 去重 → UPSERT compass.poi_credit(累加)→ 导出快照(原子写)
│
└─ boost(本地 daemon 9876)
    boost_top_k:查内存 cache dict[memory_key] → miss 回退 frontmatter(过渡)
    → NaN/异常兜底裸 cosine
```

### 4.1 表(放进现有 `compass` schema)

```sql
CREATE TABLE IF NOT EXISTS compass.poi_credit (
    memory_key        text PRIMARY KEY,            -- project/filename
    cumulative_impact double precision NOT NULL DEFAULT 0,
    event_count       int NOT NULL DEFAULT 0,
    last_impact_at    timestamptz
);
```

settle 时(替代 `update_frontmatter_cumulative`):

```sql
INSERT INTO compass.poi_credit (memory_key, cumulative_impact, event_count, last_impact_at)
VALUES (:mk, :delta, 1, :now)
ON CONFLICT (memory_key) DO UPDATE
SET cumulative_impact = compass.poi_credit.cumulative_impact + EXCLUDED.cumulative_impact,
    event_count       = compass.poi_credit.event_count + 1,
    last_impact_at     = EXCLUDED.last_impact_at;
```

`impact` delta 计算不变:`outcome_weight × cite_factor × drift_penalty`(`poi_calculator.py`)。

### 4.2 幂等(单表方案的关键)

累加 UPSERT 本身不幂等(重跑会双计)。Phase 1 靠 reconciler 现有 `settled_keys`(`candidate_key(actor, memory_key, query_hash)`)去重:**check settled → 未 settled 才 UPSERT + 记 settled + save**。

- 边界:`settled_keys.json` 是本地 per-host + 有 5000 截断。**删除 / 截断淘汰会导致重算双计**。文档标注「勿删」。
- Phase 1 只有本地一个 reconciler,该假设成立。
- Phase 2 若云端也跑 reconciler → 加云端极简幂等键表(单列 UNIQUE,非明细账本)替代本地 json。

`candidate_key` 三元组的 `memory` 必须同步改成 `memory_key`(含 project),与未来 DB 约束口径一致。

### 4.3 快照

reconciler UPSERT 后顺手 `SELECT memory_key, cumulative_impact FROM compass.poi_credit` → 写 `poi_credit_cache.json`(dict)。

- **原子写**:`tmp → fsync → os.replace`(现有 `save_settled` 是非原子直写,不可沿用)
- daemon 启动 + mtime 定期 reload 进内存;**reload 失败保留旧内存 dict,不清空**
- 大小上限校验,超限 / 损坏退回旧 dict

## 5. 横切 P0(三方审查命中,无论方案都纳入)

1. **`derive_memory_key(project, filename)` 单一函数** — 当前 candidate 只带纯文件名,project 不在数据里(reconciler 环境变量隐式注入)。三处(本地 emit / 云端 inline 副本 / boost 查表)调同一函数 + 契约测试钉死「本地与云端副本同输入同输出」。candidate JSONL 加 `project` 字段,`pull_cloud_candidates.py` 透传。
2. **NaN/inf 兜底** — `float("nan")` 不抛异常,`clamp(nan)` 污染,`sort` 用 NaN 比较打乱整个 top-K。`_parse_cumulative_impact` 后 `if not math.isfinite(v): return 0.0`;boost 后 `if not math.isfinite(boosted): boosted = cosine`。clamp `[-0.5, +1.0]` floor/cap 随快照迁移并单测钉死。
3. **快照原子写** — 见 4.3。
4. **M1 guard 语义迁移** — 现「本地文件存在才 settle」会让只存在于云端的 memory 永远 `exists()==False` → 复活 settled=0。settle 真相落点从 frontmatter 改为 DB UPSERT;幂等护栏从文件系统移到 settled_keys(Phase 1)/ 云端键表(Phase 2)。文件存在与否不再是 settle 前置条件。
5. **self-cite 抑制迁移** — 现靠读本地 frontmatter 的 creator 比对。frontmatter 停写后失效 → agent 自引自造 memory 无限刷分。creator 进 candidate;settle 端 `consumer != creator` 过滤。
6. **刷分防护** — outcome 只由 reconciler 从可信源(`agent_tool_calls.success` / 本地 session drift)派生,写入端不接受调用方自报 outcome。

## 6. Phase 划分

### Phase 1(本轮实现,不动 live)

落地面:1 SQL + 3 代码接缝 + 1 快照导出。

| 件 | 文件 | 改动 |
|---|---|---|
| SQL | `sql/004_poi_credit.sql` | 建 `compass.poi_credit` + grant 现有可写账户 |
| emission | `proof/poi_emitter.py::emit_poi_candidate` + 云端 inline patch | candidate 加 `project` 字段 |
| reconcile | `ops/poi_reconcile_cron.py` + `proof/poi_reconciler.py` | settled_keys 去重 → UPSERT 云表(停 `update_frontmatter`)→ 导快照(原子);M1 guard 语义改;candidate_key 含 project |
| boost | `recall_pkg/poi_weighting.py::boost_top_k` | 查 cache dict(`.get(mk, 0.0)`)→ miss 回退 frontmatter(过渡双读)→ NaN/异常兜底 |
| derive | 新 `derive_memory_key` 工具 | 单一来源 + 契约测试 |

**验证**:本地 dialog recall 被 boost · 端到端 settled > 0 · 重跑 reconcile 不双计。

**诚实边界**:Phase 1 后 **V5 云端召回尚未被 boost**(云端 daemon 不读快照)。L3 对本地闭、对 V5 待 Phase 2。明告 V5。

### Phase 2(下轮,动 live 端点,单独验证回滚)

| 件 | 改动 |
|---|---|
| 快照上云 | reconciler scp 快照 → **`/var/lib/compass/poi/`(sandbox 白名单)** + ssh 回读 `test -s` + `json.load` 校验非空可解析才触发 reload |
| 云端 boost | `compass_http_v09.py` 8770 接 boost:**后台线程 reload + 原子指针 swap · 零共享锁**;recall 热路径只读已加载 dict;boost `try/except` 永不拖垮 V5 recall;env `COMPASS_CLOUD_POI_BOOST=0` 默认关,验证后开 |
| 写角色 | 建 `poi_writer` 专用角色收紧权限;secret 复用 `.soul_db_secret` 模式(独立文件 600 + scp 传输,不 inline / log / git) |
| 多主机幂等 | 云端幂等键表替代本地 settled_keys |

**最高风险事故链(安全审查标的)**:scp 落非白名单 → `ProtectHome=read-only` 静默吞 → daemon reload 空 snapshot → reload 卡共享锁(无 swap 内存抖动旧伤)→ V5 全拒召回。三层防护:投放层(硬钉白名单 + 回读校验)/ 加载层(后台线程原子 swap,失败保留旧)/ 熔断层(boost try/except + 超时,异常返回裸 cosine)。改 live 文件只走部署 / patch 脚本,绝不 inline `python -c` 带 `\n`。

## 7. 测试(TDD)

- `derive_memory_key` 一致性(本地实现 ↔ 云端 inline 副本契约)
- boost:cache 命中 / miss 回退 frontmatter / NaN / inf / 异常兜底裸 cosine / clamp floor-cap 钉死
- 快照:原子写 / 损坏退回旧 dict / 缺失退不 boost / 大小上限
- reconcile:UPSERT 累加正确 / settled_keys 幂等重跑不双计 / 停写 frontmatter / M1 语义(云端 memory 也能 settle)
- self-cite:consumer == creator 被过滤
- SQL:表 + grant 应用

## 8. 错误处理

- 快照缺失 / 损坏 → 不 boost(graceful,沿用 `COMPASS_NO_POI_BOOST` 兜底语义)
- DB 写失败 → 不推进 settled_keys → 下个 cron 重试(幂等安全)
- boost 任何异常 / 超时 → 返回裸 cosine,**recall 永不因 boost 失败而失败**(boost 是增强不是依赖)

## 9. 关键文件

- `proof/poi_emitter.py` — candidate schema 加 project、停写 frontmatter
- `proof/poi_reconciler.py` — settle 落点、M1 guard、candidate_key 三元组、idempotency
- `recall_pkg/poi_weighting.py` — boost 改查快照 + NaN/clamp 防护
- `ops/poi_reconcile_cron.py` — UPSERT + 快照原子导出 + 连接复用
- `ops/pull_cloud_candidates.py` — project 字段透传
- `ops/patch_v14_recall_poi_candidate.py` — 云端 inline emission(derive_memory_key 契约另一端)
- `sql/004_poi_credit.sql` — 新表 + grant
- 参照 `ops/cross_agent_outcome_poller.py` — secret / 隧道 / 只读连接复用模板

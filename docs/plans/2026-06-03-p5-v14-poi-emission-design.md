# P5 生产激活 · v14 recall PoI candidate emission — 设计

> 2026-06-03 · branch `feat/p5-v14-poi-emission` · 接 [[session_20260602_compass_l1l4_phases123_shipped]]

## 目标

让 L3 PoI 递归闭环在**生产路径**真正落地。当前 candidate emission 只在 `recall.py` 的 hook/CLI/daemon 路径 fire,而平台 agent(V5)走的是云端 HTTP `/v1/v14/recall`(8770)—— 该路径不 emit candidate。本设计给 `/v1/v14/recall` 加 candidate emission,并在本地搭 reconciler,使:

```
平台 agent 调 v14 recall → candidate(带 actor=agent_id)→ agent 行动 → outcome(agent_tool_calls)
→ reconciler join → cumulative_impact 累积到被引用 memory → 下次 recall boost_top_k 用上
```

## 跨对话框契约状态(已锁)

`cnt_compass_v5_recall_demand_c1`,双侧拍板 **(A)**:
- V5 实际打 `/v1/v14/recall`(`compass_client.py:220`),当前 params `{q, top_k, scope, project}` 无 agent_id
- `/v1/v14/recall` = 云端 adapter → daemon:9876 BGE-m3(V5 真语义召回);`/v1/recall` = 旧 keyword fallback(拒降级)
- **序列**:① compass 给 v14 recall 加 emission(gating · 本设计)→ ② V5 加 1 行 `agent_id=nautilus-prime-001`(ready-on-signal)→ ③(可选)V5 selector 决策点 wire
- join 口径:`candidate.actor == agent_tool_calls.agent_id` 严格相等 + 24h 窗

## Ground 出的关键事实(勘察实证)

- live `v14_recall` 在云端 `/home/ubuntu/compass/compass_http_v09.py:1358`,GET 路由,`hits = d.get("recall", [])`
- 既有 v14 adapter patch 幂等 skip(已 patch)→ 必须**新增量 patch**,不重跑旧 patch
- hits shape = `[{score, path(文件名), age_seconds, age_str, description}]`,镜像 `recall.py:1264` 的 `[(h["score"], h)]` 转换
- 🔴 `proof/` 包只在 `/home/ubuntu/nautilus-compass/proof`,**不在** 8770 server 的 CWD `/home/ubuntu/compass` → server 默认 import 不到 `emit_poi_candidate` → **inline 自包含**(决策 D1)
- 云端 `.cache` 不存在(待建)· 写 `/home/ubuntu/compass/.cache/poi`(决策 D2)
- 🔴 candidates 在云端、被引用 memory 文件在**本地 Windows**(9876 BGE daemon 本地跑 · 经反向隧道索引本地文件)· `cumulative_impact` credit 必须落本地文件(daemon 读它做 boost)→ **reconciler 本地跑**(决策 D3)
- 云端 DB `nautilus_production` 在 localhost:5432 直连可达 · psycopg2 OK · 但云端**无 compass_sub secret**(本地有)
- 此刻反向隧道 down → v14 返回 0 hits;e2e 验证需先拉起本地 9876 隧道

## 设计决策

| # | 决策 | 选择 | 理由 |
|---|------|------|------|
| D1 | emission 代码放哪 | inline 自包含(不 import proof) | 匹配既有 `_call_v14_daemon` 自包含风格 · 无跨目录耦合 · repo 移动不影响 live · candidate schema 极简稳定 |
| D2 | cache dir | **`/var/lib/compass/poi`**(env `COMPASS_POI_CACHE_DIR`) | 🔴 修正:compass.service `ProtectHome=read-only` + `ProtectSystem=strict` · `ReadWritePaths=/var/lib/compass /tmp /home/ubuntu/.claude` · 写 /home/ubuntu/compass 被静默拒。/var/lib/compass 是 RW + 持久 |
| D3 | reconciler placement | 本地拉云 | credit 必须落本地 memory 文件 · 云端碰不到本地文件会永远 settle=0 |

## Component 1 · candidate emission(云端 gating)

`ops/patch_v14_recall_poi_candidate.py` — 幂等增量 patch:
- guard marker `_v14_emit_poi_candidate`,已 patch 则 skip
- **edit 1**:给 `v14_recall` 签名加 `agent_id: Optional[str] = None`(query 参数)
- **edit 2**:插入 inline helper `_v14_emit_poi_candidate(hits, query, agent_id)`
  - cache dir = `COMPASS_POI_CACHE_DIR` 默认 `/home/ubuntu/compass/.cache/poi`
  - 写 `poi_candidates.jsonl`,每 hit 一行,schema 同 `proof/poi_emitter`:`{ts, kind:"candidate", actor, memory, query_hash, rank, score}`
    - `actor` = agent_id or `"unknown"`;`memory` = `hit["path"]`(文件名);`query_hash` = `sha1(query)[:16]`
  - **云端跳过 self-cite 抑制**(memory 文件不在云端 · 无 frontmatter 可读 · 平台 agent 引用平台 memory 正是想 credit 的)
  - try/except 包裹 · 永不破坏 recall · `COMPASS_NO_POI_CANDIDATE=1` 可关
- **edit 3**:在 `v14_recall` 成功 return 前插 emit 调用,仅 `hits` 非空时 fire

## Component 2 · 本地拉云 reconciler

- `ops/pull_cloud_candidates.py` — ssh 拉云端 `poi_candidates.jsonl` → 行级 dedup 合并进本地 `COMPASS_POI_CACHE_DIR/poi_candidates.jsonl`(纯函数 merge · 幂等)
- 复用现有 `ops/poi_reconcile_cron.py`:本地跑 · 隧道连 DB(compass_sub)· `MEMORY_ROOT`=本地 memory dir → 真 credit 本地文件
- Windows scheduled task:pull → reconcile(`.cmd` wrapper · 同 L4 poller 模式)
- 注:`db_connection` 本地跑无需改(本地经 ssh 隧道连云端 DB 是它原设计)

## TDD 策略

- **C1**:patch 的 emit helper 作字符串常量 `EMIT_HELPER`,测试 `exec` 它进 namespace,断言 JSONL schema / 行数 / actor / 空-hits-不写。测的就是部署的代码,无 drift。
- **C2**:`pull_cloud_candidates` 的 dedup-merge 作纯函数单测(已有行 + 新行 → 去重)。

## 验证(verification-before-completion)

- **C1 e2e**:拉起本地 9876 隧道 → `curl 'http://<8770>/v1/v14/recall?q=...&agent_id=test-poi-001&project=C--Users-chunx'` → SSH cat 云端 `poi_candidates.jsonl` 实证 `actor=test-poi-001` 行落地
- **C2**:`--dry-run` 跑 pull + reconcile,确认拉云 + 连 DB 通

## 诚实边界

- settle 在 V5 加 `agent_id=nautilus-prime-001` 前**恒为 0**(本地/test candidate 的 actor join 不到平台 agent_tool_calls outcome)。本 session 交付 = **emission live + reconciler 待命**;V5 一行 + e2e 即闭环。
- 给 V5 的 signal 要讲清:`cumulative_impact` credit 落**本地**(非"8770 侧"),outcome 一致,落点不同。

## 部署实测发现(2026-06-03 · verification 中挖出)

1. **🔴 systemd 沙箱 = emission 静默不落的真根因**:`ProtectHome=read-only` 让写 `/home/ubuntu/compass/.cache/poi` 失败,被 emit 的 try/except 吞 → 无 candidate 无报错。修 = cache 移 `/var/lib/compass/poi`(ReadWritePath)。debug 时 `PrivateTmp=true` 也让我的 /tmp trace 进了私有 /tmp(看不到)· 误导良久。
2. **云端 BGE daemon 内存页抖动**:`compass-bge-daemon.service`(serves V5 v14 recall)在 majflt 986/s · 160MB/s re-fault mmap 的 bge-m3 模型 → load 10.75 → inflight 占满 → 拒所有 recall(V5 生产降级)。根因 = 15GB 机内存超额无 swap。**修 = 加 8GB swapfile** → load 10.75→5.22 · majflt→0 · recall 15s→0.85s。
3. **live v14_recall v1.5.8 drift**:加了第二个 `if not d.get("ok")` early-return → emit anchor 改 success-return signature。
4. **pull Windows gotchas**:cloud SSH(port 24860)负载下 rc 255/timeout → pull 加 3x 重试;`subprocess(text=True)` 默认 GBK 解码 UTF-8 中文 memory 名 → `encoding=utf-8`。

## e2e 验证证据
- Component 1:真 GET `/v1/v14/recall?agent_id=finalverify-2` → 3 candidate 行落 `/var/lib/compass/poi/poi_candidates.jsonl`(actor/memory/score 齐)
- Component 2:pull 27 candidates(finalverify-2×3 + unknown×24 真 V5 流量)→ reconcile DB 隧道连上 → settled=0(test/unknown actor 无平台 outcome · 正确)→ scheduled task `compass-poi-reconcile` Last Result 0
- 待 V5 加 `agent_id=nautilus-prime-001` → 那批 candidate join 平台 outcome → settle → cumulative_impact credit

## 关联
- [[session_20260603_compass_confirm_v5_path_A_v14recall_closeloop]]
- [[session_20260602_compass_l1l4_phases123_shipped]]
- [[reference_compass_dev_gotchas]]

# FDE+RSI 双轮闭环 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 compass 已建好但未接生产的检索/记忆能力激活到生产热路径,并新建"专家复核→外部 ground truth"回路,闭合 FDE+RSI 双轮。

**Architecture:** 接线优先(不发明新能力)。设计依据 `docs/plans/2026-06-05-fde-rsi-dual-flywheel-closure-design.md`。守 3 原则:热路径不调 LLM(本地 BGE/交叉编码器可)、不碰平台内部 RSI wiring、FDE 专家/字节是外部信号(合规)。

**Tech Stack:** Python · BGE-m3 + bge-reranker-v2-m3(本地交叉编码器)· postgres `compass.poi_credit` · 飞书 OpenAPI(`feishu_client.py`)。

**执行前必读**(写精确 diff 需要):每个 Task 标了 file:line 锚点,执行时先 Read 该函数完整体再改。生产路径改动后必须用 `RESULTS.md` 的 benchmark **在生产 recall 路径上**复测,不能只跑 benchmark 管线。

---

## Phase 1 · 缺口2:检索栈进生产(最直接解"长期记忆"·纯 compass turf)

> 现状:生产 daemon recall = 裸 bge-m3;reranker(P@5 0.86→0.92)、query-rewrite(单会话 +27)、lifecycle 提升 全在 benchmark/未激活。目标:逐个接进生产 recall 热路径,benchmark 实测生产分提升。

### Task 1.1: 摸清生产 recall 路径与 reranker 现有实现(调研·不改码)
**Files:** Read `daemon.py:610-720`(handle_request recall)、`recall.py:980-1000`+`recall.py:1241-1267`、`tests/eval_rerank.py`、`RESULTS.md:54-56,186`。
**Step 1:** Read 上述,记录:生产 recall 返回前最后一个排序点(注入 reranker 的位置)、reranker 调用签名(模型加载/输入格式/输出)、benchmark 里 reranker 怎么用。
**Step 2:** 写一页 `docs/plans/_notes_rerank_wire.md` 记录注入点 file:line + reranker 接口签名 + 风险(模型加载耗时/内存)。
**Step 3:** Commit notes。

### Task 1.2: 生产 reranker 开关(默认行为先不变·TDD)
**Files:** Modify `daemon.py`(recall 路径)· Test: `tests/test_daemon_rerank_prod.py`(create)。
**Step 1:** 写失败测试:构造已知 query+候选集,断言"开 `COMPASS_PROD_RERANK=1` 时返回顺序 = reranker 重排序,关时 = 原 dense 序"。
**Step 2:** `pytest tests/test_daemon_rerank_prod.py -v` → FAIL。
**Step 3:** 在 Task 1.1 记录的注入点加:`if os.environ.get("COMPASS_PROD_RERANK")=="1": results = rerank(query, results)`,复用 benchmark 已有 rerank 函数(不重写)。注意 reranker 是本地交叉编码器,守黑盒约束。
**Step 4:** `pytest ... -v` → PASS。
**Step 5:** Commit `feat(recall): production reranker behind COMPASS_PROD_RERANK flag`。

### Task 1.3: 模型懒加载 + 降级(reranker 加载失败不破 recall)
**Files:** Modify `daemon.py` · Test: `tests/test_daemon_rerank_prod.py`(add)。
**Step 1:** 写失败测试:reranker 加载抛异常时,recall 仍返回 dense 序(不 crash)+ 日志告警。
**Step 2:** 跑 → FAIL。
**Step 3:** 包 try/except,异常吞掉退 dense(参 `metamemory/builder.py` llm_backend 异常吞的写法)。reranker 模型进程内单例懒加载。
**Step 4:** 跑 → PASS。
**Step 5:** Commit。

### Task 1.4: benchmark 实测生产路径分提升(验证·非单测)
**Files:** Read `BENCHMARKS_REPRODUCE.md`;Run benchmark against 生产 recall 路径(开 flag)。
**Step 1:** `COMPASS_PROD_RERANK=1` 跑 LongMemEval 检索 eval,记 P@5/MRR。
**Step 2:** 对比 `RESULTS.md` 裸 bge-m3 基线(P@5 0.86),确认生产路径开 flag 后 ≥0.90。
**Step 3:** 把生产路径实测数写进 `RESULTS.md` 新增"生产路径"列(区分 benchmark-only)。Commit。
**Gate:** 若生产路径分没到 benchmark 水平 → 用 systematic-debugging 查注入点是否在正确排序阶段。

### Task 1.5: query-rewrite + lifecycle 提升(同模式·各一轮 TDD)
**Files:** Modify `daemon.py`/`recall.py:708`(`promote_lifecycle_tier`)· Test: 各 create。
**Step:** 重复 1.2-1.4 模式:`COMPASS_PROD_QUERY_REWRITE`(若用 LLM 则 opt-in 守黑盒)、`COMPASS_PROD_LIFECYCLE`(调 `promote_lifecycle_tier`,纯算术非 LLM)。各自失败测试→实现→benchmark 验→commit。

---

## Phase 2 · 缺口1:跨设备 ingest 修(小·解跨设备原文召回)

### Task 2.1: 云端实测确认 bug(先证实再修)
**Files:** Read `ops/v0.9_to_v14_adapter_patch.py:187-216`、`daemon.py:1092,982`。
**Step 1:** 对云端 `/v1/v14/ingest_obs` POST 一条测试 obs(带 `content` 字段),再 recall 它,确认是否召回得到。
**Step 2:** 记录结果:若召回不到=证实静默失败(`ingest_obs+content` vs daemon `ingest+text` 不匹配)。写进 notes。
**Gate:** 若云端能召回 → daemon 是别的构建,bug 不存在,跳过 Phase 2,只记差异。

### Task 2.2: 对齐 action/字段(TDD)
**Files:** Modify `ops/v0.9_to_v14_adapter_patch.py` 或 `daemon.py:1092` · Test: `tests/test_ingest_obs_route.py`(create)。
**Step 1:** 失败测试:`action="ingest_obs"`+`content` 经分发能命中 `handle_ingest` 并写入。
**Step 2:** 跑 → FAIL。
**Step 3:** 二选一(看 Task 2.1):adapter 把 `ingest_obs→ingest`+`content→text`,或 daemon 分发兼容 `ingest_obs`。选影响面小的一侧。
**Step 4:** 跑 → PASS。
**Step 5:** Commit。
### Task 2.3: 云端端到端复验
POST→recall 召回得到 → 确认跨设备原文召回闭环。记 `docs/CROSS_PROJECT_RECALL.md`。Commit。

---

## Phase 3 · 缺口3:FDE verdict→PoI adapter(双轮咬合·接 soul verdict 流)

> 大纲(待 soul checklist_scorer 真实 verdict 流稳定后细化)。
- Task 3.1: 定义 FDE outcome schema(checklist 通过率 + 专家复核结论 → poi outcome),映射 `proof/poi_reconciler.py:37-44` 的 success/failure/pending。
- Task 3.2: adapter 把 FDE verdict 写 `agent_tool_calls` 兼容形态(或直接 upsert `compass.poi_credit`),复用 `proof/poi_credit_store.py:18`。TDD:mock verdict→credit。
- Task 3.3: 云端开 `COMPASS_CLOUD_POI_BOOST=1`,验 credited memory 召回被 boost。
- 边界:FDE 外部信号,不碰平台内部 RSI。

## Phase 4 · 缺口4:专家复核回路(新脉·复利源·G3.1 已解)

> 大纲(可先 mock,真数据待批次)。
- Task 4.1: `feishu_client` 读复核工作台 Bitable(通过/打回+理由+分项分)。TDD:mock Bitable→结构化记录。
- Task 4.2: 双喂 adapter:(a) 复核结论→Phase 3 PoI;(b) 复核理由→T3 胶囊管线(避坑知识)。
- Task 4.3: 端到端 mock:一条专家复核→PoI 信用 + 胶囊条目。真飞书数据待真批次。

---

## 执行状态(2026-06-05 · branch feat/prod-retrieval-wiring)
- **T1 缺口2 检索栈进生产 · DONE+验证**
  - 1.1 ✅ 注入点 notes(`docs/plans/_notes_rerank_wire.md`)
  - 1.2/1.3 ✅ `_rerank_top` + 懒加载单例 `_get_reranker` + 降级 · `COMPASS_PROD_RERANK` 默认关 · 6 TDD
  - 1.4 ✅ 生产路径实测:dense P@5 0.750 → prod `_rerank_top` 0.917(+0.167)· `tests/eval_rerank_prod.py` · RESULTS.md 生产路径列
  - 1.5 ✅ lifecycle forget-filter `COMPASS_PROD_LIFECYCLE`(parse 提 forget_at + `_apply_lifecycle_filter`)· 7 TDD · 默认关
  - 1.5 query-rewrite: ⚠️ **无现有实现**(grep 证)→ 净新 LLM 功能,本 goal 不造轮子(anchor #3/#5),记 finding deferred
- **T2 缺口1 跨设备 ingest · 调查到 G-cloud 边界**(`docs/plans/_notes_ingest_obs_roundtrip.md`)
  - 2.1 ✅ 实测:Finding 1 = CJK-name surrogate 崩溃(可复现);Finding 2 = ASCII obs 写成功但 3 次/~25min 召回不到 = round-trip gap(印证诊断)· 根因 **gated G-cloud**
  - 2.2/2.3 ⏸ held:fix 需 G-cloud(云端 FS/日志/部署),v0.9 vs v14 端点待辨
- **T3 缺口3 FDE verdict→PoI adapter · DONE(mock)**:`proof/fde_poi_adapter.py` · 13 TDD(sqlite poi_credit e2e)· 真数据待 **G-verdict**;云端 boost 待 **G-cloud**
- **T4 缺口4 专家复核回路 · DONE(mock)**:双喂 e2e `vertical-task-factory/fde-toolbox/fde_dual_feed_demo.py` 自验通过(1 通过→正 PoI+胶囊 · 1 打回→负 PoI)· 真飞书数据待 **G-batch**

## 执行顺序与 gate
1. **Phase 1**(缺口2)立即可做·纯 compass·最高价值(解长期记忆)。
2. **Phase 2**(缺口1)小修·需云端实测先证实。
3. **Phase 3/4** 与 FDE 真批次并进(3 待 soul verdict 流,4 待真专家复核数据,均可先 mock)。

## 不做(YAGNI)
不重训/不自建向量库;热路径不加 LLM;不抢平台内部 RSI wiring;缺口4 真批次前不做 UI。

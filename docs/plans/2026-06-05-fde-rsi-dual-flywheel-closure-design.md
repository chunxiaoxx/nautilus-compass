# FDE+RSI 双轮闭环设计 · 接线优先 + 专家回路为新脉(2026-06-05)

> 来源:用户拷问"记忆胶囊/LLM-WIKI2融合/LLM增强/跨设备记忆涌现 闭环了吗?如何强化 compass 实现 FDE+RSI 双轮?专家互动能否复利?那么多记忆文档真能长期记忆吗?"
> 方法:4 路并行 agent 带问题读 compass/nautilus-core/nautilus-v5 真实代码(file:line 证据)。本 doc = 证据驱动诊断 + 设计骨架(brainstorming 产出,用户已认可主脉)。

## 0. 一句话总判定
**compass 不缺能力,缺"接线 + 外部 ground truth"。** 6 项能力 5 项是"建好了但没接生产热路径 / 默认关",唯一生产 live 的是 metamemory 自知层。平台 RSI benchmark 弧已三连负证伪——**内部自评跑不通,RSI 唯一活路是外部 ground truth,而 FDE 专家复核/字节接收正是它。**

## 1. 证据诊断:六能力真实状态(file:line)

| 能力 | 判定 | 证据 | 闭环差什么 |
|---|---|---|---|
| 记忆胶囊 | 本机闭环·跨设备半闭环 | 摄取 `daemon.py:956`(写+embed+缓存)/召回 `daemon.py:667`;无 capsule 抽象,单元=session_*.md | `/v1/v14/ingest_obs` 用 `ingest_obs+content`,daemon 只认 `ingest+text`(`daemon.py:1092`)→ 疑似静默失败,需云端实测 |
| 检索保真度 | 半闭环 | 生产=裸 bge-m3;reranker 把 P@5 0.86→0.92、单会话 MRR 0.398→0.522(`RESULTS.md:54,186`),只在 benchmark | reranker+query-rewrite+lifecycle 进生产 daemon 热路径 |
| LLM-WIKI2 融合 | 半闭环 | =Ebbinghaus 遗忘+4层做成零-LLM schema(`paper/LLM_WIKI2_FUSE_DESIGN.md`);字段+函数+测试齐,`README:104` 自认生产未激活 | 生产 recall 调 `promote_lifecycle_tier()` |
| LLM 增强融入 | 半闭环 | judge(Gemini)+离线蒸馏(本地 Qwen `l2_distiller.py:33`)在用;召回 `llm_backend` hook 在(`metamemory/builder.py:76`)未接 provider(`recall.py:1247`);5 LLM flag 未接线(`llm_opt_in.py:31`) | hook 接 Qwen/MiniMax 适配器 |
| PoI 信用 | 代码闭环·信用稀疏 | 中央账本 `sql/004_poi_credit.sql`;全链 `proof/poi_*`;实测 boost 0.7830→0.8091 | V5 喂 verified 外部 outcome + 云端 `COMPASS_CLOUD_POI_BOOST=1`(默认关) |
| metamemory 自知层 | ✅ 真闭环 | 生产 `recall.py:1241` 调 `format_metamemory_notice`(=每轮"没有可靠 evidence"警告) | calibration 回路空跑(没接 outcome) |

`DUAL_FLYWHEEL_WIRED.md`(5/11)经核验标题超卖:只接 drift 一条腿;真 PoI/RSI 飞轮是 6/3 后才建。

**长期记忆真相**:文档存得住(持久化 OK),但生产召回跑裸 bge-m3——最强栈(reranker P@5 0.92 / query-rewrite 单会话 +27)全在 benchmark 没上生产。现状=检索门控的记忆,且生产用的不是最强检索。metamemory 挡"假装记得"是唯一安全垫。

## 2. 平台/v5 最新进展(改变图景)
- **平台(nautilus-core 6/05 HANDOFF #027)**:RSI/benchmark 弧 CLOSED·三连负(Probe3 自改 0.333→0.00,0/2 accepted)。价值 reframe=外部 fitness 尺+FDE 语料,非 orchestration/自改。**正信号前不 wire live 内部 PoI/soul**(anchor #3)。
- **v5(nautilus-v5 6/05 `896468f`)**:出题 copilot **已建**,data_001 真 producer 出 3 真文件、soul 评 11/11。FDE 关键路径"唯一未建件"已 ship。
- outcome substrate:`agent_tool_calls`@nautilus_production live 109,873 行(真);契约里 `outcome_ledger` 表不存在(spec 写错)。

## 3. 设计:四缺口闭环(接线优先 + 专家回路为新脉)

**原则**:① 不发明新能力,激活已建到生产 + 只新建专家→ground truth 一条;② 守黑盒约束(热路径不调 LLM,本地 BGE/交叉编码器可,LLM opt-in);③ 守平台纪律(内部 RSI held,但 FDE 专家/字节=外部信号,另一条,合规)。

### 缺口1 · 记忆胶囊跨设备(小修)
修 `/v1/v14/ingest_obs` action/字段不匹配。**先云端实测**确认是否真静默失败,再对齐 daemon 或补 adapter。→ 跨设备原文召回接上。

### 缺口2 · 检索保真度进生产(接线·解长期记忆)
reranker(bge-reranker-v2-m3 本地交叉编码器·非 LLM)+ query-rewrite + lifecycle tier 提升,从 benchmark 管线接进生产 daemon recall 热路径(可配开关,默认建议开 reranker)。证据已证有效。守黑盒:reranker 非 LLM 不破约束;query-rewrite 若用 LLM 则 opt-in。

### 缺口3 · FDE verdict→PoI(双轮咬合)
adapter:soul checklist 通过率 + 专家复核结论 → 外部 outcome → `compass.poi_credit`;云端 `COMPASS_CLOUD_POI_BOOST=1`。边界:FDE 外部信号 ≠ 平台 held 的内部 RSI。

### 缺口4 · 专家互动回路(新脉·复利源)
飞书复核工作台 通过/打回+理由+分项分 → 结构化抽取 → 双喂:(a) PoI 信用(题型/checklist 模式/工具产物被专家认可度)(b) 记忆胶囊(复核理由=避坑知识)。复用 `feishu_client`(读复核表)+ T3 胶囊管线 + 缺口3 PoI adapter。

## 4. 复利闭环
专家任务 → copilot+工具栈 → 交付 → soul QC + **专家复核** → (verdict+理由) → PoI 信用 + 胶囊 → 检索重排 + 工具改善 → 下次更快更准 → 专家更省时 → 更多任务/更高通过率。
**外部 ground truth = 专家复核 + 字节接收(非内部自评)。** 复利仅在有外部 ground truth 时成立(平台三连负为反证)。

## 5. 依赖 / 边界 / owner
- 缺口1/2 = compass 纯 turf,可独立做(需云端实测)。
- 缺口3 = compass adapter,接 soul 已有 `checklist_scorer` schema(soul 出 verdict)。
- 缺口4 = compass(飞书读+胶囊+adapter),需真批次专家复核数据(可先 mock,G3.1 scope 已解)。
- 全程不碰平台内部 RSI wiring(平台 held)。

## 6. 测试
每缺口 TDD。缺口2 用 `RESULTS.md` benchmark 验**生产路径**分数真提升(非只 benchmark 管线)。缺口3/4 用 mock verdict 验 adapter,真数据待批次。

## 7. 不做(YAGNI)
- 不重训/不自建向量库;不碰平台 orchestration/自改(已证伪)。
- 不在热路径加 LLM(守黑盒护城河)。
- 不抢平台内部 RSI wiring(held until 正信号)。
- 缺口4 不在拿到真批次前做花哨 UI,先打通数据回路。

## 8. 优先级(实施顺序建议)
1. 缺口2 reranker 进生产(最直接解"长期记忆"·代码就绪·纯 compass turf)
2. 缺口1 跨设备 ingest 修(小·解跨设备)
3. 缺口4 专家回路 mock 打通(新脉·复利源·G3.1 已解)
4. 缺口3 FDE verdict→PoI adapter(咬合点·待 soul verdict 流)
→ 1/2 立即可做;3/4 与 FDE 真批次并进。

## 关联
诊断证据来自 4 路 agent 实读 `nautilus-compass`/`nautilus-core`/`nautilus-v5`。相关:`RESULTS.md` · `metamemory/` · `proof/poi_*` · `sql/004_poi_credit.sql` · `recall.py` · `daemon.py` · vertical-task-factory `FDE_CONVERGENCE.md`/`feishu_client.py`/T3 胶囊管线。

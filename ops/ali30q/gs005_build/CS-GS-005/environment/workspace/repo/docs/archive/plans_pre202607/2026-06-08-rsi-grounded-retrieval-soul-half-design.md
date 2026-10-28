# RSI grounded-retrieval · soul 半边设计(暴露端 + probe harness)

> 用户(2026-06-08 /goal platform-soul-rsi-fde-close):实现 RSI grounded-retrieval 的 soul 半边。
> 底图 = `design_20260605_rsi_fde_closed_loop_grounded_retrieval`(双轮 RSI 半边·grounded-retrieval 非 self-edit)。
> 本 doc = 同步 V5/compass 真实状态后收敛的 soul 侧实现设计。承接 `2026-06-05-rsi-fde-closed-loop-design.md` 的 W6。

## 1. 同步两框真实状态(grounded·读真代码非脑补)

- **V5 已 ship RSI 后半(6/8·commit a23ce23)**:`aggregate_agent_fitness` 按 `fde_dispatch.claimed_by` 归因每 agent 的 **pass率/均分(标量)** → 注入 prompt_builder context(worst-first·**input-nudge·非 force·非自改 prompt**)。即 V5 的 "self_modify-context" 与 grounded-retrieval 同路线,**非 Probe3 自改死路**。
- **关键缺口**:V5 fitness 是 **agent 级标量**,**丢弃 `items[].reason` 文本**。compass PoI(`from_checklist_verdict`)只读 score/overall_pass,**同样丢 reason**。
- **compass**:有 bge-m3+reranker(Seoul T4)· 拥 避坑语料/PoI turf · 主张反 D(不预建共享表)。

## 2. 深层洞察:一个 verdict 的三层粒度信号

| 粒度 | 信号 | 现状 |
|---|---|---|
| 题级 | score/overall_pass | compass PoI 已用 |
| agent 级 | pass率/均分 | V5 fitness 已 ship |
| **内容级** | **per-item fail-reason(具体避坑规则)** | **没人用 = RSI 设计要复活的"死记录"** |

`fde_verdicts.items[].reason`(如「veto: xlsx 与 docx 客户数不一致」)= 可操作避坑知识,目前完全未消费。soul 半边 = 把这第三层从死变活。

## 3. turf 切分(零撞车)

- **soul(本 session)**:(a) 结构化暴露 feed + (c) probe 度量 harness。**不碰**语义检索(compass bge-m3)/grounding 注入(V5 producer)。
- **compass(G-turf)**:摄入 feed → 避坑语料库 + bge-m3 检索/rerank。
- **V5(G-turf)**:retrieve(经 compass)+ inject 为 producer 输入硬约束。

soul 只出最强的:纯派生 feed + 度量仪器。三层粒度各归其位。

## 4. 组件设计

### 组件 1 · grounding 暴露端(纯派生·只读)
- **纯核** `phase3/backend/services/fde_grounding.py`:
  `extract_grounding(verdict_rows, *, source=None, veto_only=False, since=None, limit=None) -> list[dict]`
  跨 `fde_verdicts` 行展平 `items`,只取打回项(`pass is False` 或 `veto is True`),每条:
  `{reason, task_uid, checklist_uid, item_id, veto, source, score, created_at}`。
  纯函数(吃 row.to_dict() 列表或 ORM 行)·fail-soft(item 缺字段跳过不崩)。
- **薄路由** `phase3/backend/api/fde_grounding.py`:`GET /api/platform/fde/grounding`
  query: `source` / `veto_only`(bool) / `since`(ISO) / `limit`(int)。
  查 `FdeVerdict` 行 → 调 `extract_grounding` → envelope `{success,data,error}`。
  **无语义检索**(compass turf)。镜像 W-D `fde_scorer_poll`(纯核+薄壳)。
- **可匹配键 = raw reason + 已有结构键**(用户定):不造领域 taxonomy,reason 原文留给 compass bge-m3 语义匹配。YAGNI。

### 组件 2 · probe 度量 harness(可证伪仪器·大幅复用)
- `phase3/agent-engine/benchmarks/grounding_probe.py`:
  control(无注入)vs grounded(有注入)同题/同批两臂逐次成败 → escapes_noise 判据。
- **复用**(anchor#5):`escape_noise_stats.aggregate_paired_multiseed(seed_records, "control", "grounded")` 已提供配对 tally + `binom_sign_test` + `escapes_noise`(net_mean>0 且每 seed 正 且 sign_p<0.05)。grounding_probe = 薄 adapter:
  - `build_seed_record(control_items: dict, grounded_items: dict) -> dict` 构造 `{control:{pass_at_1, items}, grounded:{pass_at_1, items}}`(items = {task_uid 或 attempt_id: pass_bool}·pass_at_1 复用 `benchmark_verifier.pass_at_k_from_results`)。
  - `grounding_probe(seed_records) -> report` 委托 `aggregate_paired_multiseed(...,"control","grounded")`。
- **诚实判据**:`escapes_noise=True` 仅当 grounded 真稳赢噪声 → RSI grounding 有效;平/降 → 退回纯 FDE(不自欺)。

## 5. 数据流(gated 段标注)
```
fde_verdicts(daemon 积累·items[].reason)
  → GET /fde/grounding(soul 暴露·打回项 feed)              ← 本 session build
  → [compass 摄入 → bge-m3 语料库]                          ← G-turf·不做
  → [V5 producer retrieve + inject grounding]              ← G-turf·不做
  → 同题/同批 control vs grounded 轨迹
  → grounding_probe → pass@k delta + 符号检验 → escapes_noise?  ← 本 session build harness·实验 gated
```

## 6. 错误处理
- 暴露端只读·fail-soft(无 verdict → 空 feed·item 缺字段跳过)。envelope 约定。
- probe 纯函数·边界(全过/全败/零 discordant → escapes_noise=False·sign_p=1.0 已由复用层处理)。

## 7. 测试(TDD·fixture·先 RED 后 GREEN)
- `extract_grounding`:fixture verdict(混合 pass/fail/veto items)→ 只出打回项·reason 原文保留·键正确·过滤器(source/veto_only/since/limit)·fail-soft 缺字段。
- HTTP 路由:TestClient seed 多 verdict → GET envelope·过滤 query 生效。
- `grounding_probe`:合成 control/grounded seed_records → 已知 delta + 符号检验·边界(grounded 全赢→escapes_noise True / 零 delta→False / 单 seed)。

## 8. 收敛锚 + gated 边界(G-rsi·anchor#3)
- **本 session**:两组件 build + fixture TDD green。**不 live wire** compass/V5·**不部署生产**(端点只读·即便部署 inert·但守 gate 本地验)。
- **真跑实验(follow-up·gated)**:需 ① 同领域第二题(data_002→data_003·data_003 未存)② V5 producer 跑 control-vs-grounded。
- **可被打脸假说**:「外部 verdict grounding 注入让 producer 下一题 pass↑」。escapes_noise 平/降 = 诚实退回纯 FDE。

## 9. 红线(必守)
- fitness 只外部(soul QC pass→买方接收)·绝不内部 NAU/自印。
- 改进只 grounded-retrieval(真 veto reason 注入输入)·绝不 LLM 自改 prompt(Probe3 三连负)。
- 不碰 held 内部自指经济。
- 首验假说证实前不 live wire(只建管道+fixture)。

## 10. 不做(边界)
- 不建语义检索/rerank(compass)· 不碰 producer retrieve/inject(V5)· 不建共享 fde_fitness 表(V5 派生)· 不造领域 taxonomy(YAGNI)· 不部署生产(本 session)。

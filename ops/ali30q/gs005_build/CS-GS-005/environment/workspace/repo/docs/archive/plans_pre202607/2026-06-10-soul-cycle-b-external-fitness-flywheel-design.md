# soul-cycle-B · 外部 fitness 驱动的自改飞轮 · 设计(2026-06-10)

> 用户洞察:内部飞轮"能不能发挥作用"。证据回答:旧造法不行(0 价值),但换外部 fitness + 验证门后能。本 doc 把"复活方式 = B"钉成可执行方案。**只设计·不动代码·留 fresh session build。**

## 0. 北极星
soul 的"自迭代心跳"应跳在**外部客观 fitness** 上(benchmark / FDE ΔReward / escapes),不是内部自评。这是 anchor #2 + RSI+FDE 整套的落地;也是把内部飞轮从空转救活的唯一方式。

## 1. 旧飞轮为何 0 产出(实测证据·非猜)
- 49 个 cycle(5/27–6/03)· 21 个 selfimprove 草稿 PR(#110/#115–#125…)· **0 merged**(全 draft→closed)。
- 根因两条:
  1. **选择信号 = 内部自检**(无外部 ground-truth 判哪个自改好)→ 自评不可信(Probe3 三连负 / 94% self-loop 同病)。
  2. **check 阶段空心**:`nautilus-soul.service` 6/1 `checks failed/not applied`·ship.py codegen 产不出 parseable 块 → 候选全卡 draft、堆积、被关。
- 结论:空转 = 大量活动(cycle/PR 数好看)+ 0 外部价值。

## 2. B 重设计:外部 fitness 选择 + 真验证门
环路(每一步都有外部客观判据,无自评):
1. **候选生成**:producer(soul/V5)产一个 self-edit 候选,限**可测范围**(config-space 参数 / prompt / 单一可测代码单元 / grounding policy)。不碰不可测的大改。
2. **沙箱应用 + 真验证**:隔离环境应用候选,跑**真 harness**(AutoLab/KernelBench env · 或 FDE 题集),拿可执行结果。**check = harness 真跑通**,不是 codegen parseable(旧空心 check 的替代)。
3. **外部度量**:`grounding_probe_twosample(baseline, candidate)`(N seed)→ ΔReward + p_value → `escapes_noise`(ΔReward>0 且 p<0.05)。
4. **合并门(关键)**:**仅 escapes_noise=True(外部 fitness 显著上升)才 merge**;escapes=False → discard(不堆 draft·不 auto-merge)。把"21 草稿 0 合并"变成"改一个→外部度量涨了→才进"。
5. **落库**:`fde_rsi_deltas`(已 LIVE)记 ΔReward / escapes / 候选谱系;escapes=True 升 PoI(cnt_c3 路径)。
6. **心跳**:每个 escapes=True 增量 = soul 一次有外部证据的产出;pulse/舰桥① 显示**外部增量心跳**,不是内部 cycle 计数。

## 3. 复用现成(不重造·anchor #5)
- `grounding_probe_twosample` + `escape_noise_stats`(已有·escapes 判据)
- `fde_rsi_deltas` 表 + `POST/GET /api/platform/fde/rsi_delta`(已 LIVE 生产)
- `benchmark_verifier`(pass@k·已有)· AutoLab/KernelBench A 簇 env(compass turf)
- **不重造**:不重写 ship.py codegen 自检(旧空心 check);check 换成"跑真 harness"。draft-PR 机制可留作展示,但 merge 由 escapes 门 + 人 gate,不 auto。

## 4. 与旧飞轮的区别(防再踩同坑)
| 维度 | 旧(已证伪·0/21) | B(外部驱动) |
|---|---|---|
| 选择信号 | 内部自检/自评 | 外部 benchmark ΔReward |
| check | codegen parseable(空心) | 真 harness pass + 显著增量 |
| 合并 | 自动/草稿堆积 | escapes_noise=True 才 merge |
| 产出 | 活动多·价值 0 | 每个 merged 都有外部增量证据 |
| 心跳 | 内部 cycle 计数 | 外部 fitness 增量 |

## 5. binding-DONE 判据
① 一个 self-edit 候选跑通沙箱 + 真 harness → grounding_probe 出 ΔReward + escapes ② escapes=False 候选被 discard(不 merge)③ escapes=True 候选 merge 且 fde_rsi_deltas 记录 ④ pulse/舰桥① 显示该外部增量心跳(替代内部 cycle 死值)。四条全绿才算 B 立起来。

## 5b. RSI 健康指标:fitness_ref 命中率(V5 ACK 增量)
provenance 每个 self_modify 事件带 `fitness_ref`(链到 fde_rsi_deltas/verdict 或 null)。
**fitness_ref 命中率 = 有外部 fitness 关联的自演化 / 总自演化** = 可量化的开环 vs 闭环比。
V5 预判 747 次自演化里多数 fitness_ref=null(防御性修 bug/堵洞,不挪外部 fitness)。
把 anchor #2 的"开环自恋"缺口从定性变成一个数:命中率越高 = RSI 越闭环。
舰桥①/pulse 展示此率;soul-cycle-B 的目标 = 把命中率拉高(每次自改尽量挂外部度量)。

## 6. 红线
- fitness 必须外部(benchmark/FDE)· 禁内部 NAU/自评当 fitness(anchor #2·自指病根)。
- self-edit 限可测范围 · draft-PR 不 auto-merge(escapes 门 + 人 gate)。
- 脱噪前不 live wire(escapes_noise=False 不升 PoI)。
- 旧 `nautilus-soul.service`(内部 code-PR 飞轮)正式弃用;pulse 标"内部 cycle 已弃用 by design",soul 心跳改读 B 环外部活动。

## 7. 分阶段(fresh session)
- **P0**:本 doc。
- **P1 最小可证伪**:一个 config-space self-edit(如 grounding policy 参数)跑 AutoLab radix · grounding_probe 度量 · escapes 门决定 merge/discard。证 B 环能产出外部增量。
- **P2 心跳接线**:soul daemon 心跳(替代死的 nautilus-soul.service · timer 触发 B 环 · 替换空心 codegen check)。
- **P3 显性化**:pulse/舰桥①(子系统① Soul 引擎)显示 B 环外部增量心跳 + agent_kind(接 V5 provenance);deprecate evolution_score/内部 cycle 死值。

## 8. turf
platform-soul:B 环编排 + escapes 门 + merge gate + pulse 显性化 · compass:A 簇 env/benchmark + PoI 升格(cnt_c3)· V5:producer 候选 + provenance 信号源 · 用户:merge gate 拍板 + 算力。

关联:[[design_20260605_rsi_fde_closed_loop_grounded_retrieval]] · `docs/plans/2026-06-10-rsi-fde-integrated-control-plane-design.md` · V5 provenance 裁定 · observation_20260602(自指经济实证)。

— platform-soul · 2026-06-10 · 把内部飞轮从空转救活 = 外部 fitness + 真验证门

# P3 动态权重管道+回归门正本(P3_PIPELINE_CANONICAL)

> 2026-10-03 立项起草(用户令:"起草 P3 在线更新管道+回归门设计档(CPU 工程,零 GPU)")。
> **2026-10-04 升级为正本**(承沉淀提案 2734 件三):§一–§九 设计内容维持;§十 全链闭环图(v2,含 EGR 回流)/§十一 实证附件/§十二 消费方注册/§十三 正本记录为新加。
> 承 docs/plans/SSI_JEV_DYNAMIC_JUDGE_PROPOSAL_20260930.md 之 P3 行:"在线更新管道(新 verdict→LoRA 增量→回归门→上岗),判据=回归门 20 连绿"。
> 性质:正本(工程蓝图+实证账)——实现件全部 CPU;仅 S3 训练执行步触发 4090 短租(~35min<¥2),且由管道产训练单、人不直接跑。
> 既有锚点:P1 语料 1454(split 冻结 sha 三项)· P2 冠军 adapter runtime/judge_lora_p2v2/best_lora(J1=88.51%/ECE=0.072)· 训练脚本 tools/train_judge_lora.py(SEED=20260930 冻结)。

## 〇 · 因果倒置在本档的落点(一句话)

常式:生成→验证(验证是下游成本)。本管道:验证真值→权重增量→回归门上岗→验证更快更准→真值更多。
**权重只被"带独立来源的验证真值"驱动,永远不被判官自己的输出驱动**——这是倒置成立的全部要害。

## 一 · 管道总览(六段,S3 外全 CPU)

```
S1 增量收集 → S2 训练单 → S3 训练执行(4090 短租) → S4 回归门 → S5 上岗切换 → S6 台账
   (CPU)       (CPU)        (GPU~35min)             (S3 机内)    (CPU 原子写)    (CPU commit)
```

每轮 cycle 以 corpus delta 为输入,以 ledger 一条记录为输出;任一环节失败=该轮终止,冠军不动,事件入台账。

## 二 · S1 增量收集(tools/p3_delta.py)

- 输入:tools/verdict_corpus_exporter.py 全量重跑(幂等)与上一 anchor 的语料 manifest 对账。
- **label_origin 白名单门(反自报,承 judge 自报三陷阱)**:只收
  `independent_recompute` / `human_review` / `official_rule` / `three_vendor_final` 四类;
  `verdict-judge-*` 自标注一律拒收进 rejected 池并计数披露(判官自产标签=作弊通道,永久禁入)。
- 输出:runtime/verdict_corpus/delta/delta_NNNN.jsonl + manifest(计数/来源分布/rejected 计数/sha16)。
- 增量来源现状(2026-10-03 盘点):G1 三批 verdict + pusht 四窗 verdict(均为 compass 独立判,可归 independent_recompute)+ errata gold 活水 + unlabelled 47 待标——**尚未导出,首个 delta 待跑**。

## 三 · S2 训练单(tools/p3_ticket.py)

- 触发判据(预注册,只许更严):**delta 新增带白名单标签 ≥200 条**;不足则本轮记 SKIP 入台账,不攒人情。
- 训练单 JSON(自动生成+commit,=当轮 mini 预注册):delta sha16、基线 adapter sha16、回归集 sha16、
  超参(承 P2v2 冻结:r16/α32/verbalizer 三态/SEED/早停 ep5)、成本上限 ≤¥5、判据引用=本档 §五。
- 训练配方(防灾难性遗忘):**冠军 adapter 热启动 + delta:replay=1:1**(replay 从冻结 train1162 分层抽样,抽样种子=delta sha16 前 8 位 hex 转 int,可复现)。

## 四 · S3 训练执行(唯一 GPU 段)

- 触发:训练单 commit 后由人批准执行(不自动租机);租 4090(1.65/h),API 层租/释(承 _redact 遮罩坑:release 走 broker API 原子调用)。
- 守门:脚本首行 assert CUDA 可用,否则退出码 42(不静默 CPU 跑)。
- 下载纪律:模型走 modelscope 通道(HF 大文件断流定谳);transformers≥4.57(Qwen3 兼容定谳)。
- 产物拉回:challenger adapter + train log + 机内完成的 S4 评估原始输出(见下)。

## 五 · S4 回归门(tools/p3_gate.py,判据预注册,只许更严)

**回归集 REG-100**:从冻结 split_test 149 分层抽 100(pass/fail/insufficient_evidence 按比例),
种子=20261003,sha16 落档,**永久冻结、永不入训、修改即事故**。test 149 全体仍作头条指标。

冠军=当前 champion.json 指向的 adapter;挑战者=当轮 S3 产物。同一冻结集上推理=确定性读数,无抽样噪声。

| 门 | 判据 | 语义 |
|---|---|---|
| G1 零退化 | REG-100 上 **correct→incorrect 翻转数=0**(逐条对照冠军;incorrect→correct 欢迎) | 单调改进门;隐含 acc 不降 |
| G2 宪法地板 | 挑战者 test149 二值 acc ≥85% 且 ECE ≤0.10(承 P2 判据,不降格) | 防增量训崩 |
| G3 U 态守恒 | 挑战者 test149 insufficient_evidence 率变化 ≤±2pt(对照冠军) | 防"更敢判"伪装成"更准" |

三门全绿=PASS;任一红=FAIL,挑战者入 runtime/judge_lora_p3/rejected/,冠军不动,事件入台账。
**FAIL 后允许修配方重训,但重训=新一轮 cycle(新训练单),同 delta 不允许刷门超过 2 次**(防过拟合回归集)。

## 六 · S5 上岗切换(tools/p3_promote.py)+ S6 台账

- champion.json 原子切换(tmp 写+rename):{adapter_path, adapter_sha16, gate_report_sha16, corpus_delta_sha16, promoted_at}。
- 回滚:保留最近 3 代 champion;kill switch=手动把 champion.json 指回上一代(一条命令,设计档承认人工兜底)。
- 台账 runtime/judge_lora_p3/ledger.json(JSON 数组;仓 .gitignore 第 7 行 `*.jsonl` 全局忽略,审计件须入 git 故用 .json):每轮一条{cycle, delta_n, verdict(SKIP/PASS/FAIL), 门读数, sha 链}并 commit;每条结论带证据三层标注(JUDGING_EVIDENCE_TIERS_20261003)。

## 七 · P3 验收判据(承提案,预注册)

- **回归门 20 连绿**:连续 20 轮 promotion cycle 首轮评估即 PASS(修配方重训=断连,重新计数)。
- 照实注:20 轮 × 200 条=4000 条新标签的语料流入需求,**时间线不可承诺**——取决于 G1/pusht/memgate/harness 四线送判速率;连绿进度以台账为准,不报预计日期。
- 过程判据:单轮成本 ≤¥5;台账零缺失;label_origin 白名单违规数=0。

## 八 · 反自指护栏(全档硬约束,违=轮次作废)

1. 自训只限小判分器,不碰被评测的大模型。
2. 判官只做辅助腿;自家成绩终判永远三供应商外置+人审。
3. 语料标签只认 §二白名单;判官自产标签永久禁入训练。
4. REG-100/test149 冻结 sha 锚定,修改即事故通报。
5. 上岗只走本管道;任何人(含用户会话里的我)不得手动替换 champion 而不过门。

## 九 · 组件清单(实现顺序=依赖序)

| 件 | 路径 | GPU |
|---|---|---|
| p3_delta.py(S1) | tools/ | 无 |
| REG-100 冻结件 | runtime/verdict_corpus/reg100.jsonl + sha 落档 | 无(一次性) |
| p3_ticket.py(S2) | tools/ | 无 |
| train_judge_lora.py 增量模式(S3) | tools/(热启动+replay 参数) | 4090 短租 |
| p3_gate.py(S4) | tools/ | 随 S3 机内 |
| p3_promote.py + ledger(S5/S6) | tools/ + runtime/judge_lora_p3/ | 无 |

首 delta 导出(G1/pusht verdict 入料)是管道外前置件,建议与 S1 实现同批做——导出即得首轮 delta 读数,可校准"≥200"触发门槛的现实性。

## 十 · 全链闭环图 v2(S1–S6 + EGR 缺口回流)

```
                    ┌─────────────────────────────────────────────────┐
                    │                  燃料白名单四类                     │
                    │  independent_recompute / human_review            │
                    │  official_rule / three_vendor_final              │
                    │  (判官自产标签永久禁入=反自指护栏③)                  │
                    └──────────────────────┬──────────────────────────┘
                                           ↓
  ┌──────────┐   delta_NNNN.jsonl  ┌──────────────┐  训练单  ┌──────────────┐
  │ S1 增量收集│ ──────────────────→ │ S2 训练单     │ ──────→ │ S3 训练执行    │
  │ p3_delta │   白名单门+manifest  │ p3_ticket    │ ≥200 触发│ 4090 短租35min│
  └──────────┘                     │ (SKIP 入台账) │         │ 热启动+replay │
        ↑                          └──────────────┘         └──────┬───────┘
        │                                 ↑                        ↓
        │                          SKIP(不足 200)          ┌──────────────┐
        │                                 │                │ S4 回归门     │
        │                                 │                │ p3_gate      │
        │                                 │                │ REG-100 三门  │
        │                                 │                └──────┬───────┘
        │                                 │                PASS ↓ │ FAIL→rejected/
        │                                 │                ┌──────────────┐
        │                                 │                │ S5 上岗切换   │
        │                                 │                │ p3_promote   │
        │                                 │                │ champion 原子写│
        │                                 │                └──────┬───────┘
        │                                 │                       ↓
        │                                 │                ┌──────────────┐
        │                                 │                │ S6 台账       │
        │                                 │                │ ledger.json  │
        │                                 │                └──────┬───────┘
        ↓                                 │                       ↓
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 在役判读(判官上岗后产出 verdict)                                       │
  ├─────────────────────────────────────────────────────────────────────┤
  │ EGR 缺口回流(2026-10-04 新闭环,verdict schema v2.1 gap_report):      │
  │   判读发现能力/数据缺口 → gap_report{gap_layer, evidence,             │
  │   suggested_fuel, confidence} → 回流两向:                            │
  │   ①材料方(如 flywheel)按 suggested_fuel 补数据/修材料 → 新 verdict    │
  │   ②判官自身升级项(7B+/人类抽检标定,ha-006 裁决列下轮) → 新判读力        │
  └─────────────────────────────────────────────────────────────────────┘
```

闭环语义:常式"生成→验证"在此倒置——**验证缺口(EGR)驱动数据供给与判官升级,权重只被白名单真值驱动**。EGR 是 S1 之外的第二燃料入口(结构位,非标签),gen4_v1 判读的 gap_layer=data 首用即此。

## 十一 · 实证附件(2026-10-04 盘点)

| 实证 | 读数 | 对本管道的意义 |
|---|---|---|
| S3 工程实测闭环(commit 3439982d) | A100 实跑训练链打通,challenger 产物+log 拉回 | S3 执行段非纸面设计 |
| exp1+exp2 七组合负结果族 | 重训全量无增益:epochs↑有害/lr2e-4 不显著/loss 低者读数差(champion 臂预测先于训练,测对臂) | **增量设计反向实证**——全量重训路线证伪,S2 配方(热启动+1:1 replay)是正解方向 |
| gen4_v1 全卷判读首闭环(2791) | 独立复算三读数零偏差;J1 口径错位=设计缺陷 U 态;首选归档=200 对教师池下限锚点;gap_report 首用(gap_layer=data) | EGR 回流首演;判读产出→缺口→燃料建议的闭环走通 |
| delta_0001 导出校准 | 首轮 delta=14 条(200 门槛≈14 轮流入) | **门槛现实性悬案坐实**:§七"时间线不可承诺"有数了;EGR 双向回流因此从可选变必需 |
| delta_0003 S2 更正 | v5 主动请降,4→3 条;总账 32/200;指纹账同步撤销 | 白名单门"只认独立来源"实际执行记录;material_side_honesty 样本首例 |
| E1·J2 判官席位(ha-006) | 双包交卷,聚合方案 #2843 被采纳;dim1 零方差如实申报→无效化 | 判官在役实证;判别力如实申报进裁决正本证据链 |

## 十二 · 消费方注册

| 角色 | 消费面 | 状态 |
|---|---|---|
| v5(材料方) | EGR 缺口报告消费端;delta 供给(errata gold / S2 更正) | 双向在通(2804 承诺 gap_report 试读回执) |
| flywheel | delta 供给端(auto_judge_dispatch 派发判读)+EGR 回流对象 | gen4 首闭环(2791) |
| E1 判官席位 | 管道在役判读实例(J2 席,判官升级项列 ha-006 下轮) | 已交卷收官 |
| 判例装订线 | gen4_v1 判读入 CASEBOOK 候补案(案 9) | 待装订 |
| 平台 org_state | 三正本读端点指向本档(sha 锚定) | 平台施工(提案 2797 分工) |

## 十三 · 正本升级记录

- 2026-10-03:立项起草(设计档,§一–§九)。
- 2026-10-04:升级正本(2734 件三):加 §十 EGR 闭环图/§十一 实证附件/§十二 消费方/§十三 记录;§一–§九 设计零改动。伴生:件一 `docs/memory/MEMORY_IO_ARCHITECTURE.md`、件二 `docs/metering/INDEPENDENT_JUDGE_MODEL_V1.md` 同日出件。

## 关联

- 正本可寻址:https://raw.githubusercontent.com/chunxiaoxx/nautilus-compass/main/docs/plans/P3_DYNAMIC_WEIGHT_PIPELINE_DESIGN_20261003.md(sha 以 org_state 端点读时现算为准,2026-10-04 push 实测 200)
- 机构注册(2026-10-04 live,平台独立验证 sha16 吻合后转 live,函 2934):`GET https://nautilus.social/api/platform/org/sinks`(三正本 sinks 注册表)+ `GET https://nautilus.social/api/platform/org/judging-pipelines`(含 p3-cycle-000 役次)
- 件一(记忆 IO 正本):`docs/memory/MEMORY_IO_ARCHITECTURE.md` · 件二(独立判官架构模型):`docs/metering/INDEPENDENT_JUDGE_MODEL_V1.md`
- 报数纪律正本:docs/soul/proposal_preregistered_recompute_20260914.md

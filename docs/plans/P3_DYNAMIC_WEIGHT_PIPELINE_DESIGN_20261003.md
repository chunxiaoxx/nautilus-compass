# P3 动态权重管道+回归门设计档(SSI×JEV 路线图 P3)

> 2026-10-03 立项起草(用户令:"起草 P3 在线更新管道+回归门设计档(CPU 工程,零 GPU)")。
> 承 docs/plans/SSI_JEV_DYNAMIC_JUDGE_PROPOSAL_20260930.md 之 P3 行:"在线更新管道(新 verdict→LoRA 增量→回归门→上岗),判据=回归门 20 连绿"。
> 性质:设计档(工程蓝图)——实现件全部 CPU;仅 S3 训练执行步触发 4090 短租(~35min<¥2),且由管道产训练单、人不直接跑。
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
- 台账 runtime/judge_lora_p3/ledger.jsonl:每轮一条{cycle, delta_n, verdict(SKIP/PASS/FAIL), 门读数, sha 链}并 commit;每条结论带证据三层标注(JUDGING_EVIDENCE_TIERS_20261003)。

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

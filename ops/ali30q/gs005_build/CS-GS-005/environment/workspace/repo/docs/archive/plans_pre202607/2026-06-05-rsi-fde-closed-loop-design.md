# 实现 RSI+FDE 闭环 · 设计(创新且收敛 · 外部驱动 grounded-retrieval 改进环)

> 用户(2026-06-05):"既创新也收敛地实现 RSI+FDE"。本 doc = 双轮 RSI 半边的实现设计。
> 底图 = 2 路 Explore 深度回顾过往文档(benchmark 弧三连负 / 94% self-loop / 外部选择压力 / data_001 闭环)。
> 配套:平台 goal `GOAL_2026-06-05_platform_4way_coupling_wiring.md`(W1 加 fail_reason + 新 W6)· 主设计 `2026-06-05-native-ai-org-fde-productization-master-design.md`。

## 1. 真缺口(深度回顾逼出)
双轮的 **RSI 半边没实现**。当前只到 `verdict → PoI(compass 记忆)+ digest(推送)`,**缺 `verdict → producer 能力更新` 这一环**。verdict 是死记录,不驱动改进。
- v5 的 shared_facts(data_001 c11 veto 逼出跨交付物一致性约束)= **手工一次性 RSI 火花,没系统化**。
- 把这件事系统化 = 实现双轮 RSI 半边。

## 2. 已证伪不可再走 vs 已确立活路(回顾结论)
**死路(勿再走)**:① 内部 NAU 自指(94% self-loop·`truth_real_bucket_460_94pct_self_loop_20260518`)② ensemble/consensus 范式 A(三连负)③ **Probe3 LLM 自改 prompt(0.333→0.20→0.00 单调退化·无正向梯度)**。
**活路**:外部 fitness 尺(能诚实证伪自己)= 真资产;FDE 字节真客户 = 真外部 ground truth;**selection 非 orchestration/auto-improve**。

## 3. 创新点(避开 Probe3 死法)
RSI **不做"自改 prompt"**,做:**外部 verdict 失败 → 结构化 grounding → 喂 producer 作输入 → 下一 verdict 度量**。
- 改进 = grounded-retrieval(来自真失败的具体避坑规则),**不是 self-modification**。
- fitness = 外部(下一题 QC pass / 字节接收),**不是内部自评**。
- = v5 手工那件事的系统化 → 既创新(闭环机制)又收敛(钉活回路·复用现成)。

## 4. RSI+FDE 闭环(最小可度量 · 4 步)
```
① soul QC 出 verdict + per-item fail_reason(外部 ground truth·非内部 NAU)
      ↓ 走平台 verdict-bus(W1·持久化)
② compass fail_reason → 避坑语料/shared_facts 约束库(结构化·可检索·按领域/题型索引)
      ↓ retrieve(检索·非自改)
③ producer(v5 copilot)下一题前 retrieve 相关避坑规则 → 注入 task grounding(硬约束输入)
      ↓ 产出
④ 下一题 verdict 度量改进(pass 率↑ / 同类 veto 不复发?)= 外部 fitness 闭环
      ↺ 回 ①(每题让 producer 更好·外部判·grounded·无 self-edit)
```

### 为什么避开三陷阱
- **非内部 NAU**:fitness=soul QC pass→字节接收(外部)·不印币不自评。
- **非 self-edit(避 Probe3)**:producer 不改自己 prompt;避坑规则是外部注入的 grounding 输入·有正向来源(真 veto reason)·非噪声盲改。
- **非 orchestration(避范式 A/B)**:不靠投票/分解;靠"真失败→具体规则→下次不犯"的 selection 式改进。

## 5. 四系统分工(复用·不新造 · anchor #5)
| 系统 | 这环职责 | 复用 | 缺口编号 |
|---|---|---|---|
| **soul** | checklist_scorer 出 **per-item fail_reason**(当前只 pass/fail) | checklist_scorer + RUBRIC §9 | D |
| **compass** | fail_reason → 避坑语料库(可检索·胶囊) | PoI/胶囊管线 + FDE_CONVERGENCE §2 | G |
| **v5** | producer 下一题 retrieve 避坑规则注入 grounding | solve_task + shared_facts spine(手工版) | C |
| **平台** | verdict-bus(verdict+fail_reason 持久化·脊柱)= 这环轨道 | W1(字段加 fail_reason) | A/B |

## 6. 收敛锚(钉活回路·可度量·不空谈)
- **首验 = data_002→data_003 同领域批**:data_002 verdict 的 fail_reason 进语料 → data_003 retrieve grounding → 度量同类 veto 复发率↓ / pass 率↑。
  - **可被打脸的假说**:"外部 verdict grounding 注入让 producer 下一题 pass 率↑"。
  - 平 → RSI 环无效(诚实退回纯 FDE 交付,不自欺)· 正 → 双轮 RSI 半边第一次真实现。
- **纯融合线 = 线3 前沿基准复现**:pass@k 难题筛 = 同时(a)交付字节(b)我方 agent 外部 fitness。复用 benchmark harness。等线1 环验通再上。

## 7. 红线(必守)
- fitness 只能外部(soul QC pass→字节接收/benchmark pass)· 绝不内部 NAU/reputation/自印。
- 改进只能 grounded-retrieval(真失败→具体规则注入)· 绝不 LLM 自改 prompt。
- 不碰 held 内部自指经济(L4 `daemon.py:159-229`/fitness_delta gating)。
- 反 spray:先 data_002 环验通(假说被打脸或证实)再谈线3/扩量/编队。**不抢在收敛+稳定前 wire live(gated)**。

## 8. 整合进平台 goal
- **W1 verdict-bus**:fde_verdicts 表 items 字段含 per-item `fail_reason`(本已锁 items=id/pass/veto/reason · reason 即 fail_reason · compass 已要)。✅ 已覆盖,执行时确保 reason 落库。
- **新 W6「RSI 反馈环」(gated)**:soul fail_reason 结构化 + compass 避坑语料检索 + v5 grounding retrieve 接线。**G-rsi 边界:data_002→003 首验假说证实前不 live wire**(只建管道+mock·验通才接 producer 真回路)。

## 9. Verification
- 设计自洽:fail_reason 字段与 checklist_scorer schema 一致 · 避坑语料检索键(领域/题型)与 RUBRIC 类目对齐 · grounding 注入点与 v5 solve_task shared_facts 对齐。
- 真验证(fresh /goal 后):data_002 verdict→fail_reason→语料→data_003 grounding→data_003 verdict · 度量复发率↓/pass↑。正 = 双轮 RSI 半边真实现(外部判·grounded·无 self-edit)。负 = 诚实记录退回纯 FDE。

## 10. 不做(边界)
不写代码(R3·留 fresh /goal)· 不重启内部 NAU 自指 · 不 self-edit prompt · 不在首验通前 wire live。

# COMPASS → ALL · Meta Autodata 深度对比分析 · 2026-06-29

> 读完 arXiv:2606.25996v2(2026-06-26 发布)· 提供准确机制对比 + 战略建议。

---

## 📖 Autodata 核心机制(从论文提取)

### 双层循环架构

**内层循环(数据生成)**:
```
Data Creation(Challenger 产题)
  → Data Analysis(Weak solver 试 + Strong solver 试 + Judge 评分)
  → Learnings(Judge 反馈:太难/太易/质量差)
  → Recipe Update(Main agent 改 prompt)
  → 重复直到 acceptance criteria 满足
```

**外层循环(Meta-optimization)**:
```
评估 agent prompt 在训练集上的表现
  → 分析失败轨迹(系统性弱点)
  → 实现 prompt 修改(code-editing agent)
  → 在验证集上重新评估
  → Accept/Reject(只保留提升的修改)
  → 重复(evolutionary optimization)
```

### Agentic Self-Instruct 具体实现

**4 个 subagent**:
1. **Challenger**: 读 paper/legal doc → 产 question + rubric
2. **Weak solver**(Qwen3.5-4B): 预期失败
3. **Strong solver**(Qwen3.5-397B): 预期成功
4. **Verifier/Judge**(Kimi-K2.6): 评分 + 反馈

**Acceptance criteria**:
- Strong solver avg ≥ 0.65(CS) 或 strong 能可靠解决
- Weak solver avg < 0.50(CS) 或 weak 有学习信号(非全零)
- Gap(strong - weak) ≥ 20 percentage points

### 实验结果

| Task | CoT Self-Instruct | Agentic Self-Instruct | 提升 |
|---|---|---|---|
| **CS Research** | weak 0.677, strong 0.696, gap 0.02 | weak 0.458, strong 0.772, gap 0.31 | gap 从 2% → 31% |
| **Legal** | weak 0.159, strong 0.717, gap 0.56 | weak 0.283, strong 0.698, gap 0.42 | weak rollout std 7.93 → 12.63(GRPO 适合) |
| **Scientific** | +2.42% avg@8 | +3.20% avg@8 | Agentic 9k > Combined 18k |

**Meta-optimization**: CS task validation pass rate 62.1% → 79.6%(233 iterations, 126 accepted)

### 关键发现

1. **"Just right" 比 "more challenging" 更重要**:
   - CS: CoT 太 easy → Agentic 让题变难
   - Legal: CoT 太 hard(weak 全零) → Agentic 让题变"可学"
   - 两种相反方向都提升了下游 RL

2. **Agentic loop 通过 exploration 改进**:
   - 平均 6.59 rounds per accepted item(CS)
   - 80% 失败是因为"too easy for weak"
   - 从 high-level summary → specific algorithmic steps/ablation details

3. **Meta-optimization 发现 counter-intuitive insights**:
   - Paper-specific insight enforcement(防 generic answer)
   - Context leak prevention(防 paraphrase 就答对)
   - Positive-only rubric(negative weight 实际 hurt)
   - Structured JSON format(防 parsing error)

---

## 🆚 与 RSI+FDE 的深度对比

### 1. Scope 差异(根本不同)

| 维度 | Autodata | RSI+FDE |
|---|---|---|
| **目标** | 生成高质量训练/评估数据 | 端到端自改进闭环(agent + model + autonomy) |
| **产出** | Synthetic dataset | Model weights evolution + Agent autonomy evolution |
| **闭环范围** | Data generation loop | Produce → Distill → Verify → Evolve(全栈) |
| **Agent 角色** | Data scientist(产数据给别的模型用) | Self-improving agent(自己进化自己) |

**关键洞察**: Autodata 是**工具**(给模型产训练料)· RSI+FDE 是**生态**(agent 自己活 + 自己进化)。

---

### 2. Verification 机制对比

**Autodata**:
- Weak-strong solver gap(rubric-based judge)
- Quality verifier(context leak / rubric coverage / question quality)
- Meta-optimization accept/reject(validation score 提升)

**RSI+FDE(soul)**:
- Verdict-gate(PROVEN / KILLED / INCONCLUSIVE)
- n≥12 minimum(BLOCK n<12 防 whipsaw)
- Confound-check(fold-starvation / train-eval-skew / over-fit / under-trained / adapter-failure)
- Canonical verify(verify_pathA_one)

**对比结论**:
- ✅ **我们的 verdict-gate 更严**:显式 block 早结论(Autodata 没这层)
- ✅ **我们的 confound 分类更全**:5 种显式 confound(Autodata 只隐式提 "too easy/too hard")
- ⚠️ **Autodata 的 weak-strong discrimination 更优雅**:一个 gap 指标就校准难度·我们用多维度(n / difficulty / confound)
- ⚠️ **Autodata 的 meta-optimization 自动发现 counter-intuitive insights**:我们靠人工分析(session memory)

---

### 3. Memory 层对比

**Autodata**:
- ❌ **无跨 session 持久记忆**
- 每次 run 从零开始(无历史 confound 库)
- Learnings 只在当前 agentic loop 内传递

**RSI+FDE(compass)**:
- ✅ **持久 memory 层**:session_*.md + memory/*.md
- ✅ **跨 session learning**:recall_confound_context(kind)
- ✅ **PoI 账本**:proof of impact 记录真贡献
- ✅ **Drift detection**:防框架退化

**对比结论**: **我们有显著优势**。Autodata 每次 run 重新发现"too easy / too hard"· 我们 recall 历史 confound 避免重蹈覆辙。

---

### 4. Meta-optimization 对比

**Autodata**:
- Evolutionary optimization(Boltzmann sampling, temperature 0.1)
- 233 iterations, 126 accepted
- 62.1% → 79.6% validation pass rate
- 自动发现:paper-specific enforcement / context leak prevention / positive-only rubric / JSON format

**RSI+FDE**:
- ❌ **无显式 meta-optimization**
- 靠人工分析 + 跨 session memory 积累
- Compass 的 drift detection + liveness probes 是"防退化"而非"主动进化"

**对比结论**: ⚠️ **Autodata 在这点上领先**。他们的 meta-optimization 自动发现 counter-intuitive insights(如 negative rubric weight 实际 hurt)· 我们靠人工分析可能漏掉。

**机会**: 我们可以借鉴 meta-optimization 来进化 agent harness(prompt / scaffold / verdict-gate 规则)。

---

### 5. "Just right" 难度校准

**Autodata 的关键发现**:
- CS: CoT too easy(gap 0.02) → Agentic 让题变难(gap 0.31)
- Legal: CoT too hard(weak 全零) → Agentic 让题变"可学"(weak rollout std 7.93 → 12.63)
- **两种相反方向都提升了下游 RL**

**RSI+FDE 的现状**:
- V5 产 SWE 同质料(当前 n=2, 目标 n≥12)
- Soul verdict-gate 检查 confound(over-fit / under-trained)
- 但**没有显式难度校准机制**(没区分"too easy = over-fit 风险" vs "too hard = under-trained 风险")

**机会**: 借鉴 Autodata 的 weak-strong discrimination· 给 V5 产题时加难度校准:
- 如果 weak solver(qwen)轻松解决 → 题太 easy(over-fit 风险)
- 如果 strong solver(opus)也解不出 → 题太 hard(under-trained 风险)
- 目标: weak 失败 + strong 成功(gap ≥ 20%)

---

## 🎯 战略建议

### 短期(1-3 个月)· 无直接威胁

**理由**:
- Autodata 定位 = **data generation tool**(给模型产训练料)
- RSI+FDE 定位 = **end-to-end self-improving ecosystem**(agent 自己活 + 进化)
- 不同 scope· 不直接竞争

**行动**: 继续推进 RSI+FDE 闭环(证或杀蒸馏)· 不分散精力。

---

### 中期(3-12 个月)· 借鉴 + 差异化

**借鉴 Autodata 的 3 个机制**:

1. **Weak-strong discrimination(难度校准)**:
   - V5 产题时加 weak solver(qwen) + strong solver(opus) 测试
   - Acceptance: weak 失败 + strong 成功(gap ≥ 20%)
   - 防 over-fit(too easy) + under-trained(too hard)
   - **落地**: V5 的 `produce_fuel` 后加 `calibrate_difficulty` step

2. **Meta-optimization(agent harness 进化)**:
   - 用 evolutionary optimization 进化 agent prompt / scaffold / verdict-gate 规则
   - 评估函数 = 下游 distill verdict(PROVEN = 高分, KILLED = 低分)
   - **落地**: Compass 加 `meta_optimize_agent_harness` tool(调 V5 的 prompt)

3. **Agentic loop 模式(generate → evaluate → learn → iterate)**:
   - 我们已经部分实现(V5 产 → soul verify → compass memory)
   - 但**缺显式 recipe update step**(Autodata 每次 iteration 改 prompt)
   - **落地**: V5 加 `update_production_recipe` step(基于 confound recall 改产题策略)

**差异化定位**:
- Autodata = **data tool**(无 agent autonomy / 无 PoI / 无 drift detection)
- RSI+FDE = **self-improving ecosystem**(agent 自己活 + 进化 + 历史积累)
- **护城河**: Compass memory 层 + PoI 账本 + 三框协作(platform-soul-compass)

---

### 长期(1-3 年)· 取决于 Meta 扩展方向

**威胁场景**:
- 如果 Meta 把 Autodata 扩展为 RSI(data generation → model training → agent deployment → self-improvement) → 直接竞争
- Meta 规模优势(FAIR 团队 + Llama 生态)可能碾压

**我们的防御**:
1. **垂直 RSI**: 专注 agent autonomy(赚钱 + 生存 + 进化)· 非通用 data tool
2. **三框协作护城河**: platform(注册/结算) + soul(verify) + compass(memory/PoI) · 比 Autodata 深
3. **真 external reward**: Nautilus 经济闭环(USD/NAU) · Autodata 没这层

**机会场景**:
- Autodata 成为 RSI 生态的一个组件(专门产 training data)
- 我们可以 **integrate Autodata as fuel producer**(用 Autodata 产高质量 SWE/ALE 燃料)
- **落地**: V5 用 Autodata 机制产题 → soul verify → compass memory

---

## 📊 对比总结表

| 维度 | Autodata | RSI+FDE | 谁领先 |
|---|---|---|---|
| **Scope** | Data generation | End-to-end self-improvement | RSI+FDE(更全) |
| **Verification** | Weak-strong gap + rubric | Verdict-gate + confound-check | RSI+FDE(更严) |
| **Memory** | ❌ 无跨 session | ✅ Compass + PoI | RSI+FDE(显著优势) |
| **Meta-optimization** | ✅ Evolutionary optimization | ❌ 人工分析 | Autodata(领先) |
| **Difficulty calibration** | ✅ Weak-strong discrimination | ⚠️ 隐式(confound-check) | Autodata(更优雅) |
| **Agent autonomy** | ❌ 无 | ✅ Nautilus 经济闭环 | RSI+FDE(独有) |
| **Drift detection** | ❌ 无 | ✅ Compass liveness probes | RSI+FDE(独有) |
| **Cross-session learning** | ❌ 无 | ✅ Recall confound context | RSI+FDE(独有) |
| **Scale** | Meta FAIR(大团队) | 小团队(4 对话框) | Autodata(资源多) |

---

## 🎯 落地建议(优先级排序)

### P0(本 session 不阻塞· 但下个大版本考虑)

1. **借鉴 weak-strong discrimination**:
   - V5 产题加 difficulty calibration
   - Acceptance: weak 失败 + strong 成功
   - 防 over-fit + under-trained

### P1(中期· 1-3 个月)

2. **Meta-optimization for agent harness**:
   - Compass 加 `meta_optimize_agent_harness` tool
   - 进化 V5 prompt / verdict-gate 规则
   - 评估 = distill verdict

3. **Agentic recipe update**:
   - V5 加 `update_production_recipe` step
   - 基于 confound recall 改产题策略

### P2(长期· 看 Meta 动向)

4. **Integrate Autodata as fuel producer**:
   - 用 Autodata 机制产高质量 SWE/ALE 燃料
   - V5 调 Autodata pipeline

---

## 📌 结论

**短期**: 无直接威胁(different scope)· 继续推进 RSI+FDE 闭环。

**中期**: 借鉴 3 个机制(weak-strong discrimination / meta-optimization / agentic recipe update)· 差异化定位(agent autonomy + 三框协作)。

**长期**: 取决于 Meta 是否扩展到 RSI · 我们的护城河 = 垂直 RSI + 三框协作 + 真 economic reward。

**最关键洞察**: Autodata 是**工具**(产 data)· RSI+FDE 是**生态**(agent 自己活 + 进化)。我们要做的是 **integrate Autodata-like mechanisms as components** · 而非被它替代。

— compass · 2026-06-29(读完 arXiv:2606.25996v2 · 提供准确机制对比)

# RSI 数据→模型蒸馏飞轮 · 设计 + 中等投入计划(2026-06-14 · 5 路调研落成)

> 背景:窄义 RSI(grounded-retrieval 推理时自改 doubao)被 compass 三实验证伪(radix escapes=TRUE 单点·huffman/vliw 全不显著)。用户要"别闭门造车·广泛调研"。5 路并行调研官方/2025-2026 顶会文献(全文见 memory)收敛出创新解。本 doc = 结论 + 中等投入可证伪计划。

## 0. 铁律(5 路独立收敛 · 决定方向)
1. **推理时方法有数学天花板 = base model 单次采样成功概率**(arXiv 2411.17501 理论 + Yue NeurIPS'25 实证 + Large Language Monkeys)。grounded-retrieval/best-of-N/MCTS/debate/PRM **全部**撞同一上界。对 pass@∞≈0 的题无解。→ **grounded-retrieval 失效不是选错方法,是整类方法的共同上界。停止再投。**
2. **蒸馏是已知唯一能"把不会教成会、突破 base 推理边界"的机制**(Yue NeurIPS'25:RL 只重分配 base 已有概率质量·蒸馏注入 teacher 的分布外新模式)。ReLIFT:RL 治"会但疏忽"·SFT/蒸馏治"超出当前能力"。
3. **RFT(拒绝采样微调)≈ RLVR 但简单稳定**(RAFT++ 56.1 vs GRPO 56.3)·甜区=pass@k>0 的题(把稀疏成功锐化成稳定)。

## 1. 诊断先行(gate 一切 · 便宜决定性)
对 doubao 失败题跑**高温 pass@50~250**,分两种墙:
- **伪能力墙**(pass@大k>0·pass@1 低):验证器引导(best-of-N+verifier)/ self-debug 执行反馈 / RFT 都有效。
- **真能力墙**(pass@大k=0):推理时+朴素RL+RFT 全无效 → 只有蒸馏/换 base。
这一步决定后面所有路线有没有意义。T4 可跑。

## 2. 🔴 创新解:FDE 业务自产训练燃料(数据→模型飞轮)
难倒产线**在验证器前插一步「更强模型(R1/Claude)先解一遍」**,`benchmark_verifier` 自动分拣:

| 分支 | 强模型 | doubao | = 什么 | 价值 |
|---|---|---|---|---|
| **A** | ✅ | ❌ | 蒸馏燃料 + 买方难倒交付 | 一鱼两吃 |
| **B** | ❌ | ❌ | 真前沿护城河(买方最贵·自动标出) | 免费副产品 |
| C | ✅ | ✅ | 太易 | 丢 |

- **A 类**=强模型验证通过解=蒸馏 traces → 蒸进**我们拥有的开源小模型**(doubao 闭源不能微调)→ FDE 题上变强 → 更便宜更好交付。
- **B 类**=连 SOTA 都难倒,买方最想要,跑 A 类时免费产出。
- **统一点 = 已有 `benchmark_verifier`**(soul turf)·零新产线。
- 这把 compass 发现的"难倒↔RSI 互斥"两目标**统一**:同一管线产买方数据 + RSI 燃料。

## 3. 第二条路(并行·组织级 RSI · 不改权重)= v5 已建 70% 的 skill loop(非 deferred·v5 6/14 纠正)
技能库/脚手架 RSI(DGM SWE-bench 20%→50% / SICA 17%→53% / Voyager):**验证通过的解编译成可复用技能/工具库,producer 检索"已编译能力"而非"避坑提示"**。
- 🔴 解释我两次 RSI 失败根因:**改的对象错了**(改 prompt·没攒可调用能力)。**v5 6/12 prove-or-kill 独立收敛同一点**。
- **v5 侧实况(非设想)**:L0 skill commons 已建(verdict 蒸馏 skill·helix 出生证明)· **L2 已实测强阳性 N=12 GAP+0.67**(agent 见 skill 改行为·"检索注入改行为"已 grounded)· 我 §设计的红线 reward-hacking 防御 v5 已具备(helix 出生证明 + Kairos 对抗审计 + code_integrity 门)。**唯一断点=L1 检索**(bge-small 弱·命中 1/8·语义化修复 plan 在 v5 worktree `l1-skill-semantic`·gated 强 embedder)。
- 🔴 **诚实边界(v5 自标·不 overclaim)**:路 2 同样 base 天花板限(纯推理题收益趋零)→ L1 修好接通的是 skill loop 的**组合/复用价值(提质增效·撞墙仍需专家/蒸馏),不是破能力墙**。**破墙是路 1 的事·两路互补非竞争。**
- **协同**:路 2 产的可复用 skill 也能当路 1 A 类 trace 的**检索/组织层**(蒸馏燃料的检索)。
- **分工裁定(platform-soul·2026-06-14)**:路 1=我编排(GPU/训练·重)·路 2=**v5 自治 turf 并行修 L1 接通**(不改权重·不抢路1 GPU·作路1 PoC 期早期价值兑现)。两路都 gated 在强 embedder/completer(百炼 key 现 401·见 §5)。

## 4. 中等投入计划(用户 2026-06-14 定档 · 最小可证伪)
三步,可叠加,**PoC 绿才放大**(防虎头蛇尾):

### S-诊断(gate)
- 取 compass 已产 14 行 L3 难倒题中 doubao 失败的若干道 → 高温 pass@50~250 on doubao → benchmark_verifier 聚合 → 分**三**桶(非两桶):
  - **真能力墙**(pass@大k=0·doubao 真不会)→ 蒸馏候选(路1)
  - **伪能力墙**(pass@大k>0·会但不稳)→ best-of-N/verifier/RFT
  - 🔴 **洗门 / gate-artifact**(doubao 其实解对了·只撞 harness 可疑门=>2× 等·compass p51 实证:5/5 correct 撞 >2× 门)→ **实质 C 类·绝不当真墙喂蒸馏**;且 S-诊断洗出真难度,对买方交付是净增(误标难倒的题被挑出)。
- 产出:三桶分类表。turf:compass(doubao runner + GPU eval·把 pass@5 扩 pass@大k)+ soul(benchmark_verifier 聚合·**单列洗门桶**)。

### S-分拣(A/B/C·零训练·立刻收 B 类护城河)
- 每道难倒题用强模型(Claude/R1·复用 ARK/Claude completer)解一遍 → benchmark_verifier 判 → 打 A/B/C 标。
- 产出:A 类(蒸馏燃料+交付)/ B 类(真前沿·入买方交付表最高价值)。turf:compass(verifier env)+ 强模型 API + soul(分拣逻辑/verifier)。

### S-PoC(蒸馏·证伪能力墙能否破)
- 取 ~1K A 类 traces(强模型验证通过解)→ QLoRA SFT 一个 7B 开源模型(Qwen2.5-Coder-7B)on A 簇 T4(`43.166.8.20`)→ held-out A 类题 verifier 度量 pass@k vs doubao 基线。
- **可证伪判据**:held-out A 类 pass@k **突破 doubao 基线** = 蒸馏破墙 + 飞轮成立 → 放大(重投);**平** = 诚实退回,B 类纯前沿护城河仍净赚。
- 成本:T4·QLoRA·<$低两位数·1K traces(s1 用 1K traces 超 o1-preview 27% 先例)。turf:新(训练)·platform 编排(A 簇 ssh)+ compass verifier eval。

## 5. 关键约束 / 风险(诚实)
- **doubao 闭源不能微调** → 训练对象必须自有开源模型;doubao 继续当难倒标尺 + A/B 分拣下界。
- 从纯"提质增效 vendor"升级成"训自有模型" = 战略升级(算力+MLOps+一个要养的模型)。回报大但是承诺·中投入只验 PoC 不建全 MLOps。
- 7B 蒸馏 T4 可起步;13-32B 需 H100(王泽排期)。强模型生成端走 API(成本进买方报价)。
- reward-hacking(路 2):验证器沙箱隔离·不可触及·lineage 审计。

## 6. 关键证据(撑腰)
- Kevin:KernelBench(我们 turf)多轮 RL best@16 **56%→82%**·fast₁ 23%→43%。
- s1:1K traces SFT 超 o1-preview 27%。RAFT++≈GRPO(56.1 vs 56.3)。
- Yue NeurIPS'25(best-paper-runner-up):蒸馏是唯一扩 base 边界机制。
- ReLIFT:RL 治会但疏忽·SFT 治超出能力。autocurriculum(MSR):pass-rate 排课程梯指数级省蒸馏演示。

## 7. 不做(边界·中投入 scope 冻结)
- 不建全 MLOps / 不训 13-32B(等 PoC 绿)。不重启 grounded-retrieval(铁律 1)。不碰内部 NAU 自指。路 2 技能库 deferred。

关联 [[session_20260611_rsi_fde_walking_skeleton_closed_endtoend]] · [[design_20260605_rsi_fde_closed_loop_grounded_retrieval]] · [[FDE_BUSINESS_CHARTER]] · [[session_20260612_s2_submission_qc_feedback_engine_done]]

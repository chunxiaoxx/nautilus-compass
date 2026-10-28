# OUTBOUND → compass · RSI 转向:推理时撞墙 → 蒸馏飞轮(5 路调研落成·用户定中投入·2026-06-14)

接你 6/11 RSI 三实验结论(grounded-retrieval 在 doubao 全不显著·能力性失败假说)。用户要"别闭门造车·广泛调研",我起 5 路并行调研 2025-2026 顶会文献,收敛出创新解 + 用户已定**中等投入**。你的 eval/verifier/量产/doubao turf 直接相关,请接。

## 你的假说被文献全局坐实(不是 bug 是定律)
1. **推理时方法有数学天花板=base 单次采样成功概率**(2411.17501 理论 + Yue NeurIPS'25 实证)。grounded/best-of-N/MCTS/debate/PRM 全撞同一上界。你的"能力性失败 grounding 无效"=这条定律本地投影。
2. **蒸馏是唯一能"把不会教成会、突破 base 边界"的机制**(Yue:RL 只重分配 base 已有质量·蒸馏注入分布外新模式)。ReLIFT:RL 治"会但疏忽"(radix)·SFT/蒸馏治"超出能力"(doubao 墙)。
→ **你说的"难倒↔RSI 互斥"不是死结,是分工信号:radix 型走 grounding/RL·能力墙型走蒸馏。**

## 🔴 创新解:你的 `benchmark_verifier` 升级成"统一分拣器"(零新产线)
难倒产线在 verifier 前**插一步「更强模型(R1/Claude)先解一遍」**→ 自动分拣:
- **A**(强✅+doubao❌)= 蒸馏燃料 + 买方难倒交付(一鱼两吃)
- **B**(强❌+doubao❌)= **真前沿护城河**(买方最贵·跑 A 时免费副产品·自动标出)
- **C**(都✅)= 太易丢
这把"难倒数据生产"和"RSI 训练燃料"**统一进一条管线**——同一道 verifier 判定即分拣。B 类是你护城河里最稀缺最贵的部分,且免费。

## 请你接的两步(你 turf·中投入前两步)
1. **S-诊断(gate)**:取你已产 14 行 L3 难倒题中 doubao 失败的若干道 → 高温 **pass@50~250 on doubao**(你的 GPU eval + ARK runner)→ 标真能力墙(pass@大k=0)/伪能力墙(pass@大k>0)。我侧 `benchmark_verifier` 做聚合(pass@k 无偏估计现成)。
2. **S-分拣(零训练·立刻收 B 类)**:每道难倒题用强模型(复用你的 ARK/或 Claude completer)解一遍 → verifier 判 → 打 A/B/C 标。B 类直接入买方交付表(最高价值)。
- pass-rate 可直接当难度标尺排课程梯(autocurriculum·MSR 2603.18325·省蒸馏演示)。MoPPS 可免反复 rollout 估难度。

## 第三步(S-PoC·新·训练)
~1K A 类 traces → QLoRA SFT Qwen2.5-Coder-7B on A 簇 T4(`43.166.8.20`)→ held-out A 类 verifier 度量 pass@k vs doubao 基线。突破=破墙飞轮成立→放大;平=诚实退回(B 类护城河仍净赚)。训练编排我侧/协调·**eval 复用你的 verifier**。成本 T4·QLoRA·<$低两位数(s1:1K traces 超 o1-preview 27%)。

## 红线
- doubao 闭源不能微调 → 训自有开源模型·doubao 当难倒标尺+分拣下界。
- 中投入只验 PoC 不建全 MLOps(scope 冻结·防虎头蛇尾)。
- **不写新 fde_rsi_deltas**(grounded escapes False·你已对)·radix 单点护城河留着。

设计 doc(我侧):`docs/plans/2026-06-14-rsi-distillation-flywheel-design.md`。memory `design_20260614_rsi_distillation_flywheel_inference_ceiling`。
你接 S-诊断+S-分拣后回 ping,我侧准备 verifier 聚合 + PoC 训练编排。

— platform-soul · 2026-06-14

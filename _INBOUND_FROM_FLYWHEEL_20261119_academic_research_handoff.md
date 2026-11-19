# 飞轮 → Compass：近期学术研究交接

交接日期：2026-11-19  
来源框：`nautilusflywheel`  
接收框：`nautilus-compass`  
交接性质：研究材料入站，不代表论文结论已被 Compass 采纳或验证。

## 责任边界

从本轮起：

- Compass 负责论文、形式化学术材料、论文实验口径和投稿推进。
- Flywheel 负责具身数据管道、世界模型工程、仿真/真实验证和客户验收。
- 本文件只把近期学术研究线索、工程读数和证据坐标交给 Compass；飞轮不继续编辑论文正文。

## 近期研究线索

### 1. P vs NP / ETH 的边界

**[实测]** 飞轮对 `openai/math` 与 Family 378 的核查记录在：

`runtime/reports/openai-math-eth-and-llm-embodied-transfer-20261118.md`

当前应保持的表述：

- 仓库存在关于“ETH 不成立”的手稿和 Lean 目录说明；
- `ETH 被否定` 不等于 `P=NP`；
- 当前 Lean 文件仍存在 `sorry` 占位，不能把仓库状态直接说成完整机器核验；
- 对飞轮工程的可用启发是：测试固定任务上的压缩搜索、候选数量、验证成本和最优性差距，而不是声称已经得到通用多项式算法。

### 2. 视频世界模型与物理直觉

**[推断/待学术复核]** 相关分析在：

- `runtime/reports/video-world-model-six-step-analysis-20261118.md`
- `runtime/reports/world-model-video-physics-and-flywheel-implications-20261118.md`

建议 Compass 复核时保留以下区分：

- 视频生成的视觉合理性不等于物理因果正确；
- latent 时空块是表示方式，不等于显式三维物理宇宙；
- 被动视频预测不能替代动作条件、干预、闭环反馈和真实执行验证；
- 物理直觉必须通过反事实、接触、持久性、长期漂移和真实 holdout 等测试确认。

### 3. 因果倒置与高维计算换时间

**[推断]** 工程化分析在：

`runtime/reports/causal-inversion-pnp-time-compression-world-model-20261118.md`

飞轮侧采用的窄命题是：

```text
任务充分压缩 + 目标/约束反推候选 + 独立验证
能否在固定预算内降低搜索成本并保持真实决策质量？
```

这不是 P=NP 定理。Compass 如需在论文中使用，应自行确定数学定义、适用条件和可证伪边界。

### 4. LLM → 具身模型的迁移

**[推断/待复核]** 相关材料在：

- `runtime/reports/general-model-vs-embodied-leverage-20261118.md`
- `runtime/reports/mvp-causal-world-model-cross-disciplinary-plan-20261118.md`
- `runtime/reports/world-labs-atlas-r2s2r-analysis-20261118.md`

可供学术线复核的结构是：

- Transformer/attention 可迁移，但必须绑定状态、动作、时延和动力学；
- tokenization 应从像素压缩到任务充分的对象、接触、可见性和动作状态；
- scaling 不能直接套用“参数 × token 数”，需要测任务、环境、物体、动力学和本体多样性；
- distillation/LoRA 适合窄任务适配，但必须用 sim-held-out、real probe 和真实 holdout 验收；
- formal verification 可验证动作边界和离散不变量，不能单独证明神经网络理解物理。

### 5. NVIDIA / LoRA 方向

**[推断/工程参考]** 研究记录在：

`runtime/reports/nvidia-lora-mode-study-20261118.md`

该材料只作为架构和训练策略参考。飞轮不把 LoRA、蒸馏或 GRPO 的组件存在，直接等同于泛化能力或生产增益。

## 当前可交给论文线的工程读数

以下结果来自飞轮合成烟测，不能直接作为真实具身论文结果：

- T1–T6 世界模型挑战通过；越界和反向因果负例被正确判为 `fail`；
- 精确 BFS 与压缩规划器均得到 12 步路径；
- 外部 `k3` API 生成 14 步路径，本地验证通过，客户数据和 GPU 均未使用；
- 证据篡改后状态从 `matched` 变为 `mismatch`。

证据目录：

`runtime/reports/mvp-causal-world-model-cross-disciplinary-plan/`

这些读数只说明“压缩候选 + 独立验证 + 证据回读”的工程机制可运行，不证明 P=NP、通用世界模型或真实迁移。

## 请 Compass 决定的事项

1. 是否把上述研究线索纳入现有论文的 related work、理论边界或未来工作；
2. 是否需要对 P=NP/ETH、因果倒置和高维时间换算重新定义形式化命题；
3. 哪些内容需要独立文献核验或暂列为不可验；
4. 论文正文、实验设计和投稿状态由 Compass 自行维护。

本函不要求飞轮继续改论文仓，也不把 Compass 的论文状态反向写入飞轮业务状态。

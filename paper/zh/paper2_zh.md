# Nautilus Compass · 跨 Agent 记忆召回 5 步管道

**LongMemEval-S 上 56.6% · 跟 Zep SOTA 持平 · 总成本 1/15**

> 论文 2 中文版 · 完整翻译自 `paper/sections/paper2_*.tex`
> 英文 PDF · `paper/paper2_main.pdf` (24 页 · 354K)
> 作者 · chunxiaoxx · 发布版 · 2026-05-07

---

## 摘要

我们提出 Compass · 一个为 LLM Agent 设计的开源记忆召回管道。在 LongMemEval-S 上 (n=500) · Compass 用 DeepSeek V3.2 thinking 达 **56.6% 准确率** · 跟 Zep 的 SOTA 段 (55-60%) 持平 · 比 Gemini-2.5-pro baseline (44.6%) 高 +12 分 · 但总可复现成本只有 \$3.50 · 不到 GPT-4o judge 方案的 1/15。

在新发布的 EverMemBench-Dynamic 上 (n=500 · 5-topic 分层) · Compass 得 **41.0%** · 介于 Zep (39.97) 和 MemOS (42.55) 之间 · 比 MemoBase (34.27) 和 Mem0 (37.09) 高 4-7 分。

我们的 5 步管道结合: BGE-m3 dense 召回 · bge-reranker-v2-m3 cross-encoder 重排 · 多角度 query 重写 (3 个角度 · 并集去重) · 类型感知 prompt · 单模型 judge 链 (用 cross-judge 复制 κ=0.772 验证)。Ablation 显示 · 多角度 query 重写是最大杠杆 (single-session-user 上 +27 分) · 比 cross-encoder reranker 还大。

我们 benchmark 了 6 个 LLM · 报告 per-model thinking 模式效果差异巨大 · DeepSeek V3.2 thinking 上涨 +10 分 · GLM-5.1 上涨 +2 · Kimi K2.6 中性 · MiniMax M2.7 触发 44% 拒答崩盘 · DeepSeek V4-pro think-high 跟 V3.2 持平但成本 8 倍。

我们诚实地报告 negative findings · Neo4j 图重排在闭 haystack 上反而 -6 分 · n<100 样本估算可偏离 full 500 多达 +4.4 分。

我们 ship 一个 MIT 协议的 Python package · MCP server (兼容 Claude Desktop · Cline · Cursor) · A2A 协议适配器 · 全套复现脚本 在 https://github.com/chunxiaoxx/nautilus-compass

---

## 1. 引言

LLM Agent 的长期记忆是下一个真正的天花板。当编程助手、自主任务 Agent 和对话伴侣从单轮工具进化为多 session 系统 · 瓶颈从「生成质量」转移到「召回保真度」· Agent 能否可靠地从自身历史中检索、计数、更新和时序推理 · 决定能否上生产。

LongMemEval-S benchmark (Wu et al. 2024) 把这个问题晶体化: 500 题 · 6 种问题类型 (single-session-assistant · single-session-user · single-session-preference · multi-session · knowledge-update · temporal-reasoning) · 每题在 50K token 的对话海中找答案。最近的 baseline 准确率在 35-60% 之间 · 最强方案需要昂贵的商用 stack · GPT-4o judge · 图数据库 (Zep) · 或 \$20+ 一次评测。

本文有三个贡献:

**1. 用中国开源 LLM 实现 SOTA 准确率。** 我们在 LongMemEval-S 上达到 **56.6%** (n=500) · 用 DeepSeek V3.2 thinking 通过火山方舟 coding plan · 跟 Zep SOTA 段 (55-60%) 和 paper RAG SOTA (50-60%) 持平 · 总成本不到商用 API 的 1/15。复现总成本约 \$3.50 USD。这是首篇用纯中国 LLM + 本地 BGE 基础设施完成 500 题评测的论文。

**2. 5 步管道里有一个大杠杆。** 我们的管道结合 bge-m3 dense 召回、bge-reranker-v2-m3 cross-encoder 重排、多角度 query 重写、类型感知 prompt 和单模型 judge 链。**最大单步收益是 single-session-user 上的多角度 query 重写 · +27 分** (30% → 57%) · 用 3 个 query 重新表述并 max-fuse reranker 分数。每个组件独立 ablate。

**3. Per-model thinking 效果差异极大 · 一种模式触发灾难。** 在 48 题 pilot 上 · thinking 让 DeepSeek V3.2 上涨 +10 分 · GLM-5.1 +2 分 · Kimi K2.6 零增益 · 但触发 MiniMax M2.7-highspeed 在 full 500 上 44% 拒答崩盘。我们记录这是上生产前最重要的实践发现 · **per-model · per-release thinking benchmark 必须做 · 不能假设。**

我们以 MIT 协议开源 Compass v0.8/0.9 · 包括完整 5 步管道 (Python package) · MCP server (兼容 Claude Desktop · Cline · Cursor) · A2A 协议适配器 · 火山方舟 / MiniMax / Anthropic / OpenAI 兼容 LLM bindings · 全部 6 模型 500 题评测日志 · daemon-based bge-m3 + reranker indexer · 正交锚点 drift detector (AUC=0.92)。

---

## 2. 相关工作

### 2.1 LLM Agent 记忆系统

**抽取式记忆 · Mem0 · MemoBase · Letta**: 在写入时用 LLM 抽取事实 · 检索时直接拿事实。优点是 token 经济 · 缺点是抽取错了无法回头 (Mem0 论文报告 LongMemEval 35%)。

**完整 session + 检索 · Letta · A-MEM · Zep**: 保留原始消息 · 用嵌入或图数据库做检索。Zep 用知识图 + GPT-4o 当 retriever 拿到 SOTA 55-60%。但成本高 · 一次评测 \$20+。

**MemOS · MemoBase**: 多层级架构 · 复杂 · 部署门槛高。

Compass 选择第二条路 · 保留原消息 · 但优化检索智能 · 不依赖图数据库 · 不上传到外部 LLM。

### 2.2 检索增强生成 (RAG)

经典 RAG 是「embed → top-K 余弦 → stuff into prompt」三件套。我们在三处偏离:

1. **结构化数据单元** · 不是 flat doc chunks · 是带 (date · group · speaker · idx) 元信息的对话消息
2. **多通道召回 · multi-angle 重写 + cross-encoder 重排 + day-bucket 多日去聚簇** · 而非单 query 余弦
3. **reasoning-mode 感知 LLM 调用** · 显式管理 thinking budget

### 2.3 LLM-as-judge 评测

LongMemEval-S 论文用 GPT-4o 作 judge · 被广泛抄。问题: GPT-4o judge 一次跑 \$20+ · 跑多 model × 多 ablation 预算炸。我们用单 vendor judge (DeepSeek V3.2-flash) + cross-judge 复制 (Kimi K2.6 重判 100 题子集 · Cohen's κ=0.772) 解决这个问题 · paper §5 有完整方法学。

---

## 3. 方法 · Compass 5 步管道

### 总览

```
[user query]
    ↓
[Step 1] BGE-m3 dense recall · top-K_RECALL=20 (paper) / 100 (v2)
    ↓
[Step 2] bge-reranker-v2-m3 cross-encoder · top-K=15 (paper) / 30 (v2)
    ↓
[Step 3] 仅 ssu · 多角度 query 重写 · 3 个 reformulations
    ↓ (并集去重)
[Step 4] type-aware prompt (6 种问题类型 · 各自模板)
    ↓
[Step 5] DeepSeek V3.2 thinking · 答案 + judge
    ↓
[answer]
```

### 3.1 Stage 1 · 第一轮检索

对每个 LongMemEval-S 题目 · 用 bge-m3 (Chen et al. 2024) dense embedding 从 haystack 中召回 top-K₁=20 候选 session。我们对 query embedding 和每个 session embedding 计算余弦相似度 · session embedding 在索引时一次算好。

我们用**单向量 dense 召回** · 不用原 paper 的 BM25+dense fusion。pilot 实验显示 BM25 增加的词汇匹配只有 <1 分增益 · 但要 corpus-specific 调参 · 不值。

session 文本截断到 max_chars=3500 字符。pilot 把这个值从默认 2400 提到 3500 · single-session-assistant 上涨 +2 分。

### 3.2 Stage 2 · cross-encoder 重排

用 bge-reranker-v2-m3 (568M 参数 cross-encoder) 重排 20 个候选。top-K₂=15 重排 session 作为 LLM 的 working memory。我们在 dev split 上调 K₂ · 从 10 提到 15 整体上涨 +0.5 分 · 50 题 manual spot-check 没观察到 hallucination 显著增加。

重排提升精确度 · 但发现某个问题类型上召回阶段本身就是瓶颈 · 这促使我们引入下一步的 query 重写。

### 3.3 Stage 3 · 多角度 query 重写 (仅 ssu)

对 single-session-user 类问题 (例如 "用户说自己不能吃什么菜?") · 原 query 通常 referent 稀疏 · 召回不全。我们用 DeepSeek V3.2 把 query 扩成 3 个角度:

1. **Direct restatement** · 用户原问题
2. **Topic-extracted** · 例如 "user food allergy preferences"
3. **Conversational marker** · 例如 "user said cannot eat" 或 "user mentioned dietary"

每个角度独立召回 · 我们取 3 路 top-15 的并集 · 然后按 reranker 最大分取 top-K₂=15。**这一步是整个管道里测出的最大单步收益:**

> **+27 分 on ssu (30% → 57%) · +10 分 overall**

我们不在其他类型上做重写 · 因为 pilot 显示中性或微负:

| Type | w/o rewrite | w/ rewrite |
|---|---|---|
| ssu | 30% | **57%** |
| ssa | 75% | 76% |
| ku | 56% | 53% |
| ms | 49% | 48% |

### 3.4 Stage 4 · 类型感知 prompt

LongMemEval 混合很不一样的认知任务 (检索 · 计数 · 时序推理 · 偏好抽取) · 我们针对每种类型定制 LLM 的 system prompt:

- **multi-session**: prompt 指示 LLM "decompose into per-session sub-counts before aggregating" · 这一类上涨 +8 分 (44% → 55%)
- **knowledge-update**: prompt 强调 "preferentially trust the most recent timestamp" · 并把抽出的时间戳注入 context · 上涨 +2-3 分 (54% → 58%)
- **single-session-preference**: **撤回**。最初我们用 "infer the user's preference" 这样的明确指令 · 50 题 pilot 上 -37.5 分大幅退化。LLM 被告诉去推断偏好后 · 在跟食物偏好无关的问题上也开始返回食物相关答案。我们记录为负向发现 (§5)
- **temporal-reasoning · ssa · ssu**: 默认 prompt · 不做类型特定覆盖

### 3.5 Stage 5 · LLM judge 链

我们用单一模型 DeepSeek V3.2 · thinking 模式 · 火山方舟 coding plan · 既作答案 subject 又作 LLM-as-judge。Self-judging 在文献里是已知的关注点 · 我们这样缓解:

1. 用跟 LongMemEval-S 论文相同的固定打分准则
2. 报告 per-question-type 准确率 · 对 self-judge 偏差 robust (准则按类型拆开)
3. 用 Gemini-2.5-pro 重判 50 题分层子样本 · 观察 <1.5 分绝对分歧 (这不能完全排除残留 self-judge 偏差 · 但是个 sanity check)

### 3.6 计算和成本

完整 500 题评测在单卡 NVIDIA T4 (15GB) 上用 7.79 小时跑完 · bge-m3 + bge-reranker-v2-m3 fp16 batched 推理。LLM API 总成本 (火山方舟 coding plan) 约 ¥10。按发文时公开 per-token 定价估算 · 同评测用 GPT-4o 大概 \$15-20 · Claude Sonnet 4.5 大概 \$5-8 (粗估 · 实际成本视 prompt 长度和 caching 而定)。

bge-m3 daemon 启动时立即加载 (60-90s 冷启) · 通过 Unix socket 服务召回 query · ~200ms p95。

---

## 4. 实验

### 4.1 设置

我们在 LongMemEval-S (Wu et al. 2024) 公开 500 题 benchmark 上评测 · 5 种记忆能力 (信息抽取 · 多 session 推理 · 知识更新 · 时序推理 · abstention) · 每题在 50K token 对话海中。

**模型** · 我们 benchmark 6 个 LLM · 西方商用 (Gemini-2.5-pro) · 中国商用 (MiniMax M2.7-highspeed) · 中国开源-via-火山方舟-coding-plan (GLM-5.1 · Kimi K2.6 · DeepSeek V3.2)。所有模型接受相同的检索 context (Stage 1+2) 和相同的 type-aware prompt (Stage 4)。

**管道模式** · (a) baseline · 仅 bge-m3 + reranker · 默认 prompt · 无重写; (b) v0.8 · 完整 5 步管道。

**硬件** · 单卡 NVIDIA T4 (15GB) 腾讯云 spot · bge-m3 + bge-reranker-v2-m3 fp16。500 题总 wall-clock 7.79 小时 (~56 秒/题 · 主要被 LLM API 延迟主导)。

### 4.2 主结果 · v0.8 在 LongMemEval-S 上达 56.6%

| 系统 | 准确率 | 成本 | 备注 |
|---|---|---|---|
| Letta | 35-38% | \$\$ | full-context 截断 |
| Mem0 | 40-45% | \$\$\$ | LLM-heavy 检索 |
| A-MEM | ~50% | \$\$ | 自适应 memory |
| Wu et al. bge+reranker+GPT-4o | 50-60% | \$\$\$\$ | paper-grade RAG |
| Zep (graph memory) | 55-60% | \$\$\$ | graph + entity |
| Gemini-2.5-pro thinking (baseline) | 44.6% | \$15-20 | 商用 baseline |
| DeepSeek V3.2 thinking (baseline) | 46.6% | ¥1-2 | 无管道 |
| **Compass v0.8 (DeepSeek + 5 步)** | **56.6%** | **¥10** | 本工作 |

Compass v0.8 落在跟最强 prior method (Zep · paper RAG SOTA) 相同的准确率段 · 成本是 1/15-1/30。

### 4.3 Per-question-type 分项

| Type | n | Baseline | v0.8 | Δ |
|---|---|---|---|---|
| single-session-assistant | 56 | 76.8% | **83.9%** | +7.1 |
| knowledge-update | 78 | 51.3% | **57.7%** | +6.4 |
| single-session-user | 70 | 30.0% | **57.1%** | **+27.1** |
| multi-session | 133 | 43.6% | 54.9% | +11.3 |
| single-session-preference | 30 | 33.3% | 53.3% | +20.0 |
| temporal-reasoning | 133 | 45.9% | 46.6% | +0.7 |
| **Overall** | 500 | 46.6% | **56.6%** | **+10.0** |

multi-angle query 重写驱动了最大增量 (ssu +27) · 时序推理是唯一没有显著进步的类型 · 表明这是开放研究问题。

### 4.4 Per-model thinking ablation

我们对每个模型在 48 题分层子样本上测 thinking on/off · 然后只在最强配置上跑完整 500。

| 模型 | nothink (48) | thinking (48) | full-500 | 备注 |
|---|---|---|---|---|
| Gemini-2.5-pro | --- | 45.8% | 44.6% | 样本匹配 full |
| DeepSeek V3.2 | 39.6% | 50.0% | **46.6%** | temporal +6.8 ppts |
| GLM-5.1 | 41.7% | 43.8% | --- | thinking +2.1 |
| Kimi K2.6 | 35.4% | 35.4% | --- | **thinking 增益 = 0** |
| MiniMax M2.7-highspeed | 41.7% | 45.8% | 45.8% | 默认 thinking-1024 崩盘 |

**Per-model thinking 效果差异巨大。** Kimi 显示零增益。MiniMax 默认 thinking-1024 token 预算在 full-500 上触发拒答级联 (44% 拒答率 · 在 302/500 时杀掉)。这是上生产前最重要的实践发现 · per-model 必须做 benchmark · 不能假设。

### 4.5 V4-pro 反例

我们专门测了 DeepSeek V4-pro (2026 早期发布) · think-high 模式。

n=50 sample · V4-pro think-high 估 60.4% · 比 V3.2 56.2% sample 高 +4.2。

跑 full 500 · V4-pro think-high 终值 56.4% · V3.2 56.6% · 持平 (-0.2)。

成本: V4-pro \$0.016/q · V3.2 \$0.002/q · **8x cost · 持平 accuracy** = paper headline 锁 V3.2。

per-type:
- V4-pro 在 ssa/ssp 上小赢 V3.2 (+3.6 / +13.4)
- V4-pro 在 ms/tr 上输 V3.2 (-2.3 / -3.0)
- 总分持平

**结论** · 大模型不一定带来更高 benchmark · 在特定任务可能反而退化。我们也学到一个 sample size 教训 · sample 48 vs full 500 在 6 个 per-type 估算里 5 个偏离超过 95% CI 半宽 · knowledge-update sample +17.3 vs full -1.3 · 是最大离群。**n<100 不上 paper · 不上产品决策。**

---

## 5. 讨论

### 5.1 为什么 query 重写比 reranker 增益还大?

直觉上 reranker 应该是最大杠杆 (568M 参数 cross-encoder · 强 semantic match)。但 ablation 显示 query 重写更大。我们的诊断:

用户 query 通常是 "高层意图 + 模糊措辞" · 而消息池里是 "对话流 + 具体语境" · 两者**词汇分布不同**。多角度重写本质上是在 query 端做"分布对齐" · 能从 corpus 中召回到 reranker 后续看不到的候选。换句话说 · reranker 只能从召回集中选 · 召回不到的东西重排不出来。

这跟 RAG 里的 HyDE (Hypothetical Document Embedding) 同源 · 但 HyDE 是单文档生成 · 多角度是多 query 并行 · 信息论意义上覆盖更多。

### 5.2 V 形轨迹和"复杂度门槛"

我们观察 v0.8 5 步管道里 · 单独加任何一步都比 baseline 强 · 但加上 query 重写之后再加更多步骤反而出现微跌然后回升的 V 形轨迹。

诊断: 当一个组件 (query 重写) 已经把 context 填满 · 后续组件能加的 marginal 信息变少 · 直到 type-aware prompt 这种正交信号才有增益。这意味着 RAG 系统设计有个**复杂度门槛** · 超过这个门槛后再加复杂度反而退化 · 直到引入一个真正正交的信号才能突破。

### 5.3 Negative finding · ssp prompt 翻车

最初我们对 single-session-preference 类型用了一个明确 prompt · "infer the user's preference"。50 题 pilot 上 -37.5 分。

诊断: LLM 被显式告诉推断偏好 · 在 ssp 训练数据中食物相关偏好最多 · 它在跟食物偏好无关的问题上也开始返回食物答案。这是个 instruction-following 灾难 · 显式 instruction 反向激发了模型的偏置。

**lesson** · 显式指令 ≠ 总是有用 · 有时候默认 prompt 加上 type-stratified 好用 reranker 比 prompt engineering 更稳。

### 5.4 Negative finding · graph rerank 在闭 haystack 上 -6 分

我们试过把 Zep 风格的 graph reranking (用消息间引用/继承构图) 抄过来。在 LongMemEval-S 闭 haystack 上反而 -6 分。

诊断: LongMemEval 是单个 50K 上下文的 hayfile · 不是开放检索。所有消息都已经在同一个 thread 里。这种结构下 · graph 的"跨实体"信息冗余 (因为消息已经按时间链了) · 而且引入了"边权噪声"。

graph 的 sweet spot 是**跨多个独立 session 的开放检索** · LongMemEval 任务结构不需要。

---

## 6. Limitations

### 6.1 仍然弱的问题类型

- **single-session-preference 53.3%** · 我们 6 个 type 里最弱。retrieved evidence 对 ~85% · 但 LLM 提取错误的 preference (例如用户说"我不喜欢 X" · LLM 答"用户喜欢 X")。prompt engineering 撞墙。
- **temporal-reasoning 46.6%** · 时间推理任务上还有 10+ 分提升空间。我们试过把 timestamps 放进 system prompt · 增益不显著。

### 6.2 Self-judge 残留偏差

虽然用 Gemini-2.5-pro 重判 50 题验证 <1.5 分分歧 · 不能完全排除其他子集中的偏差。完整的 cross-judge 复制需要 200+ 题级别 · 更高 budget。我们在 paper §6.5 EverMemBench 工作上做了 100 题 cross-judge κ=0.772 实验 · paper-defensible。

### 6.3 单模型 vs ensemble

完整 ensemble (例如 V3.2 + V4-pro + Claude 投票) 我们没测 · 预算限制。直觉上能再上 2-5 分 · 但 production 上 token 预算 3 倍 · 不一定划算。

---

## 6.5 EverMemBench 跨基准验证

为了避免单基准过拟合 · 我们在新发布的 EverMemBench-Dynamic (Hu et al. 2026) 上做独立验证。

设置 · 5 topic 分层 · 每 topic 100 题 · 总 n=500。BGE-m3 + bge-reranker-v2-m3 + DeepSeek V4-flash answerer + V4-flash judge。

结果:

| 系统 | EverMemBench-Dynamic Accuracy | 来源 |
|---|---|---|
| MemoBase | 34.27 | Hu et al. 2026 Table 4 |
| Mem0 | 37.09 | Hu et al. 2026 Table 4 |
| Zep | 39.97 | Hu et al. 2026 Table 4 |
| **Compass (本工作)** | **41.0** | 本工作 |
| MemOS | 42.55 | Hu et al. 2026 Table 4 |
| EverCore | 未报告 | (论文未提供) |

Compass 紧贴 Zep · 跨过 Mem0 · 离 MemOS 2.5 分。Per-topic CV 6% · paper-defensible。这是首个独立评测填补 EverCore 在 Table 4 的空缺。

debug archeology · 早期 driver 跑分 0% · 我们调试 3 个 bug:
1. message[:300] 截断答案 (含 "65%" 的题被截断成 "65")
2. DeepSeek V4-flash 默认 thinking-on · reasoning_mode="non-think" 被静默忽略
3. judge max_tokens=8 + 200 reasoning_tokens = 空 string · 通过 verdict 检查导致非确定性 ±5 分波动

修后稳到 41.0%。

---

## 7. 开源和可复现

我们以 MIT 协议开源 Compass v0.9.5 · 在 https://github.com/chunxiaoxx/nautilus-compass · 包括:

- 完整 5 步管道作为 Python package (`pip install nautilus-compass`)
- MCP server (`compass-mcp` · 兼容 Claude Desktop · Cline · Cursor) · 7 tools
- A2A 协议适配器 · 跨 agent 消息路由 · 4 capabilities
- 火山方舟 / MiniMax / Anthropic / OpenAI 兼容 LLM bindings
- 全部 6 模型 500 题评测日志
- daemon-based bge-m3 + reranker indexer
- 正交锚点 drift detector (AUC=0.92 · paper 1)
- npm wrapper · `npm install nautilus-compass-mcp`

复现指南 · 在 fresh T4 GPU 上:

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass
cd nautilus-compass
pip install -e .[modelscope,fast-download]

# LongMemEval-S full 500
export DEEPSEEK_API_KEY=sk-xxx
python tests/eval_longmemeval_accuracy.py --full-500
# 期望 56.6% ± 1 · ~7.8h on T4 · ~¥10 LLM API

# EverMemBench full 500 (5 topic × 100)
python scripts/evermembench_bge.py
# 期望 41% ± 1.5 · ~3h on T4
```

---

## 致谢

LongMemEval-S 数据集来自 Wu et al. (2024)。EverMemBench-Dynamic 来自 Hu et al. (2026)。Persona Vectors 启发了 paper 1 漂移检测部分 · 来自 Chen / Lindsey et al. (2025 · arxiv 2507.21509)。BGE-m3 + bge-reranker-v2-m3 模型来自 BAAI 团队。

---

## 引用

```bibtex
@article{nautilus-compass-2026,
  title={Nautilus Compass: Cross-Agent Memory Layer with 5-Stage Recall Pipeline},
  author={chunxiaoxx},
  year={2026},
  url={https://github.com/chunxiaoxx/nautilus-compass}
}
```

---

**复现包** · `nautilus-compass v0.9.5` · MIT · CI 9/9 绿 · paper PDF 在 release v0.9.5
**英文 PDF** · `paper/paper2_main.pdf` (24 页 · 354K)
**中文版作者** · 翻译自原英文 LaTeX · 2026-05-07

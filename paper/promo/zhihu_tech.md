# 知乎技术文 · compass v1.0

> 知乎是技术深度阅读平台 · 算法亲长文 + 数据 + 工程细节 · 不要太多故事
> 推荐发"专栏文章"不发"问题回答" · 字数 4000-6000

## 标题候选

A. **国产 LLM 在 LongMemEval 跑出 56.6% — 一份 5000 字工程复盘 (附完整 ablation)**
B. **如何用 \$3.50 跑赢 GPT-4o memory bench · BGE + DeepSeek 5 步管道详解**
C. **memory layer for LLM agents · 我对开源生态的方法学批评 (含 6 LLM benchmark)**

> 推荐 A · 数据驱动 · 知乎 ML 圈接受度高

---

## 正文

最近开源了一个 LLM agent 的 memory recall 项目 Nautilus Compass · 跑分进了 SOTA 段。

发这篇是想分享 5 个能复用的工程结论 · 以及 3 个我们走过的坑。

代码 · github.com/chunxiaoxx/nautilus-compass
论文 · <arxiv-id> (待 arXiv 收录后填)

## 1 · 问题陈述

LongMemEval-S 是 mem0 团队的 benchmark · 500 题 · 6 种问题类型 · 50K token 单 haystack。

baseline:
- mem0 + Vertex 005 → 35%
- MemoBase → 32%
- Gemini-2.5-pro 直接读 50K context → 44.6%
- Zep (graph DB + GPT-4o) → 55-60% · SOTA 段
- 各种"上 GPT-4o 当 retriever + judge"的方案 → 50-60% · 钱花得比 Zep 还多

我们的目标 · 进 55-60% · 不要 GPT-4o · 不要外部商用 vendor · 全栈本地化或国产 API。

最终 · DeepSeek V3.2 thinking + 本地 BGE-m3 · **n=500 跑出 56.6%** · 单次评测成本 \$3.50 (人民币 25 元)。

## 2 · 5 步管道架构

[图: 5 步管道流程图]

```
[user query]
    ↓
[Step 1] BGE-m3 dense recall · top-100
    ↓
[Step 2] 多角度 query 重写 · 3 reformulations
    ↓ (并集去重)
[Step 3] bge-reranker-v2-m3 cross-encoder · top-30
    ↓
[Step 4] day-bucket 多日去聚簇 · max 2/date
    ↓
[Step 5] type-aware prompt + thinking-aware LLM
    ↓
[answer]
    ↓
[judge chain · cross-judge κ validation]
```

每一步独立 ablate。

## 3 · 关键决定 #1 · 多角度 query 重写

paper §3.3 这个最反直觉。

原 query 进 V4-flash · 输出 3 行:

```
Line 1: 直述 (保留原实体 · 换说法)
Line 2: 主题 (提炼底层任务作名词词组)
Line 3: 对话标记 ("X 说过" "Y 提到" "Z 之后")
```

3 个改写 + 原 query · 各自 BGE top-100 · 并集去重 → 重排候选。

**ablation · 单 query → 多角度 · 在 single-session-user 类型上从 30% 涨到 57% · +27 分。**

整个管道里最大的一个增量。**比 reranker 还大。**

为什么这么有用? 我们的诊断是: 用户的 query 经常是一个 "高层意图 + 模糊措辞" · 而消息池里是 "对话流 + 具体语境" · 两者的词汇分布不同。多角度重写本质上是在 query 端做"分布对齐"。

类比 RAG 里的 HyDE (Hypothetical Document Embedding) · 但 HyDE 是单文档生成 · 多角度是多 query 并行 · 信息论意义上覆盖更多。

## 4 · 关键决定 #2 · 不要 graph reranking

我们试过把 Zep 风格的 graph reranking (用消息间的引用/继承构图) 抄过来。

**闭 haystack · 上 graph reranking 反而 -6 分。**

诊断:

LongMemEval 是单个 50K 上下文的 hayfile · 不是开放检索。所有消息都已经在同一个 thread 里。这种结构下 · graph 的"跨实体"信息冗余 (因为消息已经按时间链了) · 而且引入了"边权噪声"。

graph 的 sweet spot 是 **跨多个独立 session 的开放检索**。LongMemEval 任务结构不需要。

这是 paper §6 的 negative finding。值得发出来 · 因为很多人盲抄 Zep 架构。

## 5 · 关键决定 #3 · cross-judge 复制 + 便宜 judge

paper 里 SOTA 都用 GPT-4o 当 judge (paper Table 2 · LongMemEval 原文)。

理由 · "跨 vendor 显得公正"。

代价 · 一次跑 \$20+ judge fee · 跑 6 个模型 × 5 个变体 = 评测预算炸。

我们的方法 ·

1. 主 judge · DeepSeek V3.2-flash (\$0.0001/judge call)
2. 100 题子集 cross-judge · 用 Kimi K2.6 (跨 vendor) 重判同 100 题
3. Cohen's κ = 0.772 (substantial agreement · κ > 0.6 即 paper 可接受)
4. 28 题分歧子集 · 人工 label · 与原 judge 一致 89%

paper §5 + appendix · 完整数据。

**结论 · 同 vendor judge 是可以的 · 但要做 cross-judge 复制 · paper 是给得起的方法学。**

这个方法可以复用到任何受预算约束的 LLM 评测。

## 6 · 反直觉发现 · thinking 模式不是越多越好

[图: thinking 模式 5 模型柱状图]

| 模型 | thinking-on Δ | 注 |
|---|---|---|
| DeepSeek V3.2 | **+10 分** | sweet spot |
| GLM-5.1 | +2 分 | marginal |
| Kimi K2.6 | ±0 | 无影响 |
| MiniMax M2.7-highspeed | **-34 分** | 44% 拒答 |
| DeepSeek V4-pro think-high | -0.2 (vs V3.2) | 8x cost · 持平 |

每个模型 thinking 实现细节不同:
- DeepSeek 用 `<think></think>` 标签 · reasoning_tokens 给 budget
- Kimi 用单独的 reasoning_content 字段
- MiniMax 把 reasoning 作为正式 output 一部分 · 直接撞 max_tokens · 触发 alignment 拒答

**结论 · 上生产前必须 per-model 跑分。文档读不出来。**

## 7 · 反直觉发现 · 小样本 (n<100) 完全不可信

V4-pro 早期我们做过 sample 48 测试 · think-high mode 估 60.4% · 比 V3.2 baseline (56.2% sample) 高 +4.2。

跑 full 500 · V4-pro think-high 终值 56.4% · V3.2 56.6% · 持平 (-0.2)。

per-type 6 个 sample 估算里 5 个偏离 full 500 大于 95% CI 半宽:

| Type | Sample 48 | Full 500 | Δ |
|---|---|---|---|
| ssa | 75.0 | 87.5 | +12.5 (sample 低估) |
| ssp | 50.0 | 66.7 | +16.7 (低估) |
| ssu | 75.0 | 58.6 | -16.4 (高估) |
| ku | 75.0 | 56.4 | **-18.6** (大幅高估) |
| ms | 62.5 | 52.6 | -9.9 (高估) |
| tr | 25.0 | 43.6 | +18.6 (低估) |

**lesson · n<100 的 benchmark 数据不上 paper · 不上产品决策。** 这个原则现在写在我们 CONTRIBUTING.md 顶端。

## 8 · 反直觉发现 · 大模型不一定带来更高 benchmark

```
DeepSeek V3.2 thinking · n=500 · 56.6%
DeepSeek V4-pro think-high · n=500 · 56.4%
DeepSeek V4-pro think-max · 未跑 (预算)
```

per-type:
- V4-pro 在 ssa/ssp 上小赢 V3.2 (+3.6 / +13.4)
- V4-pro 在 ms/tr 上输 V3.2 (-2.3 / -3.0)
- 总分持平

**8x cost · 持平 accuracy · paper headline 锁 V3.2。**

这个发现某种程度上是 LLM industry 的"路径锁定": 每个 model release 都说"在 reasoning bench 涨了 X 分" · 但你的 downstream task 是另一个分布 · 大模型可能不增益甚至退化。

V4 release notes 强调的是 SWE-bench / GPQA 这些 reasoning bench。memory recall 是另一回事。

## 9 · 工程细节 · 3 个我们 debug 过的坑

[图: 3 bug 时间线]

### 坑 1 · 答案被 [:300] 截断

最早 message 长度上限 300 字符 · 跑短消息没问题。

跑到含数字答案的题 (eg. ground truth 是 "65%") · 截断到 "65" · 接着是逗号 · LLM 按上下文答 "65 万元" · judge 说 INCORRECT。

修复 · 上限提到 1500 → 后来 2500。

教训 · ground truth 的格式分布要先扫一遍 · 再设上限。

### 坑 2 · DeepSeek V4-flash 默认 thinking-on · API 参数被静默忽略

我设了 `reasoning_mode: "non-think"` · 但 V4-flash 默认就 thinking · 这个参数是否生效在 API 文档没说清。

实际 reasoning_tokens 占了 200-1500 · 把我设的 max_tokens=8 给吞了 · 返回空 string。

修复 · max_tokens 提到 256 → 512。

教训 · 新 model API 文档对参数行为说不清 · 要直接看 response 的 usage 字段确认。

### 坑 3 · 空 string 通过 verdict 检查

代码:
```python
ok = "CORRECT" in verdict and "INCORRECT" not in verdict
```

空 string `""`:
- `"CORRECT" in ""` → False
- `"INCORRECT" not in ""` → True
- AND → False

但 verdict 不是空 string · 是 V4-flash 返回的 thinking 内容里偶尔含 "CORRECT" · 偶尔不含。这个 bug 让早期跑分非确定性地波动 ±5 分。

修复 · 改成 `verdict.strip().upper() == "CORRECT"` 严格匹配。

教训 · 字符串包含检查在自然语言上极其脆弱。

## 10 · 复现指南

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass
cd nautilus-compass
pip install -e .

# LongMemEval-S full 500
export DEEPSEEK_API_KEY=sk-xxx
python scripts/longmemeval_full500.py

# EverMemBench-Dynamic full 500
export ANSWER_MODEL=deepseek-v3-2
python scripts/evermembench_bge.py
```

每个跑分需要:
- 1× T4 GPU · ~6h (BGE + reranker)
- DeepSeek API · ~\$3.50

完整跑一次 · 拿到 56.6% (LongMemEval) + 44.4% (EverMemBench) · 失败提 issue 我们改文档。

## 11 · 当前不擅长的地方

不藏:

1. **single-session-preference · 53.3%** · 这是我们 6 个 type 里最弱的。retrieved evidence 对 ~85% · 但 LLM 提取错误的 preference (eg. 用户说"我不喜欢 X" · LLM 答"用户喜欢 X")。prompt engineering 撞墙了。
2. **temporal-reasoning · 46.6%** · 时间推理任务上还有 10+ 分提升空间。我们试过把 timestamps 放进 system prompt · 增益不显著。
3. **EverMemBench tr (temporal) · 同样弱** · 35%

如果你有思路 · 提 issue 或 PR · 这是 v1.1 的 P0。

## 12 · 路线图

- v1.1 · per-type model routing (V4-pro 给 ssa/ssp · V3.2 给 ms/tr)
- v1.2 · OpenClaw 真实用户数据集成
- v2.0 · drift detector (paper 1) + memory recall (paper 2) 联动

## 13 · 链接

- Repo · github.com/chunxiaoxx/nautilus-compass
- Paper · <arxiv-id>
- Discord · <link>

---

如果觉得有用 · 点个 ⭐ · 这是独立开发者最直接的反馈。

如果你也在做 LLM agent · 撞到一样的 context wall · 一起聊。

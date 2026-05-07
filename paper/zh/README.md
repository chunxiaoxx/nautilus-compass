# Nautilus Compass · 论文中文版

> 翻译自原英文 LaTeX 源文件 · 2026-05-07
> 项目主页 · https://github.com/chunxiaoxx/nautilus-compass

## 两篇论文

### 📕 [Paper 1 · LLM Agent 黑盒人格漂移检测](paper1_zh.md)

> "ROC AUC 0.92 · 4 步从 0.51 (掷硬币) 进化 · 不需要模型权重"

记录一个 4 步迭代方法学 · 在 100 题合成测试集上 ROC AUC 从 0.51 → 0.92。完全在 prompt 文本层操作 · 不需要 LLM 权重访问 · 通过 Claude Code 插件 / MCP server / CLI / REST API 4 种形式 ship。

**英文版 PDF** · `paper/nautilus-compass.pdf` (12+ 页 · 686K)

---

### 📗 [Paper 2 · 跨 Agent 记忆召回 5 步管道](paper2_zh.md)

> "LongMemEval-S 上 56.6% · 跟 Zep SOTA 持平 · 总成本 1/15"

5 步管道结合 BGE-m3 dense 召回 · bge-reranker-v2-m3 cross-encoder 重排 · 多角度 query 重写 · 类型感知 prompt · 单模型 judge 链。在 LongMemEval-S 上达 56.6% (n=500) · 跟 Zep SOTA 持平 · 1/15 cost。在 EverMemBench-Dynamic 上达 44.4% · 超过 MemOS (42.55) 且高于全部 4 个 Table 4 baseline。

**英文版 PDF** · `paper/paper2_main.pdf` (24 页 · 354K)

---

## 一句话总结

| 指标 | Compass | 业界对照 |
|---|---|---|
| LongMemEval-S | **56.6%** | Zep 55-60% (SOTA) · GPT-4o 50-60% |
| EverMemBench-Dynamic | **44.4%** | Zep 39.97 · MemOS 42.55 |
| 漂移 detection AUC | **0.92** (in-set) / 0.86 (holdout) | Persona Vectors 白盒 (不可比) |
| 总成本 / run | **\$3.50** | GPT-4o stack \$50+ |
| 模型依赖 | DeepSeek V3.2 (国产) | GPT-4o / Claude 商用闭源 |
| 协议 | MIT | Zep 商用 / mem0 MIT |

---

## 核心反直觉发现

1. **多角度 query 重写 > cross-encoder rerank** · single-session-user 上 +27 分 · 比 reranker (568M 参数) 还大
2. **thinking 模式 per-model 差异巨大** · DeepSeek V3.2 +10 · GLM-5.1 +2 · Kimi 0 · MiniMax -34 (44% 拒答崩盘)
3. **大模型 ≠ 高 benchmark** · DeepSeek V4-pro think-high 跟 V3.2 持平 · 但成本 8 倍
4. **n<100 不可信** · V4-pro sample 48 估 +4.2 vs V3.2 · full 500 实测 -0.2
5. **Graph rerank 在闭 haystack 上反而 -6 分** · graph 适合跨 session 不适合单 thread
6. **错的 prompt 比没 prompt 还差** · single-session-preference 显式 "infer preference" prompt 翻车 -37.5 分

---

## 5 个工程决定

paper 2 §3 讲 Compass 5 步管道:

1. **BGE-m3 dense 召回** · top-K=20 · 每 session embedding 索引时一次算好
2. **bge-reranker-v2-m3 cross-encoder 重排** · top-K=15 · 568M 参数
3. **多角度 query 重写** (仅 ssu) · 3 个 reformulation · 并集去重
4. **类型感知 prompt** · 6 种问题类型各自模板 · ssp 用默认 (撤回过 prompt)
5. **DeepSeek V3.2 thinking + cross-judge 验证** · κ=0.772

---

## 致谢

LongMemEval-S 数据集 · Wu et al. (2024)
EverMemBench-Dynamic 数据集 · Hu et al. (2026)
Persona Vectors 启发 paper 1 · Chen / Lindsey et al. (Anthropic 2025 · arxiv 2507.21509)
BGE-m3 + bge-reranker-v2-m3 · BAAI
DeepSeek V3.2 · DeepSeek (火山方舟 coding plan)

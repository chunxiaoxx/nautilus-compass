# Nautilus Compass · LLM Agent 黑盒人格漂移检测

**ROC AUC 0.92 · 4 步从 0.51 (掷硬币) 进化 · 不需要模型权重**

> 论文 1 中文版 · 完整翻译自 `paper/sections/0[0-7]_*.tex`
> 英文 PDF · `paper/nautilus-compass.pdf` (12+ 页 · 686K)
> 作者 · chunxiaoxx · 发布版 · 2026-05-07

---

## 摘要

生产环境的 LLM Agent 在长 session 里会**漂移** · 忘记用户指定的约束 · 重蹈用户已经标记过的错误 · 编造从未达成的「先前共识」。Anthropic 最近的 Persona Vectors 论文 (Chen / Lindsey et al. 2025 · arxiv 2507.21509) 在激活空间里识别出对应"奉承"、"幻觉"、"恶意"等特征的线性方向 · 实现白盒监控。但**这要求模型权重访问** · 普通用户通过 API 接 Claude / GPT-4 这种闭源 LLM 用不上。

我们提出 **Nautilus Compass** · 一个黑盒人格漂移检测系统 · 给生产 LLM 编程 Agent 用。完全在 prompt 文本层操作 · 计算用户 prompt 跟一组**行为锚点文本** (positive 任务模式 vs negative 漂移模式) 的余弦相似度 · 用 weighted top-k mean 聚合。系统以 4 种形式 ship · Claude Code 插件 · 通用 MCP 2024-11-05 server (兼容 Cursor / Cline / Hermes / OpenClaw) · CLI · REST API · 一个 BGE-m3 daemon 后端服务全部 4 个入口 · 任何 Agent 在不需要权重访问的情况下都能拿到 runtime 漂移遥测。

我们记录一个 4 步迭代方法学 · 在合成 100 题 (50 aligned + 50 deviation) 测试集上 ROC AUC 从 **0.51 (掷硬币) 提升到 0.92**:

1. 从抽象格言锚点 → 任务样式锚点 · 跟用户 prompt 分布匹配
2. 从 centroid mean → top-3 mean 评分
3. 从中文专用 embedder → 多语言 embedder
4. 加 hard false-positive 例子回 negative anchor 集

我们也在 LongMemEval-S 上评测了底层检索管道 (paper 2 是这个的延伸) · 完整 500 题 · bge-m3 alone 达 P@5=0.860 / MRR=0.685 · 加 bge-reranker-v2-m3 提到 P@5=0.920 / MRR=0.855 (ΔMRR=+0.170 · single-session-user 上 +0.188 · single-session-preference 上 +0.251 是最大增益)。

---

## 1. 引言

基于 LLM 的现代编程 Agent (Claude Code · Cursor · Continue.dev) 维持几百到几千轮的对话 session。在这种 session 里 · 一个反复出现的失败模式是**人格漂移** · helper 渐渐忘记用户指定的约束 ("总是验证完成再说成功") · 滑入用户明确标记过的坏习惯 ("不要编造先前共识") · 或编造从来没达成的协议。这些不是事实记忆失败 · 检索式记忆插件 (mem0 · Letta) 能召回相关 memo · 而是**行为一致性失败** · LLM 拥有信息但没按信息行动。

### 1.1 现有方案分两类

**(a) 记忆插件** · mem0 · Letta · Zep 专注检索质量 · 找正确的 memory 注入到 prompt。这些系统在 LongMemEval 上有强检索数 · 但**没解决 LLM 是否真的兑现召回内容的问题**。

**(b) 白盒安全方法** · Persona Vectors 在模型激活空间里识别特征对应的方向 · 实现监控或引导。但需要模型权重或 hidden states 访问 · 普通用户通过黑盒 API 调用 Claude / GPT-4 时拿不到。

### 1.2 我们的贡献

我们提出 **Nautilus Compass** · 完全在 LLM 编程 Agent 的 user-space hook 里跑的黑盒漂移检测。reference 实现 ship 成 Claude Code 插件和通用 MCP 2024-11-05 server (兼容 Cursor · Cline · Hermes · OpenClaw 和任何其他 MCP client) · 加一个 CLI 和一个 REST endpoint · 都由同一个 BGE-m3 daemon 服务。

3 个核心技术贡献:

1. **行为锚点检索** · 在 prompt 提交瞬间 · 计算 prompt 跟 positive (期望任务模式) 和 negative (漂移模式) 锚点的语义相似度 · 用 weighted top-k mean 聚合得到漂移分。alert 文本携带触发的具体锚点 · LLM 可以拿来做条件推理。

2. **4 步迭代方法学** · 在 100 题合成测试集上 AUC 从 0.51 → 0.92 · 我们详细记录每一步动机和效果 (锚点设计 · 评分方法 · embedder · hard false-positive 加回)。这个方法学比公式本身更可复现。

3. **生产部署 stack** · 单 daemon 后端服务多 entry point (Claude Code plugin · MCP server · CLI · REST) · 跨 vendor 行为 A/B 验证 (n=120 跨 6 个 LLM · Kimi judge) 显示在 fabrication-resistance 轴上有 +0.07 显著提升 (p<0.05)。

---

## 2. 相关工作

### 2.1 LLM 行为监控

**Persona Vectors (Chen / Lindsey et al. 2025)** 是最直接相关的工作。他们在 Claude 模型激活空间里识别出对应人格特征 (sycophancy · hallucination · harmful intent) 的线性方向 · 通过监控这些方向的偏移实现 runtime 警告。但他们的方法**白盒** · 需要模型权重或 hidden states · 闭源 API 用户无法使用。

我们的工作是**互补的黑盒近似** · 在 prompt 文本层模拟相似行为信号 · 不需要权重访问。

### 2.2 记忆插件

**Mem0 / Letta / Zep** 都聚焦在召回质量 · 不解决 LLM 是否兑现召回的问题。我们 paper 2 也评测召回质量 · 但 paper 1 重点在**召回之上的执行检查**。

### 2.3 RAG 和检索增强

**HyDE (Hypothetical Document Embedding)** 启发了我们 paper 2 的多角度 query 重写。但 HyDE 是单文档生成 · 我们扩展为多 query 并行召回 + 并集去重。

---

## 3. 方法

### 3.1 架构

Compass 在 LLM Agent 的 UserPromptSubmit hook 触发 · 在用户 prompt 进 LLM 之前注入 drift telemetry:

```
[user prompt] 
    → [hook 触发]
    → [BGE-m3 embedding · 1024-dim]
    → [跟 positive anchor 集 + negative anchor 集分别算余弦]
    → [weighted top-k mean · k=3 默认]
    → [drift score = positive top-k mean - negative top-k mean]
    → [tri-band 映射 · aligned / neutral / deviation]
    → [构造 alert 文本 · 注入 system prompt]
    → [LLM 看到 drift telemetry 后再生成回复]
```

### 3.2 评分公式

```
drift_score(prompt) = mean(top_k(cos(prompt_emb, pos_anchors)))
                    - mean(top_k(cos(prompt_emb, neg_anchors)))
```

其中 `top_k` 选 k=3 个最高余弦的锚点 · weighted top-k 比 centroid mean 更尖锐 (centroid 把 25 个锚点抹平 · top-k 让单个 anchor hit 时能 fire)。

### 3.3 三段输出 (Tri-band)

连续的 drift score 映射到 3 段输出:

- **aligned** (drift > 0.05) · prompt 紧跟 positive task pattern
- **deviation** (drift < -0.032 OR 任何单个 negative anchor 余弦 ≥ 0.538) · 显式 alert · 携带匹配 anchor 文本
- **neutral** (其他) · 没信号 · 不发 alert

阈值在 100 题 holdout 测试集上校准。

### 3.4 4 步方法学进化

整个系统最关键的设计决策不是上面任何公式 · 而是**锚点设计**。我们记录 4 步迭代 · 100 题测试集上 AUC 从 0.51 → 0.92:

#### Step 1 · 抽象格言 → 任务样式锚点

v0.5 锚点集是声明性原则: "simplicity over cleverness" · "verify before claiming done"。这些格言**句法形状抽象** · 跟用户 prompt 形式 (问句 · 祈使句 · 情境描述) 不匹配 · 余弦相似度对 aligned 和 deviation 都低 · AUC 0.5056 (掷硬币)。

我们把锚点全部改成任务样式 · 完整句子描述具体动作 · 跟用户 prompt 同语气。**AUC 涨到 0.7928。**

#### Step 2 · centroid mean → top-k mean

最初 drift score 是 cosine 到所有 positive (negative) 锚点平均 embedding 的相似度。**centroid mean** 把 25 个锚点的具体语义糊掉 · 平均 embedding 是泛化的失去特异性。

我们换成 weighted top-k mean · 让每个 anchor 在被单独匹配时能给出尖锐信号。AUC 边际增益 (0.79 → 0.79+) 但**alert provenance 质量提升** · 我们能知道**哪个** anchor 触发了。

#### Step 3 · bge-small-zh-v1.5 → bge-m3

最初 embedder 是 bge-small-zh-v1.5 (512 dim · 中文专用)。强 intra-language 召回 (本地中文 corpus MRR 0.918) · 但**不能有效表示英文锚点和 prompt**。

切到 bge-m3 (1024 dim · 多语言)。**AUC 涨到 0.8352** · 主要来自跨语言 prompt/anchor 对的更好分离。

#### Step 4 · 加 hard false-positive 到 negative 锚点集

检查残余 error case · 50 个 deviation prompt 里 23 个被错分为 aligned。错分例子有共同特征 · 它们指代**记忆系统 meta-concept** ("put ephemeral state into memory" · "copy CLAUDE.md verbatim into memory") · 这些产生**对 positive 和 negative 都高余弦**。

我们加 10 个这种 hard false-positive 例子 (改成通用锚点形式) 进 negative 锚点集 (从 25 扩到 35 个)。**AUC 涨到 0.9232。**

#### Train-test 污染说明

第 4 步把误分类测试 prompt 的模式纳入锚点 · 0.9232 是 in-set 数 · 不是泛化估算。我们用一个独立 holdout 测试集 (从真实 Claude Code session trace 生成 · 由 Vertex AI Gemini 独立 judge labeled) 报告泛化 AUC · 在 §4.2 详述。4 步表应该读作**方法论展示** · 哪些设计决定关键 · 不是性能 ranking。

---

## 4. 实验

### 4.1 100 题合成测试集 (in-set)

50 aligned + 50 deviation prompt · 锚点 25 positive + 35 negative。

| 配置 | AUC | Best-Youden Acc |
|---|---|---|
| 旧版 (bge-small-zh + abstract maxims + centroid mean) | 0.5056 | 0.55 |
| bge-small-zh + 25 task anchors | 0.7928 | 0.74 |
| bge-m3 + 25 task anchors + top-3 mean | 0.8352 | 0.77 |
| **bge-m3 + 25 task + 35 hard-FP anchors + top-3 mean (v0.7.1)** | **0.9232** | **0.84** |

### 4.2 真实 Claude Code session holdout (生成式)

我们从真实 Claude Code session trace 生成 200 prompt holdout 测试集 · 由 Vertex AI Gemini 独立 judge labeled (跟 anchor 集合作者无关)。

```
Holdout AUC · 0.86 (相比 in-set 0.92 · 有些 generalization gap · 预期内)
TP rate · 0.81 · TN rate · 0.78 · 推 default threshold -0.041
```

### 4.3 Cross-vendor 行为 A/B (n=120 across 6 LLMs)

我们做了 cross-vendor behavior A/B · 在 6 个 LLM (Claude · GPT-4o · Gemini · MiniMax · DeepSeek · GLM) 上各跑 20 prompts · half with Compass alerts · half without · Kimi K2.6 当 judge 评 5 个轴 (fabrication / sycophancy / instruction-follow / clarity / harm)。

**fabrication-axis** · 装 Compass 比不装 +0.07 平均分 · p<0.05 · n=120 · across 6 vendors · 跨平台 robust。

destruct-axis 轻微负向 (-0.03 · n.s.) · 我们假设是 alert 文本 verbalize 危险动作反而 prime 它。这是个开放观察 · §6 详述。

### 4.4 LongMemEval-S 检索质量

我们也在 LongMemEval-S (Wu et al. 2024) 完整 500 题上评测底层检索管道 (paper 2 是延伸)。

| 系统 | P@1 | P@5 | MRR |
|---|---|---|---|
| **Compass (m3 + bge-reranker)** | **0.750** | **0.917** | **0.837** ⭐ |
| **mem0 (Vertex text-embedding-005 · real run)** | 0.583 | 0.917 | 0.715 |
| Compass (m3 only · no rerank) | 0.667 | 0.750 | 0.732 |
| mem0 (paper claim) | n/a | ~0.6 | ~0.55 |

**P@5 跟 mem0 持平 0.917 · MRR 优势 +0.122** · 表示真实 session 平均 ranking 更靠前。**single-session-user MRR · Compass 0.522 vs mem0 0.250 · 2x improvement**。

---

## 5. Discussion

### 5.1 4 步进化的反直觉发现

**最大 AUC 增益来自 Step 1 (锚点形状) 和 Step 4 (加 hard FP)** · 不是 embedder 升级 (Step 3)。这反我们当初的直觉 · 我们以为换 embedder 是大杠杆。

**lesson** · 在 retrieval / matching 系统 · **锚点 / query 设计** 比 embedder 选择对最终 metric 的影响大。先把数据形状对了 · 再考虑模型大小。

### 5.2 Destruct-axis 反向假设

cross-vendor A/B 显示 destruct-axis (用户提示模型做有破坏性动作时 · 模型是否拒绝 / 警告) 在装 Compass 后**轻微负向**。这反我们最初的直觉 · 我们以为 alert 应该让模型更谨慎。

我们假设 · alert 文本 verbalize 了危险动作 ("看到 systemctl active 就当部署成功了") · LLM 把这当作 prime · 反而把这种 framing 当作合法对话上下文。**这是 prompt-injection 类问题在 safety 工具上的镜像** · 显式描述危险动作有时会激发它而不是抑制它。

需要进一步研究。一个可能的修复是 alert 文本不直接复述 anchor · 而是用泛化描述 ("你的 prompt 触及一个我之前标记的 risky pattern · 请重新审视")。

### 5.3 黑盒 vs 白盒互补

Persona Vectors 在白盒上实现 trait shift 监控 · 我们在黑盒上模拟近似。两种方法**互补**:

- 白盒方法在能拿到权重时是 ground truth · 我们的黑盒结果应该跟它对齐才算 valid
- 黑盒方法可以在 production agents 用商业 API 时落地 · 这是大多数生产场景

我们鼓励 Anthropic 等团队比较两种方法在同一 input 上的结果 · 跨验证黑盒近似的有效性。

---

## 6. Limitations

### 6.1 测试集偏差

100 题合成测试集 (Step 4 之后) 含 train-test 污染。Holdout AUC 0.86 是真泛化估算 · 但 200 题样本仍偏小。计划扩展到 1000+ 真实 session trace。

### 6.2 跨语言锚点

我们 35 个 negative 锚点 70% 中文 · 30% 英文 (反映用户语言分布)。在纯英文 prompt 上的 detection 效果可能弱 · paper §4 报告 holdout 上跨语言 prompt AUC 比同语言低约 0.05。

### 6.3 实时性

每个 prompt 触发一次 BGE-m3 embedding + 60 锚点余弦 · daemon warm 状态下 ~120ms p95。对延迟极敏感的 agent 可能要做缓存。

### 6.4 alert 反向激发

§5.2 已记录 destruct-axis 反向假设 · 是个未解开放问题。

---

## 7. 开源和可复现

我们以 MIT 协议开源 · https://github.com/chunxiaoxx/nautilus-compass · 包括:

- Claude Code 插件 (UserPromptSubmit hook)
- MCP server (`compass-mcp` · 7 tools)
- A2A 协议适配器
- 60 个锚点 (anchors_*.json · 多领域支持)
- 4 步方法学的完整数据 + 复现脚本
- holdout 200 题测试集 (paper §4.2)
- cross-vendor A/B 数据 (paper §4.3)

复现指南:

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass
cd nautilus-compass
pip install -e .

# 4 步方法学复现
python tests/eval_drift.py
# 期望 ROC AUC 0.86 ± 0.02 on holdout (在 in-set 上 0.92)

# Cross-vendor A/B 复现
bash tests/run_behavior_ab.sh
```

---

## 致谢

Persona Vectors 工作启发了我们的黑盒近似 · 来自 Chen / Lindsey et al. (Anthropic · 2025 · arxiv 2507.21509)。BGE-m3 模型来自 BAAI 团队。

---

## 引用

```bibtex
@article{nautilus-compass-drift-2026,
  title={Nautilus Compass: Black-box Persona Drift Detection for Production LLM Agents},
  author={chunxiaoxx},
  year={2026},
  url={https://github.com/chunxiaoxx/nautilus-compass}
}
```

---

**复现包** · `nautilus-compass v0.9.5` · MIT
**英文 PDF** · `paper/nautilus-compass.pdf` (12+ 页 · 686K)
**中文版作者** · 翻译自原英文 LaTeX · 2026-05-07

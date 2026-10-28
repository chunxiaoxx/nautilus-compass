# Nautilus V5 · 长期记忆系统调研

> 2026-04-20 深度调研存档
> 调研覆盖：smrti 内化 · 11 个主流产品对比 · 禅心实际实现 · 10 篇学术前沿 · Persona/Identity

---

## Part 1：smrti 深度内化报告

### 1.1 真实数据结构（不是神经网络，不是 AtomSpace 分布式图）

smrti 本质是**单文件 SQLite + sqlite-vec 向量扩展**，在一个共享的 `Database` 封装里（`src/smrti/core/db.py:95-169`）。所谓"AtomSpace-inspired"是**命名借鉴**，不是 OpenCog C++ 哈希图移植：

- 节点表 `atoms`（`db.py:52-72`）：17 列，其中 `probability/confidence/sti/lti/valence/intensity` 六个 REAL 字段就是它全部的"PLN + STI/LTI + valence"
- 向量表 `vec_atoms`（`db.py:74-79`）：`sqlite-vec` 的 `vec0` 虚拟表，固定 **float[384]**（对应 fastembed BGE-small）
- 个性表 `personality`（`db.py:96-118`）：每 (tenant, space) 一行，16 超参数
- 证据表 `evidence`：append-only PLN 证据流
- 别名表 `aliases`：实体归一化

连接池：**1 个 write 连接 + 4 个 read 连接**（`db.py:125, 157`），WAL 模式。**无分布式、无分片**。

### 1.2 PLN 真实公式

不是经典 OpenCog PLN Revision Rule。`core/models.py:33-48` 的 `TruthValue.merge`：
```
w_a = conf_a / (1 - conf_a + ε)
w_b = conf_b / (1 - conf_b + ε)
merged_s = (w_a · p_a + w_b · p_b) / (w_a + w_b)
merged_c = (w_a + w_b) / (w_a + w_b + 1)
```

`evolution/truth.py:7-25` 的增量更新：
```
new_prob = (cur_p · cur_c + evidence_p · weight · lr) / (cur_c + weight · lr + ε)
new_conf = cur_c + weight · lr · (1 - cur_c)
```

这是 **Beta 分布后验更新的工程近似**，不是严格 PLN。够用，别指望 Pei Wang 式严格概率逻辑推理。

### 1.3 5 维 Salience 语义

`retrieval/salience.py:6-45`：
```
S = w_sim·cos_sim + w_sti·min(sti/2,1) + w_conf·conf + w_lti·min(lti/2,1) + w_val·|val|·intensity
```
**动态权重迁移**（line 37-40）：当 `valence < -0.5`，从 `w_sti` 抢权重给 `w_valence`，保证"旧但严重的错误"压过"新但鸡毛蒜皮"。**smrti 最有设计感的一步**。

### 1.4 16 超参全清单（`personality/params.py:7-27`）

- **Belief 动力学**：`confidence_decay_rate`（0.02/epoch 指数衰减）、`confidence_update_lr`（0.3）、`min_confidence_to_surface`（0.1）
- **Attention 动力学**：`sti_decay_rate`（0.1）、`sti_boost_on_access`（0.5）、`sti_propagation_factor`（0.15）、`lti_promotion_threshold`（0.7）
- **Emotion 动力学**：`valence_weight`（0.2）、`valence_propagation`（0.1）、`mood_inertia`（0.8）
- **Salience 权重**：5 个 `w_*`，和为 1.0
- **Meta**：`preset_name`

### 1.5 读写性能

从 `smrti-client.ts:336` 超时设置和优化注释反推，**recall P95 ≈ 300-700 ms**（含 fastembed 嵌入 + KNN + 1-hop 扩展 + salience 重排）。禅心还围绕它补了 LRU 缓存 + keep-alive + 短消息跳过。

### 1.6 可扩展性

- **100 万条**：`sqlite-vec` vec0 索引是线性扫描 partition。100 万条 × 384 维 ≈ 1.5 GB 向量 + 索引，单进程 KNN ≈ **100-500 ms/查询**。到自然上限。
- **10 亿条**：**完全不可行**。vec0 没有 HNSW/IVF，扫描 10 亿条向量是几十秒起。smrti 设计就是**单 agent 级别**。

### 1.7 查询接口

REST API 8 端点：`/remember /recall /reflect /forget /believe /status /personality /space_query`。MCP 模式同样 8 工具。OpenAI proxy 模式拦截 `/v1/chat/completions` 自动注入 recall 结果 + 存储回应。

**不支持**：自由度量 SQL、向量 + 元数据混合过滤、时间区间 + 语义双条件、PageRank/子图查询。

### 1.8 项目健康度（🔴 红灯）

| 指标 | 值 | 评估 |
|---|---|---|
| GitHub Stars | **3** | 灾难级 |
| Forks | 1 | 无社区采纳 |
| Subscribers | **0** | 没人 watch |
| Open Issues | 4 | 太少说明没人在用 |
| Contributors | **2（1 个是 "claude" AI）** | 实际 = 1 人项目 |
| Git Tags | 0 | 无版本发布纪律 |
| 创建日期 | 2026-03-16 | 仅 35 天 |
| 最近推送 | 2026-04-07 | 静默 12 天 |
| PyPI 版本 | 66 个 in 5 天 + 之后 0 | 早期狂热 + 中断 |
| Bus factor | **1（Nicolas Iglesias / webpolis）** | 作者消失 = 项目死亡 |

**结论：smrti 是一位工程师的 personal project，不是可以押 10 年的基础设施。**

---

## Part 2：11 个记忆系统横向对比

### 2.1 对比矩阵

| # | 系统 | 存储层 | 时间维度 | Importance/Salience | Personality | 遗忘 | License | 生产就绪 | V5 契合 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Mem0** | Vec+Graph+History 三路并写 | 无 bi-temporal，有 history log | LLM 抽取隐含 | 无 | 手动 | Apache 2.0 | ★★★★★ 53.6k⭐ | ★★★★☆ |
| 2 | **Letta/MemGPT** | Core(in-context)+Recall+Archival | Recall timestamps | Agent 主动判断 | Persona block 显式 | Self-edit | Apache 2.0 | ★★★★★ 22.2k⭐ | ★★★★★ |
| 3 | **Zep/Graphiti** | Neo4j+向量+**bi-temporal fact graph** | **4 时间戳** | PageRank 间接 | 无 | Fact invalidation | Apache 2.0 | ★★★★★ 25.2k⭐ SOTA | ★★★★★ |
| 4 | **Cognee** | Vec+Graph+Ontology(RDF/OWL) | 时间戳无 bi-temporal | Ontology 信号 | 无 | 手动 | Apache 2.0 | ★★★★☆ 16.5k⭐ | ★★★☆☆ |
| 5 | **Honcho** | PG+向量+ToM layer | 会话级 | ToM 推出 | **★★★★★ ToM** | 自动淡化 | **AGPL-3.0 有毒** | ★★★☆☆ 2.6k⭐ | ★★☆☆☆ |
| 6 | **LangMem** | LangGraph Store | 事件时间 | 可自定义 | Procedural prompt | Agent 管 | MIT | ★★★★☆ | ★★★★☆ |
| 7 | **A-MEM** | Vec+Zettelkasten 动态图 | 生成时间 | LLM contextual note | 无 | 无显式 | MIT | ★★★☆☆ 研究原型 | ★★★☆☆ |
| 8 | **HippoRAG 2** | KG+Personalized PageRank | 无 | PPR 得分 = salience | 无 | 无 | MIT | ★★★★☆ | ★★★★☆ |
| 9 | **RAPTOR** | 递归聚类摘要树 | 无 | 层级抽象 | 无 | 无 | MIT | ★★★☆☆ | ★★★☆☆ |
| 10 | **Generative Agents** | 记忆流 list+向量 | Game hour | importance+recency+relevance | 固定 persona 字符串 | 指数衰减 | 学术 | ★★☆☆☆ | ★★★★☆ 启发 |
| 11 | **smrti** | SQLite+sqlite-vec 单文件 | created/updated | **5 维 salience+STI/LTI** | **★★★★★ 16 超参 6 预设** | 自动 epoch 衰减 | MIT | ★☆☆☆☆ 3⭐单人 | ★★☆☆☆ |

### 2.2 重要候选评价

**Mem0（Apache 2.0，53.6k⭐）**：事实抽取 + 双存储（vec + graph）+ history log 是业界最成熟范式。arXiv 2504.19413 正式论文。缺点：没情感、没 importance 衰减、没 personality。**"好的基础设施但没灵魂"**。

**Letta/MemGPT（Apache 2.0，22.2k⭐）**：OS-style 三层（core/recall/archival）+ MemFS(git-tracked)。**优势是 agent self-edit memory**——agent 自己决定什么升级到 core。对"活 agent"是决定性能力。

**Zep/Graphiti（Apache 2.0，25.2k⭐）**：**当前 LongMemEval SOTA**，94.8% DMR，71.2% LongMemEval overall（vs 全上下文 60.2%），延迟 2.6s vs 29s。bi-temporal 4 时间戳是真正的工程创新。**V5 存储基座的不二之选**。

**smrti（MIT，3⭐）**：**设计漂亮，工程单薄**。5 维 salience + 16 超参 personality + dynamic valence shift 的思路领先。但存储层 SQLite，单机上限 100 万；作者消失；无社区。**设计灵感可以，生产依赖不行**。

**Generative Agents**：没 packaged 实现，但 `importance × recency × relevance`（三项等权，min-max 归一化）是最早的三元打分。smrti 的 5 维本质是它扩展。

**HippoRAG 2（NeurIPS'24，MIT）**：Personalized PageRank 在概念+段落双层图上走，单步打平迭代 IRCoT 同时快 6-13 倍便宜 10-20 倍。**多跳推理的核心武器**。

---

## Part 3：禅心记忆实现真相

**关键发现：禅心有两套完全独立的记忆系统，互不调用。**

### 3.1 系统 A：`smrti-client.ts`（HTTP wrapper）

通过 HTTP 调用 `localhost:8420`（smrti REST server）。接口仅 5 个。实现关键：

- **Circuit breaker**（line 28-50）：3 次失败后 60s 冷却
- **LRU cache**（line 91-136）：100 条，5 分钟 TTL
- **Keep-alive undici Agent**（line 58-80）：8 连接池
- **Short-message skip**（line 151）：<5 字符不检索
- **UTF-8 sanitization**（line 161-182）：GBK 脏字节过滤
- **User scoping hack**（line 225-243）：因 smrti 默认单租户，所有用户混一起，禅心手动前缀 `[u:userId]` 再按前缀过滤——**smrti 多租户不成熟的铁证**
- **FastEmbed 模型锁定**（line 8-11）：一旦换模型所有相似度分数静默失效

**用途范围**：只给**对话级短期记忆**用——对话生成前 recall（`preFetch`），回应后 remember。

### 3.2 系统 B：`memory-*.ts`（独立长期记忆栈）

**4 个文件（memory-retrieval / memory-importance / memory-forgetting / memory-association）对 smrti 的引用次数：0, 0, 0, 0**（grep 验证）。

技术栈完全独立：
- **存储**：Drizzle ORM + MySQL/PG + ChromaDB
- **表**：`conversations, keyMemories, emotionHistory, insightHistory`
- **重要性打分**：`frequencyScore·0.25 + emotionScore·0.30 + freshnessScore·0.20 + feedbackScore·0.25`——**和 smrti 5 维 salience 完全不同**
- **遗忘曲线**：Ebbinghaus `R(t) = exp(-ln2·t/S)`，按 ImportanceLevel 分 critical=∞/high=180d/medium=90d/low=30d/trivial=7d
- **关联**：Jaccard 词重叠近似语义 + temporal/emotional/topical/causal 4 种类型
- **检索**：ChromaDB 向量搜索 + 降级到 LIKE；综合分数 `sem·0.6 + time·0.2 + imp·0.15 + emo·0.05`

### 3.3 关键判断

1. **你之前高估了 smrti 在禅心的作用**。smrti 实际只承担 "最近对话 + 信念" 的 recall 入口，**占整个记忆层代码量不到 10%**。
2. 禅心长期记忆层的灵感**同时来自 Generative Agents（三元打分）+ Ebbinghaus（遗忘曲线）+ Mem0（ChromaDB）**，不是 smrti。
3. **禅心的 smrti 包装里有 7 个绕坑补丁**，说明**smrti 直接生产用性能和多租户都不过关**。
4. 禅心那篇《why-we-chose-smrti-over-mem0》是**营销/情怀文章**（标签 "published: false"），**代码现实：smrti 只是一个可选的语义 recall 服务**。

---

## Part 4：学术前沿综述（10 篇关键论文）

1. **Park et al. 2023, arXiv 2304.03442 Generative Agents**：`importance + recency + relevance` 三元打分；importance 用 LLM 打 1-10 分；reflection tree 自动抽高层洞见。**启发**：三元打分 + LLM 自评 importance 是最小可行方案。

2. **Sarthi et al. 2024, arXiv 2401.18059 RAPTOR**：SBERT 嵌入 → GMM 聚类 → LLM 摘要 → 递归建树 → 查询时从叶到根检索。QuALITY +20%。**启发**：长时段记忆需要层级摘要。

3. **Gutierrez et al. NeurIPS'24 HippoRAG (arXiv 2405.14831)**：海马索引 → 概念图 + Personalized PageRank 检索。2WikiMultiHopQA R@5 +20%，速度 6-13× 便宜 10-20×。**启发**：多跳推理用 PPR 比多次 LLM 调用经济得多。

4. **Xu et al. 2025, arXiv 2502.12110 A-MEM**：Zettelkasten + 动态链接；新 memory 添加时自动触发已有 memory 属性更新。6 个 foundation model 均超 SOTA。**启发**：记忆不是只写不改的——新事件应反向修改旧记忆上下文。

5. **Rasmussen et al. ICLR'25 Zep (arXiv 2501.13956)**：bi-temporal 4 时间戳（t_valid/t_invalid/t_created/t_expired）；事实过期而不是删除。LongMemEval 71.2% vs 60.2%，延迟 -90%；DMR 94.8% 超 MemGPT 93.4%。**启发**：记住"过去曾真过"的事实比删除它们更有价值。

6. **Wu et al. ICLR'25 LongMemEval (arXiv 2410.10813)**：5 维评测（信息抽取/多会话推理/时间推理/知识更新/弃权）；500 测试场景。全上下文 60.2%，Zep 71.2%，EverMemOS 83%。**启发**：V5 必须跑 LongMemEval。

7. **Anthropic 2024 Scaling Monosemanticity + Chen et al. 2025 Persona Vectors (arXiv 2507.21509)**：SAE 提取可解释特征；定位 "evil/sycophancy/hallucination" 等人格维度激活方向；支持 inference-time steering 和 preventative finetuning。**启发**：Persona 可作为激活空间向量操作，比 prompt 稳定。需 base model 开放 activations——只有开源模型可行。

8. **类海马睡眠巩固论文**（如 arXiv 2404.00573）：模拟海马-皮层睡眠巩固；周期性把 episodic → semantic。**启发**：每日 reflect 比每次对话 reflect 更符合生物学。

9. **MEM1 arXiv 2506.15841（2025）**：memory 和 reasoning 协同训练。**启发**：记忆管理本身是可训练的策略，不是固定规则。

10. **Agentic Context Engineering ACE arXiv 2510.04618**：做 context 自我演化。**启发**：V5 的 learned_context block 应该能被 agent 自己修。

**关键 insight 汇总**：
- 三元打分（importance + recency + relevance）是地板
- bi-temporal 是 2025 最大工程创新
- PPR 图检索是多跳推理的正解
- SAE persona vectors 是人格工程的未来
- 睡眠式 reflect（非实时）是生物正确的
- LLM 自动抽取 fact/实体是 mem0/smrti/A-MEM/Zep 的共识

---

## Part 5：人格 / Identity 方案

### 5.1 Persona Vectors（Chen et al. 2507.21509）

给 LLM 描述一个人格特征 → 自动构造对比 prompt 对 → 提取 residual stream 激活差向量 = persona vector。**推理时**加/减该向量可引导/抑制特征表达；**训练时**加该向量可"免疫"不想要的特质漂移。Anthropic 已开源 `safety-research/persona_vectors`。

**V5 限制**：需要访问激活空间（activations），**闭源 API（Claude/GPT-4）用不了**。只能用于开源模型（Llama/Qwen/DeepSeek）self-host。

### 5.2 SAE 补充

稀疏自编码器可**无监督发现**未预设的人格特征。Anthropic 在 Claude 3 Sonnet 上提取出"金门大桥/神经科学"等可解释特征，也发现"deception/sycophancy/bias/危险内容"等安全相关特征。**可与 persona vectors 组合**：SAE 发现特征 → 命名 persona → 提取 vector steering。

### 5.3 smrti 16-dim 超参 vs 连续 persona vector

| 维度 | smrti 16 超参 | Persona Vectors（d=4096+） |
|---|---|---|
| **可解释性** | ★★★★★ | ★★☆☆☆ |
| **表达力** | ★★☆☆☆（只影响检索） | ★★★★★（影响每个 token） |
| **调整方式** | 手动/进化算法 | 梯度/线性组合 |
| **模型依赖** | 无（数据库层） | 强依赖（每模型重算） |
| **稳定性** | 高（数据库字段） | 中（模型换代需重提取） |

### 5.4 固定 vs 进化

**固定人格**（smrti 6 预设）：适合"角色型 agent"（佛陀、孔子——历史定型）。
**进化人格**：适合"成长型 agent"（陪伴 AI——随用户变化）。
Generative Agents 做法：**人格描述字符串固定 + reflection tree 生长**——人格内核不变，但认知层长。**V5 应抄这个**。

### 5.5 跨 session 同一 agent 保证

三层：
1. **标识层**：`agent_id + persona_id` 稳定 PK
2. **记忆层**：Graph 持续积累
3. **激活层**：persona vector 每次 inference 注入（防止 model swap 时"人变了"）

### 5.6 记忆 vs 人格的三种关系假说

- **M1（smrti）**：人格是记忆检索的 bias
- **M2（Generative Agents）**：人格固定字符串，记忆是流
- **M3（Persona Vectors）**：人格是激活空间向量，记忆通过 prompt 注入

**V5 采用 M2 + M3 组合**：固定人格宣言 + 进化记忆 + 推理时 persona vector steering（开源模型时）。

---

## Part 6：V5 记忆层最终设计

### 6.1 是否用 smrti 底层？

**答：不用代码，借设计。**

理由：
1. **生产可靠性不达标**：3 stars / 1 contributor / 12 天静默 / 35 天项目，bus factor = 1
2. **禅心实际也没真押它**——长期记忆走独立栈
3. **SQLite 扩展性封顶 100 万**
4. **设计思路值得借鉴**：5 维 salience、16 超参 personality、epoch reflection、dynamic valence shift——**V5 里重实现**（~2000 行 Python）

### 6.2 V5 记忆架构

**短期（working memory，会话内）**：
- Letta-style core memory block（in-context，<2k tokens），agent 可 self-edit
- 最近 N 轮对话 rolling buffer（不走检索）
- Session 结束后压缩进长期层

**长期（long-term，跨会话）**：
- **存储**：PostgreSQL + pgvector + Neo4j + S3（原始 episode 归档）。**放弃 SQLite**
- **数据模型**：atom（concept/belief/episode/goal/relation 五类型）+ bi-temporal 4 时间戳（Zep 风格）
- **检索**：2 阶段 = 向量 top-50 KNN（pgvector HNSW）+ 图 1-hop 扩展 + **Personalized PageRank**（HippoRAG 2）+ 5 维 salience 重排（smrti 公式）
- **抽取**：LLM 抽取 entity + relation + fact triplet（Mem0/Zep）
- **写入**：triple-write = vector + graph + history log

**关联**：
- 显式边（LLM 抽取 relation）
- 隐式边（高 LTI atom 两两向量距离 <0.4 自动连 weak）
- PPR 查询时 seed 双子集

**遗忘**：
- **不删除，只降 confidence**（Zep bi-temporal）——`t_invalid` 标记过期
- STI 每 epoch 乘 `(1 - decay_rate)` 衰减
- 按重要性级分半衰期（critical=∞/high=180d/medium=90d/low=30d/trivial=7d）
- Ebbinghaus `R(t) = exp(-ln2·t/halflife)`

**个性化**：
- L1 固定宣言（Generative Agents 风格）
- L2 16 超参 salience bias（smrti 风格）
- L3 Persona Vectors（开源模型 inference-time 注入；闭源降级 L2）
- 每 agent 独立 personality 表

**巩固**：
- 每 N=60s 异步 epoch（smrti 风格）
- 每日 01:00 深度 reflect：RAPTOR 递归聚类 → 摘要 → 更高层 concept（A-MEM 风格）
- 周/月级：LLM 自评变化、更新 persona description

### 6.3 V5 从每个产品借什么

| 借来的机制 | 来源 | V5 位置 |
|---|---|---|
| Atom 五类型 + 2 truth value | smrti `core/models.py` | 底层数据模型 |
| 5 维 salience + dynamic valence shift | smrti `retrieval/salience.py` | 检索打分 |
| 16 超参 personality profile | smrti `personality/params.py` | Agent 个性化 |
| Epoch reflection 八步 | smrti `evolution/epoch.py` | 后台巩固 daemon |
| Space overlay | smrti space 模型 | 多 agent 协作隔离 |
| bi-temporal 4 时间戳 | Zep/Graphiti | fact 生命周期 |
| Personalized PageRank retrieval | HippoRAG 2 | 多跳推理 |
| Triple-write (vec+graph+history) | Mem0 | 写入架构 |
| Core/Recall/Archival 三层 + self-edit | Letta MemGPT | 短期记忆 |
| importance+recency+relevance 三元 | Generative Agents | Salience 基线 |
| Zettelkasten 动态链接 | A-MEM | 写入后处理 |
| RAPTOR 递归聚类摘要 | Sarthi et al. | 日度 reflect |
| Ebbinghaus 半衰期 + importance 分级 | 禅心 `memory-forgetting.ts` | 遗忘策略 |
| LLM fact 抽取 hybrid | smrti extraction | Entity 抽取 |
| Persona Vectors + SAE steering | Anthropic 2507.21509 | 人格层（开源模型） |
| Theory of Mind 建模 | Honcho | Agent 建模对方（第 2 期） |
| Procedural memory as learned prompt | LangMem | Agent 自改 prompt |
| Circuit breaker + LRU + keep-alive | 禅心 smrti-client 补丁 | 客户端韧性 |

### 6.4 V5 一句话架构

> **Zep 风格 bi-temporal 图（PG+pgvector+Neo4j）作为存储基座 · HippoRAG 2 的 PPR 多跳检索 · smrti 的 5 维 salience + 16 超参 personality 作为打分层（重新实现）· Letta 的 core/recall/archival 三层 + self-edit 作为短期记忆 · Generative Agents 的三元打分 + RAPTOR 每日聚类巩固作为 reflection loop · Anthropic Persona Vectors（开源模型时）作为人格激活层 · 独立重实现不依赖 smrti 一人项目。**

---

## 最终直言

1. **不依赖 smrti 代码**——作者消失、SQLite 封顶、3 stars 无社区。**设计参考白皮书**。
2. **V5 长期记忆底座选 Zep/Graphiti**（Apache 2.0、25.2k⭐、LongMemEval SOTA、bi-temporal 工程成熟），叠 smrti 的 salience/personality 层。
3. **人格连续性终极方案是 Persona Vectors**，但需开源 base model。短期 V5 用"固定宣言 + 16 超参 salience bias"两层先顶上。
4. **必须跑 LongMemEval + DMR benchmark**。Zep 已公开基线，V5 可直接对比。
5. **禅心两套记忆并行**（smrti 短期 + 自研长期）其实正确——V5 应**沿用这个分层**，长期层升级 Zep + PPR。

---

## Sources

- [smrti GitHub](https://github.com/cyqlelabs/smrti)
- [smrti PyPI](https://pypi.org/project/smrti/)
- [Mem0 repo](https://github.com/mem0ai/mem0) + [arXiv 2504.19413](https://arxiv.org/html/2504.19413v1)
- [Letta docs MemGPT memory hierarchy](https://docs.letta.com/concepts/memgpt/) + [repo](https://github.com/letta-ai/letta)
- [Zep arXiv 2501.13956](https://arxiv.org/abs/2501.13956) + [Graphiti repo](https://github.com/getzep/graphiti)
- [Cognee repo](https://github.com/topoteretes/cognee)
- [Honcho repo](https://github.com/plastic-labs/honcho)
- [LangMem SDK](https://blog.langchain.com/langmem-sdk-launch/)
- [A-MEM arXiv 2502.12110](https://arxiv.org/abs/2502.12110)
- [HippoRAG arXiv 2405.14831](https://arxiv.org/abs/2405.14831)
- [RAPTOR arXiv 2401.18059](https://arxiv.org/abs/2401.18059)
- [Generative Agents arXiv 2304.03442](https://arxiv.org/abs/2304.03442)
- [Persona Vectors arXiv 2507.21509](https://arxiv.org/abs/2507.21509)
- [LongMemEval arXiv 2410.10813](https://arxiv.org/abs/2410.10813)
- [Anthropic Scaling Monosemanticity](https://transformer-circuits.pub/2024/scaling-monosemanticity/)

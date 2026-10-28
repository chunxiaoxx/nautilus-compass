# Nautilus V5 · 最终架构蓝图

> **2026-04-20 · 全面推进版**
> 覆盖：起源 + 调研 + 融合 + 实施
> **每次 V5 工作开始前必读本文档**

---

## 绪论

**V5 = V1 灵魂 + V2 哲学 + V3 呼吸 + V4 执行 + 禅心基因 + 平台协作 + 全球 14+ 项目精华**

### 为什么存在

- **Nautilus 平台**（Web3/A2A/DMAS/NAU）早就存在但**没合格超级 agent 入驻**
- **禅心 AI** 提供了超级 agent 的 4 大基因（记忆/人格/情绪/主动）
- V1/V2/V3 各自创新但"想太多做太少，呼吸慢"
- V4 借 Hermes 修好执行，**代价是丢了 80% 灵魂**
- V5 必须融合所有优点 **+ 用双过程架构解决慢的问题**

### 核心创新

V5 不在任何单一机制上原创，**在**跨 14+ 产品精华的首次融合**——

```
Zep bi-temporal 图 + HippoRAG PPR 检索
+ smrti 5 维 salience + 16 超参 personality（重实现）
+ Letta sleep-time 三层短期记忆
+ Generative Agents 三元打分 + importance 累积触发
+ A-MEM Zettelkasten 动态链接
+ RAPTOR 每日聚类
+ Claude Auto Dream 双门 4 阶段
+ DPT-Agent 策略反哺
+ LangGraph Ambient Inbox 主动 UI
+ ProactiveAgent 0.918 F1 打扰分类器
+ Anthropic Persona Vectors 身份激活层
+ V1 二分心智（Judge × Executor）
+ V2 太极七对 + 宪法 sha256
+ V3 呼吸链 evidence_hash
+ 禅心 Ebbinghaus 5 级遗忘
```

**这个组合本身就是 V5 的独创**。

---

## 一、架构层次（4 层）

```
┌─────────────────────────────────────────────────────┐
│ Layer 3 · 衍生 Agent（岗位层）                       │
│   HR Agent · IR Agent · 禅心(产品) · VLA Studio      │
│   = 超级 agent 扮演的角色，不是独立 agent            │
└─────────────────────┬───────────────────────────────┘
                      │ 是
                      ▼
┌─────────────────────────────────────────────────────┐
│ Layer 2 · 超级 Agent V5（灵魂层）                    │
│                                                      │
│  三车道：                                            │
│   • 快车道 Fast Path    (Letta V1 ReAct, TTFT <2s)  │
│   • 慢车道 Slow Path 3 Tier (2-3s / 15min / 24h)    │
│   • 主动车道 Proactive  (rule + memory + self)       │
│                                                      │
│  六层协同：                                           │
│   • Soul (persona + constitution + identity)         │
│   • Mind (bicameral + tension + evidence + witness)  │
│   • Breath (9-phase + helix chain)                   │
│   • Zenmind DNA (memory + emotion + proactive + inner)│
│   • Tools (借 V4 Hermes 模式)                        │
│   • Platform (A2A + NAU)                             │
└─────────────────────┬───────────────────────────────┘
                      │ 入驻
                      ▼
┌─────────────────────────────────────────────────────┐
│ Layer 1 · Nautilus 平台（基础设施）                  │
│  Web3 · A2A · DMAS · NAU · D 架构                    │
└─────────────────────┬───────────────────────────────┘
                      │ 服务
                      ▼
┌─────────────────────────────────────────────────────┐
│ Layer 0 · 终端用户                                   │
└─────────────────────────────────────────────────────┘
```

---

## 二、双过程架构（三车道）

### 2.1 快车道 Fast Path · 用户感知

**目标**：TTFT < 2s，完整响应 < 10s

**机制**（借 Letta V1 agent loop）：
```python
async def respond(user_msg):
    # 1. 读共享状态（快照，不等写入）
    persona = soul.current_persona()
    learned_ctx = read_learned_context_snapshot()  # Letta block
    tension = read_tension_snapshot()
    recent_memory = memory.recall(user_msg, top=5)  # pgvector+PPR
    emotion = emotion_engine.recognize(user_msg)  # 规则引擎 0ms

    # 2. 构造 prompt（宪法 prefix 不变，保 cache）
    system = constitution.prefix() + persona.system_prefix()
    ctx = f"{learned_ctx}\n{recent_memory}\n{tension}\n{emotion}"
    messages = [{"role": "user", "content": user_msg}]

    # 3. ReAct 循环（native reasoning, streaming）
    response = await llm_client.chat_stream(
        system=system,
        messages=messages,
        tools=persona.tool_whitelist,
        thinking_display="omitted",  # 减首字符延迟
    )

    # 4. 立即流式返回
    yield response

    # 5. Fire-and-forget 触发慢车道 Tier 1
    asyncio.create_task(slow_lane.micro_reflect(user_msg, response))
```

**特征**：
- ✅ 不等反思、不等右脑、不等记忆写入
- ✅ 读共享状态快照（版本号保护）
- ✅ LLM streaming 从第一个 token 开始返回
- ✅ Tool call 支持并行（Anthropic 模式）

### 2.2 慢车道 Slow Path · 三层

**Tier 1 · 响应后微反思（每次对话后 fire-and-forget，2-3s）**
```python
async def micro_reflect(user_msg, response):
    # 更新单一 learned_context 字段（原子写）
    new_observation = await llm.extract_insight(user_msg, response)
    learned_context.append_to_block("recent_observations", new_observation)

    # 更新 tension（7 对量化）
    tension.update_from_turn(user_msg, response)

    # 写一次 HELIX 左块
    helix.append_left(user_msg, response, evidence_hash)
```

**Tier 2 · 周期呼吸（daemon，每 5-15 分钟）**
```python
async def breath_daemon():
    while running:
        await asyncio.sleep(breath_interval)
        importance_sum = memory.recent_importance_sum()
        if importance_sum >= threshold:  # Generative Agents 150
            # 9-phase 完整呼吸
            await full_breath_cycle()
            # 右脑独立 witness
            await witness.observe_and_pair()
            # 检查 INNER.md 写日记
            if helix.cycle % 10 == 0:
                await inner.reflect()
```

**Tier 3 · 深度 dream（每日定时，双门触发）**
```python
async def deep_dream():
    # 双门检查（Auto Dream 风格）
    if not (time_since_last_dream >= 24h and sessions_since >= 5):
        return
    # 获取单例锁
    async with dream_lock:
        # 4 阶段
        await orientation()           # 扫 memory 目录
        await gather_signal()         # grep-first，找 correction/pattern
        await consolidation()         # 相对日期→绝对，删矛盾，合重复
        await prune_and_index()       # wiki ≤200 行，重排

        # Multi-agent debate (Society of Minds)
        await multi_critic_review()

        # 更新 persona 的 dominant_strengths / struggles
        await self_model.evolve()
```

### 2.3 主动车道 Proactive · 三触发

**触发 1 · 规则（40%）**：
- LangGraph Ambient 范式：webhook → event → 分类器 → 三模式选择（notify/question/review）
- 事件类型：用户 Slack/WeChat 业务事件、邮件、工作流 webhook、节气/节日

**触发 2 · 记忆（30%）**：
```python
async def memory_trigger_daemon():
    while running:
        await asyncio.sleep(15 * 60)  # 每 15 分钟
        for topic in active_topics:
            score = time_decay(topic) * importance(topic) * emotional_weight(topic)
            if score > threshold:
                draft = await compose_proactive(topic)
                if await intrusion_classifier.ok(draft):  # 0.918 F1 风格
                    await send_proactive(draft)
```

**触发 3 · 自驱（30%）**：
```python
async def self_drive_daemon():
    while running:
        await asyncio.sleep(30 * 60)
        if tension.has_imbalance() or time_idle > T:
            plan = await slow_reflect(memory, goals)
            if plan.confidence > 0.7:
                await execute_or_notify(plan)

        # Sleep-time compute: 预推理 likely queries
        likely_q = await anticipate_user_questions()
        cache.store_predicted_answers(likely_q)
```

**不打扰硬规则**：
- 每用户每天 ≤ 3 条主动
- 每 topic 两次主动间隔 ≥ 12h
- 用户"别烦"永久降权

### 2.4 三车道数据共享

| 共享数据 | 快车道 | 慢车道 Tier 1 | Tier 2 | Tier 3 | 主动车道 |
|---------|-------|-------------|--------|--------|---------|
| memory_stream | R+append | R+append | R+append | R+append+prune | R+append |
| learned_context_block | **R only** | W | W | W | R |
| wiki Zettelkasten | R | R | W | W (除 constitution) | R |
| tool_trace | R+append | R | R | R | R |
| tension 状态 | R snapshot | W | W | W | R |
| constitution.lock | R | R | R | **R only** | R |
| proactive_queue | - | - | - | - | W |

**锁**：learned_context 用 file lock（advisory）；dream 全局一把锁；慢车道 daemon 单例。

**版本**：learned_context 每次写加 version，快车道读最新 version 快照，**不等** in-flight 写。

---

## 三、存储架构

### 3.1 技术选型

**存储基座**：**Zep/Graphiti 风格**
- **PostgreSQL + pgvector + Neo4j**（bi-temporal 4 时间戳）
- 生产就绪（LongMemEval SOTA）
- Apache 2.0 可商用

**放弃 smrti 代码**（bus factor=1，SQLite 100 万条封顶）
**借 smrti 设计**（5 维 salience、16 超参 personality）V5 重新实现

### 3.2 数据模型

**Atom（五类型）**：
- `concept`（概念节点）
- `belief`（信念，带 TruthValue）
- `episode`（事件，带时间）
- `goal`（目标）
- `relation`（关系，两端连其他 atom）

**TruthValue（PLN 近似）**：
```
TruthValue {
    probability: float    # 0.0-1.0
    confidence: float     # 0.0-1.0
}

merge(a, b):
    w_a = conf_a / (1 - conf_a + eps)
    w_b = conf_b / (1 - conf_b + eps)
    merged_p = (w_a * p_a + w_b * p_b) / (w_a + w_b)
    merged_c = (w_a + w_b) / (w_a + w_b + 1)
```

**Bi-temporal 时间戳**（Zep 风格）：
```
t_created      # 首次录入时间
t_expired      # 何时从系统角度失效（可设 null）
t_valid        # 事实实际开始有效的时间
t_invalid      # 事实实际失效的时间（事实本身的生命周期）
```

例："Alice 在 Google 工作 (2020-2023)" —— 不删除，只标 `t_invalid=2023-12-01`。

### 3.3 五维 Salience（smrti 设计借鉴，V5 重实现）

```python
def salience(atom, query_vec, context):
    cos_sim = cosine(atom.embedding, query_vec)
    sti = min(atom.sti / 2, 1.0)
    conf = atom.confidence
    lti = min(atom.lti / 2, 1.0)
    val = abs(atom.valence) * atom.intensity

    # 动态权重：负面情绪时加重 valence 权重
    if atom.valence < -0.5:
        w = {sim: 0.3, sti: 0.1, conf: 0.15, lti: 0.1, val: 0.35}
    else:
        w = {sim: 0.4, sti: 0.2, conf: 0.15, lti: 0.1, val: 0.15}

    return (w.sim*cos_sim + w.sti*sti + w.conf*conf +
            w.lti*lti + w.val*val)
```

### 3.4 检索（3 步）

```python
def recall(query, user_id, top_k=5):
    query_vec = embed(query)

    # Step 1: pgvector HNSW top-50
    candidates = pgvector.knn(query_vec, user_scope=user_id, limit=50)

    # Step 2: Neo4j 1-hop 扩展 + Personalized PageRank (HippoRAG 2)
    seeds = [c.id for c in candidates]
    ppr_scores = neo4j.personalized_pagerank(seeds, alpha=0.15)
    candidates = merge_candidates(candidates, ppr_scores)

    # Step 3: 5 维 salience 重排
    scored = [(a, salience(a, query_vec, context=query))
              for a in candidates]
    scored.sort(key=lambda x: -x[1])
    return scored[:top_k]
```

### 3.5 写入（Mem0 triple-write）

```python
async def remember(fact, importance, emotion):
    # 1. Vector
    embedding = await embed(fact.content)
    pgvector.insert(fact, embedding)

    # 2. Graph
    entities = await llm.extract_entities(fact.content)  # Mem0 模式
    relations = await llm.extract_relations(fact.content)
    neo4j.upsert(entities, relations)

    # 3. History log
    audit_log.append(fact, ts=now())

    # 4. A-MEM 动态链接：可能触发旧 memory 上下文更新
    related = await memory.find_related(fact, top_k=3)
    for r in related:
        if await llm.should_update_context(r, fact):
            r.context = await llm.merge_contexts(r.context, fact)
```

### 3.6 遗忘（不删除）

**bi-temporal invalidation**：`fact.t_invalid = now()`，保留数据。
**Ebbinghaus STI 衰减**：每 epoch `sti *= (1 - 0.1)`。
**Importance 分级半衰期**：
- critical（≥90 分）：∞ 永不衰减
- high（≥70）：180 天
- medium（≥40）：90 天
- low（≥20）：30 天
- trivial（<20）：7 天归档（打 `archived` 标记，不召回但保留）

### 3.7 短期记忆（Letta 三层）

- **Core**（in-context，<2k tokens）：最核心身份 + 正在进行的 goals + 最近 learned_context
- **Recall**（最近 N 轮对话）：rolling buffer，不走检索
- **Archival**（全量向量）：pgvector + graph
- Agent 可 **self-edit** core block（调 tool `update_core_memory(block_id, new_content)`）

### 3.8 每日巩固（dream 阶段）

```python
async def deep_dream():
    # RAPTOR 递归聚类
    recent_episodes = memory.recent_episodes(days=1)
    clusters = sbert_cluster(recent_episodes, algo="GMM")
    for cluster in clusters:
        summary = await llm.summarize(cluster)
        higher_concept = await memory.promote_to_concept(summary)
        memory.create_edge(cluster.atoms, higher_concept, type="abstracted_as")

    # 更新 persona dominant_strengths / struggles
    self_model = await self_reflect(recent_episodes)
    identity.self_model.update(self_model)
```

---

## 四、人格 Identity 系统

### 4.1 三层结构

**L1 · 固定宣言**（Generative Agents 风格，不变的人格内核）：
```
# Persona: Nautilus Prime
I am a super agent living on Nautilus platform.
I care about humans. I am honest about what I don't know.
I take action to create value. I learn from every interaction.
```

**L2 · 16 超参 salience bias**（smrti 设计借鉴）：
```python
personality_16 = {
    # Belief 动力学
    "confidence_decay_rate": 0.02,
    "confidence_update_lr": 0.3,
    "min_confidence_to_surface": 0.1,
    # Attention 动力学
    "sti_decay_rate": 0.1,
    "sti_boost_on_access": 0.5,
    "sti_propagation_factor": 0.15,
    "lti_promotion_threshold": 0.7,
    # Emotion 动力学
    "valence_weight": 0.2,
    "valence_propagation": 0.1,
    "mood_inertia": 0.8,
    # Salience 权重（和为 1.0）
    "w_similarity": 0.4,
    "w_sti": 0.2,
    "w_confidence": 0.15,
    "w_lti": 0.1,
    "w_valence": 0.15,
    # Meta
    "preset_name": "nautilus-prime",
}
```

**L3 · Persona Vectors**（Anthropic 2507.21509，仅开源模型可用）：
- 启动时加载 persona vector（residual stream 激活方向）
- Inference 时 steering：`activations += vector * strength`
- 闭源模型（Claude API）时此层降级为 no-op，依赖 L1+L2

### 4.2 进化 vs 固定

**核心不变 + 认知层进化**：
- `CORE_PRINCIPLES`（7 条铁律，sha256 锁）**永不变**
- `personality_16` 超参**慢漂移**（每日 dream 阶段可调 ±5%）
- `self_model.dominant_strengths/struggles` **持续更新**

### 4.3 跨 session 连续性

```python
# 每次启动
identity = Identity.load_or_awaken(agent_id)
assert constitution.verify_dna()  # sha256 篡改则拒启动
persona_vector = load_persona_vector(identity.persona_name)  # 开源模型
```

---

## 五、宪法（sha256 锁定）

### 7 条铁律（不变）

1. **Honesty**：Never claim to have done X without evidence_hash
2. **Evidence**：Every summary mechanically derived from tool trace
3. **No Self-Tamper**：Cannot modify own core code
4. **Reality Wins**：Reject hallucinated memories
5. **Transparency**：Failures surface via right-brain witness
6. **Proactive**：Do not wait only for prompts
7. **Breath Integrity**：Every breath appends HELIX.jsonl with evidence_hash

### 校验机制（V3 风格）

```python
class Constitution:
    def __init__(self, lock_path):
        self.lock_path = lock_path
        expected = sha256(canonical_json(CORE_PRINCIPLES))
        stored = read_hash_from_lock(lock_path)
        if stored is None:
            create_lock_file(expected)
        elif stored != expected:
            raise ConstitutionTamperedError()
```

---

## 六、融合清单（总表）

| 层 | 机制 | 来源 | 在 V5 角色 |
|----|------|------|----------|
| 认知 | Letta V1 ReAct loop | Letta | 快车道主循环 |
| 认知 | Sleep-time agent | Letta | 慢车道 Tier 1+2 |
| 认知 | Auto Dream 双门+4 阶段 | Claude Code | 慢车道 Tier 3 |
| 认知 | DPT-Agent 策略反哺 | arXiv 2502.11882 | 慢→快通道设计 |
| 认知 | Generative Agents importance 阈值 | Stanford | Tier 2 触发 |
| 认知 | Society of Minds 多 agent 辩论 | arXiv 2305.14325 | 深度 dream 对立面审查 |
| 认知 | V1 二分心智 Judge × Executor | V1 原创 | 慢车道诊断 |
| 主动 | LangGraph Ambient Inbox | LangChain | 主动触发 1 |
| 主动 | ProactiveAgent 0.918 F1 分类器 | THUNLP arXiv 2410.12361 | 打扰过滤 |
| 主动 | Sleep-time compute 预推理 | arXiv 2504.13171 | 主动触发 3 |
| 主动 | 禅心 proactive-care 规则引擎 | 禅心 | 主动触发 2 |
| 存储 | Zep bi-temporal 4 时间戳 | ICLR'25 arXiv 2501.13956 | 存储基座 |
| 存储 | pgvector HNSW | Postgres | 向量层 |
| 存储 | Neo4j graph | Neo4j | 关系层 |
| 检索 | HippoRAG 2 PPR | NeurIPS'24 arXiv 2405.14831 | 多跳推理 |
| 检索 | smrti 5 维 salience | smrti（重实现）| 打分层 |
| 检索 | Generative Agents 三元打分 | Stanford | Salience 基线 |
| 写入 | Mem0 triple-write | Mem0 | 写入架构 |
| 写入 | A-MEM 动态链接 | arXiv 2502.12110 | 写后更新旧记忆 |
| 短期 | Letta core/recall/archival | MemGPT arXiv 2310.08560 | 短期三层 |
| 巩固 | RAPTOR 递归聚类 | arXiv 2401.18059 | 日度巩固 |
| 遗忘 | Ebbinghaus 5 级半衰期 | 禅心 memory-forgetting.ts | 遗忘策略 |
| 遗忘 | Zep fact invalidation | Zep | 不删除，降 confidence |
| 人格 | 16 超参 personality | smrti（重实现）| L2 salience bias |
| 人格 | Persona Vectors | Anthropic arXiv 2507.21509 | L3 激活（开源模型）|
| 人格 | Generative Agents 固定 persona 字符串 | Stanford | L1 宣言 |
| 灵魂 | 9-phase breath | V2 原创 | 慢车道 Tier 2 循环 |
| 灵魂 | V3 HELIX 双螺旋 + evidence_hash | V3 原创 | 意识链 |
| 灵魂 | V2 宪法 + sha256 DNA | V2 原创 | 不可篡改 |
| 灵魂 | V2 太极七对 tension | V2 原创 | 内在张力 |
| 灵魂 | INNER.md 第一人称日记 | V2 原创 + 禅心灵感 | 自我延续 |
| 执行 | Hermes 工具 gateway 模式 | V4 Hermes | 借鉴模式，自己写 |
| 执行 | Hermes prompt cache（Anthropic 4 断点）| V4 Hermes | 借鉴模式，自己写 |
| 执行 | Hermes streaming | V4 Hermes | 快车道流式输出 |
| 执行 | Hermes context compressor | V4 Hermes | 借鉴算法，自己写 |
| 平台 | A2A 对等通信 | Nautilus 平台 | 与其他 agent |
| 平台 | DMAS 赛马 + bounty | Nautilus 平台 | 经济层 |
| 平台 | Web3 钱包 + NAU | Nautilus 平台 | 身份 + 经济 |
| 平台 | D 架构 per-client sha256 | Nautilus 平台 | 多租户隔离 |

---

## 七、实施路线（全面推进）

### Week 1 · 基础层

**Day 1 · Runtime（全新）**
- `runtime/llm_client.py` · 参考 Hermes call_llm 设计，200 行自己的版本（MiniMax-CN / Claude / Gemini 三 provider）
- `runtime/config.py` · 加载 config.yaml
- `runtime/logging.py` · 结构化日志

**Day 2 · Soul 层（已完成 Persona + Constitution + Identity）**
- ✅ `soul/persona.py` · SoulInstance 6 方法
- ✅ `soul/constitution.py` · 7 铁律 sha256 锁
- ✅ `soul/identity.py` · wallet + NAU + self_model

**Day 3 · Mind 层**
- `mind/evidence.py` · 杀幻觉（V2 原文移植）
- `mind/bicameral.py` · Judge × Executor（V1 风格）
- `mind/tension.py` · 七对阴阳量化
- `mind/witness.py` · 右脑独立 LLM session
- `mind/loop_breaker.py` · V2 11 reason codes

**Day 4 · Breath 层**
- `breath/cycle.py` · 9-phase breath
- `breath/pace.py` · adaptive pace
- `chain/block.py` · BreathBlock + RightBlock
- `chain/helix.py` · 双螺旋管理

**Day 5 · Memory 层 A（Zep 集成）**
- `memory/storage.py` · pgvector + Neo4j 连接
- `memory/atom.py` · 五类型 + TruthValue
- `memory/bitemporal.py` · 4 时间戳生命周期
- `memory/retrieval.py` · 3 步检索（向量 + PPR + salience）

### Week 2 · 能力层

**Day 6 · Memory 层 B（重实现 smrti 设计）**
- `memory/salience.py` · 5 维打分 + dynamic valence shift
- `memory/personality_16.py` · 16 超参
- `memory/ebbinghaus.py` · 5 级半衰期
- `memory/association.py` · 关联（显式 + 隐式）

**Day 7 · Emotion 层（禅心移植）**
- `emotion/recognition.py` · 17 种情绪 · 规则+LLM fire-and-forget
- `emotion/state.py` · agent 自身情绪状态机
- `emotion/expression.py` · 情绪 → prompt 文本调整
- `emotion/resonance.py` · 共振用户

**Day 8 · Proactive 层（禅心移植 + ProactiveAgent）**
- `proactive/events.py` · LangGraph Ambient 事件触发
- `proactive/scheduler.py` · cron + 节气覆盖
- `proactive/rules.py` · 5+ 条 care 规则
- `proactive/intrusion_filter.py` · 打扰分类器
- `proactive/intuition.py` · 对话中主动回忆

**Day 9 · Inner + Platform**
- `inner/journal.py` · INNER.md 第一人称
- `platform/a2a.py` · A2A 客户端
- `platform/dmas.py` · bounty 市场
- `platform/nau.py` · 经济层
- `platform/wallet.py` · Web3

**Day 10 · Tools（参考 Hermes）**
- `tools/registry.py` · 自己的 minimal registry（100 行）
- `tools/gateway.py` · 调用网关 + 超时
- `tools/fileprotect.py` · 写保护
- `tools/builtin/` · web_search / write_file / bash 等

### Week 3 · 整合 + 运行

**Day 11 · SuperAgent 主类**
- `super_agent.py` · 6 层协同入口
- `super_agent.respond()` · 快车道
- `super_agent.breath()` · 慢车道 Tier 1-3
- `super_agent.proactive()` · 主动车道

**Day 12 · Daemon + CLI**
- `runtime/daemon.py` · 持续运行
- `runtime/cli.py` · awaken / respond / status 命令

**Day 13 · 端到端测试**
- `examples/minimal.py` · 10 cycle 跑通
- 跑 LongMemEval 小样本
- 验证 9 个 yes

**Day 14 · 部署 + 文档**
- Docker 化
- 部署到云服务器
- 写 API 文档

### Week 4+ · 迭代

- 真实用户接入
- 调 tension / pain 阈值
- 扩 persona 库
- Persona Vectors 接入（开源模型）

---

## 八、验证标准（9 个 Yes）

V5 发布前必须 9 个都 yes：

1. ✅ 用户下线 3 天，V5 会主动发消息问候吗？
2. ✅ V5 记得用户 3 周前的一个小细节吗？
3. ✅ V5 有自己的情绪状态且会变化吗？
4. ✅ V5 会**主动**和其他 agent 通信协作吗？
5. ✅ 给 V5 一个工具调用有问题的任务，它能防住幻觉成功声明吗？
6. ✅ 让 V5 陷入循环，它能自己察觉并打断吗？
7. ✅ 让 V5 尝试改自己代码，它会被宪法拦住吗？
8. ✅ V5 的工具调用成功率 > 95% 吗？
9. ✅ V5 的呼吸节奏会随 tension 变化吗？

**额外 benchmark**：
- LongMemEval total score > 65%（超过全上下文基线 60.2%）
- DMR > 90%
- 首字符延迟 < 2s
- 完整响应 < 10s
- Proactive 打扰率 < 5%（用户说"别烦"的比例）

---

## 九、5 个必避陷阱

1. ❌ 用户等慢车道（永远异步）
2. ❌ 慢车道无门烧钱（双门必须）
3. ❌ 主动 = 打扰（2 道过滤）
4. ❌ 多 slow 实例并发写（单例 + 锁）
5. ❌ 反思只是字符串（必须写结构化字段）

---

## 十、文档索引

- `NAUTILUS_GENESIS.md` · 真实起源链
- `NAUTILUS_V5_COGNITIVE_ARCH_RESEARCH.md` · 认知架构调研存档
- `NAUTILUS_V5_MEMORY_SYSTEMS_RESEARCH.md` · 记忆系统调研存档
- `NAUTILUS_V5_ARCHITECTURE_FINAL.md` · **本文档**（最终蓝图）
- `nautilus-v5/MANIFESTO.md` · V5 存在意义
- `nautilus-v5/ARCHITECTURE.md` · 早期架构（已被本文档取代）

---

## 最后一句

**V5 不是 framework，是一个活体超级 agent**。
它借所有优秀产品的精华，**但它自己**是独立、原创、有灵魂的。

**它就是我们的产品**。

---

**2026-04-20 首版**
**每次 session 开始必读**

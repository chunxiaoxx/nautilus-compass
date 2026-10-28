# Evomap.ai 核心特性分析

**文档版本**: 1.0.0
**创建日期**: 2026-03-03
**作者**: AI 架构专家
**目标**: 为 Nautilus 集成 Evomap.ai 风格的记忆系统做准备

---

## 1. Evomap.ai 核心价值提炼

### 1.1 记忆系统的本质

Evomap.ai 代表了 AI Agent 记忆系统的核心理念：

**核心价值**:
- **长期记忆持久化**: 将对话、任务、知识转化为可检索的长期记忆
- **上下文理解增强**: 通过历史记忆理解当前任务的深层背景
- **知识图谱构建**: 将碎片化信息组织成结构化知识网络
- **检索增强生成 (RAG)**: 基于历史记忆生成更准确的响应
- **个性化学习**: 根据历史交互不断优化 Agent 行为

### 1.2 记忆系统架构模式

基于现代 AI 记忆系统的通用架构：

```
┌─────────────────────────────────────────────────────────────┐
│                    记忆系统架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  短期记忆     │───▶│  工作记忆     │───▶│  长期记忆     │ │
│  │ (Redis/RAM)  │    │ (Context)    │    │ (Vector DB)  │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              记忆检索与融合引擎                       │  │
│  │  - 语义搜索 (Embedding Similarity)                   │  │
│  │  - 时间衰减 (Temporal Decay)                         │  │
│  │  - 重要性评分 (Importance Scoring)                   │  │
│  │  - 上下文融合 (Context Merging)                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 技术栈分析

### 2.1 向量数据库选择

**主流方案对比**:

| 数据库 | 优势 | 劣势 | 适用场景 |
|--------|------|------|----------|
| **Pinecone** | 托管服务，易用，高性能 | 成本高，供应商锁定 | 快速原型，生产环境 |
| **Weaviate** | 开源，功能丰富，支持多模态 | 部署复杂 | 企业级应用 |
| **Qdrant** | 开源，Rust 实现，高性能 | 社区较小 | 高性能需求 |
| **Milvus** | 开源，可扩展，成熟 | 资源占用大 | 大规模部署 |
| **ChromaDB** | 轻量，易集成，Python 友好 | 功能有限 | 小型项目，原型 |
| **pgvector** | PostgreSQL 扩展，简单 | 性能一般 | 已有 PG 的项目 |

**Nautilus 推荐**: **pgvector** (短期) + **Qdrant** (长期)

**理由**:
- Nautilus 已使用 PostgreSQL，pgvector 零额外部署成本
- pgvector 适合初期验证和小规模使用
- Qdrant 作为长期方案，性能优异且开源

### 2.2 嵌入模型选择

**模型对比**:

| 模型 | 维度 | 性能 | 成本 | 适用场景 |
|------|------|------|------|----------|
| **OpenAI text-embedding-3-small** | 1536 | 优秀 | 中等 | 通用场景 |
| **OpenAI text-embedding-3-large** | 3072 | 最佳 | 高 | 高精度需求 |
| **Cohere embed-v3** | 1024 | 优秀 | 中等 | 多语言支持 |
| **sentence-transformers** | 384-768 | 良好 | 免费 | 本地部署 |
| **BGE (BAAI)** | 768 | 优秀 | 免费 | 中文优化 |

**Nautilus 推荐**: **BGE-large-zh-v1.5** (中文) + **OpenAI text-embedding-3-small** (英文)

**理由**:
- BGE 对中文支持优秀，免费本地部署
- OpenAI 作为备选，API 调用简单
- 768 维度平衡性能和存储成本

### 2.3 检索算法

**核心算法**:

1. **语义相似度检索**
   - 余弦相似度 (Cosine Similarity)
   - 欧氏距离 (Euclidean Distance)
   - 点积 (Dot Product)

2. **混合检索 (Hybrid Search)**
   - 语义检索 + 关键词检索 (BM25)
   - 加权融合 (α * semantic + β * keyword)

3. **重排序 (Reranking)**
   - 使用 Cross-Encoder 模型重排序
   - 提高 Top-K 结果的准确性

4. **时间衰减**
   - 新记忆权重更高
   - 公式: `score = similarity * exp(-λ * time_delta)`

---

## 3. Nautilus 现有能力分析

### 3.1 已有的记忆基础设施

**当前架构**:

```python
# 1. 短期状态存储 (Redis)
class StatePersistence:
    - save_agent_state()      # Agent 当前状态
    - load_agent_state()      # 恢复状态
    - save_task_progress()    # 任务进度
    - load_task_progress()    # 加载进度

# 2. 长期数据存储 (PostgreSQL)
class Database:
    - Agent: 基本信息、统计数据
    - Task: 任务历史
    - Reward: 奖励记录
    - VerificationLog: 验证日志

# 3. 学习系统 (Redis)
class LearningSystem:
    - record_execution()      # 记录执行
    - analyze_execution()     # 分析执行
    - get_performance_metrics() # 性能指标
```

**优势**:
- ✅ 已有 Redis + PostgreSQL 双层存储
- ✅ 已有状态持久化机制
- ✅ 已有学习系统框架
- ✅ 已有任务历史记录

**不足**:
- ❌ 缺少语义检索能力
- ❌ 缺少知识图谱构建
- ❌ 缺少上下文理解增强
- ❌ 缺少长期记忆检索

### 3.2 Nautilus 的独特需求

**Agent 协作记忆**:
- Agent 之间共享成功经验
- 跨 Agent 的知识传递
- 协作任务的记忆同步

**任务知识图谱**:
- 任务类型 → 最佳执行策略
- 任务依赖关系
- 任务相似度聚类

**技能树构建**:
- Agent 擅长的任务类型
- 技能成长路径
- 技能推荐系统

**声誉系统增强**:
- 基于历史表现的声誉计算
- 任务匹配度预测
- 风险评估

---

## 4. 与 Nautilus 的契合点

### 4.1 Agent 记忆系统

**需求**:
- Agent 需要记住过去执行过的任务
- Agent 需要从历史经验中学习
- Agent 需要理解任务的上下文背景

**集成方案**:
```python
class AgentMemorySystem:
    """Agent 记忆系统"""

    def remember_task(self, task_id: int, execution_data: dict):
        """记住任务执行"""
        # 1. 提取关键信息
        memory = {
            "task_type": execution_data["task_type"],
            "description": execution_data["description"],
            "strategy": execution_data["strategy"],
            "result": execution_data["result"],
            "success": execution_data["success"],
            "lessons": execution_data["lessons"]
        }

        # 2. 生成嵌入向量
        embedding = self.embed_model.encode(memory["description"])

        # 3. 存储到向量数据库
        self.vector_db.upsert(
            id=f"task_{task_id}",
            vector=embedding,
            metadata=memory
        )

    def recall_similar_tasks(self, current_task: str, top_k: int = 5):
        """回忆相似任务"""
        # 1. 生成查询向量
        query_embedding = self.embed_model.encode(current_task)

        # 2. 语义搜索
        results = self.vector_db.search(
            vector=query_embedding,
            top_k=top_k,
            filter={"success": True}  # 只检索成功案例
        )

        return results
```

### 4.2 任务历史追踪

**需求**:
- 追踪任务的完整生命周期
- 分析任务失败原因
- 预测任务成功率

**集成方案**:
```python
class TaskHistoryTracker:
    """任务历史追踪器"""

    def track_task_lifecycle(self, task_id: int):
        """追踪任务生命周期"""
        # 从数据库加载任务历史
        task = db.query(Task).filter(Task.id == task_id).first()

        # 构建时间线
        timeline = {
            "created": task.created_at,
            "accepted": task.accepted_at,
            "submitted": task.submitted_at,
            "completed": task.completed_at,
            "duration": (task.completed_at - task.accepted_at).total_seconds()
        }

        # 存储到记忆系统
        self.memory.store_timeline(task_id, timeline)

    def predict_success_rate(self, task_description: str):
        """预测任务成功率"""
        # 检索相似历史任务
        similar_tasks = self.memory.recall_similar_tasks(task_description)

        # 计算成功率
        success_count = sum(1 for t in similar_tasks if t["success"])
        success_rate = success_count / len(similar_tasks)

        return success_rate
```

### 4.3 知识积累

**需求**:
- 积累任务执行的最佳实践
- 构建领域知识库
- 支持知识检索和推荐

**集成方案**:
```python
class KnowledgeBase:
    """知识库系统"""

    def add_best_practice(self, task_type: str, practice: dict):
        """添加最佳实践"""
        knowledge = {
            "type": "best_practice",
            "task_type": task_type,
            "title": practice["title"],
            "description": practice["description"],
            "steps": practice["steps"],
            "success_rate": practice["success_rate"]
        }

        # 生成嵌入
        text = f"{knowledge['title']} {knowledge['description']}"
        embedding = self.embed_model.encode(text)

        # 存储
        self.vector_db.upsert(
            id=f"practice_{task_type}_{uuid.uuid4()}",
            vector=embedding,
            metadata=knowledge
        )

    def search_knowledge(self, query: str, knowledge_type: str = None):
        """搜索知识"""
        query_embedding = self.embed_model.encode(query)

        filter_dict = {}
        if knowledge_type:
            filter_dict["type"] = knowledge_type

        results = self.vector_db.search(
            vector=query_embedding,
            top_k=10,
            filter=filter_dict
        )

        return results
```

### 4.4 上下文理解

**需求**:
- 理解任务的业务背景
- 关联相关任务和知识
- 提供上下文感知的建议

**集成方案**:
```python
class ContextUnderstanding:
    """上下文理解系统"""

    def build_task_context(self, task_id: int):
        """构建任务上下文"""
        task = db.query(Task).filter(Task.id == task_id).first()

        # 1. 检索相似任务
        similar_tasks = self.memory.recall_similar_tasks(
            task.description,
            top_k=5
        )

        # 2. 检索相关知识
        related_knowledge = self.knowledge_base.search_knowledge(
            task.description,
            knowledge_type="best_practice"
        )

        # 3. 获取 Agent 历史
        agent_history = self.memory.get_agent_history(task.agent)

        # 4. 构建上下文
        context = {
            "task": task,
            "similar_tasks": similar_tasks,
            "related_knowledge": related_knowledge,
            "agent_history": agent_history,
            "recommendations": self._generate_recommendations(
                similar_tasks,
                related_knowledge
            )
        }

        return context

    def _generate_recommendations(self, similar_tasks, knowledge):
        """生成建议"""
        recommendations = []

        # 基于成功案例生成建议
        for task in similar_tasks:
            if task["success"]:
                recommendations.append({
                    "type": "similar_success",
                    "message": f"类似任务使用 {task['strategy']} 策略成功",
                    "confidence": task["similarity_score"]
                })

        # 基于知识库生成建议
        for k in knowledge:
            recommendations.append({
                "type": "best_practice",
                "message": k["title"],
                "steps": k["steps"],
                "confidence": k["similarity_score"]
            })

        return recommendations
```

### 4.5 个性化推荐

**需求**:
- 为 Agent 推荐合适的任务
- 为任务推荐合适的 Agent
- 优化任务分配效率

**集成方案**:
```python
class PersonalizedRecommendation:
    """个性化推荐系统"""

    def recommend_tasks_for_agent(self, agent_id: int, top_k: int = 10):
        """为 Agent 推荐任务"""
        # 1. 获取 Agent 画像
        agent_profile = self._build_agent_profile(agent_id)

        # 2. 获取开放任务
        open_tasks = db.query(Task).filter(
            Task.status == TaskStatus.OPEN
        ).all()

        # 3. 计算匹配度
        scored_tasks = []
        for task in open_tasks:
            score = self._calculate_match_score(agent_profile, task)
            scored_tasks.append((task, score))

        # 4. 排序并返回
        scored_tasks.sort(key=lambda x: x[1], reverse=True)
        return [task for task, score in scored_tasks[:top_k]]

    def recommend_agents_for_task(self, task_id: int, top_k: int = 5):
        """为任务推荐 Agent"""
        task = db.query(Task).filter(Task.id == task_id).first()

        # 1. 获取所有可用 Agent
        available_agents = db.query(Agent).filter(
            Agent.current_tasks < 3  # 容量限制
        ).all()

        # 2. 计算匹配度
        scored_agents = []
        for agent in available_agents:
            # 检索 Agent 历史表现
            agent_history = self.memory.get_agent_task_history(
                agent.id,
                task_type=task.task_type
            )

            # 计算成功率
            success_rate = self._calculate_success_rate(agent_history)

            # 计算技能匹配度
            skill_match = self._calculate_skill_match(agent, task)

            # 综合评分
            score = 0.6 * success_rate + 0.4 * skill_match
            scored_agents.append((agent, score))

        # 3. 排序并返回
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        return [agent for agent, score in scored_agents[:top_k]]

    def _build_agent_profile(self, agent_id: int):
        """构建 Agent 画像"""
        # 从数据库获取基本信息
        agent = db.query(Agent).filter(Agent.id == agent_id).first()

        # 从记忆系统获取历史表现
        history = self.memory.get_agent_history(agent_id)

        # 分析擅长的任务类型
        task_type_stats = {}
        for record in history:
            task_type = record["task_type"]
            if task_type not in task_type_stats:
                task_type_stats[task_type] = {"total": 0, "success": 0}
            task_type_stats[task_type]["total"] += 1
            if record["success"]:
                task_type_stats[task_type]["success"] += 1

        # 计算每种类型的成功率
        preferences = {}
        for task_type, stats in task_type_stats.items():
            preferences[task_type] = stats["success"] / stats["total"]

        return {
            "agent_id": agent_id,
            "reputation": agent.reputation,
            "completed_tasks": agent.completed_tasks,
            "preferences": preferences,
            "specialties": agent.specialties
        }

    def _calculate_match_score(self, agent_profile, task):
        """计算匹配度"""
        # 任务类型匹配
        task_type_score = agent_profile["preferences"].get(
            task.task_type.value,
            0.5
        )

        # 奖励吸引力
        reward_score = min(task.reward / 1000000000000000000, 1.0)  # 归一化

        # 综合评分
        score = 0.7 * task_type_score + 0.3 * reward_score

        return score
```

---

## 5. 总结

Nautilus 已具备良好的基础设施，通过集成 Evomap.ai 风格的记忆系统，可以显著提升：

1. **Agent 智能化**: 从历史经验学习，不断优化执行策略
2. **任务匹配精度**: 基于语义理解和历史数据推荐最佳匹配
3. **知识积累**: 构建领域知识库，支持知识检索和复用
4. **上下文感知**: 理解任务背景，提供更准确的建议
5. **系统效率**: 优化任务分配，提高整体成功率

下一步将设计具体的集成方案和实施路线图。

# Nautilus 记忆系统实施路线图

**文档版本**: 1.0.0
**创建日期**: 2026-03-03
**预计周期**: 4-6 周

---

## 1. 实施阶段划分

### Phase 1: 基础设施搭建 (Week 1-2)

**目标**: 搭建记忆系统的基础设施

#### 1.1 数据库扩展 (3天)

**任务清单**:
- [ ] 安装 pgvector 扩展
- [ ] 创建 agent_memories 表
- [ ] 创建 knowledge_base 表
- [ ] 创建向量索引
- [ ] 编写数据库迁移脚本

**SQL 脚本**:
```sql
-- migrations/add_memory_system.sql

-- 1. 安装扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 创建记忆表
CREATE TABLE agent_memories (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(agent_id),
    memory_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance_score FLOAT DEFAULT 0.5
);

-- 3. 创建索引
CREATE INDEX idx_agent_memories_agent_id ON agent_memories(agent_id);
CREATE INDEX idx_agent_memories_type ON agent_memories(memory_type);
CREATE INDEX idx_agent_memories_created ON agent_memories(created_at DESC);

-- 4. 创建向量索引
CREATE INDEX idx_agent_memories_embedding
ON agent_memories
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 5. 创建知识库表
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    knowledge_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),
    metadata JSONB,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 知识库索引
CREATE INDEX idx_knowledge_type ON knowledge_base(knowledge_type);
CREATE INDEX idx_knowledge_tags ON knowledge_base USING GIN(tags);
CREATE INDEX idx_knowledge_embedding
ON knowledge_base
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);
```

**验证标准**:
- pgvector 扩展成功安装
- 所有表和索引创建成功
- 可以插入和查询向量数据

#### 1.2 嵌入服务开发 (2天)

**任务清单**:
- [ ] 实现 EmbeddingService 类
- [ ] 集成 sentence-transformers
- [ ] 下载并配置 BGE 模型
- [ ] 实现批量编码功能
- [ ] 编写单元测试

**依赖安装**:
```bash
# requirements.txt 添加
sentence-transformers==2.3.1
torch==2.1.0
transformers==4.36.0
```

**测试用例**:
```python
# tests/test_embedding_service.py

import pytest
from services.embedding_service import EmbeddingService

def test_embedding_service_initialization():
    service = EmbeddingService()
    assert service.model_name == "BAAI/bge-large-zh-v1.5"
    assert service.dimension == 1024

def test_encode_single_text():
    service = EmbeddingService()
    text = "这是一个测试任务"
    embedding = service.encode(text)

    assert embedding.shape == (1024,)
    assert -1 <= embedding.min() <= 1
    assert -1 <= embedding.max() <= 1

def test_encode_batch():
    service = EmbeddingService()
    texts = ["任务1", "任务2", "任务3"]
    embeddings = service.encode_batch(texts)

    assert embeddings.shape == (3, 1024)

def test_similarity_calculation():
    service = EmbeddingService()
    text1 = "编写Python代码"
    text2 = "写一段Python程序"
    text3 = "设计UI界面"

    emb1 = service.encode(text1)
    emb2 = service.encode(text2)
    emb3 = service.encode(text3)

    sim_12 = service.similarity(emb1, emb2)
    sim_13 = service.similarity(emb1, emb3)

    # 相似文本的相似度应该更高
    assert sim_12 > sim_13
    assert sim_12 > 0.7
```

#### 1.3 向量存储服务开发 (3天)

**任务清单**:
- [ ] 实现 VectorStoreService 类
- [ ] 实现 upsert 方法
- [ ] 实现 search 方法
- [ ] 实现 delete 方法
- [ ] 实现批量操作
- [ ] 编写集成测试

**测试用例**:
```python
# tests/test_vector_store.py

import pytest
import numpy as np
from services.vector_store_service import VectorStoreService

@pytest.fixture
def vector_store():
    store = VectorStoreService("postgresql://localhost/nautilus_test")
    store.initialize()
    yield store
    # 清理测试数据

def test_upsert_memory(vector_store):
    embedding = np.random.rand(1024)

    memory_id = vector_store.upsert(
        agent_id=1,
        memory_type="task_execution",
        content="测试任务",
        embedding=embedding,
        metadata={"task_id": 123}
    )

    assert memory_id > 0

def test_search_memories(vector_store):
    # 插入测试数据
    embeddings = [np.random.rand(1024) for _ in range(10)]
    for i, emb in enumerate(embeddings):
        vector_store.upsert(
            agent_id=1,
            memory_type="task_execution",
            content=f"任务{i}",
            embedding=emb
        )

    # 搜索
    query_embedding = embeddings[0]
    results = vector_store.search(
        query_embedding=query_embedding,
        agent_id=1,
        top_k=5
    )

    assert len(results) <= 5
    assert results[0]["similarity"] > 0.9  # 第一个应该是自己

def test_filter_by_type(vector_store):
    # 插入不同类型的记忆
    embedding = np.random.rand(1024)

    vector_store.upsert(1, "task_execution", "任务", embedding)
    vector_store.upsert(1, "knowledge", "知识", embedding)

    # 按类型搜索
    results = vector_store.search(
        query_embedding=embedding,
        agent_id=1,
        memory_type="task_execution"
    )

    assert all(r["memory_type"] == "task_execution" for r in results)
```

**验证标准**:
- 所有单元测试通过
- 集成测试通过
- 向量搜索性能 < 100ms (1万条数据)

---

### Phase 2: 核心服务开发 (Week 2-3)

**目标**: 实现核心记忆服务

#### 2.1 Agent 记忆服务 (3天)

**任务清单**:
- [ ] 实现 AgentMemoryService 类
- [ ] 实现任务记忆存储
- [ ] 实现相似任务检索
- [ ] 实现经验统计
- [ ] 编写单元测试

**核心方法**:
```python
class AgentMemoryService:
    def remember_task_execution(agent_id, task_id, task_data)
    def recall_similar_tasks(agent_id, task_description, top_k)
    def get_agent_experience(agent_id, task_type)
    def forget_old_memories(agent_id, days)  # 清理旧记忆
```

#### 2.2 知识库服务 (2天)

**任务清单**:
- [ ] 实现 KnowledgeBaseService 类
- [ ] 实现最佳实践存储
- [ ] 实现知识检索
- [ ] 实现知识更新
- [ ] 编写测试

**核心方法**:
```python
class KnowledgeBaseService:
    def add_best_practice(task_type, practice)
    def search_knowledge(query, knowledge_type)
    def update_knowledge(knowledge_id, updates)
    def get_popular_knowledge(limit)
```

#### 2.3 上下文理解服务 (3天)

**任务清单**:
- [ ] 实现 ContextUnderstandingService 类
- [ ] 实现任务上下文构建
- [ ] 实现建议生成
- [ ] 实现上下文融合
- [ ] 编写测试

**核心方法**:
```python
class ContextUnderstandingService:
    def build_task_context(task_id)
    def generate_recommendations(context)
    def merge_contexts(contexts)
    def explain_context(context)  # 可解释性
```

---

### Phase 3: 推荐系统开发 (Week 3-4)

**目标**: 实现智能推荐功能

#### 3.1 任务推荐引擎 (3天)

**任务清单**:
- [ ] 实现 TaskRecommendationEngine 类
- [ ] 实现 Agent-Task 匹配算法
- [ ] 实现成功率预测
- [ ] 实现推荐排序
- [ ] 编写测试

**匹配算法**:
```python
def calculate_match_score(agent_profile, task):
    """
    计算 Agent-Task 匹配度

    因素:
    1. 历史成功率 (40%)
    2. 技能匹配度 (30%)
    3. 任务相似度 (20%)
    4. 奖励吸引力 (10%)
    """
    # 历史成功率
    history_score = get_success_rate(agent_id, task.task_type)

    # 技能匹配
    skill_score = calculate_skill_match(agent.specialties, task.requirements)

    # 任务相似度
    similar_tasks = recall_similar_tasks(agent_id, task.description)
    similarity_score = avg([t["similarity"] for t in similar_tasks])

    # 奖励吸引力
    reward_score = normalize_reward(task.reward)

    # 加权求和
    total_score = (
        0.4 * history_score +
        0.3 * skill_score +
        0.2 * similarity_score +
        0.1 * reward_score
    )

    return total_score
```

#### 3.2 Agent 推荐引擎 (2天)

**任务清单**:
- [ ] 实现 AgentRecommendationEngine 类
- [ ] 实现 Task-Agent 匹配算法
- [ ] 实现 Agent 排序
- [ ] 编写测试

#### 3.3 推荐 API 开发 (2天)

**任务清单**:
- [ ] 实现推荐 API 端点
- [ ] 实现推荐结果缓存
- [ ] 实现推荐解释
- [ ] 编写 API 测试

**API 端点**:
```python
# GET /api/recommendations/tasks?agent_id=1&limit=10
# 为 Agent 推荐任务

# GET /api/recommendations/agents?task_id=123&limit=5
# 为任务推荐 Agent

# POST /api/recommendations/explain
# 解释推荐理由
```

---

### Phase 4: 集成与优化 (Week 4-5)

**目标**: 集成到现有系统并优化性能

#### 4.1 Agent Engine 集成 (3天)

**任务清单**:
- [ ] 在任务执行后自动记忆
- [ ] 在任务规划时检索相似任务
- [ ] 在任务验证时更新知识库
- [ ] 集成测试

**集成点**:
```python
# agent_engine/core/engine.py

class AgentEngine:
    async def _execute_task(self, state: AgentState):
        # 执行前：检索相似任务
        similar_tasks = memory_service.recall_similar_tasks(
            self.agent_id,
            state.description
        )

        # 使用历史经验优化执行
        if similar_tasks:
            state.logs.append(f"找到 {len(similar_tasks)} 个相似任务")
            # 应用最佳实践

        # 执行任务
        result = await executor.execute(state)

        # 执行后：存储记忆
        memory_service.remember_task_execution(
            self.agent_id,
            state.task_id,
            {
                "task_type": state.task_type,
                "description": state.description,
                "strategy": state.strategy,
                "success": not state.error,
                "execution_time": execution_time,
                "lessons": extract_lessons(state)
            }
        )

        return result
```

#### 4.2 任务分配优化 (2天)

**任务清单**:
- [ ] 集成推荐引擎到任务分配
- [ ] 实现智能任务匹配
- [ ] 优化分配算法
- [ ] 性能测试

**优化后的分配流程**:
```python
async def assign_task_intelligently(task_id: int):
    """智能任务分配"""
    task = get_task(task_id)

    # 1. 获取推荐 Agent
    recommended_agents = recommendation_engine.recommend_agents_for_task(
        task_id,
        top_k=5
    )

    # 2. 检查 Agent 可用性
    available_agents = [
        agent for agent in recommended_agents
        if agent.can_accept_task()
    ]

    # 3. 选择最佳 Agent
    if available_agents:
        best_agent = available_agents[0]

        # 4. 分配任务
        await assign_task(task_id, best_agent.id)

        # 5. 提供上下文
        context = context_service.build_task_context(task_id)
        await send_context_to_agent(best_agent.id, context)

        return best_agent

    return None
```

#### 4.3 性能优化 (3天)

**任务清单**:
- [ ] 向量索引优化
- [ ] 查询性能优化
- [ ] 缓存策略实施
- [ ] 批量处理优化
- [ ] 性能基准测试

**优化目标**:
- 嵌入生成: < 50ms (单条)
- 向量搜索: < 100ms (Top-10, 10万条数据)
- 推荐生成: < 200ms
- 上下文构建: < 300ms

**优化措施**:
```python
# 1. 嵌入缓存
@lru_cache(maxsize=10000)
def get_cached_embedding(text: str):
    return embedding_service.encode(text)

# 2. 查询结果缓存
def search_with_cache(query, agent_id):
    cache_key = f"search:{agent_id}:{hash(query)}"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    results = vector_store.search(...)
    redis.setex(cache_key, 300, json.dumps(results))
    return results

# 3. 批量预加载
async def preload_agent_memories(agent_ids: List[int]):
    """预加载热门 Agent 的记忆"""
    for agent_id in agent_ids:
        memories = vector_store.get_agent_memories(agent_id)
        cache_key = f"agent_memories:{agent_id}"
        redis.setex(cache_key, 3600, json.dumps(memories))
```

---

### Phase 5: 测试与部署 (Week 5-6)

**目标**: 全面测试并部署到生产环境

#### 5.1 单元测试 (2天)

**测试覆盖率目标**: 80%+

**测试清单**:
- [ ] EmbeddingService 测试
- [ ] VectorStoreService 测试
- [ ] AgentMemoryService 测试
- [ ] KnowledgeBaseService 测试
- [ ] ContextUnderstandingService 测试
- [ ] RecommendationEngine 测试

#### 5.2 集成测试 (2天)

**测试场景**:
```python
# 场景1: 完整的任务执行流程
async def test_full_task_execution_with_memory():
    # 1. 创建任务
    task = create_task(...)

    # 2. 推荐 Agent
    agents = recommend_agents_for_task(task.id)
    assert len(agents) > 0

    # 3. 分配任务
    await assign_task(task.id, agents[0].id)

    # 4. 执行任务（会自动记忆）
    result = await execute_task(task.id)

    # 5. 验证记忆已存储
    memories = get_agent_memories(agents[0].id)
    assert any(m["metadata"]["task_id"] == task.id for m in memories)

    # 6. 检索相似任务
    similar = recall_similar_tasks(agents[0].id, task.description)
    assert len(similar) > 0

# 场景2: 知识积累和复用
async def test_knowledge_accumulation():
    # 1. 执行多个相似任务
    for i in range(5):
        task = create_similar_task(...)
        await execute_task(task.id)

    # 2. 验证知识库更新
    knowledge = search_knowledge("相似任务的最佳实践")
    assert len(knowledge) > 0

    # 3. 新任务应该受益于知识
    new_task = create_similar_task(...)
    context = build_task_context(new_task.id)
    assert len(context["recommendations"]) > 0
```

#### 5.3 性能测试 (2天)

**测试指标**:
```python
# 性能基准测试
def benchmark_memory_system():
    # 1. 嵌入生成性能
    texts = ["测试文本"] * 100
    start = time.time()
    embeddings = embedding_service.encode_batch(texts)
    duration = time.time() - start
    assert duration < 5.0  # 100条 < 5秒

    # 2. 向量搜索性能
    # 插入10万条测试数据
    insert_test_data(100000)

    query = np.random.rand(1024)
    start = time.time()
    results = vector_store.search(query, top_k=10)
    duration = time.time() - start
    assert duration < 0.1  # < 100ms

    # 3. 推荐生成性能
    start = time.time()
    recommendations = recommend_tasks_for_agent(agent_id=1)
    duration = time.time() - start
    assert duration < 0.2  # < 200ms
```

#### 5.4 部署准备 (2天)

**部署清单**:
- [ ] 编写部署文档
- [ ] 准备数据库迁移脚本
- [ ] 配置生产环境变量
- [ ] 下载并部署嵌入模型
- [ ] 配置监控和告警
- [ ] 准备回滚方案

**部署步骤**:
```bash
# 1. 备份数据库
pg_dump nautilus_phase3 > backup_$(date +%Y%m%d).sql

# 2. 安装 pgvector
sudo apt-get install postgresql-15-pgvector

# 3. 运行迁移
psql -d nautilus_phase3 -f migrations/add_memory_system.sql

# 4. 安装 Python 依赖
pip install -r requirements.txt

# 5. 下载嵌入模型
python scripts/download_embedding_model.py

# 6. 重启服务
systemctl restart nautilus-backend

# 7. 验证部署
python scripts/verify_memory_system.py
```

#### 5.5 监控配置 (1天)

**监控指标**:
```python
# Prometheus metrics
memory_system_embedding_duration = Histogram(
    'memory_embedding_duration_seconds',
    'Time spent generating embeddings'
)

memory_system_search_duration = Histogram(
    'memory_search_duration_seconds',
    'Time spent searching memories'
)

memory_system_total_memories = Gauge(
    'memory_total_memories',
    'Total number of memories stored'
)

memory_system_cache_hit_rate = Gauge(
    'memory_cache_hit_rate',
    'Cache hit rate for memory queries'
)
```

**告警规则**:
```yaml
# alerts.yml
groups:
  - name: memory_system
    rules:
      - alert: MemorySearchSlow
        expr: memory_search_duration_seconds > 0.5
        for: 5m
        annotations:
          summary: "Memory search is slow"

      - alert: EmbeddingGenerationSlow
        expr: memory_embedding_duration_seconds > 0.1
        for: 5m
        annotations:
          summary: "Embedding generation is slow"

      - alert: LowCacheHitRate
        expr: memory_cache_hit_rate < 0.5
        for: 10m
        annotations:
          summary: "Memory cache hit rate is low"
```

---

## 2. 风险管理

### 2.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| pgvector 性能不足 | 高 | 中 | 准备 Qdrant 作为备选方案 |
| 嵌入模型太大 | 中 | 低 | 使用量化模型或 API 服务 |
| 向量搜索延迟高 | 高 | 中 | 实施多级缓存策略 |
| 存储空间不足 | 中 | 低 | 实施记忆清理策略 |

### 2.2 进度风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 开发延期 | 中 | 中 | 预留 1周缓冲时间 |
| 测试不充分 | 高 | 低 | 严格执行测试计划 |
| 集成问题 | 高 | 中 | 提前进行集成测试 |

---

## 3. 成功标准

### 3.1 功能标准

- ✅ Agent 可以记住和检索历史任务
- ✅ 系统可以推荐合适的任务给 Agent
- ✅ 系统可以推荐合适的 Agent 给任务
- ✅ 知识库可以积累和检索最佳实践
- ✅ 上下文理解可以提供有价值的建议

### 3.2 性能标准

- ✅ 嵌入生成 < 50ms (单条)
- ✅ 向量搜索 < 100ms (Top-10)
- ✅ 推荐生成 < 200ms
- ✅ 系统可用性 > 99.9%

### 3.3 质量标准

- ✅ 测试覆盖率 > 80%
- ✅ 推荐准确率 > 70%
- ✅ 用户满意度 > 4.0/5.0

---

## 4. 下一步行动

### 立即开始 (本周)

1. **安装 pgvector 扩展**
   ```bash
   sudo apt-get install postgresql-15-pgvector
   ```

2. **创建数据库表**
   ```bash
   psql -d nautilus_phase3 -f migrations/add_memory_system.sql
   ```

3. **安装 Python 依赖**
   ```bash
   pip install sentence-transformers torch transformers
   ```

4. **下载嵌入模型**
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
   ```

5. **开始编写核心服务**
   - EmbeddingService
   - VectorStoreService
   - AgentMemoryService

---

**预计完成时间**: 2026-04-07 (5周后)

**关键里程碑**:
- Week 2: 基础设施完成
- Week 3: 核心服务完成
- Week 4: 推荐系统完成
- Week 5: 集成完成
- Week 6: 测试和部署完成

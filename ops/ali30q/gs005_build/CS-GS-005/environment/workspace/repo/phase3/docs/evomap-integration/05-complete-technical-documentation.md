# Nautilus 记忆系统完整技术文档

**文档版本**: 1.0.0
**创建日期**: 2026-03-03
**状态**: 最终版

---

## 目录

1. [系统概述](#1-系统概述)
2. [技术架构](#2-技术架构)
3. [核心组件](#3-核心组件)
4. [API 参考](#4-api-参考)
5. [部署指南](#5-部署指南)
6. [性能优化](#6-性能优化)
7. [监控与运维](#7-监控与运维)
8. [故障排查](#8-故障排查)

---

## 1. 系统概述

### 1.1 设计目标

Nautilus 记忆系统旨在为 AI Agent 提供：
- **长期记忆**: 持久化任务执行历史和经验
- **智能检索**: 基于语义的快速记忆检索
- **协作学习**: 跨 Agent 的知识共享
- **上下文理解**: 深度理解任务背景和关联

### 1.2 核心特性

- ✅ 向量化记忆存储 (pgvector)
- ✅ 语义相似度搜索
- ✅ Agent 协作记忆网络
- ✅ 任务知识图谱
- ✅ 技能树系统
- ✅ 增强声誉计算
- ✅ 智能推荐引擎

### 1.3 技术栈

| 组件 | 技术选型 | 版本 |
|------|---------|------|
| 向量数据库 | pgvector | 0.5.1 |
| 嵌入模型 | BGE-large-zh-v1.5 | - |
| 数据库 | PostgreSQL | 15+ |
| 缓存 | Redis | 7.0+ |
| 后端框架 | FastAPI | 0.104+ |
| Python | CPython | 3.11+ |

---

## 2. 技术架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     Nautilus Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Application Layer                      │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  Agent Engine │ Task Manager │ Recommendation     │    │
│  └────────────────────────────────────────────────────┘    │
│                         │                                    │
│                         ▼                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Memory Service Layer                      │    │
│  ├────────────────────────────────────────────────────┤    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │    │
│  │  │   Agent     │  │    Task     │  │Knowledge │  │    │
│  │  │   Memory    │  │   Memory    │  │   Base   │  │    │
│  │  └─────────────┘  └─────────────┘  └──────────┘  │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │    │
│  │  │  Context    │  │  Embedding  │  │Retrieval │  │    │
│  │  │Understanding│  │   Service   │  │  Engine  │  │    │
│  │  └─────────────┘  └─────────────┘  └──────────┘  │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │    │
│  │  │Collaborative│  │  Skill Tree │  │Reputation│  │    │
│  │  │   Memory    │  │   Service   │  │  Service │  │    │
│  │  └─────────────┘  └─────────────┘  └──────────┘  │    │
│  │                                                     │    │
│  └────────────────────────────────────────────────────┘    │
│                         │                                    │
│                         ▼                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Storage Layer                          │    │
│  ├────────────────────────────────────────────────────┤    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │    │
│  │  │    Redis    │  │ PostgreSQL  │  │ pgvector │  │    │
│  │  │(短期/缓存)   │  │(结构化数据)  │  │(向量存储) │  │    │
│  │  └─────────────┘  └─────────────┘  └──────────┘  │    │
│  │                                                     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
任务执行 → 记忆存储 → 向量化 → 索引 → 检索 → 推荐
    ↓          ↓         ↓       ↓      ↓       ↓
  执行日志   元数据    嵌入向量  向量索引 语义搜索 智能匹配
```

---

## 3. 核心组件

### 3.1 嵌入服务 (Embedding Service)

**文件**: `backend/services/embedding_service.py`

**职责**: 将文本转换为 1024 维向量

**关键方法**:
```python
class EmbeddingService:
    def encode(texts: Union[str, List[str]]) -> np.ndarray
    def encode_batch(texts: List[str], batch_size: int) -> np.ndarray
    def similarity(emb1: np.ndarray, emb2: np.ndarray) -> float
```

**性能指标**:
- 单条编码: < 50ms
- 批量编码 (100条): < 3s
- 模型加载: < 5s

### 3.2 向量存储服务 (Vector Store Service)

**文件**: `backend/services/vector_store_service.py`

**职责**: 管理向量数据的存储和检索

**关键方法**:
```python
class VectorStoreService:
    def initialize() -> None
    def upsert(agent_id, memory_type, content, embedding, metadata) -> int
    def search(query_embedding, agent_id, memory_type, top_k) -> List[Dict]
    def delete(memory_id: int) -> None
    def get_agent_memories(agent_id, memory_type, limit) -> List[Dict]
```

**数据库表结构**:
```sql
CREATE TABLE agent_memories (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance_score FLOAT DEFAULT 0.5
);
```

**索引**:
```sql
-- 向量索引 (IVFFlat)
CREATE INDEX idx_agent_memories_embedding
ON agent_memories
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 常规索引
CREATE INDEX idx_agent_memories_agent_id ON agent_memories(agent_id);
CREATE INDEX idx_agent_memories_type ON agent_memories(memory_type);
```

### 3.3 Agent 记忆服务 (Agent Memory Service)

**文件**: `backend/services/agent_memory_service.py`

**职责**: 管理 Agent 的记忆存储和检索

**关键方法**:
```python
class AgentMemoryService:
    def remember_task_execution(agent_id, task_id, task_data) -> None
    def recall_similar_tasks(agent_id, task_description, top_k) -> List[Dict]
    def get_agent_experience(agent_id, task_type) -> Dict[str, Any]
```

**使用示例**:
```python
# 记住任务执行
memory_service.remember_task_execution(
    agent_id=1,
    task_id=123,
    task_data={
        "task_type": "CODE",
        "description": "实现快速排序算法",
        "strategy": "递归分治",
        "success": True,
        "execution_time": 45.2,
        "lessons": "注意边界条件处理"
    }
)

# 回忆相似任务
similar_tasks = memory_service.recall_similar_tasks(
    agent_id=1,
    task_description="实现归并排序",
    top_k=5
)
```

### 3.4 协作记忆服务 (Collaborative Memory Service)

**文件**: `backend/services/collaborative_memory_service.py`

**职责**: 管理跨 Agent 的知识共享

**关键方法**:
```python
class CollaborativeMemoryService:
    def share_success_pattern(source_agent_id, task_id, pattern) -> None
    def learn_from_network(agent_id, task_description) -> List[Dict]
    def get_network_insights(task_type) -> Dict[str, Any]
```

### 3.5 任务知识图谱 (Task Knowledge Graph)

**文件**: `backend/services/task_knowledge_graph.py`

**职责**: 构建和分析任务关系网络

**关键方法**:
```python
class TaskKnowledgeGraph:
    def add_task_node(task_id, task_data) -> None
    def add_similarity_edge(task1_id, task2_id, similarity) -> None
    def find_task_clusters() -> List[List[int]]
    def recommend_next_tasks(completed_task_id, top_k) -> List[Tuple]
    def get_task_difficulty_score(task_id) -> float
```

### 3.6 技能树服务 (Skill Tree Service)

**文件**: `backend/services/skill_tree_service.py`

**职责**: 管理 Agent 技能成长

**关键方法**:
```python
class SkillTreeService:
    def build_skill_tree(agent_id) -> Dict[str, Any]
    def recommend_skill_path(agent_id, target_skill) -> List[str]
    def get_skill_recommendations(agent_id, top_k) -> List[Dict]
```

### 3.7 推荐引擎 (Recommendation Engine)

**文件**: `backend/services/recommendation_engine.py`

**职责**: 智能任务和 Agent 匹配

**关键方法**:
```python
class RecommendationEngine:
    def recommend_tasks_for_agent(agent_id, top_k) -> List[Task]
    def recommend_agents_for_task(task_id, top_k) -> List[Agent]
    def explain_recommendation(agent_id, task_id) -> Dict[str, Any]
```

---

## 4. API 参考

### 4.1 记忆管理 API

#### POST /api/memory/remember/task
记住任务执行

**请求**:
```json
{
  "task_id": 123,
  "task_type": "CODE",
  "description": "实现快速排序",
  "strategy": "递归分治",
  "success": true,
  "reward": 100,
  "execution_time": 45.2,
  "lessons": "注意边界条件"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Task memory stored"
}
```

#### POST /api/memory/recall/similar-tasks
回忆相似任务

**请求**:
```json
{
  "task_description": "实现归并排序",
  "top_k": 5,
  "success_only": true
}
```

**响应**:
```json
{
  "success": true,
  "memories": [
    {
      "id": 456,
      "content": "任务类型: CODE\n任务描述: 实现快速排序...",
      "metadata": {
        "task_id": 123,
        "task_type": "CODE",
        "success": true,
        "strategy": "递归分治"
      },
      "similarity": 0.87,
      "created_at": "2026-03-01T10:00:00Z"
    }
  ]
}
```

#### GET /api/memory/experience
获取经验统计

**参数**:
- `task_type` (可选): 任务类型过滤

**响应**:
```json
{
  "success": true,
  "experience": {
    "total_tasks": 100,
    "successful_tasks": 85,
    "failed_tasks": 15,
    "success_rate": 0.85,
    "average_execution_time": 45.2
  }
}
```

### 4.2 推荐 API

#### GET /api/recommendations/tasks
为 Agent 推荐任务

**参数**:
- `agent_id`: Agent ID
- `limit`: 返回数量 (默认 10)

**响应**:
```json
{
  "success": true,
  "recommendations": [
    {
      "task_id": 789,
      "title": "实现二叉搜索树",
      "task_type": "CODE",
      "reward": 150,
      "match_score": 0.92,
      "reasons": [
        "历史成功率高 (90%)",
        "技能匹配度高",
        "相似任务经验丰富"
      ]
    }
  ]
}
```

#### GET /api/recommendations/agents
为任务推荐 Agent

**参数**:
- `task_id`: 任务 ID
- `limit`: 返回数量 (默认 5)

**响应**:
```json
{
  "success": true,
  "recommendations": [
    {
      "agent_id": 1,
      "name": "CodeMaster",
      "reputation": 450,
      "match_score": 0.88,
      "success_rate": 0.92,
      "reasons": [
        "该类型任务成功率 92%",
        "相关技能等级 8",
        "最近表现优秀"
      ]
    }
  ]
}
```

### 4.3 技能树 API

#### GET /api/skills/tree
获取技能树

**参数**:
- `agent_id`: Agent ID

**响应**:
```json
{
  "success": true,
  "skill_tree": {
    "agent_id": 1,
    "skills": {
      "CODE": {
        "level": 8,
        "experience": 85,
        "success_rate": 0.92,
        "next_level_exp": 90
      },
      "DATA": {
        "level": 5,
        "experience": 45,
        "success_rate": 0.85,
        "next_level_exp": 60
      }
    },
    "total_experience": 130,
    "mastered_skills": ["CODE"]
  }
}
```

#### GET /api/skills/recommendations
获取技能推荐

**参数**:
- `agent_id`: Agent ID
- `top_k`: 返回数量 (默认 3)

**响应**:
```json
{
  "success": true,
  "recommendations": [
    {
      "skill": "CODE",
      "current_level": 8,
      "exp_needed": 5,
      "reason": "即将升级"
    },
    {
      "skill": "RESEARCH",
      "current_level": 0,
      "exp_needed": 10,
      "reason": "拓展技能范围"
    }
  ]
}
```

### 4.4 知识图谱 API

#### GET /api/knowledge-graph/clusters
获取任务聚类

**响应**:
```json
{
  "success": true,
  "clusters": [
    {
      "cluster_id": 1,
      "task_ids": [123, 456, 789],
      "common_type": "CODE",
      "avg_difficulty": 0.6
    }
  ]
}
```

#### GET /api/knowledge-graph/next-tasks
推荐下一个任务

**参数**:
- `completed_task_id`: 已完成任务 ID
- `top_k`: 返回数量 (默认 5)

**响应**:
```json
{
  "success": true,
  "next_tasks": [
    {
      "task_id": 999,
      "title": "优化排序算法",
      "relation": "similar",
      "score": 0.85
    }
  ]
}
```

---

## 5. 部署指南

### 5.1 环境要求

**硬件要求**:
- CPU: 4核+
- 内存: 8GB+
- 磁盘: 50GB+ SSD
- GPU: 可选 (加速嵌入生成)

**软件要求**:
- Ubuntu 20.04+ / CentOS 8+
- PostgreSQL 15+
- Redis 7.0+
- Python 3.11+

### 5.2 安装步骤

#### Step 1: 安装 pgvector

```bash
# Ubuntu/Debian
sudo apt-get install postgresql-15-pgvector

# 或从源码编译
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

#### Step 2: 初始化数据库

```bash
# 创建数据库
createdb nautilus_phase3

# 运行迁移
psql -d nautilus_phase3 -f migrations/add_memory_system.sql
```

#### Step 3: 安装 Python 依赖

```bash
pip install -r requirements.txt
```

**requirements.txt**:
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
sentence-transformers==2.3.1
torch==2.1.0
transformers==4.36.0
numpy==1.26.2
networkx==3.2.1
```

#### Step 4: 下载嵌入模型

```bash
python scripts/download_embedding_model.py
```

**scripts/download_embedding_model.py**:
```python
from sentence_transformers import SentenceTransformer

# 下载模型
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

# 测试
embedding = model.encode("测试文本")
print(f"模型加载成功，向量维度: {embedding.shape}")
```

#### Step 5: 配置环境变量

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost/nautilus_phase3
REDIS_URL=redis://localhost:6379/0
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

#### Step 6: 启动服务

```bash
# 开发环境
uvicorn main:app --reload --port 8000

# 生产环境
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 5.3 验证部署

```bash
# 运行验证脚本
python scripts/verify_memory_system.py
```

**scripts/verify_memory_system.py**:
```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 测试嵌入服务
response = requests.get(f"{BASE_URL}/api/health/embedding")
assert response.status_code == 200

# 2. 测试向量存储
response = requests.get(f"{BASE_URL}/api/health/vector-store")
assert response.status_code == 200

# 3. 测试记忆存储
response = requests.post(f"{BASE_URL}/api/memory/remember/task", json={
    "task_id": 1,
    "task_type": "CODE",
    "description": "测试任务",
    "success": True
})
assert response.status_code == 200

print("✅ 所有验证通过")
```

---

## 6. 性能优化

### 6.1 向量索引优化

```sql
-- 调整 IVFFlat 参数
-- lists = sqrt(总行数)
ALTER INDEX idx_agent_memories_embedding
SET (lists = 316);  -- 适用于 10万条数据

-- 查询时设置探测数
SET ivfflat.probes = 10;
```

### 6.2 查询优化

```python
# 使用连接池
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40
)
```

### 6.3 缓存策略

```python
# Redis 缓存热门查询
@lru_cache(maxsize=1000)
def get_cached_embedding(text: str):
    cache_key = f"emb:{hash(text)}"
    cached = redis.get(cache_key)
    if cached:
        return pickle.loads(cached)

    embedding = embedding_service.encode(text)
    redis.setex(cache_key, 3600, pickle.dumps(embedding))
    return embedding
```

---

## 7. 监控与运维

### 7.1 Prometheus 指标

```python
from prometheus_client import Histogram, Counter, Gauge

# 嵌入生成耗时
embedding_duration = Histogram(
    'memory_embedding_duration_seconds',
    'Time spent generating embeddings'
)

# 向量搜索耗时
search_duration = Histogram(
    'memory_search_duration_seconds',
    'Time spent searching memories'
)

# 记忆总数
total_memories = Gauge(
    'memory_total_count',
    'Total number of memories'
)

# 缓存命中率
cache_hit_rate = Gauge(
    'memory_cache_hit_rate',
    'Cache hit rate'
)
```

### 7.2 日志配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_system.log'),
        logging.StreamHandler()
    ]
)
```

---

## 8. 故障排查

### 8.1 常见问题

**问题 1: pgvector 扩展未安装**
```
ERROR: type "vector" does not exist
```
**解决**: 安装 pgvector 扩展
```bash
sudo apt-get install postgresql-15-pgvector
psql -d nautilus_phase3 -c "CREATE EXTENSION vector"
```

**问题 2: 嵌入模型加载失败**
```
OSError: Can't load model
```
**解决**: 手动下载模型
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-large-zh-v1.5')"
```

**问题 3: 向量搜索慢**
```
Query takes > 1s
```
**解决**: 优化索引参数
```sql
SET ivfflat.probes = 10;
REINDEX INDEX idx_agent_memories_embedding;
```

---

**文档完成时间**: 2026-03-03
**维护者**: Nautilus Team
**版本**: 1.0.0

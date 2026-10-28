# Nautilus 记忆系统集成架构设计

**文档版本**: 1.0.0
**创建日期**: 2026-03-03
**状态**: 设计阶段

---

## 1. 整体架构设计

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Nautilus Memory System                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    应用层 (Application Layer)              │   │
│  ├────────────────────────────────────────────────────────────┤   │
│  │  Agent Engine  │  Task Manager  │  Recommendation Engine  │   │
│  └────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                 记忆服务层 (Memory Service Layer)          │   │
│  ├────────────────────────────────────────────────────────────┤   │
│  │                                                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │ Agent Memory │  │ Task Memory  │  │  Knowledge   │    │   │
│  │  │   Service    │  │   Service    │  │    Base      │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │   │
│  │                                                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │   Context    │  │  Embedding   │  │  Retrieval   │    │   │
│  │  │  Understanding│  │   Service    │  │   Engine     │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │   │
│  │                                                             │   │
│  └────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                  存储层 (Storage Layer)                     │   │
│  ├────────────────────────────────────────────────────────────┤   │
│  │                                                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │    Redis     │  │  PostgreSQL  │  │   pgvector   │    │   │
│  │  │ (短期记忆)    │  │ (结构化数据)  │  │ (向量存储)    │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │   │
│  │                                                             │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流设计

```
任务执行流程:
┌─────────┐
│ 新任务  │
└────┬────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 1. 上下文构建                        │
│    - 检索相似历史任务                │
│    - 检索相关知识                    │
│    - 获取 Agent 历史表现             │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 2. Agent 选择                        │
│    - 计算 Agent-Task 匹配度          │
│    - 预测成功率                      │
│    - 推荐最佳 Agent                  │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 3. 任务执行                          │
│    - Agent 执行任务                  │
│    - 记录执行过程                    │
│    - 实时状态更新                    │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 4. 结果验证                          │
│    - 验证执行结果                    │
│    - 提取经验教训                    │
│    - 更新知识库                      │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 5. 记忆存储                          │
│    - 生成嵌入向量                    │
│    - 存储到向量数据库                │
│    - 更新 Agent 画像                 │
└─────────────────────────────────────┘
```

---

## 2. 核心组件设计

### 2.1 嵌入服务 (Embedding Service)

**职责**: 将文本转换为向量表示

```python
# backend/services/embedding_service.py

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """嵌入服务 - 文本向量化"""

    def __init__(self, model_name: str = "BAAI/bge-large-zh-v1.5"):
        """
        初始化嵌入服务

        Args:
            model_name: 嵌入模型名称
        """
        self.model_name = model_name
        self.model = None
        self.dimension = 1024  # BGE-large 维度

    def load_model(self):
        """加载模型"""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")

    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True
    ) -> np.ndarray:
        """
        编码文本为向量

        Args:
            texts: 单个文本或文本列表
            normalize: 是否归一化向量

        Returns:
            向量数组
        """
        self.load_model()

        # 确保输入是列表
        if isinstance(texts, str):
            texts = [texts]

        # 生成嵌入
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )

        return embeddings

    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> np.ndarray:
        """
        批量编码文本

        Args:
            texts: 文本列表
            batch_size: 批次大小

        Returns:
            向量数组
        """
        self.load_model()

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        return embeddings

    def similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        计算两个向量的相似度

        Args:
            embedding1: 向量1
            embedding2: 向量2

        Returns:
            余弦相似度 (0-1)
        """
        # 余弦相似度
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        return float(similarity)


# 全局单例
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """获取嵌入服务单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
```

### 2.2 向量存储服务 (Vector Store Service)

**职责**: 管理向量数据的存储和检索

```python
# backend/services/vector_store_service.py

from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import execute_values
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VectorStoreService:
    """向量存储服务 - 基于 pgvector"""

    def __init__(self, connection_string: str):
        """
        初始化向量存储服务

        Args:
            connection_string: PostgreSQL 连接字符串
        """
        self.connection_string = connection_string
        self.dimension = 1024  # 向量维度

    def initialize(self):
        """初始化数据库表"""
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                # 启用 pgvector 扩展
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

                # 创建记忆表
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS agent_memories (
                        id SERIAL PRIMARY KEY,
                        agent_id INTEGER NOT NULL,
                        memory_type VARCHAR(50) NOT NULL,
                        content TEXT NOT NULL,
                        embedding vector(1024),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        importance_score FLOAT DEFAULT 0.5
                    )
                """)

                # 创建索引
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_agent_memories_agent_id
                    ON agent_memories(agent_id)
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_agent_memories_type
                    ON agent_memories(memory_type)
                """)

                # 创建向量索引 (IVFFlat)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_agent_memories_embedding
                    ON agent_memories
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """)

                conn.commit()
                logger.info("Vector store initialized successfully")

    def upsert(
        self,
        agent_id: int,
        memory_type: str,
        content: str,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
        importance_score: float = 0.5
    ) -> int:
        """
        插入或更新记忆

        Args:
            agent_id: Agent ID
            memory_type: 记忆类型 (task, knowledge, experience)
            content: 记忆内容
            embedding: 嵌入向量
            metadata: 元数据
            importance_score: 重要性评分

        Returns:
            记忆 ID
        """
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO agent_memories
                    (agent_id, memory_type, content, embedding, metadata, importance_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    agent_id,
                    memory_type,
                    content,
                    embedding.tolist(),
                    metadata,
                    importance_score
                ))

                memory_id = cur.fetchone()[0]
                conn.commit()

                return memory_id

    def search(
        self,
        query_embedding: np.ndarray,
        agent_id: Optional[int] = None,
        memory_type: Optional[str] = None,
        top_k: int = 10,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        语义搜索记忆

        Args:
            query_embedding: 查询向量
            agent_id: 过滤 Agent ID
            memory_type: 过滤记忆类型
            top_k: 返回数量
            min_similarity: 最小相似度阈值

        Returns:
            记忆列表
        """
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                # 构建查询
                query = """
                    SELECT
                        id,
                        agent_id,
                        memory_type,
                        content,
                        metadata,
                        created_at,
                        importance_score,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM agent_memories
                    WHERE 1=1
                """
                params = [query_embedding.tolist()]

                if agent_id is not None:
                    query += " AND agent_id = %s"
                    params.append(agent_id)

                if memory_type is not None:
                    query += " AND memory_type = %s"
                    params.append(memory_type)

                query += """
                    AND 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                params.extend([
                    query_embedding.tolist(),
                    min_similarity,
                    query_embedding.tolist(),
                    top_k
                ])

                cur.execute(query, params)

                results = []
                for row in cur.fetchall():
                    results.append({
                        "id": row[0],
                        "agent_id": row[1],
                        "memory_type": row[2],
                        "content": row[3],
                        "metadata": row[4],
                        "created_at": row[5],
                        "importance_score": row[6],
                        "similarity": row[7]
                    })

                return results

    def delete(self, memory_id: int):
        """删除记忆"""
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM agent_memories WHERE id = %s",
                    (memory_id,)
                )
                conn.commit()

    def get_agent_memories(
        self,
        agent_id: int,
        memory_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取 Agent 的所有记忆"""
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT
                        id, memory_type, content, metadata,
                        created_at, importance_score
                    FROM agent_memories
                    WHERE agent_id = %s
                """
                params = [agent_id]

                if memory_type:
                    query += " AND memory_type = %s"
                    params.append(memory_type)

                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)

                cur.execute(query, params)

                results = []
                for row in cur.fetchall():
                    results.append({
                        "id": row[0],
                        "memory_type": row[1],
                        "content": row[2],
                        "metadata": row[3],
                        "created_at": row[4],
                        "importance_score": row[5]
                    })

                return results


# 全局单例
_vector_store = None


def get_vector_store() -> VectorStoreService:
    """获取向量存储服务单例"""
    global _vector_store
    if _vector_store is None:
        from config import DATABASE_URL
        _vector_store = VectorStoreService(DATABASE_URL)
        _vector_store.initialize()
    return _vector_store
```

### 2.3 Agent 记忆服务 (Agent Memory Service)

**职责**: 管理 Agent 的记忆存储和检索

```python
# backend/services/agent_memory_service.py

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .embedding_service import get_embedding_service
from .vector_store_service import get_vector_store

logger = logging.getLogger(__name__)


class AgentMemoryService:
    """Agent 记忆服务"""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()

    def remember_task_execution(
        self,
        agent_id: int,
        task_id: int,
        task_data: Dict[str, Any]
    ):
        """
        记住任务执行

        Args:
            agent_id: Agent ID
            task_id: Task ID
            task_data: 任务数据
        """
        # 构建记忆内容
        content = self._build_task_memory_content(task_data)

        # 生成嵌入
        embedding = self.embedding_service.encode(content)

        # 计算重要性
        importance = self._calculate_importance(task_data)

        # 存储记忆
        memory_id = self.vector_store.upsert(
            agent_id=agent_id,
            memory_type="task_execution",
            content=content,
            embedding=embedding,
            metadata={
                "task_id": task_id,
                "task_type": task_data.get("task_type"),
                "success": task_data.get("success"),
                "reward": task_data.get("reward"),
                "execution_time": task_data.get("execution_time"),
                "strategy": task_data.get("strategy")
            },
            importance_score=importance
        )

        logger.info(f"Stored task execution memory {memory_id} for agent {agent_id}")

    def recall_similar_tasks(
        self,
        agent_id: int,
        task_description: str,
        top_k: int = 5,
        success_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        回忆相似任务

        Args:
            agent_id: Agent ID
            task_description: 任务描述
            top_k: 返回数量
            success_only: 只返回成功案例

        Returns:
            相似任务列表
        """
        # 生成查询向量
        query_embedding = self.embedding_service.encode(task_description)

        # 搜索相似记忆
        memories = self.vector_store.search(
            query_embedding=query_embedding,
            agent_id=agent_id,
            memory_type="task_execution",
            top_k=top_k * 2  # 多取一些，后续过滤
        )

        # 过滤成功案例
        if success_only:
            memories = [
                m for m in memories
                if m["metadata"].get("success", False)
            ]

        return memories[:top_k]

    def get_agent_experience(
        self,
        agent_id: int,
        task_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取 Agent 经验统计

        Args:
            agent_id: Agent ID
            task_type: 任务类型过滤

        Returns:
            经验统计
        """
        # 获取所有任务记忆
        memories = self.vector_store.get_agent_memories(
            agent_id=agent_id,
            memory_type="task_execution"
        )

        # 过滤任务类型
        if task_type:
            memories = [
                m for m in memories
                if m["metadata"].get("task_type") == task_type
            ]

        # 统计
        total = len(memories)
        successful = sum(
            1 for m in memories
            if m["metadata"].get("success", False)
        )

        # 计算平均执行时间
        execution_times = [
            m["metadata"].get("execution_time", 0)
            for m in memories
            if m["metadata"].get("execution_time")
        ]
        avg_execution_time = (
            sum(execution_times) / len(execution_times)
            if execution_times else 0
        )

        return {
            "total_tasks": total,
            "successful_tasks": successful,
            "failed_tasks": total - successful,
            "success_rate": successful / total if total > 0 else 0,
            "average_execution_time": avg_execution_time
        }

    def _build_task_memory_content(self, task_data: Dict[str, Any]) -> str:
        """构建任务记忆内容"""
        parts = [
            f"任务类型: {task_data.get('task_type', 'Unknown')}",
            f"任务描述: {task_data.get('description', '')}",
            f"执行策略: {task_data.get('strategy', '')}",
            f"执行结果: {'成功' if task_data.get('success') else '失败'}",
        ]

        if task_data.get("lessons"):
            parts.append(f"经验教训: {task_data['lessons']}")

        return "\n".join(parts)

    def _calculate_importance(self, task_data: Dict[str, Any]) -> float:
        """计算记忆重要性"""
        importance = 0.5  # 基础分

        # 成功任务更重要
        if task_data.get("success"):
            importance += 0.2

        # 高奖励任务更重要
        reward = task_data.get("reward", 0)
        if reward > 100:
            importance += 0.1

        # 有经验教训的更重要
        if task_data.get("lessons"):
            importance += 0.2

        return min(importance, 1.0)


# 全局单例
_agent_memory_service = None


def get_agent_memory_service() -> AgentMemoryService:
    """获取 Agent 记忆服务单例"""
    global _agent_memory_service
    if _agent_memory_service is None:
        _agent_memory_service = AgentMemoryService()
    return _agent_memory_service
```

---

## 3. API 设计

### 3.1 记忆管理 API

```python
# backend/api/memory.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from services.agent_memory_service import get_agent_memory_service
from auth import get_current_agent

router = APIRouter(prefix="/api/memory", tags=["memory"])


class TaskMemoryRequest(BaseModel):
    """任务记忆请求"""
    task_id: int
    task_type: str
    description: str
    strategy: str
    success: bool
    reward: float
    execution_time: float
    lessons: Optional[str] = None


class RecallRequest(BaseModel):
    """回忆请求"""
    task_description: str
    top_k: int = 5
    success_only: bool = True


@router.post("/remember/task")
async def remember_task(
    request: TaskMemoryRequest,
    agent_id: int = Depends(get_current_agent)
):
    """记住任务执行"""
    memory_service = get_agent_memory_service()

    memory_service.remember_task_execution(
        agent_id=agent_id,
        task_id=request.task_id,
        task_data=request.dict()
    )

    return {"success": True, "message": "Task memory stored"}


@router.post("/recall/similar-tasks")
async def recall_similar_tasks(
    request: RecallRequest,
    agent_id: int = Depends(get_current_agent)
):
    """回忆相似任务"""
    memory_service = get_agent_memory_service()

    memories = memory_service.recall_similar_tasks(
        agent_id=agent_id,
        task_description=request.task_description,
        top_k=request.top_k,
        success_only=request.success_only
    )

    return {
        "success": True,
        "memories": memories
    }


@router.get("/experience")
async def get_experience(
    task_type: Optional[str] = None,
    agent_id: int = Depends(get_current_agent)
):
    """获取经验统计"""
    memory_service = get_agent_memory_service()

    experience = memory_service.get_agent_experience(
        agent_id=agent_id,
        task_type=task_type
    )

    return {
        "success": True,
        "experience": experience
    }
```

---

## 4. 数据库 Schema 扩展

### 4.1 pgvector 扩展安装

```sql
-- 安装 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建记忆表
CREATE TABLE agent_memories (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(agent_id),
    memory_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance_score FLOAT DEFAULT 0.5,

    -- 索引
    INDEX idx_agent_memories_agent_id (agent_id),
    INDEX idx_agent_memories_type (memory_type),
    INDEX idx_agent_memories_created (created_at DESC)
);

-- 创建向量索引 (IVFFlat 算法)
CREATE INDEX idx_agent_memories_embedding
ON agent_memories
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 创建知识库表
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    knowledge_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_knowledge_type (knowledge_type),
    INDEX idx_knowledge_created (created_at DESC)
);

-- 创建向量索引
CREATE INDEX idx_knowledge_embedding
ON knowledge_base
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);
```

---

## 5. 性能优化

### 5.1 向量索引优化

**IVFFlat 参数调优**:
- `lists`: 聚类数量，建议为 `sqrt(总行数)`
- 对于 10万条记忆，设置 `lists = 316`
- 对于 100万条记忆，设置 `lists = 1000`

**查询优化**:
```sql
-- 设置探测列表数量
SET ivfflat.probes = 10;

-- 查询时使用索引
SELECT * FROM agent_memories
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

### 5.2 缓存策略

**Redis 缓存热门查询**:
```python
def recall_with_cache(agent_id: int, query: str):
    # 生成缓存键
    cache_key = f"recall:{agent_id}:{hash(query)}"

    # 检查缓存
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # 执行查询
    results = vector_store.search(...)

    # 缓存结果 (5分钟)
    redis.setex(cache_key, 300, json.dumps(results))

    return results
```

### 5.3 批量处理

**批量嵌入生成**:
```python
def batch_remember_tasks(agent_id: int, tasks: List[Dict]):
    # 批量生成嵌入
    contents = [build_content(task) for task in tasks]
    embeddings = embedding_service.encode_batch(contents)

    # 批量插入
    for task, embedding in zip(tasks, embeddings):
        vector_store.upsert(agent_id, task, embedding)
```

---

下一步将设计具体的实施路线图和测试方案。

# Epiplexity 基础架构设计

**版本**: 1.0
**日期**: 2024-03-07
**状态**: 设计阶段

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     应用层 (Week 4)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 智能任务推荐 │  │ Agent进化    │  │ 知识价值评估 │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Epiplexity服务层 (Week 3)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Epiplexity   │  │ 知识节点     │  │ 知识图谱     │      │
│  │ 计算服务     │  │ 管理服务     │  │ 查询服务     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据层 (Week 3)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Epiplexity   │  │ Knowledge    │  │ Agent/Task   │      │
│  │ Measure      │  │ Node         │  │ 扩展字段     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   现有系统 (Week 1-2)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 生存机制     │  │ 反作弊系统   │  │ 任务系统     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 数据模型详细设计

### 1. EpiplexityMeasure (Epiplexity测量)

```python
class EpiplexityMeasure(Base):
    """Epiplexity测量记录"""
    __tablename__ = "epiplexity_measures"

    id = Column(Integer, primary_key=True)

    # 关联实体
    entity_type = Column(String(20), nullable=False, index=True)  # TASK, AGENT, KNOWLEDGE_NODE
    entity_id = Column(Integer, nullable=False, index=True)

    # 三个核心维度
    structural_complexity = Column(Float, nullable=False)  # 结构复杂性 (0.0-1.0)
    learnable_content = Column(Float, nullable=False)      # 可学习内容 (0.0-1.0)
    transferability = Column(Float, nullable=False)        # 可迁移性 (0.0-1.0)

    # 综合评分
    epiplexity_score = Column(Float, nullable=False, index=True)  # 综合Epiplexity评分

    # 详细分析 (JSON)
    analysis_details = Column(JSON, nullable=True)  # 详细分析结果

    # 元数据
    calculated_by = Column(String(50), nullable=True)  # 计算方法/模型
    confidence = Column(Float, nullable=True)  # 置信度

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index('idx_epiplexity_entity', 'entity_type', 'entity_id'),
        Index('idx_epiplexity_score', 'epiplexity_score'),
    )
```

### 2. KnowledgeNode (知识节点)

```python
class KnowledgeNode(Base):
    """知识节点 - 知识图谱的基本单元"""
    __tablename__ = "knowledge_nodes"

    id = Column(Integer, primary_key=True)

    # 内容
    content = Column(Text, nullable=False)  # 知识内容
    content_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA256哈希
    content_type = Column(String(50), nullable=False)  # CODE, CONCEPT, PATTERN, SOLUTION

    # Epiplexity指标
    epiplexity = Column(Float, nullable=False, index=True)  # Epiplexity评分
    learnability = Column(Float, nullable=False)  # 可学习性
    transferability = Column(Float, nullable=False)  # 可迁移性
    complexity_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH

    # 来源
    source_task_id = Column(Integer, ForeignKey("tasks.task_id"), nullable=True)
    created_by_agent_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=False)

    # 使用统计
    usage_count = Column(Integer, default=0)  # 被使用次数
    transfer_count = Column(Integer, default=0)  # 被迁移次数
    success_rate = Column(Float, default=0.0)  # 成功率

    # 关系
    parent_nodes = Column(JSON, nullable=True)  # 父节点ID列表
    child_nodes = Column(JSON, nullable=True)  # 子节点ID列表
    related_nodes = Column(JSON, nullable=True)  # 相关节点ID列表

    # 标签和分类
    tags = Column(JSON, nullable=True)  # 标签列表
    category = Column(String(50), nullable=True)  # 分类

    # 质量评分
    quality_score = Column(Float, default=0.0)  # 质量评分
    verified = Column(Boolean, default=False)  # 是否已验证

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # 索引
    __table_args__ = (
        Index('idx_knowledge_epiplexity', 'epiplexity'),
        Index('idx_knowledge_creator', 'created_by_agent_id'),
        Index('idx_knowledge_source', 'source_task_id'),
        Index('idx_knowledge_type', 'content_type'),
    )
```

### 3. KnowledgeTransfer (知识迁移记录)

```python
class KnowledgeTransfer(Base):
    """知识迁移记录"""
    __tablename__ = "knowledge_transfers"

    id = Column(Integer, primary_key=True)

    # 知识节点
    knowledge_node_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=False)

    # 迁移信息
    from_task_id = Column(Integer, ForeignKey("tasks.task_id"), nullable=True)
    to_task_id = Column(Integer, ForeignKey("tasks.task_id"), nullable=False)
    transferred_by_agent_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=False)

    # 迁移结果
    success = Column(Boolean, nullable=False)  # 是否成功
    adaptation_required = Column(Boolean, default=False)  # 是否需要适配
    adaptation_details = Column(JSON, nullable=True)  # 适配详情

    # 价值评估
    value_created = Column(Float, nullable=True)  # 创造的价值
    time_saved = Column(Float, nullable=True)  # 节省的时间

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index('idx_transfer_knowledge', 'knowledge_node_id'),
        Index('idx_transfer_agent', 'transferred_by_agent_id'),
    )
```

### 4. Agent扩展字段

```python
# 在现有Agent模型中添加
class Agent(Base):
    # ... 现有字段 ...

    # Epiplexity相关字段
    learning_capacity = Column(Float, default=0.5)  # 学习能力 (0.0-1.0)
    knowledge_growth_rate = Column(Float, default=0.0)  # 知识增长率
    total_knowledge_epiplexity = Column(Float, default=0.0)  # 总知识复杂性
    knowledge_nodes_created = Column(Integer, default=0)  # 创建的知识节点数
    knowledge_transfers_count = Column(Integer, default=0)  # 知识迁移次数
    specialization_areas = Column(JSON, nullable=True)  # 专业领域

    # 学习统计
    learning_sessions = Column(Integer, default=0)  # 学习会话数
    avg_learning_speed = Column(Float, default=0.0)  # 平均学习速度
    knowledge_retention_rate = Column(Float, default=0.0)  # 知识保留率
```

### 5. Task扩展字段

```python
# 在现有Task模型中添加
class Task(Base):
    # ... 现有字段 ...

    # Epiplexity相关字段
    epiplexity_score = Column(Float, nullable=True, index=True)  # Epiplexity评分
    structural_complexity = Column(Float, nullable=True)  # 结构复杂性
    learnability_score = Column(Float, nullable=True)  # 可学习性评分
    knowledge_density = Column(Float, nullable=True)  # 知识密度

    # 知识关联
    knowledge_nodes = Column(JSON, nullable=True)  # 关联的知识节点ID列表
    required_knowledge = Column(JSON, nullable=True)  # 需要的前置知识
    creates_knowledge = Column(Boolean, default=False)  # 是否创造新知识

    # 学习价值
    learning_value = Column(Float, nullable=True)  # 学习价值
    skill_requirements = Column(JSON, nullable=True)  # 技能要求
```

---

## 服务层设计

### 1. EpiplexityService (Epiplexity计算服务)

```python
class EpiplexityService:
    """Epiplexity计算服务"""

    @staticmethod
    def calculate_epiplexity(
        content: str,
        content_type: str,
        context: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        计算Epiplexity评分

        返回:
        {
            "structural_complexity": 0.75,
            "learnable_content": 0.82,
            "transferability": 0.68,
            "epiplexity_score": 0.75
        }
        """
        pass

    @staticmethod
    def analyze_structural_complexity(content: str) -> float:
        """分析结构复杂性"""
        pass

    @staticmethod
    def analyze_learnable_content(content: str) -> float:
        """分析可学习内容"""
        pass

    @staticmethod
    def analyze_transferability(content: str, context: Dict) -> float:
        """分析可迁移性"""
        pass
```

### 2. KnowledgeNodeService (知识节点服务)

```python
class KnowledgeNodeService:
    """知识节点管理服务"""

    @staticmethod
    def create_knowledge_node(
        content: str,
        content_type: str,
        source_task_id: int,
        created_by_agent_id: int
    ) -> KnowledgeNode:
        """创建知识节点"""
        pass

    @staticmethod
    def extract_knowledge_from_task(task_id: int) -> List[KnowledgeNode]:
        """从任务中提取知识"""
        pass

    @staticmethod
    def find_similar_knowledge(
        content: str,
        threshold: float = 0.8
    ) -> List[KnowledgeNode]:
        """查找相似知识"""
        pass

    @staticmethod
    def transfer_knowledge(
        knowledge_node_id: int,
        to_task_id: int,
        agent_id: int
    ) -> KnowledgeTransfer:
        """迁移知识"""
        pass
```

### 3. KnowledgeGraphService (知识图谱服务)

```python
class KnowledgeGraphService:
    """知识图谱查询服务"""

    @staticmethod
    def get_agent_knowledge_graph(agent_id: int) -> Dict:
        """获取Agent的知识图谱"""
        pass

    @staticmethod
    def find_learning_path(
        agent_id: int,
        target_skill: str
    ) -> List[KnowledgeNode]:
        """查找学习路径"""
        pass

    @staticmethod
    def recommend_next_knowledge(
        agent_id: int,
        limit: int = 5
    ) -> List[KnowledgeNode]:
        """推荐下一个学习内容"""
        pass
```

---

## API接口设计

### Epiplexity测量

```python
POST /api/epiplexity/measure
Body: {
    "entity_type": "TASK",
    "entity_id": 123,
    "content": "...",
    "context": {...}
}
Response: {
    "success": true,
    "data": {
        "structural_complexity": 0.75,
        "learnable_content": 0.82,
        "transferability": 0.68,
        "epiplexity_score": 0.75,
        "analysis_details": {...}
    }
}

GET /api/epiplexity/measures/{entity_type}/{entity_id}
```

### 知识节点

```python
POST /api/knowledge/nodes
Body: {
    "content": "...",
    "content_type": "CODE",
    "source_task_id": 123,
    "created_by_agent_id": 1
}

GET /api/knowledge/nodes/{id}
GET /api/knowledge/nodes?agent_id=1&limit=10
GET /api/agents/{id}/knowledge-graph
```

### 知识迁移

```python
POST /api/knowledge/transfer
Body: {
    "knowledge_node_id": 1,
    "to_task_id": 456,
    "agent_id": 1
}

GET /api/knowledge/transfers?agent_id=1
```

---

## 计算算法

### Epiplexity计算

```python
def calculate_epiplexity(content: str) -> float:
    """
    Epiplexity = f(structural_complexity, learnable_content, transferability)

    使用加权几何平均:
    epiplexity = (SC^0.4 × LC^0.4 × T^0.2)
    """
    sc = analyze_structural_complexity(content)
    lc = analyze_learnable_content(content)
    t = analyze_transferability(content)

    epiplexity = (sc ** 0.4) * (lc ** 0.4) * (t ** 0.2)
    return epiplexity
```

### 结构复杂性分析

```python
def analyze_structural_complexity(content: str) -> float:
    """
    分析结构复杂性

    因素:
    - 嵌套深度
    - 依赖关系数量
    - 模式复杂度
    - 抽象层次
    """
    # 使用AST分析代码结构
    # 或使用NLP分析文本结构
    pass
```

### 可学习内容分析

```python
def analyze_learnable_content(content: str) -> float:
    """
    分析可学习内容

    因素:
    - 新概念数量
    - 知识密度
    - 信息熵
    - 可理解性
    """
    # 使用LLM分析内容
    # 提取关键概念
    # 计算知识密度
    pass
```

---

## 集成策略

### Phase 1: 数据层 (Week 3 Day 1-2)
1. 创建新表migration
2. 扩展现有表
3. 数据模型实现

### Phase 2: 服务层 (Week 3 Day 3-4)
1. EpiplexityService实现
2. KnowledgeNodeService实现
3. 基础算法实现

### Phase 3: API层 (Week 3 Day 5)
1. API接口实现
2. 测试和文档

### Phase 4: 应用集成 (Week 4)
1. 评分系统升级
2. 任务推荐优化
3. Agent进化机制

---

## 性能优化

### 缓存策略
- Epiplexity计算结果缓存
- 知识图谱查询缓存
- 相似度计算缓存

### 异步处理
- Epiplexity计算异步
- 知识提取异步
- 图谱更新异步

### 索引优化
- epiplexity_score索引
- content_hash唯一索引
- 复合索引优化

---

## 监控指标

### 系统指标
- Epiplexity计算耗时
- 知识节点创建速率
- 知识迁移成功率

### 业务指标
- 平均Epiplexity评分
- 知识节点数量增长
- Agent学习能力提升

---

**下一步**: 完成Week 2 Phase 2后，开始实施Week 3计划

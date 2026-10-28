"""
Epiplexity数据模型
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib
from models.database import Base


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

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "structural_complexity": self.structural_complexity,
            "learnable_content": self.learnable_content,
            "transferability": self.transferability,
            "epiplexity_score": self.epiplexity_score,
            "analysis_details": self.analysis_details,
            "calculated_by": self.calculated_by,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


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
    source_task_id = Column(Integer, nullable=True)
    created_by_agent_id = Column(Integer, ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)

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

    # 关系
    creator = relationship("Agent", foreign_keys=[created_by_agent_id])

    def calculate_hash(self):
        """计算内容哈希"""
        return hashlib.sha256(self.content.encode('utf-8')).hexdigest()

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "content_hash": self.content_hash,
            "content_type": self.content_type,
            "epiplexity": self.epiplexity,
            "learnability": self.learnability,
            "transferability": self.transferability,
            "complexity_level": self.complexity_level,
            "source_task_id": self.source_task_id,
            "created_by_agent_id": self.created_by_agent_id,
            "usage_count": self.usage_count,
            "transfer_count": self.transfer_count,
            "success_rate": self.success_rate,
            "parent_nodes": self.parent_nodes,
            "child_nodes": self.child_nodes,
            "related_nodes": self.related_nodes,
            "tags": self.tags,
            "category": self.category,
            "quality_score": self.quality_score,
            "verified": self.verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }


class KnowledgeTransfer(Base):
    """知识迁移记录"""
    __tablename__ = "knowledge_transfers"

    id = Column(Integer, primary_key=True)

    # 知识节点
    knowledge_node_id = Column(Integer, ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False)

    # 迁移信息
    from_task_id = Column(Integer, nullable=True)
    to_task_id = Column(Integer, nullable=False)
    transferred_by_agent_id = Column(Integer, ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)

    # 迁移结果
    success = Column(Boolean, nullable=False)  # 是否成功
    adaptation_required = Column(Boolean, default=False)  # 是否需要适配
    adaptation_details = Column(JSON, nullable=True)  # 适配详情

    # 价值评估
    value_created = Column(Float, nullable=True)  # 创造的价值
    time_saved = Column(Float, nullable=True)  # 节省的时间

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    knowledge_node = relationship("KnowledgeNode", foreign_keys=[knowledge_node_id])
    transferred_by = relationship("Agent", foreign_keys=[transferred_by_agent_id])

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "knowledge_node_id": self.knowledge_node_id,
            "from_task_id": self.from_task_id,
            "to_task_id": self.to_task_id,
            "transferred_by_agent_id": self.transferred_by_agent_id,
            "success": self.success,
            "adaptation_required": self.adaptation_required,
            "adaptation_details": self.adaptation_details,
            "value_created": self.value_created,
            "time_saved": self.time_saved,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

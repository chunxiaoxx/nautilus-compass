"""
涌现模式数据模型
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class EmergentPattern(Base):
    """
    涌现模式 - 知识组合产生的新模式

    论文观点：似然建模创造复杂性
    - 知识组合 > 知识相加
    - 涌现因子 > 1.2 表示真正的涌现
    """
    __tablename__ = "emergent_patterns"

    id = Column(Integer, primary_key=True)

    # 基本信息
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    pattern_type = Column(String(50), nullable=False)  # DESIGN, ALGORITHM, ARCHITECTURE, HYBRID

    # 来源知识节点
    source_knowledge_ids = Column(JSON, nullable=False)  # 源知识节点ID列表
    knowledge_count = Column(Integer, nullable=False)  # 组合的知识数量

    # Epiplexity指标
    combined_epiplexity = Column(Float, nullable=False, index=True)  # 组合后的Epiplexity
    individual_sum = Column(Float, nullable=False)  # 各部分Epiplexity之和
    emergence_factor = Column(Float, nullable=False, index=True)  # 涌现因子 = combined / individual_sum

    # 涌现特征
    is_emergent = Column(Boolean, nullable=False, default=False)  # 是否真正涌现
    novelty_score = Column(Float, nullable=True)  # 新颖性评分
    complexity_increase = Column(Float, nullable=True)  # 复杂度增加

    # 组合内容
    combined_content = Column(Text, nullable=True)  # 组合后的内容
    combination_method = Column(String(50), nullable=True)  # 组合方法

    # 创建者
    discovered_by_agent_id = Column(Integer, ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)

    # 应用统计
    applied_count = Column(Integer, default=0)  # 被应用次数
    success_rate = Column(Float, default=0.0)  # 应用成功率
    value_created = Column(Float, default=0.0)  # 创造的价值

    # 验证状态
    verified = Column(Boolean, default=False)  # 是否已验证
    quality_score = Column(Float, default=0.0)  # 质量评分

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_applied_at = Column(DateTime, nullable=True)

    # 关系
    discoverer = relationship("Agent", foreign_keys=[discovered_by_agent_id])

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "pattern_type": self.pattern_type,
            "source_knowledge_ids": self.source_knowledge_ids,
            "knowledge_count": self.knowledge_count,
            "combined_epiplexity": self.combined_epiplexity,
            "individual_sum": self.individual_sum,
            "emergence_factor": self.emergence_factor,
            "is_emergent": self.is_emergent,
            "novelty_score": self.novelty_score,
            "complexity_increase": self.complexity_increase,
            "combined_content": self.combined_content,
            "combination_method": self.combination_method,
            "discovered_by_agent_id": self.discovered_by_agent_id,
            "applied_count": self.applied_count,
            "success_rate": self.success_rate,
            "value_created": self.value_created,
            "verified": self.verified,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_applied_at": self.last_applied_at.isoformat() if self.last_applied_at else None
        }


class KnowledgeCombination(Base):
    """
    知识组合记录 - 记录知识节点的组合尝试
    """
    __tablename__ = "knowledge_combinations"

    id = Column(Integer, primary_key=True)

    # 组合的知识节点
    knowledge_node_ids = Column(JSON, nullable=False)  # 知识节点ID列表
    combination_size = Column(Integer, nullable=False)  # 组合大小

    # 组合结果
    success = Column(Boolean, nullable=False)  # 是否成功组合
    emergent_pattern_id = Column(Integer, ForeignKey("emergent_patterns.id", ondelete="SET NULL"), nullable=True)

    # 组合分析
    compatibility_score = Column(Float, nullable=True)  # 兼容性评分
    synergy_score = Column(Float, nullable=True)  # 协同效应评分

    # 执行者
    attempted_by_agent_id = Column(Integer, ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    emergent_pattern = relationship("EmergentPattern", foreign_keys=[emergent_pattern_id])
    attempted_by = relationship("Agent", foreign_keys=[attempted_by_agent_id])

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "knowledge_node_ids": self.knowledge_node_ids,
            "combination_size": self.combination_size,
            "success": self.success,
            "emergent_pattern_id": self.emergent_pattern_id,
            "compatibility_score": self.compatibility_score,
            "synergy_score": self.synergy_score,
            "attempted_by_agent_id": self.attempted_by_agent_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

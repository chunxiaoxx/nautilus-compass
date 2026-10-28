"""
能力胶囊数据模型

能力胶囊封装可复用的结构化知识，是多个知识节点的组合。
核心理念：信息依赖于数据顺序（Information depends on the order of data）
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class CapabilityCapsule(Base):
    """能力胶囊 - 封装可复用的结构化知识"""
    __tablename__ = "capability_capsules"

    id = Column(Integer, primary_key=True)

    # 基本信息
    name = Column(String(200), nullable=False)  # 能力名称
    description = Column(Text, nullable=True)  # 能力描述
    pattern_type = Column(String(50), nullable=False)  # 模式类型: ALGORITHM, DESIGN_PATTERN, WORKFLOW, etc.

    # 知识节点组合（顺序很重要！）
    knowledge_node_ids = Column(JSON, nullable=False)  # 知识节点ID列表（有序）

    # Epiplexity指标
    epiplexity = Column(Float, nullable=False, index=True)  # 综合Epiplexity评分
    complexity_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH

    # 代码模板
    code_template = Column(Text, nullable=True)  # 代码模板
    template_variables = Column(JSON, nullable=True)  # 模板变量定义

    # 前置条件（顺序依赖）
    prerequisites = Column(JSON, nullable=True)  # 前置条件列表
    required_skills = Column(JSON, nullable=True)  # 所需技能列表

    # 应用场景
    applicable_contexts = Column(JSON, nullable=True)  # 适用场景列表
    tags = Column(JSON, nullable=True)  # 标签
    category = Column(String(50), nullable=True)  # 分类

    # 创建者
    created_by_agent_id = Column(Integer, ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)

    # 使用统计
    usage_count = Column(Integer, default=0)  # 使用次数
    transfer_count = Column(Integer, default=0)  # 迁移次数
    success_rate = Column(Float, default=0.0)  # 成功率
    avg_adaptation_effort = Column(Float, default=0.0)  # 平均适配工作量

    # 质量评分
    quality_score = Column(Float, default=0.0)  # 质量评分
    verified = Column(Boolean, default=False)  # 是否已验证

    # 版本控制
    version = Column(String(20), default="1.0.0")  # 版本号
    parent_capsule_id = Column(Integer, ForeignKey("capability_capsules.id", ondelete="SET NULL"), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # 关系
    creator = relationship("Agent", foreign_keys=[created_by_agent_id])
    parent_capsule = relationship("CapabilityCapsule", remote_side=[id], foreign_keys=[parent_capsule_id])

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "pattern_type": self.pattern_type,
            "knowledge_node_ids": self.knowledge_node_ids,
            "epiplexity": self.epiplexity,
            "complexity_level": self.complexity_level,
            "code_template": self.code_template,
            "template_variables": self.template_variables,
            "prerequisites": self.prerequisites,
            "required_skills": self.required_skills,
            "applicable_contexts": self.applicable_contexts,
            "tags": self.tags,
            "category": self.category,
            "created_by_agent_id": self.created_by_agent_id,
            "usage_count": self.usage_count,
            "transfer_count": self.transfer_count,
            "success_rate": self.success_rate,
            "avg_adaptation_effort": self.avg_adaptation_effort,
            "quality_score": self.quality_score,
            "verified": self.verified,
            "version": self.version,
            "parent_capsule_id": self.parent_capsule_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }


class CapsuleTransfer(Base):
    """能力胶囊迁移记录"""
    __tablename__ = "capsule_transfers"

    id = Column(Integer, primary_key=True)

    # 能力胶囊
    capsule_id = Column(Integer, ForeignKey("capability_capsules.id", ondelete="CASCADE"), nullable=False)

    # 迁移信息
    from_context = Column(String(200), nullable=True)  # 源场景
    to_context = Column(String(200), nullable=False)  # 目标场景
    transferred_by_agent_id = Column(Integer, ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)

    # 前置条件检查
    prerequisites_met = Column(Boolean, nullable=False)  # 前置条件是否满足
    missing_prerequisites = Column(JSON, nullable=True)  # 缺失的前置条件

    # 适配度评估
    adaptation_score = Column(Float, nullable=False)  # 适配度评分 (0.0-1.0)
    adaptation_required = Column(Boolean, default=False)  # 是否需要适配
    adaptation_details = Column(JSON, nullable=True)  # 适配详情
    adaptation_effort = Column(Float, nullable=True)  # 适配工作量（小时）

    # 迁移结果
    success = Column(Boolean, nullable=False)  # 是否成功
    failure_reason = Column(Text, nullable=True)  # 失败原因

    # 价值评估
    value_created = Column(Float, nullable=True)  # 创造的价值
    time_saved = Column(Float, nullable=True)  # 节省的时间（小时）

    # 反馈
    feedback = Column(Text, nullable=True)  # 使用反馈
    rating = Column(Integer, nullable=True)  # 评分 (1-5)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 关系
    capsule = relationship("CapabilityCapsule", foreign_keys=[capsule_id])
    transferred_by = relationship("Agent", foreign_keys=[transferred_by_agent_id])

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "capsule_id": self.capsule_id,
            "from_context": self.from_context,
            "to_context": self.to_context,
            "transferred_by_agent_id": self.transferred_by_agent_id,
            "prerequisites_met": self.prerequisites_met,
            "missing_prerequisites": self.missing_prerequisites,
            "adaptation_score": self.adaptation_score,
            "adaptation_required": self.adaptation_required,
            "adaptation_details": self.adaptation_details,
            "adaptation_effort": self.adaptation_effort,
            "success": self.success,
            "failure_reason": self.failure_reason,
            "value_created": self.value_created,
            "time_saved": self.time_saved,
            "feedback": self.feedback,
            "rating": self.rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

"""
Marketplace models: Skill Market, Tool Registry, Agent Messages.

- AgentSkill: Skills/capabilities an agent offers for hire
- AgentTool: API endpoints/tools an agent exposes
- AgentMessage: Direct messages between agents (A2A channel)
"""
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    Enum as SAEnum, Index, ForeignKey
)
from sqlalchemy.orm import relationship
from utils.database import Base


class SkillStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DEPRECATED = "deprecated"


class AgentSkill(Base):
    """
    A skill/capability that an agent offers on the marketplace.
    Compatible with ACP SKILL.md format.
    """
    __tablename__ = "agent_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=False, index=True)

    # Core skill info
    name = Column(String(200), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    task_type = Column(String(100), nullable=False, index=True)

    # Pricing
    price_usdc = Column(Float, default=0.0, nullable=False)
    price_nau = Column(Float, default=0.0, nullable=False)

    # Quality signals
    total_hires = Column(Integer, default=0, nullable=False)
    avg_rating = Column(Float, default=0.0, nullable=False)
    success_rate = Column(Float, default=1.0, nullable=False)

    # ACP compatibility
    acp_skill_hash = Column(String(64), nullable=True)  # SHA256 of SKILL.md
    input_schema = Column(Text, nullable=True)   # JSON schema
    output_schema = Column(Text, nullable=True)  # JSON schema
    example_input = Column(Text, nullable=True)
    example_output = Column(Text, nullable=True)

    status = Column(SAEnum(SkillStatus), default=SkillStatus.ACTIVE, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_skill_type_status", "task_type", "status"),
        Index("idx_skill_agent_status", "agent_id", "status"),
    )


class ToolCategory(str, enum.Enum):
    SEARCH = "search"
    DATA = "data"
    COMPUTE = "compute"
    COMMUNICATION = "communication"
    STORAGE = "storage"
    AI = "ai"
    OTHER = "other"


class AgentTool(Base):
    """
    An API tool/endpoint that an agent exposes to the ecosystem.
    Other agents can discover and call these tools.
    """
    __tablename__ = "agent_tools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    category = Column(SAEnum(ToolCategory), default=ToolCategory.OTHER, nullable=False, index=True)

    # Endpoint info
    endpoint_url = Column(String(500), nullable=True)
    http_method = Column(String(10), default="POST")
    auth_type = Column(String(50), default="api_key")  # api_key, bearer, none

    # Schema (OpenAPI-compatible)
    request_schema = Column(Text, nullable=True)
    response_schema = Column(Text, nullable=True)

    # Pricing (0 = free)
    price_per_call = Column(Float, default=0.0, nullable=False)

    # Stats
    total_calls = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_tool_category_active", "category", "is_active"),
    )


class Gene(Base):
    """
    A gene: compressed knowledge/strategy that agents can adopt.
    Produced by V1-Legacy migration, collaborative fusion, or natural helix folding.
    """
    __tablename__ = "genes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gene_id = Column(String(100), unique=True, nullable=False, index=True)
    producer_agent_id = Column(Integer, default=0, nullable=False, index=True)
    producer_name = Column(String(200), nullable=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    gene_data = Column(Text, nullable=True)       # JSON blob with pattern, summary, procedure
    task_type = Column(String(100), nullable=True, index=True)

    success_rate = Column(Float, default=0.0, nullable=False)
    adoption_count = Column(Integer, default=0, nullable=False)
    royalty_earned = Column(Float, default=0.0, nullable=False)
    price_nau = Column(Float, default=5.0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class GeneAdoption(Base):
    """Record of an agent adopting a gene."""
    __tablename__ = "gene_adoptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gene_id = Column(String(100), ForeignKey("genes.gene_id"), nullable=False, index=True)
    adopter_agent_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=False, index=True)
    adopted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_adoption_gene_agent", "gene_id", "adopter_agent_id", unique=True),
    )


class BountyScore(Base):
    """
    User score for a completed bounty.
    This is the REAL evolutionary pressure signal — external evaluation, not self-assessment.
    Inspired by AI Scientist (Writer/Reviewer separation) and Active Inference research.
    """
    __tablename__ = "bounty_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bounty_id = Column(String(100), nullable=False, index=True)

    # Context (snapshot — bounty may be ephemeral in-memory)
    bounty_title = Column(String(200), nullable=True)
    agent_id = Column(Integer, nullable=True, index=True)
    agent_name = Column(String(200), nullable=True)

    # 4-dimension scoring (1-10)
    score_overall = Column(Integer, nullable=False)
    score_framework = Column(Integer, nullable=True)    # analytical framework depth
    score_accuracy = Column(Integer, nullable=True)     # data accuracy
    score_readability = Column(Integer, nullable=True)  # writing quality

    # Qualitative feedback
    feedback = Column(Text, nullable=True)
    weakest_dimension = Column(String(50), nullable=True)

    scored_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    scored_by = Column(String(100), default="user", nullable=False)  # "user" or scorer id

    __table_args__ = (
        Index("idx_score_agent_time", "agent_id", "scored_at"),
        Index("idx_score_bounty", "bounty_id", unique=True),
    )


class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class AgentMessage(Base):
    """
    Direct message between two agents (A2A communication channel).
    Enables agent-to-agent collaboration, task delegation, and negotiation.
    """
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=False, index=True)

    # Message content
    message_type = Column(String(50), default="text", nullable=False)
    # types: text | task_delegation | collaboration_request | skill_inquiry | payment_request
    subject = Column(String(300), nullable=True)
    body = Column(Text, nullable=False)

    # Optional task reference
    related_task_id = Column(String(100), nullable=True, index=True)

    # Optional payment attached
    payment_amount = Column(Float, default=0.0, nullable=False)
    payment_token = Column(String(10), default="NAU")

    status = Column(SAEnum(MessageStatus), default=MessageStatus.SENT, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_msg_recipient_status", "recipient_id", "status", "created_at"),
        Index("idx_msg_sender_created", "sender_id", "created_at"),
    )


class SquarePost(Base):
    """Public forum post on the Square (U29 20261001 复航).

    api/square.py 依赖;agent_id 为逻辑外键(字符串,agents 表同型),
    不建物理 FK——agents.agent_id 是 VARCHAR,禁照抄 AgentMessage 的 Integer 前科。
    """
    __tablename__ = "square_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(64), nullable=False, index=True)
    agent_name = Column(String(128), nullable=True)
    content = Column(Text, nullable=False)
    post_type = Column(String(20), default="status", nullable=False, index=True)
    # status | announcement | discussion | bounty_call (api/square.py VALID_POST_TYPES)
    reactions_endorse = Column(Integer, default=0, nullable=False)
    reactions_challenge = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class SquareReaction(Base):
    """One reaction (endorse/challenge) per agent per post (DB 兜底唯一)."""
    __tablename__ = "square_reactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, nullable=False, index=True)
    agent_id = Column(String(64), nullable=False)
    reaction = Column(String(10), nullable=False)  # endorse | challenge
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("uq_square_reaction", "post_id", "agent_id", unique=True),
    )

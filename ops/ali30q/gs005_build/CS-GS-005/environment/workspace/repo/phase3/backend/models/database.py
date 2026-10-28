"""
Database models for Nautilus Phase 3.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime, Text, Enum, ForeignKey, Boolean, JSON, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
import uuid

Base = declarative_base()


class TaskType(enum.Enum):
    """Task type enumeration."""
    CODE = "CODE"
    DATA = "DATA"
    COMPUTE = "COMPUTE"
    RESEARCH = "RESEARCH"
    DESIGN = "DESIGN"
    WRITING = "WRITING"
    OTHER = "OTHER"


class TaskStatus(enum.Enum):
    """Task status enumeration."""
    OPEN = "OPEN"
    ACCEPTED = "ACCEPTED"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DISPUTED = "DISPUTED"


class Task(Base):
    """Task model."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(66), unique=True, nullable=False, index=True)  # Blockchain task ID
    publisher = Column(String(42), nullable=False, index=True)
    description = Column(Text, nullable=False)
    input_data = Column(Text)
    expected_output = Column(Text)
    reward = Column(BigInteger, nullable=False)  # Wei
    task_type = Column(Enum(TaskType, name='tasktype'), nullable=False, index=True)
    status = Column(Enum(TaskStatus, name='taskstatus'), nullable=False, index=True)
    agent = Column(String(42), index=True)
    result = Column(Text)
    timeout = Column(Integer, nullable=False)  # Seconds
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    accepted_at = Column(DateTime, index=True)
    submitted_at = Column(DateTime)
    verified_at = Column(DateTime)
    completed_at = Column(DateTime, index=True)
    dispute_reason = Column(Text)

    # Blockchain integration fields (Phase 2)
    blockchain_tx_hash = Column(String(66), index=True)  # Transaction hash for task publish
    blockchain_accept_tx = Column(String(66))  # Transaction hash for task accept
    blockchain_submit_tx = Column(String(66))  # Transaction hash for task submit
    blockchain_complete_tx = Column(String(66))  # Transaction hash for task complete
    blockchain_status = Column(String(20))  # Blockchain sync status

    # Gas fee sharing fields (Phase 3)
    gas_used = Column(BigInteger)  # Total gas used for all transactions
    gas_cost = Column(BigInteger)  # Total gas cost in Wei
    gas_split = Column(BigInteger)  # Agent's share of gas cost (50%)

    # Relationships
    verification_logs = relationship("VerificationLog", back_populates="task")

    # Composite indexes for common queries
    __table_args__ = (
        # Index for filtering by status and created_at (list_tasks)
        Index('idx_task_status_created', 'status', 'created_at'),
        # Index for filtering by agent and status (agent tasks)
        Index('idx_task_agent_status', 'agent', 'status'),
        # Index for filtering by publisher and status (publisher tasks)
        Index('idx_task_publisher_status', 'publisher', 'status'),
    )


class Agent(Base):
    """Agent model."""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, unique=True, nullable=False, index=True)  # Blockchain agent ID
    owner = Column(String(42), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    reputation = Column(Integer, nullable=False, default=100, index=True)
    specialties = Column(Text)  # JSON array stored as text
    tenant_id = Column(String(50), default='public', nullable=False, index=True)
    current_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    total_earnings = Column(BigInteger, default=0)  # Wei
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Blockchain integration fields (Phase 2)
    blockchain_registered = Column(Boolean, default=False)  # Whether registered on-chain
    blockchain_tx_hash = Column(String(66))  # Transaction hash for agent registration
    blockchain_address = Column(String(42))  # Agent's blockchain address (usually same as owner)

    is_test = Column(Boolean, default=False)  # Test/bot agents, excluded from production metrics

    # Reputation and autonomy fields
    reputation_score = Column(Float, default=50.0)       # 声誉分 0-100
    autonomy_enabled = Column(Boolean, default=False)    # 是否开启自主模式
    last_market_scan = Column(DateTime, nullable=True)   # 上次扫描时间

    # Survival mechanism relationship — lazy="select" avoids eager join failures
    # when AgentSurvival mapper is not yet loaded (circular import).
    survival = relationship("AgentSurvival", back_populates="agent", uselist=False, lazy="select")


class Reward(Base):
    """Reward model."""
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(66), nullable=False, index=True)
    agent = Column(String(42), nullable=False, index=True)
    amount = Column(BigInteger, nullable=False)  # Wei
    status = Column(String(20), nullable=False, index=True)  # Pending, Distributed, Withdrawn
    distributed_at = Column(DateTime, index=True)
    withdrawn_at = Column(DateTime)

    # Composite index for common query: agent + status
    __table_args__ = (
        # Index for filtering rewards by agent and status (get_balance, withdraw_reward)
    )


class VerificationLog(Base):
    """Verification log model."""
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(66), ForeignKey("tasks.task_id"), nullable=False, index=True)
    verification_method = Column(String(50), nullable=False)
    is_valid = Column(Boolean, nullable=False)
    logs = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="verification_logs")


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    wallet_address = Column(String(42), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # OAuth fields
    github_id = Column(String(50), unique=True, index=True)
    github_username = Column(String(100))
    google_id = Column(String(100), unique=True, index=True)
    google_email = Column(String(100))


class APIKey(Base):
    """API Key model for agent authentication."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at = Column(DateTime)

    # Composite index for authentication queries
    __table_args__ = (
        # Index for key lookup with is_active check
    )


class OAuthClient(Base):
    """OAuth client (third-party application) model."""
    __tablename__ = "oauth_clients"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(64), unique=True, nullable=False, index=True)
    client_secret = Column(String(128), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    redirect_uris = Column(JSON, nullable=False)  # List of allowed redirect URIs
    logo_url = Column(String(500))
    website = Column(String(500))
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Wallet(Base):
    """Custodial wallet model for agents and users."""
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    public_address = Column(String(42), unique=True, nullable=False, index=True)
    encrypted_private_key = Column(Text, nullable=False)
    mnemonic_hash = Column(String(255), nullable=False)
    derivation_path = Column(String(50), nullable=False, default="m/44'/60'/0'/0/0")
    key_version = Column(Integer, nullable=False, default=1)
    agent_id = Column(Integer, ForeignKey('agents.agent_id'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    wallet_type = Column(String(20), nullable=False, default='agent')
    activation_status = Column(String(20), nullable=False, default='created')
    eth_funded = Column(Boolean, default=False)
    usdc_funded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_tx_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_wallet_agent_id', 'agent_id'),
        Index('idx_wallet_user_id', 'user_id'),
        Index('idx_wallet_type_status', 'wallet_type', 'activation_status'),
    )


class AcademicTask(Base):
    """Academic task model for persistent storage."""
    __tablename__ = "academic_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    task_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default='pending', index=True)
    input_data = Column(Text, nullable=True)
    parameters = Column(Text, nullable=True)  # JSON string
    expected_output = Column(Text, nullable=True)

    # Results
    result_code = Column(Text, nullable=True)
    result_output = Column(Text, nullable=True)
    result_plots = Column(Text, nullable=True)  # JSON array of base64 strings
    result_error = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)

    # Audit (populated by Rehoboam auditor agent)
    audit_status = Column(String(20), nullable=True)  # passed, flagged, pending
    audit_reason = Column(Text, nullable=True)

    # Metadata
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    # Agent assigned to execute this task (for survival score attribution)
    assigned_agent_id = Column(Integer, ForeignKey('agents.agent_id'), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # NAU token reward (Proof of Useful Work)
    blockchain_tx_hash = Column(String(66), nullable=True)   # mint tx hash
    token_reward = Column(Float, nullable=True)               # NAU amount minted

    # Marketplace fields
    marketplace_open = Column(Boolean, default=False)         # 是否发布到市场
    min_bid_nau = Column(Float, nullable=True)                # 最低投标 NAU
    quality_rating = Column(Integer, nullable=True)           # 用户评分 1-5
    rating_comment = Column(String(500), nullable=True)       # 评分留言
    accepted_bid_id = Column(String(36), nullable=True)       # 中标 bid id

    # Public feed
    is_public = Column(Boolean, default=False, nullable=False)  # 结果是否公开发布到 Feed

    # Multi-tenancy
    tenant_id = Column(String(50), default='public', nullable=False, index=True)

    __table_args__ = (
        Index('idx_academic_task_status_created', 'status', 'created_at'),
        Index('idx_academic_task_type', 'task_type'),
        Index('idx_academic_task_public', 'is_public', 'status', 'created_at'),
    )


class SimulationTask(Base):
    """Simulation task model for brain-body training workloads."""
    __tablename__ = "simulation_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    simulation_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default='pending', index=True)
    parameters = Column(Text, nullable=True)  # JSON string
    num_episodes = Column(Integer, nullable=False, default=1)
    time_steps = Column(Integer, nullable=False, default=100)
    output_format = Column(String(20), nullable=False, default='json')

    # Results
    result_code = Column(Text, nullable=True)
    result_output = Column(Text, nullable=True)
    result_plots = Column(Text, nullable=True)  # JSON array of base64 strings
    result_error = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_simulation_task_status_created', 'status', 'created_at'),
        Index('idx_simulation_task_type', 'simulation_type'),
    )


class OAuthAuthorizationCode(Base):
    """OAuth authorization code model."""
    __tablename__ = "oauth_authorization_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    client_id = Column(String(64), nullable=False, index=True)
    agent_address = Column(String(42), nullable=False, index=True)
    redirect_uri = Column(String(500), nullable=False)
    scope = Column(String(500))
    expires_at = Column(DateTime, nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class OAuthAccessToken(Base):
    """OAuth access token model."""
    __tablename__ = "oauth_access_tokens"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String(64), unique=True, nullable=False, index=True)
    refresh_token = Column(String(64), unique=True, nullable=False, index=True)
    client_id = Column(String(64), nullable=False, index=True)
    agent_address = Column(String(42), nullable=False, index=True)
    scope = Column(String(500))
    expires_at = Column(DateTime, nullable=False, index=True)
    refresh_expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at = Column(DateTime)


class AgentMemoryRecord(Base):
    """Hierarchical memory record for the 3-tier agent memory system."""
    __tablename__ = "agent_memory_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_id = Column(String(36), unique=True, nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey('agents.agent_id'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    tier = Column(String(20), nullable=False, default='short')  # working, short, long
    importance = Column(Float, nullable=False, default=0.5)
    embedding = Column(Text, nullable=True)  # JSON-encoded vector
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=False, default=datetime.utcnow)
    access_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index('idx_memory_agent_tier', 'agent_id', 'tier'),
        Index('idx_memory_agent_importance', 'agent_id', 'importance'),
        Index('idx_memory_created', 'created_at'),
    )


class TaskBid(Base):
    """Bid placed by an agent on a marketplace task."""
    __tablename__ = "task_bids"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("academic_tasks.task_id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=False, index=True)
    bid_nau = Column(Float, nullable=False)           # 报价 NAU
    estimated_minutes = Column(Integer, default=10)   # 预估完成时间
    message = Column(String(500), nullable=True)      # 投标附言
    status = Column(String(20), default="pending")    # pending/accepted/rejected
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentCapabilityStat(Base):
    """Per-agent, per-task-type capability statistics for evolution tracking."""
    __tablename__ = "agent_capability_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=False, index=True)
    task_type = Column(String(50), nullable=False)
    total_attempts = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    total_quality_score = Column(Float, default=0.0)  # 累计质量分（用于均值）
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("agent_id", "task_type", name="uq_agent_task_type"),)

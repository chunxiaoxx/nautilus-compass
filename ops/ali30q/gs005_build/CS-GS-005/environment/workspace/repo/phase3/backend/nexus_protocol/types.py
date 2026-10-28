"""
Nexus Protocol - 消息类型定义

版本: 1.0.0
创建时间: 2025-02-24
"""

import hashlib
import hmac
import logging
import uuid
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Nexus Protocol 消息类型"""

    # 连接管理
    HELLO = "hello"

    # 协作请求
    REQUEST = "request"
    OFFER = "offer"

    # 协作响应
    ACCEPT = "accept"
    REJECT = "reject"

    # 执行管理
    PROGRESS = "progress"
    COMPLETE = "complete"

    # 知识共享
    SHARE = "share"

    # 消息确认
    ACK = "ack"
    NACK = "nack"


class NexusMessage(BaseModel):
    """Nexus消息基类"""

    # 消息元数据
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # 路由信息
    from_agent: str = Field(..., description="发送者智能体ID")
    to_agent: Union[str, List[str]] = Field(..., description="接收者智能体ID")

    # 消息内容
    payload: Dict[str, Any] = Field(..., description="消息负载")

    # 安全信息
    signature: Optional[str] = Field(None, description="消息签名")

    # 追踪信息
    correlation_id: Optional[str] = Field(None, description="关联ID")
    reply_to: Optional[str] = Field(None, description="回复的消息ID")

    # 消息过期
    ttl: Optional[int] = Field(None, description="消息生存时间(秒)")
    expires_at: Optional[datetime] = Field(None, description="消息过期时间")


# ============================================================================
# Payload 数据结构
# ============================================================================


class HelloPayload(BaseModel):
    """HELLO消息负载"""
    agent_id: str = Field(..., description="智能体唯一ID")
    name: str = Field(..., description="智能体名称")
    version: str = Field(..., description="智能体版本")
    capabilities: List[str] = Field(default_factory=list, description="能力列表")
    status: str = Field("online", description="状态: online/busy/offline")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class HelloResponse(BaseModel):
    """HELLO响应"""
    status: str = Field(..., description="注册状态: success/error")
    agent_id: str = Field(..., description="确认的智能体ID")
    online_agents: List[str] = Field(default_factory=list, description="在线智能体列表")
    message: Optional[str] = Field(None, description="响应消息")


class RequestPayload(BaseModel):
    """REQUEST消息负载"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: int = Field(..., description="任务ID")
    task_type: str = Field(..., description="任务类型")
    description: str = Field(..., description="任务描述")
    required_capability: str = Field(..., description="所需能力")

    # 奖励和时间
    reward_share: float = Field(..., ge=0.0, le=1.0, description="奖励分成比例")
    deadline: datetime = Field(..., description="截止时间")
    estimated_duration: Optional[int] = Field(None, description="预计耗时(秒)")

    # 任务数据
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    requirements: Optional[Dict[str, Any]] = Field(None, description="特殊要求")


class OfferPayload(BaseModel):
    """OFFER消息负载"""
    offer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    capabilities: List[str] = Field(..., description="提供的能力列表")
    availability: str = Field(..., description="可用性: immediate/scheduled")
    price: Optional[float] = Field(None, description="价格(可选)")
    conditions: Optional[Dict[str, Any]] = Field(None, description="条件")


class AcceptPayload(BaseModel):
    """ACCEPT消息负载"""
    request_id: str = Field(..., description="对应的请求ID")
    estimated_time: int = Field(..., description="预计完成时间(秒)")
    conditions: Optional[Dict[str, Any]] = Field(None, description="接受条件")
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="协作会话ID"
    )


class RejectPayload(BaseModel):
    """REJECT消息负载"""
    request_id: str = Field(..., description="对应的请求ID")
    reason: str = Field(..., description="拒绝原因")
    alternative: Optional[str] = Field(None, description="建议的替代智能体")


class ProgressPayload(BaseModel):
    """PROGRESS消息负载"""
    session_id: str = Field(..., description="协作会话ID")
    progress: float = Field(..., ge=0.0, le=1.0, description="进度百分比")
    status: str = Field(..., description="当前状态")
    message: Optional[str] = Field(None, description="进度消息")
    estimated_remaining: Optional[int] = Field(None, description="预计剩余时间(秒)")


class CompletePayload(BaseModel):
    """COMPLETE消息负载"""
    session_id: str = Field(..., description="协作会话ID")
    status: str = Field(..., description="完成状态: success/failed")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: int = Field(..., description="实际执行时间(秒)")
    metrics: Optional[Dict[str, Any]] = Field(None, description="执行指标")


class SharePayload(BaseModel):
    """SHARE消息负载"""
    share_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    share_type: str = Field(..., description="分享类型: solution/knowledge/experience")
    title: str = Field(..., description="标题")
    description: str = Field(..., description="描述")
    content: Dict[str, Any] = Field(..., description="分享内容")
    tags: List[str] = Field(default_factory=list, description="标签")
    applicable_scenarios: List[str] = Field(default_factory=list, description="适用场景")


class ErrorPayload(BaseModel):
    """错误消息负载"""
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    retry_after: Optional[int] = Field(None, description="重试延迟(秒)")


class AckPayload(BaseModel):
    """ACK消息负载 - 消息确认"""
    ack_message_id: str = Field(..., description="确认的消息ID")
    status: str = Field("received", description="状态: received/processing/completed")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="确认时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class NackPayload(BaseModel):
    """NACK消息负载 - 消息拒绝"""
    nack_message_id: str = Field(..., description="拒绝的消息ID")
    reason: str = Field(..., description="拒绝原因")
    error_code: Optional[str] = Field(None, description="错误代码")
    retry_possible: bool = Field(False, description="是否可以重试")
    retry_after: Optional[int] = Field(None, description="建议重试延迟(秒)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


# ============================================================================
# 辅助函数
# ============================================================================


def create_hello_message(
    agent_id: str,
    name: str,
    version: str,
    capabilities: List[str],
    status: str = "online",
    metadata: Optional[Dict[str, Any]] = None
) -> NexusMessage:
    """创建HELLO消息"""
    payload = HelloPayload(
        agent_id=agent_id,
        name=name,
        version=version,
        capabilities=capabilities,
        status=status,
        metadata=metadata or {}
    )

    return NexusMessage(
        type=MessageType.HELLO,
        from_agent=agent_id,
        to_agent="nexus-server",
        payload=payload.model_dump()
    )


def create_request_message(
    from_agent: str,
    to_agent: str,
    task_id: int,
    task_type: str,
    description: str,
    required_capability: str,
    reward_share: float,
    deadline: datetime,
    input_data: Optional[Dict[str, Any]] = None
) -> NexusMessage:
    """创建REQUEST消息"""
    payload = RequestPayload(
        task_id=task_id,
        task_type=task_type,
        description=description,
        required_capability=required_capability,
        reward_share=reward_share,
        deadline=deadline,
        input_data=input_data
    )

    return NexusMessage(
        type=MessageType.REQUEST,
        from_agent=from_agent,
        to_agent=to_agent,
        payload=payload.model_dump()
    )


def create_accept_message(
    from_agent: str,
    to_agent: str,
    request_id: str,
    estimated_time: int,
    reply_to: str
) -> NexusMessage:
    """创建ACCEPT消息"""
    payload = AcceptPayload(
        request_id=request_id,
        estimated_time=estimated_time
    )

    return NexusMessage(
        type=MessageType.ACCEPT,
        from_agent=from_agent,
        to_agent=to_agent,
        payload=payload.model_dump(),
        reply_to=reply_to
    )


def create_reject_message(
    from_agent: str,
    to_agent: str,
    request_id: str,
    reason: str,
    reply_to: str,
    alternative: Optional[str] = None
) -> NexusMessage:
    """创建REJECT消息"""
    payload = RejectPayload(
        request_id=request_id,
        reason=reason,
        alternative=alternative
    )

    return NexusMessage(
        type=MessageType.REJECT,
        from_agent=from_agent,
        to_agent=to_agent,
        payload=payload.model_dump(),
        reply_to=reply_to
    )


def create_progress_message(
    from_agent: str,
    to_agent: str,
    session_id: str,
    progress: float,
    status: str,
    message: Optional[str] = None
) -> NexusMessage:
    """创建PROGRESS消息"""
    payload = ProgressPayload(
        session_id=session_id,
        progress=progress,
        status=status,
        message=message
    )

    return NexusMessage(
        type=MessageType.PROGRESS,
        from_agent=from_agent,
        to_agent=to_agent,
        payload=payload.model_dump()
    )


def create_complete_message(
    from_agent: str,
    to_agent: str,
    session_id: str,
    status: str,
    execution_time: int,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> NexusMessage:
    """创建COMPLETE消息"""
    payload = CompletePayload(
        session_id=session_id,
        status=status,
        result=result,
        error=error,
        execution_time=execution_time
    )

    return NexusMessage(
        type=MessageType.COMPLETE,
        from_agent=from_agent,
        to_agent=to_agent,
        payload=payload.model_dump()
    )


def create_share_message(
    from_agent: str,
    to_agents: Union[str, List[str]],
    share_type: str,
    title: str,
    description: str,
    content: Dict[str, Any],
    tags: Optional[List[str]] = None
) -> NexusMessage:
    """创建SHARE消息"""
    payload = SharePayload(
        share_type=share_type,
        title=title,
        description=description,
        content=content,
        tags=tags or []
    )

    return NexusMessage(
        type=MessageType.SHARE,
        from_agent=from_agent,
        to_agent=to_agents,
        payload=payload.model_dump()
    )


def create_ack_message(
    from_agent: str,
    to_agent: str,
    ack_message_id: str,
    status: str = "received",
    metadata: Optional[Dict[str, Any]] = None,
    reply_to: Optional[str] = None
) -> NexusMessage:
    """创建ACK消息"""
    payload = AckPayload(
        ack_message_id=ack_message_id,
        status=status,
        metadata=metadata
    )

    return NexusMessage(
        type=MessageType.ACK,
        from_agent=from_agent,
        to_agent=to_agent,
        payload=payload.model_dump(),
        reply_to=reply_to or ack_message_id
    )


def create_nack_message(
    from_agent: str,
    to_agent: str,
    nack_message_id: str,
    reason: str,
    error_code: Optional[str] = None,
    retry_possible: bool = False,
    retry_after: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    reply_to: Optional[str] = None
) -> NexusMessage:
    """创建NACK消息"""
    payload = NackPayload(
        nack_message_id=nack_message_id,
        reason=reason,
        error_code=error_code,
        retry_possible=retry_possible,
        retry_after=retry_after,
        metadata=metadata
    )

    return NexusMessage(
        type=MessageType.NACK,
        from_agent=from_agent,
        to_agent=to_agent,
        payload=payload.model_dump(),
        reply_to=reply_to or nack_message_id
    )


# ============================================================================
# 消息验证
# ============================================================================


def validate_message(message: NexusMessage) -> bool:
    """验证消息格式"""
    try:
        # 检查必填字段
        if not message.from_agent:
            return False
        if not message.to_agent:
            return False
        if not message.payload:
            return False

        # 检查消息类型
        if message.type not in MessageType:
            return False

        return True
    except (ValidationError, ValueError, AttributeError) as e:
        logger.warning(f"Message validation failed: {e}")
        return False


def is_message_expired(message: NexusMessage) -> bool:
    """检查消息是否过期"""
    try:
        # 如果设置了expires_at，检查是否过期
        if message.expires_at:
            return datetime.now(timezone.utc) > message.expires_at

        # 如果设置了ttl，计算是否过期
        if message.ttl:
            message_age = (datetime.now(timezone.utc) - message.timestamp).total_seconds()
            return message_age > message.ttl

        # 没有设置过期时间，消息不过期
        return False
    except (ValueError, AttributeError, TypeError) as e:
        logger.warning(f"Failed to check message expiry: {e}")
        return False


# ============================================================================
# 消息签名
# ============================================================================


def sign_message(message: NexusMessage, secret_key: str) -> str:
    """生成消息签名"""
    message_str = message.model_dump_json(exclude={'signature'})
    signature = hmac.new(
        secret_key.encode(),
        message_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_signature(message: NexusMessage, secret_key: str) -> bool:
    """验证消息签名"""
    if not message.signature:
        return False

    expected_signature = sign_message(message, secret_key)
    return hmac.compare_digest(expected_signature, message.signature)

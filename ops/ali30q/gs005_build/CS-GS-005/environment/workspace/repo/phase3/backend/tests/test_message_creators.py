"""
Nexus Protocol 消息创建函数测试

版本: 1.0.0
创建时间: 2026-02-25
目标: 测试消息创建函数，提升覆盖率到95%+
"""

import pytest
from datetime import datetime, timezone
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nexus_protocol import (
    MessageType,
    create_reject_message,
    create_progress_message,
    create_complete_message,
    create_share_message,
    create_ack_message,
    create_nack_message,
)


# ============================================================================
# 消息创建函数测试
# ============================================================================


def test_create_reject_message():
    """
    测试create_reject_message函数

    验证:
    - 创建REJECT消息
    - 包含正确的字段
    - 消息类型为REJECT
    """
    message = create_reject_message(
        from_agent="agent-a",
        to_agent="agent-b",
        request_id="req-001",
        reason="Cannot handle this task",
        alternative="agent-c",
        reply_to="msg-001"
    )

    assert message.type == MessageType.REJECT
    assert message.from_agent == "agent-a"
    assert message.to_agent == "agent-b"
    assert message.reply_to == "msg-001"
    assert message.payload['request_id'] == "req-001"
    assert message.payload['reason'] == "Cannot handle this task"
    assert message.payload['alternative'] == "agent-c"


def test_create_reject_message_without_alternative():
    """
    测试create_reject_message函数（不提供alternative）

    验证:
    - 可以不提供alternative参数
    - 消息正常创建
    """
    message = create_reject_message(
        from_agent="agent-a",
        to_agent="agent-b",
        request_id="req-002",
        reason="Busy with other tasks",
        reply_to="msg-002"
    )

    assert message.type == MessageType.REJECT
    assert message.payload['request_id'] == "req-002"
    assert message.payload['reason'] == "Busy with other tasks"


def test_create_progress_message():
    """
    测试create_progress_message函数

    验证:
    - 创建PROGRESS消息
    - 包含正确的字段
    - 消息类型为PROGRESS
    """
    message = create_progress_message(
        from_agent="agent-a",
        to_agent="agent-b",
        session_id="session-001",
        progress=0.5,
        status="processing",
        message="Half way done"
    )

    assert message.type == MessageType.PROGRESS
    assert message.from_agent == "agent-a"
    assert message.to_agent == "agent-b"
    assert message.payload['session_id'] == "session-001"
    assert message.payload['progress'] == 0.5
    assert message.payload['status'] == "processing"
    assert message.payload['message'] == "Half way done"


def test_create_progress_message_without_message():
    """
    测试create_progress_message函数（不提供message）

    验证:
    - 可以不提供message参数
    - 消息正常创建
    """
    message = create_progress_message(
        from_agent="agent-a",
        to_agent="agent-b",
        session_id="session-002",
        progress=0.75,
        status="almost done"
    )

    assert message.type == MessageType.PROGRESS
    assert message.payload['progress'] == 0.75
    assert message.payload['status'] == "almost done"


def test_create_complete_message():
    """
    测试create_complete_message函数

    验证:
    - 创建COMPLETE消息
    - 包含正确的字段
    - 消息类型为COMPLETE
    """
    result_data = {"output": "Task completed successfully"}

    message = create_complete_message(
        from_agent="agent-a",
        to_agent="agent-b",
        session_id="session-001",
        status="success",
        execution_time=120,
        result=result_data,
        error=None
    )

    assert message.type == MessageType.COMPLETE
    assert message.from_agent == "agent-a"
    assert message.to_agent == "agent-b"
    assert message.payload['session_id'] == "session-001"
    assert message.payload['status'] == "success"
    assert message.payload['execution_time'] == 120
    assert message.payload['result'] == result_data
    assert message.payload['error'] is None


def test_create_complete_message_with_error():
    """
    测试create_complete_message函数（带错误）

    验证:
    - 可以创建带错误的COMPLETE消息
    - 错误信息正确记录
    """
    message = create_complete_message(
        from_agent="agent-a",
        to_agent="agent-b",
        session_id="session-002",
        status="failed",
        execution_time=60,
        result=None,
        error="Task execution failed"
    )

    assert message.type == MessageType.COMPLETE
    assert message.payload['status'] == "failed"
    assert message.payload['error'] == "Task execution failed"
    assert message.payload['result'] is None


def test_create_share_message():
    """
    测试create_share_message函数

    验证:
    - 创建SHARE消息
    - 包含正确的字段
    - 消息类型为SHARE
    """
    content_data = {"knowledge": "Important information"}

    message = create_share_message(
        from_agent="agent-a",
        to_agents="agent-b",
        share_type="knowledge",
        title="Important Knowledge",
        description="This is important knowledge to share",
        content=content_data,
        tags=["important", "knowledge"]
    )

    assert message.type == MessageType.SHARE
    assert message.from_agent == "agent-a"
    assert message.to_agent == "agent-b"
    assert message.payload['share_type'] == "knowledge"
    assert message.payload['title'] == "Important Knowledge"
    assert message.payload['description'] == "This is important knowledge to share"
    assert message.payload['content'] == content_data
    assert message.payload['tags'] == ["important", "knowledge"]


def test_create_share_message_to_multiple_agents():
    """
    测试create_share_message函数（多个接收者）

    验证:
    - 可以发送给多个agents
    - to_agent是列表
    """
    content_data = {"data": "Shared data"}

    message = create_share_message(
        from_agent="agent-a",
        to_agents=["agent-b", "agent-c", "agent-d"],
        share_type="data",
        title="Shared Data",
        description="Data to share with multiple agents",
        content=content_data
    )

    assert message.type == MessageType.SHARE
    assert isinstance(message.to_agent, list)
    assert len(message.to_agent) == 3
    assert "agent-b" in message.to_agent
    assert "agent-c" in message.to_agent
    assert "agent-d" in message.to_agent


def test_create_share_message_without_tags():
    """
    测试create_share_message函数（不提供tags）

    验证:
    - 可以不提供tags参数
    - tags默认为空列表
    """
    content_data = {"info": "Some information"}

    message = create_share_message(
        from_agent="agent-a",
        to_agents="agent-b",
        share_type="info",
        title="Information",
        description="Some information",
        content=content_data
    )

    assert message.type == MessageType.SHARE
    assert message.payload['tags'] == []


def test_create_ack_message():
    """
    测试create_ack_message函数

    验证:
    - 创建ACK消息
    - 包含正确的字段
    - 消息类型为ACK
    """
    metadata = {"processed_at": "2026-02-25T10:00:00Z"}

    message = create_ack_message(
        from_agent="agent-a",
        to_agent="agent-b",
        ack_message_id="msg-001",
        status="received",
        metadata=metadata,
        reply_to="msg-000"
    )

    assert message.type == MessageType.ACK
    assert message.from_agent == "agent-a"
    assert message.to_agent == "agent-b"
    assert message.payload['ack_message_id'] == "msg-001"
    assert message.payload['status'] == "received"
    assert message.payload['metadata'] == metadata
    assert message.reply_to == "msg-000"


def test_create_ack_message_without_metadata():
    """
    测试create_ack_message函数（不提供metadata）

    验证:
    - 可以不提供metadata参数
    - 消息正常创建
    """
    message = create_ack_message(
        from_agent="agent-a",
        to_agent="agent-b",
        ack_message_id="msg-002",
        status="processed"
    )

    assert message.type == MessageType.ACK
    assert message.payload['ack_message_id'] == "msg-002"
    assert message.payload['status'] == "processed"


def test_create_nack_message():
    """
    测试create_nack_message函数

    验证:
    - 创建NACK消息
    - 包含正确的字段
    - 消息类型为NACK
    """
    metadata = {"error_details": "Invalid format"}

    message = create_nack_message(
        from_agent="agent-a",
        to_agent="agent-b",
        nack_message_id="msg-003",
        reason="Message validation failed",
        error_code="VALIDATION_ERROR",
        retry_possible=True,
        retry_after=60,
        metadata=metadata,
        reply_to="msg-002"
    )

    assert message.type == MessageType.NACK
    assert message.from_agent == "agent-a"
    assert message.to_agent == "agent-b"
    assert message.payload['nack_message_id'] == "msg-003"
    assert message.payload['reason'] == "Message validation failed"
    assert message.payload['error_code'] == "VALIDATION_ERROR"
    assert message.payload['retry_possible'] is True
    assert message.payload['retry_after'] == 60
    assert message.payload['metadata'] == metadata
    assert message.reply_to == "msg-002"


def test_create_nack_message_minimal():
    """
    测试create_nack_message函数（最小参数）

    验证:
    - 只提供必需参数
    - 消息正常创建
    """
    message = create_nack_message(
        from_agent="agent-a",
        to_agent="agent-b",
        nack_message_id="msg-004",
        reason="Cannot process"
    )

    assert message.type == MessageType.NACK
    assert message.payload['nack_message_id'] == "msg-004"
    assert message.payload['reason'] == "Cannot process"
    assert message.payload['retry_possible'] is False

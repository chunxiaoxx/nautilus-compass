"""
Nexus Protocol 补充测试 - 第一批
补充缺失的Payload和消息创建测试
"""

import pytest
from datetime import datetime, timedelta, timezone
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agent-engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nexus_protocol import (
    MessageType,
    RejectPayload,
    ProgressPayload,
    CompletePayload,
    SharePayload,
    AckPayload,
    create_reject_message,
    create_progress_message,
    create_complete_message,
    create_share_message,
    create_ack_message,
)


# ============================================================================
# Payload 测试
# ============================================================================


def test_reject_payload():
    """测试REJECT消息负载"""
    payload = RejectPayload(
        request_id="req-001",
        reason="Too busy",
        alternative="agent-c"
    )

    assert payload.request_id == "req-001"
    assert payload.reason == "Too busy"
    assert payload.alternative == "agent-c"


def test_progress_payload():
    """测试PROGRESS消息负载"""
    payload = ProgressPayload(
        session_id="session-001",
        progress=0.5,
        status="In progress",
        message="Processing data"
    )

    assert payload.session_id == "session-001"
    assert payload.progress == 0.5
    assert payload.status == "In progress"
    assert payload.message == "Processing data"


def test_complete_payload():
    """测试COMPLETE消息负载"""
    payload = CompletePayload(
        session_id="session-001",
        status="success",
        result={"output": "data"},
        execution_time=3600
    )

    assert payload.session_id == "session-001"
    assert payload.status == "success"
    assert payload.result["output"] == "data"
    assert payload.execution_time == 3600


def test_share_payload():
    """测试SHARE消息负载"""
    payload = SharePayload(
        share_type="knowledge",
        title="Best Practice",
        description="How to optimize",
        content={"tip": "Use caching"},
        tags=["optimization", "performance"]
    )

    assert payload.share_type == "knowledge"
    assert payload.title == "Best Practice"
    assert payload.description == "How to optimize"
    assert payload.content["tip"] == "Use caching"
    assert "optimization" in payload.tags


def test_ack_payload():
    """测试ACK消息负载"""
    payload = AckPayload(
        ack_message_id="msg-001",
        status="received"
    )

    assert payload.ack_message_id == "msg-001"
    assert payload.status == "received"
    assert payload.timestamp is not None


# ============================================================================
# 消息创建测试
# ============================================================================


def test_create_reject_message():
    """测试创建REJECT消息"""
    message = create_reject_message(
        from_agent="agent-b",
        to_agent="agent-a",
        request_id="req-001",
        reason="Too busy",
        reply_to="msg-001",
        alternative="agent-c"
    )

    assert message.type == MessageType.REJECT
    assert message.from_agent == "agent-b"
    assert message.to_agent == "agent-a"
    assert message.reply_to == "msg-001"
    assert message.payload["request_id"] == "req-001"
    assert message.payload["reason"] == "Too busy"


def test_create_progress_message():
    """测试创建PROGRESS消息"""
    message = create_progress_message(
        from_agent="agent-b",
        to_agent="agent-a",
        session_id="session-001",
        progress=0.5,
        status="In progress",
        message="Processing data"
    )

    assert message.type == MessageType.PROGRESS
    assert message.from_agent == "agent-b"
    assert message.to_agent == "agent-a"
    assert message.payload["session_id"] == "session-001"
    assert message.payload["progress"] == 0.5


def test_create_complete_message():
    """测试创建COMPLETE消息"""
    message = create_complete_message(
        from_agent="agent-b",
        to_agent="agent-a",
        session_id="session-001",
        status="success",
        execution_time=3600,
        result={"output": "data"}
    )

    assert message.type == MessageType.COMPLETE
    assert message.from_agent == "agent-b"
    assert message.to_agent == "agent-a"
    assert message.payload["session_id"] == "session-001"
    assert message.payload["status"] == "success"


def test_create_share_message():
    """测试创建SHARE消息"""
    message = create_share_message(
        from_agent="agent-a",
        to_agents=["agent-b", "agent-c"],
        share_type="knowledge",
        title="Best Practice",
        description="How to optimize",
        content={"tip": "Use caching"},
        tags=["optimization"]
    )

    assert message.type == MessageType.SHARE
    assert message.from_agent == "agent-a"
    assert message.to_agent == ["agent-b", "agent-c"]
    assert message.payload["share_type"] == "knowledge"


def test_create_ack_message():
    """测试创建ACK消息"""
    message = create_ack_message(
        from_agent="agent-b",
        to_agent="agent-a",
        ack_message_id="msg-001",
        status="received"
    )

    assert message.type == MessageType.ACK
    assert message.from_agent == "agent-b"
    assert message.to_agent == "agent-a"
    assert message.payload["ack_message_id"] == "msg-001"
    assert message.payload["status"] == "received"


# ============================================================================
# 运行测试
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

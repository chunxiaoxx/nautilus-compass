"""
Nexus Protocol 补充测试 - 第二批
边界情况和错误处理测试
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
    NexusMessage,
    NackPayload,
    create_hello_message,
    create_nack_message,
    validate_message,
)


# ============================================================================
# NackPayload 测试
# ============================================================================


def test_nack_payload():
    """测试NACK消息负载"""
    payload = NackPayload(
        nack_message_id="msg-001",
        reason="Invalid format",
        error_code="INVALID_FORMAT",
        retry_possible=True,
        retry_after=60
    )

    assert payload.nack_message_id == "msg-001"
    assert payload.reason == "Invalid format"
    assert payload.error_code == "INVALID_FORMAT"
    assert payload.retry_possible is True
    assert payload.retry_after == 60


# ============================================================================
# 边界情况测试
# ============================================================================


def test_message_with_empty_string():
    """测试空字符串"""
    # 空字符串应该被接受（虽然可能不合理）
    message = create_hello_message(
        agent_id="",  # 空字符串
        name="",
        version="",
        capabilities=[]
    )

    assert message.from_agent == ""
    assert message.payload["name"] == ""


def test_message_with_special_characters():
    """测试特殊字符"""
    special_chars = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
    message = create_hello_message(
        agent_id="agent-001",
        name=special_chars,
        version="1.0.0",
        capabilities=["test"]
    )

    assert message.payload["name"] == special_chars


def test_message_with_unicode():
    """测试Unicode字符"""
    unicode_string = "你好世界 🌍 مرحبا"
    message = create_hello_message(
        agent_id="agent-001",
        name=unicode_string,
        version="1.0.0",
        capabilities=["test"]
    )

    assert message.payload["name"] == unicode_string


def test_message_with_very_long_string():
    """测试超长字符串"""
    long_string = "a" * 10000
    message = create_hello_message(
        agent_id="agent-001",
        name=long_string,
        version="1.0.0",
        capabilities=["test"]
    )

    assert message.payload["name"] == long_string
    assert len(message.payload["name"]) == 10000


# ============================================================================
# 错误处理测试
# ============================================================================


def test_validate_message_missing_from_agent():
    """测试验证缺少from_agent的消息"""
    message = NexusMessage(
        type=MessageType.HELLO,
        from_agent="",  # 空字符串
        to_agent="nexus-server",
        payload={"test": "data"}
    )

    assert validate_message(message) is False


def test_validate_message_missing_to_agent():
    """测试验证缺少to_agent的消息"""
    message = NexusMessage(
        type=MessageType.HELLO,
        from_agent="agent-001",
        to_agent="",  # 空字符串
        payload={"test": "data"}
    )

    assert validate_message(message) is False


def test_validate_message_missing_payload():
    """测试验证缺少payload的消息"""
    message = NexusMessage(
        type=MessageType.HELLO,
        from_agent="agent-001",
        to_agent="nexus-server",
        payload={}  # 空payload
    )

    # 空payload应该被拒绝
    assert validate_message(message) is False


def test_validate_message_with_valid_data():
    """测试验证有效消息"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    assert validate_message(message) is True


# ============================================================================
# create_nack_message 测试
# ============================================================================


def test_create_nack_message():
    """测试创建NACK消息"""
    message = create_nack_message(
        from_agent="agent-b",
        to_agent="agent-a",
        nack_message_id="msg-001",
        reason="Invalid format",
        error_code="INVALID_FORMAT",
        retry_possible=True,
        retry_after=60
    )

    assert message.type == MessageType.NACK
    assert message.from_agent == "agent-b"
    assert message.to_agent == "agent-a"
    assert message.payload["nack_message_id"] == "msg-001"
    assert message.payload["reason"] == "Invalid format"
    assert message.payload["retry_possible"] is True


# ============================================================================
# 运行测试
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

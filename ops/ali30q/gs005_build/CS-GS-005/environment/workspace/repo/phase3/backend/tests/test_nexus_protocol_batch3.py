"""
Nexus Protocol 补充测试 - 第三批
消息过期和签名测试
"""

import pytest
from datetime import datetime, timedelta, timezone
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agent-engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nexus_protocol import (
    NexusMessage,
    MessageType,
    create_hello_message,
    is_message_expired,
    sign_message,
    verify_signature,
)


# ============================================================================
# 消息过期测试
# ============================================================================


def test_message_ttl_not_expired():
    """测试TTL未过期的消息"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    # 手动设置TTL为60秒
    message.ttl = 60

    # 消息刚创建，不应该过期
    assert is_message_expired(message) is False


def test_message_ttl_expired():
    """测试TTL已过期的消息"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    # 设置TTL为-1秒（已过期）
    message.ttl = -1

    # 消息应该已过期
    assert is_message_expired(message) is True


def test_message_expires_at_not_expired():
    """测试expires_at未过期的消息"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    # 设置过期时间为1小时后
    message.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    # 消息不应该过期
    assert is_message_expired(message) is False


def test_message_expires_at_expired():
    """测试expires_at已过期的消息"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    # 设置过期时间为1小时前
    message.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

    # 消息应该已过期
    assert is_message_expired(message) is True


def test_message_no_expiry():
    """测试没有设置过期时间的消息"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    # 没有设置TTL和expires_at，消息不应该过期
    assert is_message_expired(message) is False


# ============================================================================
# 消息签名测试
# ============================================================================


def test_sign_message_with_empty_secret():
    """测试使用空密钥签名"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    # 使用空密钥签名
    signature = sign_message(message, "")

    assert signature is not None
    assert len(signature) == 64  # SHA256 hex digest


def test_sign_message_with_long_secret():
    """测试使用长密钥签名"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    # 使用很长的密钥
    long_secret = "a" * 1000
    signature = sign_message(message, long_secret)

    assert signature is not None
    assert len(signature) == 64

    # 验证签名
    message.signature = signature
    assert verify_signature(message, long_secret) is True


def test_verify_signature_with_modified_message():
    """测试验证被修改的消息"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    secret = "test-secret"

    # 签名
    signature = sign_message(message, secret)
    message.signature = signature

    # 修改消息内容
    message.payload["name"] = "ModifiedAgent"

    # 验证应该失败
    assert verify_signature(message, secret) is False


def test_verify_signature_without_signature():
    """测试验证没有签名的消息"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    # 没有设置签名
    assert message.signature is None

    # 验证应该失败
    assert verify_signature(message, "test-secret") is False


def test_sign_and_verify_with_different_keys():
    """测试使用不同密钥签名和验证"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    # 使用密钥1签名
    signature = sign_message(message, "secret-1")
    message.signature = signature

    # 使用密钥2验证，应该失败
    assert verify_signature(message, "secret-2") is False

    # 使用密钥1验证，应该成功
    assert verify_signature(message, "secret-1") is True


# ============================================================================
# 运行测试
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

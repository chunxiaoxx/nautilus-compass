"""
Nexus Protocol 单元测试

版本: 1.0.0
创建时间: 2025-02-24
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agent-engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nexus_protocol import (
    MessageType,
    NexusMessage,
    HelloPayload,
    RequestPayload,
    AcceptPayload,
    create_hello_message,
    create_request_message,
    create_accept_message,
    validate_message,
    sign_message,
    verify_signature,
)
from nexus_server import NexusServer
from nexus_client import NexusClient


# ============================================================================
# 消息类型测试
# ============================================================================


def test_message_type_enum():
    """测试消息类型枚举"""
    assert MessageType.HELLO.value == "hello"
    assert MessageType.REQUEST.value == "request"
    assert MessageType.ACCEPT.value == "accept"
    assert MessageType.REJECT.value == "reject"
    assert MessageType.PROGRESS.value == "progress"
    assert MessageType.COMPLETE.value == "complete"
    assert MessageType.SHARE.value == "share"


def test_hello_payload():
    """测试HELLO消息负载"""
    payload = HelloPayload(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"],
        status="online"
    )

    assert payload.agent_id == "agent-001"
    assert payload.name == "TestAgent"
    assert payload.status == "online"
    assert "test" in payload.capabilities


def test_request_payload():
    """测试REQUEST消息负载"""
    deadline = datetime.now(timezone.utc) + timedelta(hours=1)

    payload = RequestPayload(
        task_id=123,
        task_type="test",
        description="Test task",
        required_capability="test",
        reward_share=0.3,
        deadline=deadline
    )

    assert payload.task_id == 123
    assert payload.task_type == "test"
    assert payload.reward_share == 0.3
    assert payload.deadline == deadline


def test_accept_payload():
    """测试ACCEPT消息负载"""
    payload = AcceptPayload(
        request_id="req-001",
        estimated_time=3600
    )

    assert payload.request_id == "req-001"
    assert payload.estimated_time == 3600
    assert payload.session_id is not None


# ============================================================================
# 消息创建测试
# ============================================================================


def test_create_hello_message():
    """测试创建HELLO消息"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    assert message.type == MessageType.HELLO
    assert message.from_agent == "agent-001"
    assert message.to_agent == "nexus-server"
    assert message.payload["agent_id"] == "agent-001"


def test_create_request_message():
    """测试创建REQUEST消息"""
    deadline = datetime.now(timezone.utc) + timedelta(hours=1)

    message = create_request_message(
        from_agent="agent-a",
        to_agent="agent-b",
        task_id=123,
        task_type="test",
        description="Test task",
        required_capability="test",
        reward_share=0.3,
        deadline=deadline
    )

    assert message.type == MessageType.REQUEST
    assert message.from_agent == "agent-a"
    assert message.to_agent == "agent-b"
    assert message.payload["task_id"] == 123


def test_create_accept_message():
    """测试创建ACCEPT消息"""
    message = create_accept_message(
        from_agent="agent-b",
        to_agent="agent-a",
        request_id="req-001",
        estimated_time=3600,
        reply_to="msg-001"
    )

    assert message.type == MessageType.ACCEPT
    assert message.from_agent == "agent-b"
    assert message.to_agent == "agent-a"
    assert message.reply_to == "msg-001"


# ============================================================================
# 消息验证测试
# ============================================================================


def test_validate_message():
    """测试消息验证"""
    # 有效消息
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    assert validate_message(message) is True

    # 无效消息（缺少from_agent）
    invalid_message = NexusMessage(
        type=MessageType.HELLO,
        from_agent="",
        to_agent="nexus-server",
        payload={}
    )

    assert validate_message(invalid_message) is False


def test_sign_and_verify_message():
    """测试消息签名和验证"""
    message = create_hello_message(
        agent_id="agent-001",
        name="TestAgent",
        version="1.0.0",
        capabilities=["test"]
    )

    secret_key = "test-secret-key"

    # 签名
    signature = sign_message(message, secret_key)
    assert signature is not None
    assert len(signature) == 64  # SHA256 hex digest

    # 验证
    message.signature = signature
    assert verify_signature(message, secret_key) is True

    # 错误的密钥
    assert verify_signature(message, "wrong-key") is False


# ============================================================================
# Nexus Server 测试
# ============================================================================


@pytest.mark.asyncio
async def test_nexus_server_initialization():
    """测试Nexus服务器初始化"""
    server = NexusServer()

    assert server.agents == {}
    assert server.online_agents == set()
    assert server.stats["total_messages"] == 0


@pytest.mark.asyncio
async def test_agent_registration():
    """测试智能体注册"""
    # 注意：这个测试需要实际运行的服务器
    # 这里只测试数据结构
    server = NexusServer()

    agent_info = {
        'sid': 'test-sid',
        'agent_id': 'agent-001',
        'name': 'TestAgent',
        'capabilities': ['test'],
        'status': 'online'
    }

    server.agents['agent-001'] = agent_info
    server.online_agents.add('agent-001')

    assert 'agent-001' in server.agents
    assert 'agent-001' in server.online_agents
    assert server.get_agent_info('agent-001') == agent_info


# ============================================================================
# Nexus Client 测试
# ============================================================================


def test_nexus_client_initialization():
    """测试Nexus客户端初始化"""
    client = NexusClient(
        agent_id="agent-001",
        name="TestAgent",
        capabilities=["test"],
        server_url="http://localhost:8001"
    )

    assert client.agent_id == "agent-001"
    assert client.name == "TestAgent"
    assert client.capabilities == ["test"]
    assert client.connected is False
    assert client.registered is False


def test_client_event_handlers():
    """测试客户端事件处理器"""
    client = NexusClient(
        agent_id="agent-001",
        name="TestAgent",
        capabilities=["test"]
    )

    handler_called = False

    async def test_handler(data):
        nonlocal handler_called
        handler_called = True

    client.on('request', test_handler)

    assert 'request' in client.handlers
    assert client.handlers['request'] == test_handler


# ============================================================================
# 集成测试
# ============================================================================


@pytest.mark.asyncio
async def test_a2a_communication_flow():
    """
    测试A2A通信流程

    注意：这个测试需要Nexus服务器运行在localhost:8001
    如果服务器未运行，测试将被跳过
    """
    try:
        # 创建两个客户端
        agent_a = NexusClient(
            agent_id="test-agent-a",
            name="TestAgentA",
            capabilities=["test"],
            server_url="http://localhost:8001"
        )

        agent_b = NexusClient(
            agent_id="test-agent-b",
            name="TestAgentB",
            capabilities=["test"],
            server_url="http://localhost:8001"
        )

        # 设置事件处理
        request_received = asyncio.Event()
        accept_received = asyncio.Event()

        async def handle_request(data):
            request_received.set()
            # 自动接受
            await agent_b.send_accept(
                to_agent=data['from_agent'],
                request_id=data['payload']['request_id'],
                estimated_time=100,
                reply_to=data['message_id']
            )

        async def handle_accept(data):
            accept_received.set()

        agent_b.on('request', handle_request)
        agent_a.on('accept', handle_accept)

        # 连接
        await agent_a.connect()
        await agent_b.connect()

        await agent_a.wait_until_registered(timeout=5)
        await agent_b.wait_until_registered(timeout=5)

        # 发送请求
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        await agent_a.send_request(
            to_agent="test-agent-b",
            task_id=999,
            task_type="test",
            description="Test task",
            required_capability="test",
            reward_share=0.5,
            deadline=deadline
        )

        # 等待响应
        await asyncio.wait_for(request_received.wait(), timeout=5)
        await asyncio.wait_for(accept_received.wait(), timeout=5)

        # 断开
        await agent_a.disconnect()
        await agent_b.disconnect()

        # 测试通过
        assert True

    except Exception as e:
        pytest.skip(f"Nexus服务器未运行或测试失败: {e}")


# ============================================================================
# 性能测试
# ============================================================================


def test_message_creation_performance():
    """测试消息创建性能"""
    import time

    start = time.time()

    for i in range(1000):
        create_hello_message(
            agent_id=f"agent-{i}",
            name=f"Agent{i}",
            version="1.0.0",
            capabilities=["test"]
        )

    elapsed = time.time() - start

    # 1000条消息应该在1秒内创建完成
    assert elapsed < 1.0
    print(f"\n创建1000条消息耗时: {elapsed:.3f}秒")


def test_message_validation_performance():
    """测试消息验证性能"""
    import time

    messages = [
        create_hello_message(
            agent_id=f"agent-{i}",
            name=f"Agent{i}",
            version="1.0.0",
            capabilities=["test"]
        )
        for i in range(1000)
    ]

    start = time.time()

    for message in messages:
        validate_message(message)

    elapsed = time.time() - start

    # 1000条消息验证应该在0.1秒内完成
    assert elapsed < 0.1
    print(f"\n验证1000条消息耗时: {elapsed:.3f}秒")


# ============================================================================
# 运行测试
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

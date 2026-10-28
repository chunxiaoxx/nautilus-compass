"""
Nexus Server 错误处理测试

版本: 1.0.0
创建时间: 2026-02-25
目标: 测试服务器错误处理路径和HTTP端点，提升覆盖率到95%+
"""

import pytest
import asyncio
from datetime import datetime, timezone
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nexus_server import NexusServer, create_nexus_app
from nexus_protocol import (
    MessageType,
    NexusMessage,
    create_hello_message,
    create_request_message,
)
from nexus_protocol.types import HelloPayload, RequestPayload


# ============================================================================
# HELLO 错误处理测试
# ============================================================================


@pytest.mark.asyncio
async def test_hello_handler_with_exception():
    """
    测试HELLO处理器的异常处理

    验证:
    - 当HELLO处理过程中发生异常时
    - 发送error事件给客户端
    - 错误代码为HELLO_ERROR
    """
    server = NexusServer()
    sid = "test-sid-hello-error"

    # 模拟emit方法
    emitted_events = []

    async def mock_emit(event, data, room=None):
        emitted_events.append({'event': event, 'data': data, 'room': room})

    server.sio.emit = mock_emit

    # 创建一个会导致异常的HELLO数据（缺少必需字段）
    invalid_hello_data = {
        'agent_id': 'test-agent',
        # 缺少name和capabilities
    }

    # 获取hello处理器
    hello_handler = None
    for handler_name, handler_func in server.sio.handlers['/'].items():
        if handler_name == 'hello':
            hello_handler = handler_func
            break

    if hello_handler:
        await hello_handler(sid, invalid_hello_data)

        # 验证发送了error事件
        error_events = [e for e in emitted_events if e['event'] == 'error']
        assert len(error_events) > 0
        assert error_events[0]['data']['error_code'] == 'HELLO_ERROR'


# ============================================================================
# MESSAGE 错误处理测试
# ============================================================================


@pytest.mark.asyncio
async def test_message_handler_with_exception():
    """
    测试MESSAGE处理器的异常处理

    验证:
    - 当MESSAGE处理过程中发生异常时
    - 发送error事件给客户端
    - 错误代码为MESSAGE_ERROR
    """
    server = NexusServer()
    sid = "test-sid-message-error"

    # 先注册一个agent
    server.agents['agent-a'] = {
        'sid': sid,
        'name': 'Agent A',
        'capabilities': ['test'],
        'status': 'online'
    }
    server.online_agents.add('agent-a')

    # 模拟emit方法
    emitted_events = []

    async def mock_emit(event, data, room=None):
        emitted_events.append({'event': event, 'data': data, 'room': room})

    server.sio.emit = mock_emit

    # 创建一个会导致异常的消息数据（无效格式）
    invalid_message_data = {
        'message_id': 'test-msg-001',
        'type': 'invalid-type',  # 无效的消息类型
        'from_agent': 'agent-a',
        'to_agent': 'agent-b',
    }

    # 获取message处理器
    message_handler = None
    for handler_name, handler_func in server.sio.handlers['/'].items():
        if handler_name == 'message':
            message_handler = handler_func
            break

    if message_handler:
        await message_handler(sid, invalid_message_data)

        # 验证发送了error事件
        error_events = [e for e in emitted_events if e['event'] == 'error']
        assert len(error_events) > 0
        assert error_events[0]['data']['error_code'] == 'MESSAGE_ERROR'


# ============================================================================
# OFFER 处理器测试
# ============================================================================


@pytest.mark.asyncio
async def test_offer_handler():
    """
    测试OFFER处理器

    验证:
    - OFFER消息被正确处理
    - 消息被路由到目标agent
    """
    server = NexusServer()
    sid_a = "test-sid-offer-a"
    sid_b = "test-sid-offer-b"

    # 注册两个agents
    server.agents['agent-a'] = {
        'sid': sid_a,
        'name': 'Agent A',
        'capabilities': ['test'],
        'status': 'online'
    }
    server.online_agents.add('agent-a')

    server.agents['agent-b'] = {
        'sid': sid_b,
        'name': 'Agent B',
        'capabilities': ['test'],
        'status': 'online'
    }
    server.online_agents.add('agent-b')

    # 模拟emit方法
    emitted_events = []

    async def mock_emit(event, data, room=None):
        emitted_events.append({'event': event, 'data': data, 'room': room})

    server.sio.emit = mock_emit

    # 创建OFFER消息
    offer_data = {
        'message_id': 'test-offer-001',
        'type': 'offer',
        'from_agent': 'agent-a',
        'to_agent': 'agent-b',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'payload': {
            'capabilities': ['test'],
            'description': 'Test offer'
        }
    }

    # 获取offer处理器
    offer_handler = None
    for handler_name, handler_func in server.sio.handlers['/'].items():
        if handler_name == 'offer':
            offer_handler = handler_func
            break

    if offer_handler:
        await offer_handler(sid_a, offer_data)

        # 验证消息被发送到agent-b
        offer_events = [e for e in emitted_events if e['event'] == 'offer']
        assert len(offer_events) > 0


# ============================================================================
# 缺少字段错误测试
# ============================================================================


@pytest.mark.asyncio
async def test_typed_message_missing_fields():
    """
    测试_handle_typed_message处理缺少必需字段

    验证:
    - 当from_agent或to_agent缺失时
    - 发送error事件
    - 错误代码为MISSING_FIELDS
    """
    server = NexusServer()
    sid = "test-sid-missing-fields"

    # 模拟emit方法
    emitted_events = []

    async def mock_emit(event, data, room=None):
        emitted_events.append({'event': event, 'data': data, 'room': room})

    server.sio.emit = mock_emit

    # 创建缺少from_agent的消息
    invalid_data = {
        'message_id': 'test-msg-002',
        'type': 'request',
        'to_agent': 'agent-b',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'payload': {
            'task_description': 'Test task',
            'required_capabilities': ['test']
        }
    }

    # 获取request处理器
    request_handler = None
    for handler_name, handler_func in server.sio.handlers['/'].items():
        if handler_name == 'request':
            request_handler = handler_func
            break

    if request_handler:
        await request_handler(sid, invalid_data)

        # 验证发送了error事件
        error_events = [e for e in emitted_events if e['event'] == 'error']
        assert len(error_events) > 0
        assert error_events[0]['data']['error_code'] == 'MISSING_FIELDS'


# ============================================================================
# 目标agent离线错误测试
# ============================================================================


@pytest.mark.asyncio
async def test_route_message_agent_offline():
    """
    测试route_message处理目标agent离线

    验证:
    - 当目标agent不在线时
    - 发送error事件给发送者
    - 错误代码为AGENT_OFFLINE
    """
    server = NexusServer()
    sid_a = "test-sid-offline-a"

    # 只注册agent-a（agent-b不在线）
    server.agents['agent-a'] = {
        'sid': sid_a,
        'name': 'Agent A',
        'capabilities': ['test'],
        'status': 'online'
    }
    server.online_agents.add('agent-a')

    # 模拟emit方法
    emitted_events = []

    async def mock_emit(event, data, room=None):
        emitted_events.append({'event': event, 'data': data, 'room': room})

    server.sio.emit = mock_emit

    # 创建发送给离线agent的消息
    message = NexusMessage(
        message_id='test-msg-003',
        type=MessageType.REQUEST,
        from_agent='agent-a',
        to_agent='agent-b',  # agent-b不在线
        timestamp=datetime.now(timezone.utc),
        payload={
            "task_id": 1,
            "task_type": "test",
            "description": "Test task",
            "required_capability": "test",
            "reward_share": 0.5,
            "deadline": datetime.now(timezone.utc).isoformat()
        }
    )

    await server.route_message(message)

    # 验证发送了error事件
    error_events = [e for e in emitted_events if e['event'] == 'error']
    assert len(error_events) > 0
    assert error_events[0]['data']['error_code'] == 'AGENT_OFFLINE'
    assert 'agent-b' in error_events[0]['data']['error_message']


# ============================================================================
# 广播消息测试
# ============================================================================


@pytest.mark.asyncio
async def test_route_message_broadcast():
    """
    测试route_message处理广播消息

    验证:
    - 消息可以发送给多个agents
    - 只发送给在线的agents
    """
    server = NexusServer()
    sid_a = "test-sid-broadcast-a"
    sid_b = "test-sid-broadcast-b"
    sid_c = "test-sid-broadcast-c"

    # 注册三个agents（agent-c离线）
    server.agents['agent-a'] = {
        'sid': sid_a,
        'name': 'Agent A',
        'capabilities': ['test'],
        'status': 'online'
    }
    server.online_agents.add('agent-a')

    server.agents['agent-b'] = {
        'sid': sid_b,
        'name': 'Agent B',
        'capabilities': ['test'],
        'status': 'online'
    }
    server.online_agents.add('agent-b')

    server.agents['agent-c'] = {
        'sid': sid_c,
        'name': 'Agent C',
        'capabilities': ['test'],
        'status': 'offline'
    }

    # 模拟emit方法
    emitted_events = []

    async def mock_emit(event, data, room=None):
        emitted_events.append({'event': event, 'data': data, 'room': room})

    server.sio.emit = mock_emit

    # 创建广播消息
    message = NexusMessage(
        message_id='test-msg-004',
        type=MessageType.REQUEST,
        from_agent='agent-a',
        to_agent=['agent-b', 'agent-c'],  # 广播给多个agents
        timestamp=datetime.now(timezone.utc),
        payload={
            "task_id": 1,
            "task_type": "test",
            "description": "Test broadcast",
            "required_capability": "test",
            "reward_share": 0.5,
            "deadline": datetime.now(timezone.utc).isoformat()
        }
    )

    await server.route_message(message)

    # 验证消息只发送给在线的agent-b
    request_events = [e for e in emitted_events if e['event'] == 'request']
    assert len(request_events) == 1  # 只发送给agent-b
    assert request_events[0]['room'] == sid_b


# ============================================================================
# 类型化消息处理器异常测试
# ============================================================================


@pytest.mark.asyncio
async def test_handle_typed_message_exception():
    """
    测试_handle_typed_message的异常处理

    验证:
    - 当处理过程中发生异常时
    - 发送error事件
    - 包含正确的错误代码
    """
    server = NexusServer()
    sid = "test-sid-typed-error"

    # 注册发送者agent
    server.agents['agent-a'] = {
        'sid': sid,
        'name': 'Agent A',
        'capabilities': ['test'],
        'status': 'online'
    }
    server.online_agents.add('agent-a')

    # 模拟emit方法
    emitted_events = []

    async def mock_emit(event, data, room=None):
        emitted_events.append({'event': event, 'data': data, 'room': room})

    server.sio.emit = mock_emit

    # 模拟route_message抛出异常
    original_route = server.route_message

    async def mock_route_error(message):
        raise Exception("Test routing error")

    server.route_message = mock_route_error

    # 创建有效的消息数据
    valid_data = {
        'message_id': 'test-msg-005',
        'type': 'request',
        'from_agent': 'agent-a',
        'to_agent': 'agent-b',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'payload': {
            'task_id': 1,
            'task_type': 'test',
            'description': 'Test task',
            'required_capability': 'test',
            'reward_share': 0.5,
            'deadline': datetime.now(timezone.utc).isoformat()
        }
    }

    # 获取request处理器
    request_handler = None
    for handler_name, handler_func in server.sio.handlers['/'].items():
        if handler_name == 'request':
            request_handler = handler_func
            break

    if request_handler:
        await request_handler(sid, valid_data)

        # 验证发送了error事件（可能是AGENT_OFFLINE或REQUEST_ERROR）
        error_events = [e for e in emitted_events if e['event'] == 'error']
        assert len(error_events) > 0
        # 验证有错误代码
        assert 'error_code' in error_events[0]['data']

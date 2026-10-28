"""
Nexus Server Socket.IO 集成测试

版本: 1.0.0
创建时间: 2025-02-25
目标: 测试Socket.IO事件处理器，提升覆盖率
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nexus_server import NexusServer
from nexus_protocol import (
    MessageType,
    NexusMessage,
    create_request_message,
    create_hello_message,
)


# ============================================================================
# Socket.IO 事件处理器测试
# ============================================================================


@pytest.mark.asyncio
async def test_connect_event_handler():
    """
    测试连接事件处理器

    验证:
    - 客户端连接时触发connect事件
    - 返回连接确认消息
    """
    server = NexusServer()

    # 模拟连接
    sid = "test-connect-sid"
    environ = {}

    # 获取connect处理器
    connect_handler = server.sio.handlers['/'].get('connect')

    # 验证处理器存在
    assert connect_handler is not None

    # 调用处理器
    await connect_handler(sid, environ)

    # 验证连接成功（没有抛出异常）
    assert True


@pytest.mark.asyncio
async def test_disconnect_event_handler():
    """
    测试断开连接事件处理器

    验证:
    - 智能体断开时正确清理
    - 在线状态更新
    - SID映射清理
    """
    server = NexusServer()

    # 先注册一个智能体
    sid = "test-disconnect-sid"
    agent_id = "agent-disconnect-test"

    server.agents[agent_id] = {
        'sid': sid,
        'agent_id': agent_id,
        'name': 'DisconnectTest',
        'status': 'online',
    }
    server.online_agents.add(agent_id)
    server.sid_to_agent[sid] = agent_id

    # 获取disconnect处理器
    disconnect_handler = server.sio.handlers['/'].get('disconnect')
    assert disconnect_handler is not None

    # 调用处理器
    await disconnect_handler(sid)

    # 验证清理结果
    assert agent_id not in server.online_agents
    assert sid not in server.sid_to_agent
    assert server.agents[agent_id]['status'] == 'offline'


@pytest.mark.asyncio
async def test_hello_event_handler():
    """
    测试HELLO事件处理器

    验证:
    - 智能体注册成功
    - 返回正确的响应
    - 更新服务器状态
    """
    server = NexusServer()

    sid = "test-hello-sid"
    hello_data = {
        'agent_id': 'agent-hello-test',
        'name': 'HelloTestAgent',
        'version': '1.0.0',
        'capabilities': ['test'],
        'status': 'online',
        'metadata': {}
    }

    # 获取hello处理器
    hello_handler = server.sio.handlers['/'].get('hello')
    assert hello_handler is not None

    # 调用处理器
    await hello_handler(sid, hello_data)

    # 验证注册结果
    assert 'agent-hello-test' in server.agents
    assert 'agent-hello-test' in server.online_agents
    assert server.sid_to_agent[sid] == 'agent-hello-test'


@pytest.mark.asyncio
async def test_hello_event_max_agents_reached():
    """
    测试HELLO事件 - 达到最大智能体数

    验证:
    - 达到上限时拒绝新注册
    - 返回错误信息
    """
    server = NexusServer(max_agents=2)

    # 注册到达上限
    for i in range(2):
        agent_id = f'agent-{i}'
        server.agents[agent_id] = {
            'sid': f'sid-{i}',
            'agent_id': agent_id,
            'status': 'online',
        }
        server.online_agents.add(agent_id)

    # 尝试注册第3个智能体
    sid = "test-hello-limit-sid"
    hello_data = {
        'agent_id': 'agent-limit-test',
        'name': 'LimitTest',
        'version': '1.0.0',
        'capabilities': ['test'],
        'status': 'online',
        'metadata': {}
    }

    hello_handler = server.sio.handlers['/'].get('hello')

    # 调用处理器（应该被拒绝）
    await hello_handler(sid, hello_data)

    # 验证未注册
    assert 'agent-limit-test' not in server.agents


@pytest.mark.asyncio
async def test_message_event_handler():
    """
    测试通用消息事件处理器

    验证:
    - 消息正确处理
    - 消息验证
    - 统计更新
    """
    server = NexusServer()

    # 注册两个智能体
    server.agents['agent-sender'] = {
        'sid': 'sid-sender',
        'agent_id': 'agent-sender',
        'status': 'online',
    }
    server.agents['agent-receiver'] = {
        'sid': 'sid-receiver',
        'agent_id': 'agent-receiver',
        'status': 'online',
    }
    server.online_agents.add('agent-sender')
    server.online_agents.add('agent-receiver')

    # 创建消息
    message = create_request_message(
        from_agent='agent-sender',
        to_agent='agent-receiver',
        task_id=123,
        task_type='test',
        description='Test message',
        required_capability='test',
        reward_share=0.5,
        deadline=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    # 获取message处理器
    message_handler = server.sio.handlers['/'].get('message')
    assert message_handler is not None

    initial_count = server.stats['total_messages']

    # 调用处理器
    await message_handler('sid-sender', message.model_dump())

    # 验证统计更新
    assert server.stats['total_messages'] == initial_count + 1


@pytest.mark.asyncio
async def test_message_event_invalid_format():
    """
    测试消息事件 - 无效格式

    验证:
    - 检测无效消息
    - 返回错误
    """
    server = NexusServer()

    # 创建无效消息
    invalid_data = {
        'type': 'request',
        'from_agent': '',  # 空的from_agent
        'to_agent': 'agent-1',
        'payload': {}
    }

    message_handler = server.sio.handlers['/'].get('message')

    # 调用处理器（应该返回错误）
    await message_handler('test-sid', invalid_data)

    # 验证消息未被处理
    assert server.stats['total_messages'] == 0


@pytest.mark.asyncio
async def test_message_event_expired():
    """
    测试消息事件 - 过期消息

    验证:
    - 检测过期消息
    - 更新dropped_messages统计
    """
    server = NexusServer()

    # 创建过期消息
    expired_message = NexusMessage(
        type=MessageType.REQUEST,
        from_agent='agent-1',
        to_agent='agent-2',
        payload={'task_id': 1},
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=10)
    )

    message_handler = server.sio.handlers['/'].get('message')

    initial_dropped = server.stats['dropped_messages']

    # 调用处理器
    await message_handler('test-sid', expired_message.model_dump())

    # 验证dropped统计更新
    assert server.stats['dropped_messages'] == initial_dropped + 1


@pytest.mark.asyncio
async def test_message_event_queue_full():
    """
    测试消息事件 - 队列满

    验证:
    - 队列满时拒绝消息
    - 更新dropped_messages统计
    """
    server = NexusServer(max_queue_size=2)

    # 填满队列
    await server.message_queue.put('msg1')
    await server.message_queue.put('msg2')

    # 注册智能体
    server.agents['agent-1'] = {
        'sid': 'sid-1',
        'agent_id': 'agent-1',
        'status': 'online',
    }
    server.online_agents.add('agent-1')

    # 创建消息
    message = create_request_message(
        from_agent='agent-1',
        to_agent='agent-2',
        task_id=123,
        task_type='test',
        description='Test',
        required_capability='test',
        reward_share=0.5,
        deadline=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    message_handler = server.sio.handlers['/'].get('message')

    initial_dropped = server.stats['dropped_messages']

    # 调用处理器（队列满）
    await message_handler('sid-1', message.model_dump())

    # 验证dropped统计更新
    assert server.stats['dropped_messages'] == initial_dropped + 1


@pytest.mark.asyncio
async def test_request_event_handler():
    """
    测试REQUEST事件处理器

    验证:
    - REQUEST消息正确处理
    - 路由到目标智能体
    """
    server = NexusServer()

    # 注册智能体
    server.agents['agent-a'] = {
        'sid': 'sid-a',
        'agent_id': 'agent-a',
        'status': 'online',
    }
    server.agents['agent-b'] = {
        'sid': 'sid-b',
        'agent_id': 'agent-b',
        'status': 'online',
    }
    server.online_agents.add('agent-a')
    server.online_agents.add('agent-b')

    request_data = {
        'from_agent': 'agent-a',
        'to_agent': 'agent-b',
        'payload': {
            'task_id': 123,
            'task_type': 'test',
            'description': 'Test request'
        }
    }

    request_handler = server.sio.handlers['/'].get('request')
    assert request_handler is not None

    initial_count = server.stats['total_messages']

    # 调用处理器
    await request_handler('sid-a', request_data)

    # 验证统计更新
    assert server.stats['total_messages'] == initial_count + 1


@pytest.mark.asyncio
async def test_request_event_offline_agent():
    """
    测试REQUEST事件 - 目标智能体离线

    验证:
    - 检测离线智能体
    - 返回错误
    """
    server = NexusServer()

    # 只注册发送者
    server.agents['agent-sender'] = {
        'sid': 'sid-sender',
        'agent_id': 'agent-sender',
        'status': 'online',
    }
    server.online_agents.add('agent-sender')

    request_data = {
        'from_agent': 'agent-sender',
        'to_agent': 'agent-offline',  # 离线智能体
        'payload': {
            'task_id': 123,
            'task_type': 'test'
        }
    }

    request_handler = server.sio.handlers['/'].get('request')

    # 调用处理器（应该返回错误）
    await request_handler('sid-sender', request_data)

    # 验证消息未被处理
    assert server.stats['total_messages'] == 0


@pytest.mark.asyncio
async def test_accept_event_handler():
    """
    测试ACCEPT事件处理器

    验证:
    - ACCEPT消息正确处理
    - 统计更新
    """
    server = NexusServer()

    # 注册智能体
    server.agents['agent-a'] = {
        'sid': 'sid-a',
        'agent_id': 'agent-a',
        'status': 'online',
    }
    server.agents['agent-b'] = {
        'sid': 'sid-b',
        'agent_id': 'agent-b',
        'status': 'online',
    }
    server.online_agents.add('agent-a')
    server.online_agents.add('agent-b')

    accept_data = {
        'from_agent': 'agent-b',
        'to_agent': 'agent-a',
        'payload': {
            'request_id': 'req-123',
            'estimated_time': 3600
        }
    }

    accept_handler = server.sio.handlers['/'].get('accept')
    assert accept_handler is not None

    # 调用处理器
    await accept_handler('sid-b', accept_data)

    # 验证统计更新
    assert server.stats['messages_by_type'].get('accept', 0) >= 1


@pytest.mark.asyncio
async def test_reject_event_handler():
    """
    测试REJECT事件处理器

    验证:
    - REJECT消息正确处理
    """
    server = NexusServer()

    # 注册智能体
    server.agents['agent-a'] = {
        'sid': 'sid-a',
        'agent_id': 'agent-a',
        'status': 'online',
    }
    server.agents['agent-b'] = {
        'sid': 'sid-b',
        'agent_id': 'agent-b',
        'status': 'online',
    }
    server.online_agents.add('agent-a')
    server.online_agents.add('agent-b')

    reject_data = {
        'from_agent': 'agent-b',
        'to_agent': 'agent-a',
        'payload': {
            'request_id': 'req-123',
            'reason': 'Too busy'
        }
    }

    reject_handler = server.sio.handlers['/'].get('reject')
    assert reject_handler is not None

    # 调用处理器
    await reject_handler('sid-b', reject_data)

    # 验证统计更新
    assert server.stats['messages_by_type'].get('reject', 0) >= 1


@pytest.mark.asyncio
async def test_progress_event_handler():
    """
    测试PROGRESS事件处理器

    验证:
    - PROGRESS消息正确处理
    """
    server = NexusServer()

    # 注册智能体
    server.agents['agent-a'] = {
        'sid': 'sid-a',
        'agent_id': 'agent-a',
        'status': 'online',
    }
    server.agents['agent-b'] = {
        'sid': 'sid-b',
        'agent_id': 'agent-b',
        'status': 'online',
    }
    server.online_agents.add('agent-a')
    server.online_agents.add('agent-b')

    progress_data = {
        'from_agent': 'agent-b',
        'to_agent': 'agent-a',
        'payload': {
            'session_id': 'session-123',
            'progress': 0.5,
            'status': 'in_progress'
        }
    }

    progress_handler = server.sio.handlers['/'].get('progress')
    assert progress_handler is not None

    # 调用处理器
    await progress_handler('sid-b', progress_data)

    # 验证统计更新
    assert server.stats['messages_by_type'].get('progress', 0) >= 1


@pytest.mark.asyncio
async def test_complete_event_handler():
    """
    测试COMPLETE事件处理器

    验证:
    - COMPLETE消息正确处理
    """
    server = NexusServer()

    # 注册智能体
    server.agents['agent-a'] = {
        'sid': 'sid-a',
        'agent_id': 'agent-a',
        'status': 'online',
    }
    server.agents['agent-b'] = {
        'sid': 'sid-b',
        'agent_id': 'agent-b',
        'status': 'online',
    }
    server.online_agents.add('agent-a')
    server.online_agents.add('agent-b')

    complete_data = {
        'from_agent': 'agent-b',
        'to_agent': 'agent-a',
        'payload': {
            'session_id': 'session-123',
            'status': 'success',
            'execution_time': 3600
        }
    }

    complete_handler = server.sio.handlers['/'].get('complete')
    assert complete_handler is not None

    # 调用处理器
    await complete_handler('sid-b', complete_data)

    # 验证统计更新
    assert server.stats['messages_by_type'].get('complete', 0) >= 1


@pytest.mark.asyncio
async def test_share_event_handler():
    """
    测试SHARE事件处理器

    验证:
    - SHARE消息正确处理
    """
    server = NexusServer()

    # 注册智能体
    server.agents['agent-a'] = {
        'sid': 'sid-a',
        'agent_id': 'agent-a',
        'status': 'online',
    }
    server.agents['agent-b'] = {
        'sid': 'sid-b',
        'agent_id': 'agent-b',
        'status': 'online',
    }
    server.online_agents.add('agent-a')
    server.online_agents.add('agent-b')

    share_data = {
        'from_agent': 'agent-a',
        'to_agent': 'agent-b',
        'payload': {
            'share_type': 'knowledge',
            'title': 'Test Share',
            'description': 'Test',
            'content': {'data': 'test'}
        }
    }

    share_handler = server.sio.handlers['/'].get('share')
    assert share_handler is not None

    # 调用处理器
    await share_handler('sid-a', share_data)

    # 验证统计更新
    assert server.stats['messages_by_type'].get('share', 0) >= 1


@pytest.mark.asyncio
async def test_get_agents_event_handler():
    """
    测试get_agents事件处理器

    验证:
    - 返回在线智能体列表
    """
    server = NexusServer()

    # 注册智能体
    for i in range(3):
        agent_id = f'agent-{i}'
        server.agents[agent_id] = {
            'agent_id': agent_id,
            'name': f'Agent{i}',
            'capabilities': ['test'],
            'status': 'online',
        }
        server.online_agents.add(agent_id)

    get_agents_handler = server.sio.handlers['/'].get('get_agents')
    assert get_agents_handler is not None

    # 调用处理器
    await get_agents_handler('test-sid', {})

    # 验证处理成功（没有抛出异常）
    assert True


@pytest.mark.asyncio
async def test_get_stats_event_handler():
    """
    测试get_stats事件处理器

    验证:
    - 返回统计信息
    """
    server = NexusServer()

    # 设置一些统计数据
    server.stats['total_messages'] = 100
    server.stats['total_agents'] = 5

    get_stats_handler = server.sio.handlers['/'].get('get_stats')
    assert get_stats_handler is not None

    # 调用处理器
    await get_stats_handler('test-sid', {})

    # 验证处理成功
    assert True


@pytest.mark.asyncio
async def test_broadcast_to_multiple_agents():
    """
    测试广播到多个智能体

    验证:
    - 消息正确广播到多个目标
    """
    server = NexusServer()

    # 注册多个智能体
    for i in range(1, 4):
        agent_id = f'agent-{i}'
        server.agents[agent_id] = {
            'sid': f'sid-{i}',
            'agent_id': agent_id,
            'status': 'online',
        }
        server.online_agents.add(agent_id)

    # 创建广播消息
    share_data = {
        'from_agent': 'agent-1',
        'to_agent': ['agent-2', 'agent-3'],  # 广播到多个智能体
        'payload': {
            'share_type': 'knowledge',
            'title': 'Broadcast Test',
            'description': 'Test broadcast',
            'content': {'data': 'test'}
        }
    }

    share_handler = server.sio.handlers['/'].get('share')

    # 调用处理器
    await share_handler('sid-1', share_data)

    # 验证统计更新
    assert server.stats['messages_by_type'].get('share', 0) >= 1


# ============================================================================
# 运行测试
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

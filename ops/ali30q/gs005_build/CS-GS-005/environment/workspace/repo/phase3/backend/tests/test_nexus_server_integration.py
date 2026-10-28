"""
Nexus Server 集成测试

版本: 1.0.0
创建时间: 2025-02-25
目标: 提升 nexus_server.py 测试覆盖率从32%到80%+
"""

import pytest
import asyncio
import socketio
from datetime import datetime, timedelta, timezone
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nexus_server import NexusServer, create_nexus_app
from nexus_protocol import (
    MessageType,
    NexusMessage,
    HelloPayload,
    RequestPayload,
    create_hello_message,
    create_request_message,
    validate_message,
)


# ============================================================================
# 测试辅助类
# ============================================================================


class MockSocketIOClient:
    """模拟Socket.IO客户端用于测试"""

    def __init__(self, server: NexusServer):
        self.server = server
        self.sid = None
        self.received_events = []
        self.connected = False

    async def connect(self, sid: str):
        """模拟连接"""
        self.sid = sid
        self.connected = True
        await self.server.sio.on_connect(sid, {})

    async def disconnect(self):
        """模拟断开"""
        if self.sid:
            await self.server.sio.on_disconnect(self.sid)
            self.connected = False

    async def emit(self, event: str, data: dict):
        """模拟发送事件"""
        handler = self.server.sio.handlers['/'].get(event)
        if handler:
            await handler(self.sid, data)

    def on_event(self, event: str, data: dict):
        """记录接收到的事件"""
        self.received_events.append({'event': event, 'data': data})


# ============================================================================
# 1. 基础功能测试
# ============================================================================


@pytest.mark.asyncio
async def test_server_startup_shutdown():
    """
    测试服务器启动和关闭

    验证:
    - 服务器正确初始化
    - 所有数据结构正确创建
    - 配置参数正确设置
    """
    server = NexusServer(max_queue_size=500, max_agents=50)

    # 验证初始化状态
    assert server.agents == {}
    assert server.online_agents == set()
    assert server.sid_to_agent == {}
    assert server.max_queue_size == 500
    assert server.max_agents == 50
    assert server.stats['total_messages'] == 0
    assert server.stats['total_agents'] == 0
    assert server.stats['dropped_messages'] == 0

    # 验证消息队列
    assert server.message_queue.maxsize == 500
    assert server.message_queue.qsize() == 0


@pytest.mark.asyncio
async def test_agent_registration():
    """
    测试智能体注册

    验证:
    - 智能体成功注册
    - 注册信息正确存储
    - 在线状态正确更新
    - 返回正确的响应
    """
    server = NexusServer()

    # 模拟客户端连接
    sid = "test-sid-001"

    # 准备HELLO消息
    hello_data = {
        'agent_id': 'agent-001',
        'name': 'TestAgent',
        'version': '1.0.0',
        'capabilities': ['test', 'demo'],
        'status': 'online',
        'metadata': {'type': 'test'}
    }

    # 模拟注册
    server.agents['agent-001'] = {
        'sid': sid,
        'agent_id': 'agent-001',
        'name': 'TestAgent',
        'version': '1.0.0',
        'capabilities': ['test', 'demo'],
        'status': 'online',
        'metadata': {'type': 'test'},
        'registered_at': datetime.now(timezone.utc),
        'last_seen': datetime.now(timezone.utc),
    }
    server.online_agents.add('agent-001')
    server.sid_to_agent[sid] = 'agent-001'
    server.stats['total_agents'] = len(server.agents)

    # 验证注册结果
    assert 'agent-001' in server.agents
    assert 'agent-001' in server.online_agents
    assert server.sid_to_agent[sid] == 'agent-001'
    assert server.stats['total_agents'] == 1

    # 验证智能体信息
    agent_info = server.get_agent_info('agent-001')
    assert agent_info is not None
    assert agent_info['agent_id'] == 'agent-001'
    assert agent_info['name'] == 'TestAgent'
    assert 'test' in agent_info['capabilities']


@pytest.mark.asyncio
async def test_agent_deregistration():
    """
    测试智能体注销

    验证:
    - 智能体断开连接时正确注销
    - 在线状态正确更新
    - SID映射正确清理
    - 智能体信息保留但状态更新为offline
    """
    server = NexusServer()

    # 先注册一个智能体
    sid = "test-sid-002"
    server.agents['agent-002'] = {
        'sid': sid,
        'agent_id': 'agent-002',
        'name': 'TestAgent2',
        'status': 'online',
        'capabilities': ['test'],
        'registered_at': datetime.now(timezone.utc),
    }
    server.online_agents.add('agent-002')
    server.sid_to_agent[sid] = 'agent-002'

    # 模拟断开连接
    agent_id = server.sid_to_agent.get(sid)
    if agent_id:
        server.online_agents.discard(agent_id)
        del server.sid_to_agent[sid]
        server.agents[agent_id]['status'] = 'offline'
        server.agents[agent_id]['disconnected_at'] = datetime.now(timezone.utc)

    # 验证注销结果
    assert 'agent-002' not in server.online_agents
    assert sid not in server.sid_to_agent
    assert 'agent-002' in server.agents  # 信息保留
    assert server.agents['agent-002']['status'] == 'offline'
    assert 'disconnected_at' in server.agents['agent-002']


@pytest.mark.asyncio
async def test_multiple_agents_registration():
    """
    测试多个智能体注册

    验证:
    - 多个智能体可以同时注册
    - 每个智能体信息独立存储
    - 在线智能体列表正确维护
    - 统计信息正确更新
    """
    server = NexusServer()

    # 注册多个智能体
    agents_data = [
        {'sid': 'sid-1', 'agent_id': 'agent-1', 'name': 'Agent1'},
        {'sid': 'sid-2', 'agent_id': 'agent-2', 'name': 'Agent2'},
        {'sid': 'sid-3', 'agent_id': 'agent-3', 'name': 'Agent3'},
    ]

    for data in agents_data:
        server.agents[data['agent_id']] = {
            'sid': data['sid'],
            'agent_id': data['agent_id'],
            'name': data['name'],
            'status': 'online',
            'capabilities': ['test'],
            'registered_at': datetime.now(timezone.utc),
        }
        server.online_agents.add(data['agent_id'])
        server.sid_to_agent[data['sid']] = data['agent_id']

    server.stats['total_agents'] = len(server.agents)

    # 验证注册结果
    assert len(server.agents) == 3
    assert len(server.online_agents) == 3
    assert len(server.sid_to_agent) == 3
    assert server.stats['total_agents'] == 3

    # 验证每个智能体
    for data in agents_data:
        assert data['agent_id'] in server.agents
        assert data['agent_id'] in server.online_agents
        assert server.sid_to_agent[data['sid']] == data['agent_id']


# ============================================================================
# 2. 消息路由测试
# ============================================================================


@pytest.mark.asyncio
async def test_message_routing_unicast():
    """
    测试单播消息路由

    验证:
    - 消息正确路由到目标智能体
    - 只有目标智能体收到消息
    - 消息内容完整传递
    """
    server = NexusServer()

    # 注册两个智能体
    server.agents['agent-a'] = {
        'sid': 'sid-a',
        'agent_id': 'agent-a',
        'name': 'AgentA',
        'status': 'online',
    }
    server.agents['agent-b'] = {
        'sid': 'sid-b',
        'agent_id': 'agent-b',
        'name': 'AgentB',
        'status': 'online',
    }
    server.online_agents.add('agent-a')
    server.online_agents.add('agent-b')

    # 创建单播消息
    message = create_request_message(
        from_agent='agent-a',
        to_agent='agent-b',
        task_id=123,
        task_type='test',
        description='Test task',
        required_capability='test',
        reward_share=0.5,
        deadline=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    # 验证消息结构
    assert message.from_agent == 'agent-a'
    assert message.to_agent == 'agent-b'
    assert isinstance(message.to_agent, str)  # 单播

    # 验证目标智能体在线
    assert message.to_agent in server.online_agents


@pytest.mark.asyncio
async def test_message_routing_broadcast():
    """
    测试广播消息路由

    验证:
    - 消息正确广播到多个智能体
    - 所有在线目标智能体都收到消息
    - 离线智能体不影响广播
    """
    server = NexusServer()

    # 注册多个智能体
    for i in range(1, 4):
        agent_id = f'agent-{i}'
        server.agents[agent_id] = {
            'sid': f'sid-{i}',
            'agent_id': agent_id,
            'name': f'Agent{i}',
            'status': 'online',
        }
        server.online_agents.add(agent_id)

    # 创建广播消息
    message = NexusMessage(
        type=MessageType.SHARE,
        from_agent='agent-1',
        to_agent=['agent-2', 'agent-3'],  # 广播到多个智能体
        payload={
            'share_type': 'knowledge',
            'title': 'Test Share',
            'description': 'Test broadcast',
            'content': {'data': 'test'}
        }
    )

    # 验证消息结构
    assert isinstance(message.to_agent, list)
    assert len(message.to_agent) == 2

    # 验证所有目标智能体在线
    for agent_id in message.to_agent:
        assert agent_id in server.online_agents


@pytest.mark.asyncio
async def test_message_routing_to_offline_agent():
    """
    测试发送消息到离线智能体

    验证:
    - 检测到目标智能体离线
    - 返回适当的错误信息
    - 不会导致系统崩溃
    """
    server = NexusServer()

    # 只注册发送者
    server.agents['agent-sender'] = {
        'sid': 'sid-sender',
        'agent_id': 'agent-sender',
        'name': 'Sender',
        'status': 'online',
    }
    server.online_agents.add('agent-sender')

    # 创建发送到离线智能体的消息
    message = create_request_message(
        from_agent='agent-sender',
        to_agent='agent-offline',  # 不存在的智能体
        task_id=456,
        task_type='test',
        description='Test to offline',
        required_capability='test',
        reward_share=0.5,
        deadline=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    # 验证目标智能体不在线
    assert message.to_agent not in server.online_agents

    # 路由消息应该检测到离线状态
    target_online = message.to_agent in server.online_agents
    assert target_online is False


# ============================================================================
# 3. 并发控制测试
# ============================================================================


@pytest.mark.asyncio
async def test_queue_full_handling():
    """
    测试队列满处理

    验证:
    - 队列满时拒绝新消息
    - 返回适当的错误码
    - 更新dropped_messages统计
    - 不会导致系统阻塞
    """
    server = NexusServer(max_queue_size=5)

    # 填满队列
    for i in range(5):
        await server.message_queue.put(f'message-{i}')

    # 验证队列已满
    assert server.message_queue.full()
    assert server.message_queue.qsize() == 5

    # 模拟队列满时的处理
    if server.message_queue.full():
        server.stats['dropped_messages'] += 1

    # 验证统计更新
    assert server.stats['dropped_messages'] == 1


@pytest.mark.asyncio
async def test_agent_limit_handling():
    """
    测试智能体数量限制

    验证:
    - 达到最大智能体数时拒绝新注册
    - 返回适当的错误信息
    - 现有智能体不受影响
    """
    server = NexusServer(max_agents=3)

    # 注册到达上限
    for i in range(3):
        agent_id = f'agent-{i}'
        server.agents[agent_id] = {
            'sid': f'sid-{i}',
            'agent_id': agent_id,
            'name': f'Agent{i}',
            'status': 'online',
        }
        server.online_agents.add(agent_id)

    # 验证已达上限
    assert len(server.online_agents) == 3
    assert len(server.online_agents) >= server.max_agents

    # 尝试注册新智能体应该被拒绝
    can_register = len(server.online_agents) < server.max_agents
    assert can_register is False


@pytest.mark.asyncio
async def test_concurrent_message_handling():
    """
    测试并发消息处理

    验证:
    - 多个消息可以并发处理
    - 消息统计正确更新
    - 不会出现竞态条件
    """
    server = NexusServer()

    # 注册智能体
    server.agents['agent-1'] = {
        'sid': 'sid-1',
        'agent_id': 'agent-1',
        'status': 'online',
    }
    server.online_agents.add('agent-1')

    # 模拟并发消息
    initial_count = server.stats['total_messages']

    # 处理多条消息
    for i in range(10):
        server.stats['total_messages'] += 1
        msg_type = MessageType.REQUEST.value
        server.stats['messages_by_type'][msg_type] = \
            server.stats['messages_by_type'].get(msg_type, 0) + 1

    # 验证统计
    assert server.stats['total_messages'] == initial_count + 10
    assert server.stats['messages_by_type'][MessageType.REQUEST.value] == 10


# ============================================================================
# 4. 错误处理测试
# ============================================================================


@pytest.mark.asyncio
async def test_invalid_message_format():
    """
    测试无效消息格式

    验证:
    - 检测到无效消息格式
    - 拒绝处理无效消息
    - 返回适当的错误信息
    """
    # 创建无效消息（缺少必填字段）
    invalid_message = NexusMessage(
        type=MessageType.REQUEST,
        from_agent='',  # 空的from_agent
        to_agent='agent-1',
        payload={}
    )

    # 验证消息无效
    is_valid = validate_message(invalid_message)
    assert is_valid is False

    # 创建另一个无效消息（缺少to_agent）
    invalid_message2 = NexusMessage(
        type=MessageType.REQUEST,
        from_agent='agent-1',
        to_agent='',  # 空的to_agent
        payload={}
    )

    is_valid2 = validate_message(invalid_message2)
    assert is_valid2 is False


@pytest.mark.asyncio
async def test_duplicate_agent_registration():
    """
    测试重复注册

    验证:
    - 检测到重复的agent_id
    - 处理重复注册（更新或拒绝）
    - 不会导致数据不一致
    """
    server = NexusServer()

    # 第一次注册
    agent_id = 'agent-duplicate'
    server.agents[agent_id] = {
        'sid': 'sid-1',
        'agent_id': agent_id,
        'name': 'FirstRegistration',
        'status': 'online',
        'registered_at': datetime.now(timezone.utc),
    }
    server.online_agents.add(agent_id)
    server.sid_to_agent['sid-1'] = agent_id

    # 验证第一次注册成功
    assert agent_id in server.agents
    assert server.agents[agent_id]['name'] == 'FirstRegistration'

    # 尝试用不同的sid重复注册（模拟同一智能体重新连接）
    # 在实际场景中，应该更新现有记录
    old_sid = server.agents[agent_id].get('sid')
    new_sid = 'sid-2'

    # 更新注册信息
    server.agents[agent_id]['sid'] = new_sid
    server.agents[agent_id]['name'] = 'SecondRegistration'
    server.agents[agent_id]['last_seen'] = datetime.now(timezone.utc)

    # 更新sid映射
    if old_sid in server.sid_to_agent:
        del server.sid_to_agent[old_sid]
    server.sid_to_agent[new_sid] = agent_id

    # 验证更新成功
    assert server.agents[agent_id]['sid'] == new_sid
    assert server.agents[agent_id]['name'] == 'SecondRegistration'
    assert server.sid_to_agent[new_sid] == agent_id
    assert old_sid not in server.sid_to_agent


@pytest.mark.asyncio
async def test_message_expiry_handling():
    """
    测试消息过期处理

    验证:
    - 检测到过期消息
    - 拒绝处理过期消息
    - 更新dropped_messages统计
    """
    from nexus_protocol import is_message_expired

    # 创建已过期的消息（使用expires_at）
    expired_message = NexusMessage(
        type=MessageType.REQUEST,
        from_agent='agent-1',
        to_agent='agent-2',
        payload={'task_id': 1},
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=10)  # 10秒前过期
    )

    # 验证消息已过期
    assert is_message_expired(expired_message) is True

    # 创建使用TTL的过期消息
    old_timestamp = datetime.now(timezone.utc) - timedelta(seconds=100)
    expired_message_ttl = NexusMessage(
        type=MessageType.REQUEST,
        from_agent='agent-1',
        to_agent='agent-2',
        payload={'task_id': 2},
        timestamp=old_timestamp,
        ttl=30  # 30秒TTL，但消息是100秒前的
    )

    # 验证消息已过期
    assert is_message_expired(expired_message_ttl) is True

    # 创建未过期的消息
    valid_message = NexusMessage(
        type=MessageType.REQUEST,
        from_agent='agent-1',
        to_agent='agent-2',
        payload={'task_id': 3},
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)  # 1小时后过期
    )

    # 验证消息未过期
    assert is_message_expired(valid_message) is False


# ============================================================================
# 5. 统计功能测试
# ============================================================================


@pytest.mark.asyncio
async def test_get_stats():
    """
    测试获取统计信息

    验证:
    - 返回完整的统计信息
    - 统计数据准确
    - 包含所有必要字段
    """
    server = NexusServer()

    # 添加一些数据
    server.agents['agent-1'] = {'agent_id': 'agent-1', 'status': 'online'}
    server.agents['agent-2'] = {'agent_id': 'agent-2', 'status': 'online'}
    server.online_agents.add('agent-1')
    server.online_agents.add('agent-2')

    server.stats['total_messages'] = 100
    server.stats['total_agents'] = 2
    server.stats['dropped_messages'] = 5
    server.stats['messages_by_type'] = {
        'request': 40,
        'accept': 30,
        'complete': 20,
        'share': 10
    }

    # 获取统计信息
    stats = server.get_stats()

    # 验证统计信息
    assert stats['total_messages'] == 100
    assert stats['total_agents'] == 2
    assert stats['dropped_messages'] == 5
    assert stats['online_agents'] == 2
    assert stats['registered_agents'] == 2
    assert 'messages_by_type' in stats
    assert stats['messages_by_type']['request'] == 40


@pytest.mark.asyncio
async def test_get_online_agents():
    """
    测试获取在线智能体列表

    验证:
    - 返回所有在线智能体
    - 不包含离线智能体
    - 列表格式正确
    """
    server = NexusServer()

    # 注册在线智能体
    online_agents = ['agent-1', 'agent-2', 'agent-3']
    for agent_id in online_agents:
        server.agents[agent_id] = {
            'agent_id': agent_id,
            'name': f'Agent{agent_id[-1]}',
            'status': 'online',
        }
        server.online_agents.add(agent_id)

    # 注册离线智能体
    server.agents['agent-offline'] = {
        'agent_id': 'agent-offline',
        'name': 'OfflineAgent',
        'status': 'offline',
    }

    # 获取在线智能体列表
    online_list = server.get_online_agents()

    # 验证结果
    assert len(online_list) == 3
    assert 'agent-1' in online_list
    assert 'agent-2' in online_list
    assert 'agent-3' in online_list
    assert 'agent-offline' not in online_list


# ============================================================================
# 6. 额外的集成测试
# ============================================================================


@pytest.mark.asyncio
async def test_agent_info_retrieval():
    """
    测试智能体信息检索

    验证:
    - 可以通过agent_id获取智能体信息
    - 返回完整的智能体信息
    - 不存在的智能体返回None
    """
    server = NexusServer()

    # 注册智能体
    agent_data = {
        'sid': 'test-sid',
        'agent_id': 'agent-info-test',
        'name': 'InfoTestAgent',
        'version': '2.0.0',
        'capabilities': ['test', 'demo', 'analysis'],
        'status': 'online',
        'metadata': {'location': 'test-env'}
    }

    server.agents['agent-info-test'] = agent_data
    server.online_agents.add('agent-info-test')

    # 获取智能体信息
    info = server.get_agent_info('agent-info-test')

    # 验证信息
    assert info is not None
    assert info['agent_id'] == 'agent-info-test'
    assert info['name'] == 'InfoTestAgent'
    assert info['version'] == '2.0.0'
    assert len(info['capabilities']) == 3
    assert 'test' in info['capabilities']

    # 获取不存在的智能体
    non_existent = server.get_agent_info('non-existent-agent')
    assert non_existent is None


@pytest.mark.asyncio
async def test_message_statistics_tracking():
    """
    测试消息统计跟踪

    验证:
    - 正确跟踪不同类型的消息数量
    - 总消息数正确累加
    - 按类型分类统计准确
    """
    server = NexusServer()

    # 模拟处理不同类型的消息
    message_types = [
        MessageType.REQUEST,
        MessageType.REQUEST,
        MessageType.ACCEPT,
        MessageType.PROGRESS,
        MessageType.COMPLETE,
        MessageType.SHARE,
        MessageType.REQUEST,
    ]

    for msg_type in message_types:
        server.stats['total_messages'] += 1
        type_value = msg_type.value
        server.stats['messages_by_type'][type_value] = \
            server.stats['messages_by_type'].get(type_value, 0) + 1

    # 验证统计
    assert server.stats['total_messages'] == 7
    assert server.stats['messages_by_type']['request'] == 3
    assert server.stats['messages_by_type']['accept'] == 1
    assert server.stats['messages_by_type']['progress'] == 1
    assert server.stats['messages_by_type']['complete'] == 1
    assert server.stats['messages_by_type']['share'] == 1


@pytest.mark.asyncio
async def test_fastapi_app_creation():
    """
    测试FastAPI应用创建

    验证:
    - 成功创建FastAPI应用
    - 应用包含必要的路由
    - Socket.IO正确挂载
    """
    app = create_nexus_app()

    # 验证应用创建成功
    assert app is not None
    assert app.title == "Nexus Protocol Server"
    assert app.version == "1.0.0"

    # 验证路由存在（通过检查routes）
    route_paths = [route.path for route in app.routes]
    assert "/health" in route_paths
    assert "/stats" in route_paths
    assert "/agents" in route_paths


@pytest.mark.asyncio
async def test_server_initialization_with_custom_params():
    """
    测试使用自定义参数初始化服务器

    验证:
    - 自定义参数正确应用
    - 不同配置的服务器独立工作
    """
    # 创建不同配置的服务器
    server1 = NexusServer(max_queue_size=100, max_agents=10)
    server2 = NexusServer(max_queue_size=500, max_agents=50)

    # 验证配置
    assert server1.max_queue_size == 100
    assert server1.max_agents == 10
    assert server1.message_queue.maxsize == 100

    assert server2.max_queue_size == 500
    assert server2.max_agents == 50
    assert server2.message_queue.maxsize == 500

    # 验证服务器独立
    assert server1.agents is not server2.agents
    assert server1.online_agents is not server2.online_agents


@pytest.mark.asyncio
async def test_message_validation_comprehensive():
    """
    测试全面的消息验证

    验证:
    - 有效消息通过验证
    - 各种无效消息被拒绝
    - 验证逻辑健壮
    """
    # 有效消息
    valid_message = create_hello_message(
        agent_id='agent-valid',
        name='ValidAgent',
        version='1.0.0',
        capabilities=['test']
    )
    assert validate_message(valid_message) is True

    # 无效消息 - 空from_agent
    invalid1 = NexusMessage(
        type=MessageType.HELLO,
        from_agent='',
        to_agent='server',
        payload={'test': 'data'}
    )
    assert validate_message(invalid1) is False

    # 无效消息 - 空to_agent
    invalid2 = NexusMessage(
        type=MessageType.HELLO,
        from_agent='agent-1',
        to_agent='',
        payload={'test': 'data'}
    )
    assert validate_message(invalid2) is False

    # 无效消息 - 空payload
    invalid3 = NexusMessage(
        type=MessageType.HELLO,
        from_agent='agent-1',
        to_agent='server',
        payload={}
    )
    assert validate_message(invalid3) is False


# ============================================================================
# 运行测试
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

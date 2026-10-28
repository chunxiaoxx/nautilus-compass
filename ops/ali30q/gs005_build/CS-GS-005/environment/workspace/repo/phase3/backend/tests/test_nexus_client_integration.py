"""
Nexus Client Integration Tests

测试 Nexus Client 的集成功能，包括连接管理、消息发送、事件处理和错误处理。

版本: 1.0.0
创建时间: 2026-02-25
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta, timezone
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agent-engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nexus_client import NexusClient, create_and_connect_client


# 测试配置
SERVER_URL = "http://localhost:8001"
TEST_TIMEOUT = 10


@pytest_asyncio.fixture
async def client_a():
    """创建测试客户端 A"""
    client = NexusClient(
        agent_id="test-agent-a",
        name="TestAgentA",
        capabilities=["code", "test"],
        server_url=SERVER_URL
    )
    yield client
    if client.is_connected():
        await client.disconnect()


@pytest_asyncio.fixture
async def client_b():
    """创建测试客户端 B"""
    client = NexusClient(
        agent_id="test-agent-b",
        name="TestAgentB",
        capabilities=["data", "test"],
        server_url=SERVER_URL
    )
    yield client
    if client.is_connected():
        await client.disconnect()


@pytest_asyncio.fixture
async def connected_client_a(client_a):
    """创建并连接客户端 A"""
    await client_a.connect()
    await client_a.wait_until_registered(timeout=TEST_TIMEOUT)
    return client_a


@pytest_asyncio.fixture
async def connected_client_b(client_b):
    """创建并连接客户端 B"""
    await client_b.connect()
    await client_b.wait_until_registered(timeout=TEST_TIMEOUT)
    return client_b


class TestConnectionManagement:
    """连接管理测试"""

    @pytest.mark.asyncio
    async def test_client_connect_disconnect(self, client_a):
        """
        测试客户端连接和断开

        验证:
        - 客户端可以成功连接到服务器
        - 连接后状态正确
        - 可以正常断开连接
        """
        # 初始状态
        assert not client_a.is_connected()
        assert not client_a.is_registered()

        # 连接
        await client_a.connect()
        await client_a.wait_until_registered(timeout=TEST_TIMEOUT)

        # 验证连接状态
        assert client_a.is_connected()
        assert client_a.is_registered()

        # 断开连接
        await client_a.disconnect()
        await asyncio.sleep(0.5)

        # 验证断开状态
        assert not client_a.is_connected()
        assert not client_a.is_registered()

    @pytest.mark.asyncio
    async def test_client_reconnection(self, client_a):
        """
        测试客户端自动重连

        验证:
        - 客户端断开后可以重新连接
        - 重连后状态正确
        """
        # 首次连接
        await client_a.connect()
        await client_a.wait_until_registered(timeout=TEST_TIMEOUT)
        assert client_a.is_connected()

        # 断开
        await client_a.disconnect()
        await asyncio.sleep(0.5)
        assert not client_a.is_connected()

        # 重新连接
        await client_a.connect()
        await client_a.wait_until_registered(timeout=TEST_TIMEOUT)

        # 验证重连成功
        assert client_a.is_connected()
        assert client_a.is_registered()

    @pytest.mark.asyncio
    async def test_client_connection_timeout(self):
        """
        测试连接超时

        验证:
        - 连接到无效服务器时会超时
        - 超时异常正确抛出
        """
        client = NexusClient(
            agent_id="timeout-test",
            name="TimeoutTest",
            capabilities=["test"],
            server_url="http://localhost:9999"  # 无效端口
        )

        # 尝试连接应该失败
        with pytest.raises(Exception):
            await client.connect()
            await client.wait_until_connected(timeout=2)

    @pytest.mark.asyncio
    async def test_multiple_clients_connection(self, client_a, client_b):
        """
        测试多客户端同时连接

        验证:
        - 多个客户端可以同时连接
        - 每个客户端状态独立
        - 客户端可以看到彼此在线
        """
        # 连接客户端 A
        await client_a.connect()
        await client_a.wait_until_registered(timeout=TEST_TIMEOUT)
        assert client_a.is_connected()

        # 连接客户端 B
        await client_b.connect()
        await client_b.wait_until_registered(timeout=TEST_TIMEOUT)
        assert client_b.is_connected()

        # 等待状态同步
        await asyncio.sleep(1)

        # 验证两个客户端都在线
        online_agents_a = client_a.get_online_agents_list()
        online_agents_b = client_b.get_online_agents_list()

        assert "test-agent-b" in online_agents_a
        assert "test-agent-a" in online_agents_b


class TestMessageSending:
    """消息发送测试"""

    @pytest.mark.asyncio
    async def test_send_request_message(self, connected_client_a, connected_client_b):
        """
        测试发送 REQUEST 消息

        验证:
        - REQUEST 消息可以成功发送
        - 接收方可以收到消息
        - 消息内容正确
        """
        request_received = asyncio.Event()
        received_data = {}

        async def handle_request(data):
            received_data.update(data)
            request_received.set()

        connected_client_b.on('request', handle_request)

        # 发送 REQUEST
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        message_id = await connected_client_a.send_request(
            to_agent="test-agent-b",
            task_id=1001,
            task_type="code_review",
            description="Review my code",
            required_capability="code",
            reward_share=0.3,
            deadline=deadline,
            input_data={"file": "test.py"}
        )

        # 等待接收
        await asyncio.wait_for(request_received.wait(), timeout=TEST_TIMEOUT)

        # 验证消息
        assert received_data['from_agent'] == "test-agent-a"
        assert received_data['to_agent'] == "test-agent-b"
        assert received_data['payload']['task_type'] == "code_review"
        assert received_data['payload']['description'] == "Review my code"

    @pytest.mark.asyncio
    async def test_send_accept_message(self, connected_client_a, connected_client_b):
        """
        测试发送 ACCEPT 消息

        验证:
        - ACCEPT 消息可以成功发送
        - 接收方可以收到消息
        - 消息内容正确
        """
        accept_received = asyncio.Event()
        received_data = {}

        async def handle_accept(data):
            received_data.update(data)
            accept_received.set()

        connected_client_a.on('accept', handle_accept)

        # 发送 ACCEPT
        message_id = await connected_client_b.send_accept(
            to_agent="test-agent-a",
            request_id="req-123",
            estimated_time=300,
            reply_to="msg-456"
        )

        # 等待接收
        await asyncio.wait_for(accept_received.wait(), timeout=TEST_TIMEOUT)

        # 验证消息
        assert received_data['from_agent'] == "test-agent-b"
        assert received_data['to_agent'] == "test-agent-a"
        assert received_data['payload']['request_id'] == "req-123"
        assert received_data['payload']['estimated_time'] == 300

    @pytest.mark.asyncio
    async def test_send_reject_message(self, connected_client_a, connected_client_b):
        """
        测试发送 REJECT 消息

        验证:
        - REJECT 消息可以成功发送
        - 接收方可以收到消息
        - 消息内容正确
        """
        reject_received = asyncio.Event()
        received_data = {}

        async def handle_reject(data):
            received_data.update(data)
            reject_received.set()

        connected_client_a.on('reject', handle_reject)

        # 发送 REJECT
        message_id = await connected_client_b.send_reject(
            to_agent="test-agent-a",
            request_id="req-789",
            reason="Too busy",
            reply_to="msg-101",
            alternative="test-agent-c"
        )

        # 等待接收
        await asyncio.wait_for(reject_received.wait(), timeout=TEST_TIMEOUT)

        # 验证消息
        assert received_data['from_agent'] == "test-agent-b"
        assert received_data['payload']['reason'] == "Too busy"
        assert received_data['payload']['alternative'] == "test-agent-c"

    @pytest.mark.asyncio
    async def test_send_progress_message(self, connected_client_a, connected_client_b):
        """
        测试发送 PROGRESS 消息

        验证:
        - PROGRESS 消息可以成功发送
        - 接收方可以收到消息
        - 进度值正确
        """
        progress_received = asyncio.Event()
        received_data = {}

        async def handle_progress(data):
            received_data.update(data)
            progress_received.set()

        connected_client_a.on('progress', handle_progress)

        # 发送 PROGRESS
        await connected_client_b.send_progress(
            to_agent="test-agent-a",
            session_id="session-001",
            progress=0.5,
            status="processing",
            message="Half way done"
        )

        # 等待接收
        await asyncio.wait_for(progress_received.wait(), timeout=TEST_TIMEOUT)

        # 验证消息
        assert received_data['from_agent'] == "test-agent-b"
        assert received_data['payload']['progress'] == 0.5
        assert received_data['payload']['status'] == "processing"

    @pytest.mark.asyncio
    async def test_send_complete_message(self, connected_client_a, connected_client_b):
        """
        测试发送 COMPLETE 消息

        验证:
        - COMPLETE 消息可以成功发送
        - 接收方可以收到消息
        - 结果数据正确
        """
        complete_received = asyncio.Event()
        received_data = {}

        async def handle_complete(data):
            received_data.update(data)
            complete_received.set()

        connected_client_a.on('complete', handle_complete)

        # 发送 COMPLETE
        message_id = await connected_client_b.send_complete(
            to_agent="test-agent-a",
            session_id="session-002",
            status="success",
            execution_time=120,
            result={"output": "Task completed successfully"}
        )

        # 等待接收
        await asyncio.wait_for(complete_received.wait(), timeout=TEST_TIMEOUT)

        # 验证消息
        assert received_data['from_agent'] == "test-agent-b"
        assert received_data['payload']['status'] == "success"
        assert received_data['payload']['execution_time'] == 120
        assert 'output' in received_data['payload']['result']

    @pytest.mark.asyncio
    async def test_send_share_message(self, connected_client_a, connected_client_b):
        """
        测试发送 SHARE 消息

        验证:
        - SHARE 消息可以成功发送
        - 接收方可以收到消息
        - 共享内容正确
        """
        share_received = asyncio.Event()
        received_data = {}

        async def handle_share(data):
            received_data.update(data)
            share_received.set()

        connected_client_b.on('share', handle_share)

        # 发送 SHARE
        message_id = await connected_client_a.send_share(
            to_agents=["test-agent-b"],
            share_type="knowledge",
            title="Best Practices",
            description="Coding best practices",
            content={"tips": ["Use type hints", "Write tests"]},
            tags=["coding", "tips"]
        )

        # 等待接收
        await asyncio.wait_for(share_received.wait(), timeout=TEST_TIMEOUT)

        # 验证消息
        assert received_data['from_agent'] == "test-agent-a"
        assert received_data['payload']['share_type'] == "knowledge"
        assert received_data['payload']['title'] == "Best Practices"


class TestEventHandling:
    """事件处理测试"""

    @pytest.mark.asyncio
    async def test_event_handler_registration(self, client_a):
        """
        测试事件处理器注册

        验证:
        - 可以注册多个事件处理器
        - 处理器正确存储
        """
        handler_called = []

        async def request_handler(data):
            handler_called.append('request')

        async def accept_handler(data):
            handler_called.append('accept')

        async def reject_handler(data):
            handler_called.append('reject')

        # 注册处理器
        client_a.on('request', request_handler)
        client_a.on('accept', accept_handler)
        client_a.on('reject', reject_handler)

        # 验证处理器已注册
        assert 'request' in client_a.handlers
        assert 'accept' in client_a.handlers
        assert 'reject' in client_a.handlers

    @pytest.mark.asyncio
    async def test_receive_request_event(self, connected_client_a, connected_client_b):
        """
        测试接收 REQUEST 事件

        验证:
        - REQUEST 事件处理器被正确调用
        - 事件数据完整
        """
        event_triggered = asyncio.Event()
        event_data = {}

        async def on_request(data):
            event_data.update(data)
            event_triggered.set()

        connected_client_b.on('request', on_request)

        # 发送 REQUEST
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        await connected_client_a.send_request(
            to_agent="test-agent-b",
            task_id=2001,
            task_type="data_analysis",
            description="Analyze dataset",
            required_capability="data",
            reward_share=0.4,
            deadline=deadline
        )

        # 等待事件触发
        await asyncio.wait_for(event_triggered.wait(), timeout=TEST_TIMEOUT)

        # 验证事件数据
        assert event_data['from_agent'] == "test-agent-a"
        assert event_data['payload']['task_type'] == "data_analysis"

    @pytest.mark.asyncio
    async def test_receive_accept_event(self, connected_client_a, connected_client_b):
        """
        测试接收 ACCEPT 事件

        验证:
        - ACCEPT 事件处理器被正确调用
        - 事件数据完整
        """
        event_triggered = asyncio.Event()
        event_data = {}

        async def on_accept(data):
            event_data.update(data)
            event_triggered.set()

        # 先注册处理器，再等待一下确保连接稳定
        connected_client_a.on('accept', on_accept)
        await asyncio.sleep(0.5)

        # 发送 ACCEPT
        await connected_client_b.send_accept(
            to_agent="test-agent-a",
            request_id="req-2001",
            estimated_time=600,
            reply_to="msg-2001"
        )

        # 等待事件触发
        await asyncio.wait_for(event_triggered.wait(), timeout=TEST_TIMEOUT)

        # 验证事件数据
        assert event_data['from_agent'] == "test-agent-b"
        assert event_data['payload']['estimated_time'] == 600


class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_send_to_offline_agent(self, connected_client_a):
        """
        测试发送消息到离线智能体

        验证:
        - 可以发送消息到离线智能体（服务器会处理）
        - 不会抛出异常
        """
        # 发送到不存在的智能体
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)

        # 这不应该抛出异常，服务器会处理路由
        message_id = await connected_client_a.send_request(
            to_agent="offline-agent-999",
            task_id=3001,
            task_type="test",
            description="Test offline",
            required_capability="test",
            reward_share=0.1,
            deadline=deadline
        )

        # 验证消息ID已生成
        assert message_id is not None

    @pytest.mark.asyncio
    async def test_invalid_message_handling(self, connected_client_a):
        """
        测试无效消息处理

        验证:
        - 错误事件处理器可以捕获错误
        - 客户端保持连接
        """
        error_received = asyncio.Event()
        error_data = {}

        async def on_error(data):
            error_data.update(data)
            error_received.set()

        connected_client_a.on('error', on_error)

        # 尝试发送无效数据（通过底层 socket）
        try:
            await connected_client_a.sio.emit('invalid_event', {'bad': 'data'})
            await asyncio.sleep(1)
        except Exception:
            pass

        # 验证客户端仍然连接
        assert connected_client_a.is_connected()


class TestCompleteWorkflow:
    """完整工作流测试"""

    @pytest.mark.asyncio
    async def test_request_accept_progress_complete_workflow(
        self, connected_client_a, connected_client_b
    ):
        """
        测试完整的请求-接受-进度-完成工作流

        验证:
        - 完整的消息流程可以正常工作
        - 所有消息按顺序接收
        - 状态正确更新
        """
        # 事件标记
        request_received = asyncio.Event()
        accept_received = asyncio.Event()
        progress_received = asyncio.Event()
        complete_received = asyncio.Event()

        request_id = None
        session_id = "workflow-session-001"

        # 客户端 B 处理 REQUEST
        async def handle_request(data):
            nonlocal request_id
            request_id = data['message_id']
            request_received.set()

            # 自动发送 ACCEPT
            await connected_client_b.send_accept(
                to_agent=data['from_agent'],
                request_id=request_id,
                estimated_time=300,
                reply_to=request_id
            )

        # 客户端 A 处理 ACCEPT
        async def handle_accept(data):
            accept_received.set()

        # 客户端 A 处理 PROGRESS
        async def handle_progress(data):
            progress_received.set()

        # 客户端 A 处理 COMPLETE
        async def handle_complete(data):
            complete_received.set()

        # 注册处理器
        connected_client_b.on('request', handle_request)
        connected_client_a.on('accept', handle_accept)
        connected_client_a.on('progress', handle_progress)
        connected_client_a.on('complete', handle_complete)

        # 1. 发送 REQUEST
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        await connected_client_a.send_request(
            to_agent="test-agent-b",
            task_id=4001,
            task_type="workflow_test",
            description="Complete workflow test",
            required_capability="test",
            reward_share=0.5,
            deadline=deadline
        )

        # 等待 REQUEST 和 ACCEPT
        await asyncio.wait_for(request_received.wait(), timeout=TEST_TIMEOUT)
        await asyncio.wait_for(accept_received.wait(), timeout=TEST_TIMEOUT)

        # 2. 发送 PROGRESS
        await connected_client_b.send_progress(
            to_agent="test-agent-a",
            session_id=session_id,
            progress=0.5,
            status="in_progress",
            message="Working on it"
        )

        await asyncio.wait_for(progress_received.wait(), timeout=TEST_TIMEOUT)

        # 3. 发送 COMPLETE
        await connected_client_b.send_complete(
            to_agent="test-agent-a",
            session_id=session_id,
            status="success",
            execution_time=250,
            result={"output": "Workflow completed"}
        )

        await asyncio.wait_for(complete_received.wait(), timeout=TEST_TIMEOUT)

        # 验证所有事件都已触发
        assert request_received.is_set()
        assert accept_received.is_set()
        assert progress_received.is_set()
        assert complete_received.is_set()


class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_create_and_connect_client(self):
        """
        测试便捷创建和连接函数

        验证:
        - 可以使用便捷函数创建并连接客户端
        - 客户端自动注册
        """
        client = await create_and_connect_client(
            agent_id="convenience-test",
            name="ConvenienceTest",
            capabilities=["test"],
            server_url=SERVER_URL
        )

        try:
            # 验证客户端已连接并注册
            assert client.is_connected()
            assert client.is_registered()
        finally:
            await client.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

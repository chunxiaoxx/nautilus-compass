"""
简单的集成测试 - 诊断版本
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agent-engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nexus_client import NexusClient


@pytest.mark.asyncio
@pytest.mark.skip(reason="Integration test - requires running server at localhost:8001")
async def test_simple_communication():
    """简单的通信测试"""
    print("\n=== 开始集成测试 ===\n")

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
        print(f"\n✅ Agent B 收到 REQUEST: {data}\n")
        request_received.set()
        # 自动接受
        try:
            await agent_b.send_accept(
                to_agent=data['from_agent'],
                request_id=data['message_id'],
                estimated_time=100,
                reply_to=data['message_id']
            )
            print("✅ Agent B 发送了 ACCEPT\n")
        except Exception as e:
            print(f"❌ Agent B 发送 ACCEPT 失败: {e}\n")

    async def handle_accept(data):
        print(f"\n✅ Agent A 收到 ACCEPT: {data}\n")
        accept_received.set()

    agent_b.on('request', handle_request)
    agent_a.on('accept', handle_accept)

    try:
        # 连接
        print("📡 连接 Agent A...")
        await agent_a.connect()
        await agent_a.wait_until_registered(timeout=5)
        print("✅ Agent A 已连接并注册\n")

        print("📡 连接 Agent B...")
        await agent_b.connect()
        await agent_b.wait_until_registered(timeout=5)
        print("✅ Agent B 已连接并注册\n")

        # 发送请求
        print("📤 Agent A 发送 REQUEST 到 Agent B...")
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        message_id = await agent_a.send_request(
            to_agent="test-agent-b",
            task_id=999,
            task_type="test",
            description="Test task",
            required_capability="test",
            reward_share=0.5,
            deadline=deadline
        )
        print(f"✅ REQUEST 已发送，message_id: {message_id}\n")

        # 等待响应
        print("⏳ 等待 Agent B 收到 REQUEST...")
        try:
            await asyncio.wait_for(request_received.wait(), timeout=5)
            print("✅ Agent B 已收到 REQUEST\n")
        except asyncio.TimeoutError:
            print("❌ 超时：Agent B 未收到 REQUEST\n")
            raise

        print("⏳ 等待 Agent A 收到 ACCEPT...")
        try:
            await asyncio.wait_for(accept_received.wait(), timeout=5)
            print("✅ Agent A 已收到 ACCEPT\n")
        except asyncio.TimeoutError:
            print("❌ 超时：Agent A 未收到 ACCEPT\n")
            raise

        # 断开
        print("🔌 断开连接...")
        await agent_a.disconnect()
        await agent_b.disconnect()
        print("✅ 连接已断开\n")

        print("=== ✅ 测试通过！===\n")
        return True

    except Exception as e:
        print(f"\n=== ❌ 测试失败：{e} ===\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_simple_communication())
    sys.exit(0 if result else 1)

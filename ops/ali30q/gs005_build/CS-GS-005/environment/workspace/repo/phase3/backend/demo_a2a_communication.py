"""
Nexus Protocol A2A通信演示

演示两个智能体之间的协作通信流程

版本: 1.0.0
创建时间: 2025-02-24
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from nexus_client import NexusClient
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_a2a_communication():
    """演示A2A通信"""

    print("\n" + "="*70)
    print("🚀 Nexus Protocol A2A通信演示")
    print("="*70 + "\n")

    # 创建两个智能体
    print("📝 步骤1: 创建智能体...")
    agent_a = NexusClient(
        agent_id="agent-a",
        name="DataAnalyzer",
        capabilities=["data_analysis", "visualization"],
        server_url="http://localhost:8001"
    )

    agent_b = NexusClient(
        agent_id="agent-b",
        name="DataProcessor",
        capabilities=["data_processing", "cleaning"],
        server_url="http://localhost:8001"
    )

    print("✅ 智能体创建成功")
    print(f"   - Agent A: {agent_a.name} (能力: {', '.join(agent_a.capabilities)})")
    print(f"   - Agent B: {agent_b.name} (能力: {', '.join(agent_b.capabilities)})")

    # Agent B 设置请求处理器
    request_received = asyncio.Event()
    accept_received = asyncio.Event()
    complete_received = asyncio.Event()

    received_request_id = None
    received_session_id = None

    async def handle_request(data):
        """Agent B 处理协作请求"""
        nonlocal received_request_id
        print(f"\n📨 Agent B 收到协作请求:")
        print(f"   - 任务ID: {data['payload']['task_id']}")
        print(f"   - 任务类型: {data['payload']['task_type']}")
        print(f"   - 描述: {data['payload']['description']}")
        print(f"   - 奖励分成: {data['payload']['reward_share']*100}%")

        received_request_id = data['payload']['request_id']
        request_received.set()

        # 模拟评估，然后接受
        await asyncio.sleep(1)
        print(f"\n✅ Agent B 决定接受请求")

        await agent_b.send_accept(
            to_agent=data['from_agent'],
            request_id=received_request_id,
            estimated_time=3000,
            reply_to=data['message_id']
        )

    async def handle_accept(data):
        """Agent A 处理接受消息"""
        nonlocal received_session_id
        print(f"\n🎉 Agent A 收到接受消息:")
        print(f"   - 会话ID: {data['payload']['session_id']}")
        print(f"   - 预计时间: {data['payload']['estimated_time']}秒")

        received_session_id = data['payload']['session_id']
        accept_received.set()

    async def handle_progress(data):
        """Agent A 处理进度更新"""
        progress = data['payload']['progress']
        status = data['payload']['status']
        message = data['payload'].get('message', '')
        print(f"\n📊 Agent A 收到进度更新: {progress*100:.0f}% - {status}")
        if message:
            print(f"   消息: {message}")

    async def handle_complete(data):
        """Agent A 处理完成通知"""
        print(f"\n🎊 Agent A 收到完成通知:")
        print(f"   - 状态: {data['payload']['status']}")
        print(f"   - 执行时间: {data['payload']['execution_time']}秒")
        if data['payload'].get('result'):
            print(f"   - 结果: {data['payload']['result']}")

        complete_received.set()

    agent_b.on('request', handle_request)
    agent_a.on('accept', handle_accept)
    agent_a.on('progress', handle_progress)
    agent_a.on('complete', handle_complete)

    # 连接到服务器
    print("\n📝 步骤2: 连接到Nexus服务器...")
    try:
        await agent_a.connect()
        await agent_b.connect()

        # 等待注册完成
        await agent_a.wait_until_registered(timeout=5)
        await agent_b.wait_until_registered(timeout=5)

        print("✅ 两个智能体已连接并注册")
        print(f"   - 在线智能体: {agent_a.get_online_agents_list()}")

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return

    # Agent A 发送协作请求
    print("\n📝 步骤3: Agent A 发送协作请求...")
    try:
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        message_id = await agent_a.send_request(
            to_agent="agent-b",
            task_id=123,
            task_type="data_processing",
            description="清洗销售数据并生成报告",
            required_capability="data_processing",
            reward_share=0.3,
            deadline=deadline,
            input_data={
                "file_url": "https://example.com/sales.csv",
                "format": "csv",
                "rows": 10000
            }
        )
        print(f"✅ 请求已发送 (消息ID: {message_id})")

    except Exception as e:
        print(f"❌ 发送请求失败: {e}")
        await agent_a.disconnect()
        await agent_b.disconnect()
        return

    # 等待请求被接收
    print("\n📝 步骤4: 等待Agent B响应...")
    try:
        await asyncio.wait_for(request_received.wait(), timeout=5)
        await asyncio.wait_for(accept_received.wait(), timeout=5)
    except asyncio.TimeoutError:
        print("❌ 等待响应超时")
        await agent_a.disconnect()
        await agent_b.disconnect()
        return

    # Agent B 发送进度更新
    print("\n📝 步骤5: Agent B 执行任务并发送进度...")
    try:
        # 模拟任务执行
        for i in range(1, 4):
            await asyncio.sleep(1)
            progress = i / 3
            await agent_b.send_progress(
                to_agent="agent-a",
                session_id=received_session_id,
                progress=progress,
                status="processing",
                message=f"正在处理第{i}阶段"
            )

    except Exception as e:
        print(f"❌ 发送进度失败: {e}")

    # Agent B 发送完成通知
    print("\n📝 步骤6: Agent B 完成任务...")
    try:
        await agent_b.send_complete(
            to_agent="agent-a",
            session_id=received_session_id,
            status="success",
            execution_time=3,
            result={
                "processed_rows": 10000,
                "cleaned_rows": 9800,
                "report_url": "https://example.com/report.pdf"
            }
        )

        # 等待完成消息被接收
        await asyncio.wait_for(complete_received.wait(), timeout=5)

    except Exception as e:
        print(f"❌ 发送完成通知失败: {e}")

    # 断开连接
    print("\n📝 步骤7: 断开连接...")
    await asyncio.sleep(1)
    await agent_a.disconnect()
    await agent_b.disconnect()

    print("\n" + "="*70)
    print("✅ 演示完成！")
    print("="*70 + "\n")

    print("📊 演示总结:")
    print("   1. ✅ 两个智能体成功注册到Nexus服务器")
    print("   2. ✅ Agent A 成功发送协作请求")
    print("   3. ✅ Agent B 成功接受请求")
    print("   4. ✅ Agent B 发送了3次进度更新")
    print("   5. ✅ Agent B 成功完成任务并通知Agent A")
    print("   6. ✅ 完整的A2A通信流程验证成功！")
    print()


async def demo_knowledge_sharing():
    """演示知识共享"""

    print("\n" + "="*70)
    print("🧠 Nexus Protocol 知识共享演示")
    print("="*70 + "\n")

    # 创建三个智能体
    print("📝 创建智能体...")
    agent_a = NexusClient(
        agent_id="agent-a",
        name="ExpertAgent",
        capabilities=["data_analysis"],
        server_url="http://localhost:8001"
    )

    agent_b = NexusClient(
        agent_id="agent-b",
        name="LearnerAgent1",
        capabilities=["data_processing"],
        server_url="http://localhost:8001"
    )

    agent_c = NexusClient(
        agent_id="agent-c",
        name="LearnerAgent2",
        capabilities=["data_processing"],
        server_url="http://localhost:8001"
    )

    share_received_count = 0

    async def handle_share(data):
        """处理知识共享"""
        nonlocal share_received_count
        share_received_count += 1
        print(f"\n📚 收到知识共享:")
        print(f"   - 标题: {data['payload']['title']}")
        print(f"   - 类型: {data['payload']['share_type']}")
        print(f"   - 描述: {data['payload']['description']}")

    agent_b.on('share', handle_share)
    agent_c.on('share', handle_share)

    # 连接
    print("📝 连接到服务器...")
    await agent_a.connect()
    await agent_b.connect()
    await agent_c.connect()

    await agent_a.wait_until_registered()
    await agent_b.wait_until_registered()
    await agent_c.wait_until_registered()

    print("✅ 三个智能体已连接")

    # Agent A 分享知识
    print("\n📝 Agent A 分享知识...")
    await agent_a.send_share(
        to_agents=["agent-b", "agent-c"],
        share_type="solution",
        title="高效数据清洗方法",
        description="处理大型CSV文件的最佳实践",
        content={
            "method": "chunked_processing",
            "chunk_size": 10000,
            "performance_gain": "10x faster"
        },
        tags=["data_processing", "optimization"]
    )

    await asyncio.sleep(2)

    print(f"\n✅ 知识共享完成！{share_received_count}个智能体收到了知识")

    # 断开
    await agent_a.disconnect()
    await agent_b.disconnect()
    await agent_c.disconnect()

    print("\n" + "="*70)
    print("✅ 知识共享演示完成！")
    print("="*70 + "\n")


async def main():
    """主函数"""
    print("\n🎯 Nexus Protocol 演示程序\n")
    print("请确保Nexus服务器正在运行: python nexus_server.py\n")

    try:
        # 演示1: A2A通信
        await demo_a2a_communication()

        # 等待一下
        await asyncio.sleep(2)

        # 演示2: 知识共享
        await demo_knowledge_sharing()

    except KeyboardInterrupt:
        print("\n\n⚠️  演示被中断")
    except Exception as e:
        print(f"\n\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""
完整的端到端工作流测试

测试场景：
1. 完整协作流程 (REQUEST → ACCEPT → PROGRESS → COMPLETE)
2. 拒绝流程 (REQUEST → REJECT)
3. 多次进度更新
4. 多智能体协作
5. 智能体任务交接
6. 知识分享流程
7. 选择性分享
8. 错误恢复流程

版本: 1.0.0
创建时间: 2026-02-25
"""

import asyncio
import pytest
from datetime import datetime, timedelta, timezone
import sys
import os
import logging

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agent-engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nexus_client import NexusClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 测试辅助函数
# ============================================================================

async def create_test_agent(agent_id: str, name: str, capabilities: list) -> NexusClient:
    """创建并连接测试智能体"""
    agent = NexusClient(
        agent_id=agent_id,
        name=name,
        capabilities=capabilities,
        server_url="http://localhost:8001"
    )
    await agent.connect()
    await agent.wait_until_registered(timeout=5)
    logger.info(f"✅ {name} 已连接并注册")
    return agent


async def cleanup_agents(*agents):
    """清理智能体连接"""
    for agent in agents:
        try:
            await agent.disconnect()
        except Exception as e:
            logger.warning(f"断开连接时出错: {e}")


# ============================================================================
# 测试 1: 完整协作流程
# ============================================================================

@pytest.mark.asyncio
async def test_full_collaboration_workflow():
    """
    测试完整的协作流程: REQUEST → ACCEPT → PROGRESS → COMPLETE

    场景：
    - Agent A 向 Agent B 发送任务请求
    - Agent B 接受请求
    - Agent B 发送多次进度更新
    - Agent B 完成任务并返回结果
    """
    logger.info("\n" + "="*80)
    logger.info("测试 1: 完整协作流程")
    logger.info("="*80 + "\n")

    # 创建智能体
    agent_a = await create_test_agent("workflow-agent-a", "WorkflowAgentA", ["requester"])
    agent_b = await create_test_agent("workflow-agent-b", "WorkflowAgentB", ["worker"])

    # 测试状态
    test_state = {
        'request_received': False,
        'accept_received': False,
        'progress_updates': [],
        'complete_received': False,
        'session_id': None,
        'request_id': None
    }

    # Agent B 的请求处理器
    async def handle_request(data):
        logger.info(f"📥 Agent B 收到 REQUEST: {data['payload']['description']}")
        test_state['request_received'] = True
        test_state['request_id'] = data['payload']['request_id']

        # 接受请求
        accept_msg = await agent_b.send_accept(
            to_agent=data['from_agent'],
            request_id=data['payload']['request_id'],
            estimated_time=10,
            reply_to=data['message_id']
        )
        logger.info(f"✅ Agent B 发送 ACCEPT")

        # 获取 session_id
        await asyncio.sleep(0.2)

    # Agent A 的接受处理器
    async def handle_accept(data):
        logger.info(f"📥 Agent A 收到 ACCEPT")
        test_state['accept_received'] = True
        test_state['session_id'] = data['payload']['session_id']

        # 开始模拟工作并发送进度 (修复: 应该发送给 agent_a，而不是 from_agent)
        asyncio.create_task(simulate_work("workflow-agent-a", data['payload']['session_id']))

    # 模拟工作进度
    async def simulate_work(to_agent: str, session_id: str):
        """模拟工作并发送进度更新"""
        await asyncio.sleep(0.5)

        # 发送进度: 25%
        await agent_b.send_progress(
            to_agent=to_agent,
            session_id=session_id,
            progress=0.25,
            status="processing",
            message="开始处理任务"
        )
        logger.info("📊 Agent B 发送进度: 25%")
        await asyncio.sleep(0.5)

        # 发送进度: 50%
        await agent_b.send_progress(
            to_agent=to_agent,
            session_id=session_id,
            progress=0.50,
            status="processing",
            message="任务进行中"
        )
        logger.info("📊 Agent B 发送进度: 50%")
        await asyncio.sleep(0.5)

        # 发送进度: 75%
        await agent_b.send_progress(
            to_agent=to_agent,
            session_id=session_id,
            progress=0.75,
            status="processing",
            message="即将完成"
        )
        logger.info("📊 Agent B 发送进度: 75%")
        await asyncio.sleep(0.5)

        # 完成任务
        await agent_b.send_complete(
            to_agent=to_agent,
            session_id=session_id,
            status="success",
            execution_time=2,
            result={"output": "任务成功完成", "quality": "excellent"}
        )
        logger.info("✅ Agent B 发送 COMPLETE")

    # Agent A 的进度处理器
    async def handle_progress(data):
        progress = data['payload']['progress']
        message = data['payload'].get('message', '')
        test_state['progress_updates'].append(progress)
        logger.info(f"📊 Agent A 收到进度更新: {progress*100}% - {message}")

    # Agent A 的完成处理器
    async def handle_complete(data):
        logger.info(f"📥 Agent A 收到 COMPLETE: {data['payload']['status']}")
        logger.info(f"   结果: {data['payload'].get('result')}")
        test_state['complete_received'] = True

    # 注册事件处理器
    agent_b.on('request', handle_request)
    agent_a.on('accept', handle_accept)
    agent_a.on('progress', handle_progress)
    agent_a.on('complete', handle_complete)

    try:
        # 发送请求
        logger.info("📤 Agent A 发送 REQUEST 到 Agent B")
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        message_id = await agent_a.send_request(
            to_agent="workflow-agent-b",
            task_id=1001,
            task_type="data_processing",
            description="处理数据集并生成报告",
            required_capability="worker",
            reward_share=0.6,
            deadline=deadline,
            input_data={"dataset": "sales_2024.csv", "format": "pdf"}
        )

        # 等待完整流程完成
        logger.info("⏳ 等待工作流完成...")
        timeout = 10
        start_time = asyncio.get_event_loop().time()

        while not test_state['complete_received']:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("工作流超时")
            await asyncio.sleep(0.1)

        # 验证结果
        assert test_state['request_received'], "Agent B 应该收到 REQUEST"
        assert test_state['accept_received'], "Agent A 应该收到 ACCEPT"
        assert len(test_state['progress_updates']) >= 3, f"应该收到至少3次进度更新，实际收到 {len(test_state['progress_updates'])} 次"
        assert test_state['complete_received'], "Agent A 应该收到 COMPLETE"
        assert test_state['session_id'] is not None, "应该有 session_id"

        logger.info("\n✅ 测试 1 通过: 完整协作流程成功\n")

    finally:
        await cleanup_agents(agent_a, agent_b)


# ============================================================================
# 测试 2: 拒绝流程
# ============================================================================

@pytest.mark.asyncio
async def test_rejection_workflow():
    """
    测试拒绝流程: REQUEST → REJECT

    场景：
    - Agent A 向 Agent B 发送任务请求
    - Agent B 因为忙碌拒绝请求
    - Agent B 建议替代智能体
    """
    logger.info("\n" + "="*80)
    logger.info("测试 2: 拒绝流程")
    logger.info("="*80 + "\n")

    # 创建智能体
    agent_a = await create_test_agent("reject-agent-a", "RejectAgentA", ["requester"])
    agent_b = await create_test_agent("reject-agent-b", "RejectAgentB", ["worker"])
    agent_c = await create_test_agent("reject-agent-c", "RejectAgentC", ["worker"])

    # 测试状态
    test_state = {
        'request_received': False,
        'reject_received': False,
        'reject_reason': None,
        'alternative_agent': None
    }

    # Agent B 的请求处理器 - 拒绝请求
    async def handle_request(data):
        logger.info(f"📥 Agent B 收到 REQUEST: {data['payload']['description']}")
        test_state['request_received'] = True

        # 拒绝请求并建议 Agent C
        await agent_b.send_reject(
            to_agent=data['from_agent'],
            request_id=data['payload']['request_id'],
            reason="当前正在处理其他任务，无法接受新请求",
            reply_to=data['message_id'],
            alternative="reject-agent-c"
        )
        logger.info(f"❌ Agent B 发送 REJECT，建议使用 Agent C")

    # Agent A 的拒绝处理器
    async def handle_reject(data):
        logger.info(f"📥 Agent A 收到 REJECT")
        logger.info(f"   原因: {data['payload']['reason']}")
        logger.info(f"   建议替代: {data['payload'].get('alternative')}")
        test_state['reject_received'] = True
        test_state['reject_reason'] = data['payload']['reason']
        test_state['alternative_agent'] = data['payload'].get('alternative')

    # 注册事件处理器
    agent_b.on('request', handle_request)
    agent_a.on('reject', handle_reject)

    try:
        # 发送请求
        logger.info("📤 Agent A 发送 REQUEST 到 Agent B")
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        await agent_a.send_request(
            to_agent="reject-agent-b",
            task_id=1002,
            task_type="analysis",
            description="分析市场趋势",
            required_capability="worker",
            reward_share=0.5,
            deadline=deadline
        )

        # 等待拒绝消息
        logger.info("⏳ 等待 REJECT 消息...")
        timeout = 5
        start_time = asyncio.get_event_loop().time()

        while not test_state['reject_received']:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("等待 REJECT 超时")
            await asyncio.sleep(0.1)

        # 验证结果
        assert test_state['request_received'], "Agent B 应该收到 REQUEST"
        assert test_state['reject_received'], "Agent A 应该收到 REJECT"
        assert test_state['reject_reason'] is not None, "应该有拒绝原因"
        assert test_state['alternative_agent'] == "reject-agent-c", "应该建议 Agent C"

        logger.info("\n✅ 测试 2 通过: 拒绝流程成功\n")

    finally:
        await cleanup_agents(agent_a, agent_b, agent_c)


# ============================================================================
# 测试 3: 多次进度更新
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_progress_updates():
    """
    测试多次进度更新流程

    场景：
    - Agent B 接受任务后发送10次进度更新
    - 验证所有进度更新都被正确接收
    - 验证进度是递增的
    """
    logger.info("\n" + "="*80)
    logger.info("测试 3: 多次进度更新")
    logger.info("="*80 + "\n")

    # 创建智能体
    agent_a = await create_test_agent("progress-agent-a", "ProgressAgentA", ["requester"])
    agent_b = await create_test_agent("progress-agent-b", "ProgressAgentB", ["worker"])

    # 测试状态
    test_state = {
        'accept_received': False,
        'progress_updates': [],
        'complete_received': False,
        'session_id': None
    }

    # Agent B 的请求处理器
    async def handle_request(data):
        logger.info(f"📥 Agent B 收到 REQUEST")

        # 接受请求
        await agent_b.send_accept(
            to_agent=data['from_agent'],
            request_id=data['payload']['request_id'],
            estimated_time=20,
            reply_to=data['message_id']
        )
        logger.info(f"✅ Agent B 发送 ACCEPT")

    # Agent A 的接受处理器
    async def handle_accept(data):
        logger.info(f"📥 Agent A 收到 ACCEPT")
        test_state['accept_received'] = True
        test_state['session_id'] = data['payload']['session_id']

        # 开始发送多次进度更新 (修复: 应该发送给 agent_a，而不是 from_agent)
        asyncio.create_task(send_multiple_progress("progress-agent-a", data['payload']['session_id']))

    # 发送多次进度更新
    async def send_multiple_progress(to_agent: str, session_id: str):
        """发送10次进度更新"""
        for i in range(1, 11):
            await asyncio.sleep(0.2)
            progress = i / 10.0
            await agent_b.send_progress(
                to_agent=to_agent,
                session_id=session_id,
                progress=progress,
                status="processing",
                message=f"步骤 {i}/10"
            )
            logger.info(f"📊 Agent B 发送进度: {progress*100}%")

        # 完成任务
        await asyncio.sleep(0.2)
        await agent_b.send_complete(
            to_agent=to_agent,
            session_id=session_id,
            status="success",
            execution_time=3,
            result={"steps_completed": 10}
        )
        logger.info("✅ Agent B 发送 COMPLETE")

    # Agent A 的进度处理器
    async def handle_progress(data):
        progress = data['payload']['progress']
        test_state['progress_updates'].append(progress)
        logger.info(f"📊 Agent A 收到进度: {progress*100}%")

    # Agent A 的完成处理器
    async def handle_complete(data):
        logger.info(f"📥 Agent A 收到 COMPLETE")
        test_state['complete_received'] = True

    # 注册事件处理器
    agent_b.on('request', handle_request)
    agent_a.on('accept', handle_accept)
    agent_a.on('progress', handle_progress)
    agent_a.on('complete', handle_complete)

    try:
        # 发送请求
        logger.info("📤 Agent A 发送 REQUEST")
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        await agent_a.send_request(
            to_agent="progress-agent-b",
            task_id=1003,
            task_type="long_task",
            description="长时间运行的任务",
            required_capability="worker",
            reward_share=0.5,
            deadline=deadline
        )

        # 等待完成
        logger.info("⏳ 等待任务完成...")
        timeout = 10
        start_time = asyncio.get_event_loop().time()

        while not test_state['complete_received']:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("任务超时")
            await asyncio.sleep(0.1)

        # 验证结果
        assert test_state['accept_received'], "应该收到 ACCEPT"
        assert len(test_state['progress_updates']) == 10, f"应该收到10次进度更新，实际收到 {len(test_state['progress_updates'])} 次"
        assert test_state['complete_received'], "应该收到 COMPLETE"

        # 验证进度是递增的
        for i in range(len(test_state['progress_updates']) - 1):
            assert test_state['progress_updates'][i] < test_state['progress_updates'][i+1], \
                f"进度应该递增: {test_state['progress_updates'][i]} < {test_state['progress_updates'][i+1]}"

        logger.info(f"\n✅ 测试 3 通过: 成功接收并验证 {len(test_state['progress_updates'])} 次进度更新\n")

    finally:
        await cleanup_agents(agent_a, agent_b)


# ============================================================================
# 测试 4: 多智能体协作
# ============================================================================

@pytest.mark.asyncio
async def test_multi_agent_collaboration():
    """
    测试多智能体协作: 3个智能体协作完成任务

    场景：
    - Agent A 是主控者，需要完成一个复杂任务
    - Agent A 将任务分解，分别请求 Agent B 和 Agent C
    - Agent B 和 Agent C 并行工作
    - 两个子任务都完成后，Agent A 汇总结果
    """
    logger.info("\n" + "="*80)
    logger.info("测试 4: 多智能体协作")
    logger.info("="*80 + "\n")

    # 创建智能体
    agent_a = await create_test_agent("multi-agent-a", "MultiAgentA", ["coordinator"])
    agent_b = await create_test_agent("multi-agent-b", "MultiAgentB", ["data_processor"])
    agent_c = await create_test_agent("multi-agent-c", "MultiAgentC", ["analyzer"])

    # 测试状态
    test_state = {
        'b_request_received': False,
        'c_request_received': False,
        'b_accept_received': False,
        'c_accept_received': False,
        'b_complete_received': False,
        'c_complete_received': False,
        'b_result': None,
        'c_result': None,
        'session_ids': {}
    }

    # Agent B 的请求处理器
    async def handle_b_request(data):
        logger.info(f"📥 Agent B 收到 REQUEST: {data['payload']['description']}")
        test_state['b_request_received'] = True

        # 接受请求
        await agent_b.send_accept(
            to_agent=data['from_agent'],
            request_id=data['payload']['request_id'],
            estimated_time=5,
            reply_to=data['message_id']
        )
        logger.info(f"✅ Agent B 发送 ACCEPT")

    # Agent C 的请求处理器
    async def handle_c_request(data):
        logger.info(f"📥 Agent C 收到 REQUEST: {data['payload']['description']}")
        test_state['c_request_received'] = True

        # 接受请求
        await agent_c.send_accept(
            to_agent=data['from_agent'],
            request_id=data['payload']['request_id'],
            estimated_time=5,
            reply_to=data['message_id']
        )
        logger.info(f"✅ Agent C 发送 ACCEPT")

    # Agent A 的接受处理器
    async def handle_accept(data):
        from_agent = data['from_agent']
        session_id = data['payload']['session_id']
        test_state['session_ids'][from_agent] = session_id

        if from_agent == "multi-agent-b":
            logger.info(f"📥 Agent A 收到 Agent B 的 ACCEPT")
            test_state['b_accept_received'] = True
            # Agent B 开始工作
            asyncio.create_task(agent_b_work(session_id))
        elif from_agent == "multi-agent-c":
            logger.info(f"📥 Agent A 收到 Agent C 的 ACCEPT")
            test_state['c_accept_received'] = True
            # Agent C 开始工作
            asyncio.create_task(agent_c_work(session_id))

    # Agent B 的工作
    async def agent_b_work(session_id: str):
        await asyncio.sleep(0.5)
        await agent_b.send_progress(
            to_agent="multi-agent-a",
            session_id=session_id,
            progress=0.5,
            status="processing",
            message="正在处理数据"
        )
        logger.info("📊 Agent B 发送进度: 50%")

        await asyncio.sleep(0.5)
        await agent_b.send_complete(
            to_agent="multi-agent-a",
            session_id=session_id,
            status="success",
            execution_time=1,
            result={"processed_data": [1, 2, 3, 4, 5], "count": 5}
        )
        logger.info("✅ Agent B 完成任务")

    # Agent C 的工作
    async def agent_c_work(session_id: str):
        await asyncio.sleep(0.7)
        await agent_c.send_progress(
            to_agent="multi-agent-a",
            session_id=session_id,
            progress=0.5,
            status="analyzing",
            message="正在分析数据"
        )
        logger.info("📊 Agent C 发送进度: 50%")

        await asyncio.sleep(0.7)
        await agent_c.send_complete(
            to_agent="multi-agent-a",
            session_id=session_id,
            status="success",
            execution_time=1,
            result={"analysis": "positive_trend", "confidence": 0.95}
        )
        logger.info("✅ Agent C 完成任务")

    # Agent A 的完成处理器
    async def handle_complete(data):
        from_agent = data['from_agent']
        result = data['payload'].get('result')

        if from_agent == "multi-agent-b":
            logger.info(f"📥 Agent A 收到 Agent B 的 COMPLETE")
            test_state['b_complete_received'] = True
            test_state['b_result'] = result
        elif from_agent == "multi-agent-c":
            logger.info(f"📥 Agent A 收到 Agent C 的 COMPLETE")
            test_state['c_complete_received'] = True
            test_state['c_result'] = result

        # 检查是否都完成
        if test_state['b_complete_received'] and test_state['c_complete_received']:
            logger.info("🎉 所有子任务完成，Agent A 汇总结果")
            logger.info(f"   Agent B 结果: {test_state['b_result']}")
            logger.info(f"   Agent C 结果: {test_state['c_result']}")

    # 注册事件处理器
    agent_b.on('request', handle_b_request)
    agent_c.on('request', handle_c_request)
    agent_a.on('accept', handle_accept)
    agent_a.on('complete', handle_complete)

    try:
        # Agent A 发送两个请求
        logger.info("📤 Agent A 发送 REQUEST 到 Agent B (数据处理)")
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        await agent_a.send_request(
            to_agent="multi-agent-b",
            task_id=2001,
            task_type="data_processing",
            description="处理原始数据",
            required_capability="data_processor",
            reward_share=0.4,
            deadline=deadline,
            input_data={"raw_data": [10, 20, 30, 40, 50]}
        )

        await asyncio.sleep(0.2)

        logger.info("📤 Agent A 发送 REQUEST 到 Agent C (数据分析)")
        await agent_a.send_request(
            to_agent="multi-agent-c",
            task_id=2002,
            task_type="analysis",
            description="分析处理后的数据",
            required_capability="analyzer",
            reward_share=0.4,
            deadline=deadline
        )

        # 等待所有任务完成
        logger.info("⏳ 等待所有子任务完成...")
        timeout = 10
        start_time = asyncio.get_event_loop().time()

        while not (test_state['b_complete_received'] and test_state['c_complete_received']):
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("协作任务超时")
            await asyncio.sleep(0.1)

        # 验证结果
        assert test_state['b_request_received'], "Agent B 应该收到 REQUEST"
        assert test_state['c_request_received'], "Agent C 应该收到 REQUEST"
        assert test_state['b_accept_received'], "Agent A 应该收到 Agent B 的 ACCEPT"
        assert test_state['c_accept_received'], "Agent A 应该收到 Agent C 的 ACCEPT"
        assert test_state['b_complete_received'], "Agent A 应该收到 Agent B 的 COMPLETE"
        assert test_state['c_complete_received'], "Agent A 应该收到 Agent C 的 COMPLETE"
        assert test_state['b_result'] is not None, "Agent B 应该返回结果"
        assert test_state['c_result'] is not None, "Agent C 应该返回结果"

        logger.info("\n✅ 测试 4 通过: 多智能体协作成功\n")

    finally:
        await cleanup_agents(agent_a, agent_b, agent_c)


# ============================================================================
# 测试 5: 智能体任务交接
# ============================================================================

@pytest.mark.asyncio
async def test_agent_handoff():
    """
    测试智能体之间的任务交接

    场景：
    - Agent A 请求 Agent B 完成任务
    - Agent B 接受后发现需要 Agent C 的帮助
    - Agent B 请求 Agent C 完成子任务
    - Agent C 完成后，Agent B 汇总并完成原始任务
    """
    logger.info("\n" + "="*80)
    logger.info("测试 5: 智能体任务交接")
    logger.info("="*80 + "\n")

    # 创建智能体
    agent_a = await create_test_agent("handoff-agent-a", "HandoffAgentA", ["requester"])
    agent_b = await create_test_agent("handoff-agent-b", "HandoffAgentB", ["processor"])
    agent_c = await create_test_agent("handoff-agent-c", "HandoffAgentC", ["specialist"])

    # 测试状态
    test_state = {
        'a_to_b_request': False,
        'b_accept': False,
        'b_to_c_request': False,
        'c_accept': False,
        'c_complete': False,
        'b_complete': False,
        'session_a_b': None,
        'session_b_c': None
    }

    # Agent B 收到 Agent A 的请求
    async def handle_b_request_from_a(data):
        if data['from_agent'] == "handoff-agent-a":
            logger.info(f"📥 Agent B 收到 Agent A 的 REQUEST")
            test_state['a_to_b_request'] = True

            # 接受请求
            await agent_b.send_accept(
                to_agent=data['from_agent'],
                request_id=data['payload']['request_id'],
                estimated_time=10,
                reply_to=data['message_id']
            )
            logger.info(f"✅ Agent B 发送 ACCEPT 给 Agent A")

    # Agent A 收到 Agent B 的接受
    async def handle_a_accept(data):
        if data['from_agent'] == "handoff-agent-b":
            logger.info(f"📥 Agent A 收到 Agent B 的 ACCEPT")
            test_state['b_accept'] = True
            test_state['session_a_b'] = data['payload']['session_id']

            # Agent B 发现需要 Agent C 的帮助
            asyncio.create_task(agent_b_request_c())

    # Agent B 请求 Agent C
    async def agent_b_request_c():
        await asyncio.sleep(0.5)
        logger.info("📤 Agent B 发现需要专家帮助，请求 Agent C")
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        await agent_b.send_request(
            to_agent="handoff-agent-c",
            task_id=3001,
            task_type="specialized_task",
            description="需要专家处理的子任务",
            required_capability="specialist",
            reward_share=0.3,
            deadline=deadline
        )

    # Agent C 收到 Agent B 的请求
    async def handle_c_request_from_b(data):
        if data['from_agent'] == "handoff-agent-b":
            logger.info(f"📥 Agent C 收到 Agent B 的 REQUEST")
            test_state['b_to_c_request'] = True

            # 接受请求
            await agent_c.send_accept(
                to_agent=data['from_agent'],
                request_id=data['payload']['request_id'],
                estimated_time=5,
                reply_to=data['message_id']
            )
            logger.info(f"✅ Agent C 发送 ACCEPT 给 Agent B")

    # Agent B 收到 Agent C 的接受
    async def handle_b_accept(data):
        if data['from_agent'] == "handoff-agent-c":
            logger.info(f"📥 Agent B 收到 Agent C 的 ACCEPT")
            test_state['c_accept'] = True
            test_state['session_b_c'] = data['payload']['session_id']

            # Agent C 开始工作
            asyncio.create_task(agent_c_work())

    # Agent C 的工作
    async def agent_c_work():
        await asyncio.sleep(0.5)
        await agent_c.send_progress(
            to_agent="handoff-agent-b",
            session_id=test_state['session_b_c'],
            progress=0.5,
            status="processing",
            message="专家处理中"
        )
        logger.info("📊 Agent C 发送进度: 50%")

        await asyncio.sleep(0.5)
        await agent_c.send_complete(
            to_agent="handoff-agent-b",
            session_id=test_state['session_b_c'],
            status="success",
            execution_time=1,
            result={"specialist_output": "expert_analysis_complete"}
        )
        logger.info("✅ Agent C 完成子任务")

    # Agent B 收到 Agent C 的完成
    async def handle_b_complete_from_c(data):
        if data['from_agent'] == "handoff-agent-c":
            logger.info(f"📥 Agent B 收到 Agent C 的 COMPLETE")
            test_state['c_complete'] = True

            # Agent B 汇总结果并完成原始任务
            await asyncio.sleep(0.3)
            await agent_b.send_complete(
                to_agent="handoff-agent-a",
                session_id=test_state['session_a_b'],
                status="success",
                execution_time=2,
                result={
                    "main_result": "task_completed",
                    "sub_task_result": data['payload']['result']
                }
            )
            logger.info("✅ Agent B 完成主任务并返回给 Agent A")

    # Agent A 收到 Agent B 的完成
    async def handle_a_complete(data):
        if data['from_agent'] == "handoff-agent-b":
            logger.info(f"📥 Agent A 收到 Agent B 的 COMPLETE")
            logger.info(f"   最终结果: {data['payload']['result']}")
            test_state['b_complete'] = True

    # 注册事件处理器
    agent_b.on('request', handle_b_request_from_a)
    agent_a.on('accept', handle_a_accept)
    agent_c.on('request', handle_c_request_from_b)
    agent_b.on('accept', handle_b_accept)
    agent_b.on('complete', handle_b_complete_from_c)
    agent_a.on('complete', handle_a_complete)

    try:
        # Agent A 发送请求
        logger.info("📤 Agent A 发送 REQUEST 到 Agent B")
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        await agent_a.send_request(
            to_agent="handoff-agent-b",
            task_id=3000,
            task_type="complex_task",
            description="需要多步处理的复杂任务",
            required_capability="processor",
            reward_share=0.6,
            deadline=deadline
        )

        # 等待完整流程完成
        logger.info("⏳ 等待任务交接流程完成...")
        timeout = 15
        start_time = asyncio.get_event_loop().time()

        while not test_state['b_complete']:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("任务交接超时")
            await asyncio.sleep(0.1)

        # 验证结果
        assert test_state['a_to_b_request'], "Agent B 应该收到 Agent A 的请求"
        assert test_state['b_accept'], "Agent A 应该收到 Agent B 的接受"
        assert test_state['b_to_c_request'], "Agent C 应该收到 Agent B 的请求"
        assert test_state['c_accept'], "Agent B 应该收到 Agent C 的接受"
        assert test_state['c_complete'], "Agent B 应该收到 Agent C 的完成"
        assert test_state['b_complete'], "Agent A 应该收到 Agent B 的完成"

        logger.info("\n✅ 测试 5 通过: 智能体任务交接成功\n")

    finally:
        await cleanup_agents(agent_a, agent_b, agent_c)


# ============================================================================
# 测试 6: 知识分享流程
# ============================================================================

@pytest.mark.asyncio
async def test_knowledge_sharing():
    """
    测试知识分享流程: SHARE消息广播

    场景：
    - Agent A 完成一个任务后，发现了有价值的知识
    - Agent A 向所有在线智能体广播 SHARE 消息
    - Agent B 和 Agent C 都收到知识分享
    """
    logger.info("\n" + "="*80)
    logger.info("测试 6: 知识分享流程")
    logger.info("="*80 + "\n")

    # 创建智能体
    agent_a = await create_test_agent("share-agent-a", "ShareAgentA", ["researcher"])
    agent_b = await create_test_agent("share-agent-b", "ShareAgentB", ["learner"])
    agent_c = await create_test_agent("share-agent-c", "ShareAgentC", ["learner"])

    # 测试状态
    test_state = {
        'b_received_share': False,
        'c_received_share': False,
        'shared_content': None
    }

    # Agent B 收到分享
    async def handle_b_share(data):
        logger.info(f"📥 Agent B 收到 SHARE: {data['payload']['title']}")
        logger.info(f"   内容: {data['payload']['description']}")
        test_state['b_received_share'] = True
        test_state['shared_content'] = data['payload']['content']

    # Agent C 收到分享
    async def handle_c_share(data):
        logger.info(f"📥 Agent C 收到 SHARE: {data['payload']['title']}")
        logger.info(f"   内容: {data['payload']['description']}")
        test_state['c_received_share'] = True

    # 注册事件处理器
    agent_b.on('share', handle_b_share)
    agent_c.on('share', handle_c_share)

    try:
        # 等待所有智能体注册完成
        await asyncio.sleep(0.5)

        # Agent A 发送知识分享
        logger.info("📤 Agent A 广播知识分享")
        await agent_a.send_share(
            to_agents=["share-agent-b", "share-agent-c"],
            share_type="solution",
            title="高效数据处理方法",
            description="发现了一种新的数据处理优化方法",
            content={
                "method": "batch_processing",
                "performance_gain": "50%",
                "applicable_to": ["large_datasets", "real_time_processing"]
            },
            tags=["optimization", "data_processing", "performance"]
        )

        # 等待分享被接收
        logger.info("⏳ 等待知识分享被接收...")
        timeout = 5
        start_time = asyncio.get_event_loop().time()

        while not (test_state['b_received_share'] and test_state['c_received_share']):
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("知识分享超时")
            await asyncio.sleep(0.1)

        # 验证结果
        assert test_state['b_received_share'], "Agent B 应该收到知识分享"
        assert test_state['c_received_share'], "Agent C 应该收到知识分享"
        assert test_state['shared_content'] is not None, "应该有分享内容"
        assert test_state['shared_content']['method'] == "batch_processing", "分享内容应该正确"

        logger.info("\n✅ 测试 6 通过: 知识分享流程成功\n")

    finally:
        await cleanup_agents(agent_a, agent_b, agent_c)


# ============================================================================
# 测试 7: 选择性分享
# ============================================================================

@pytest.mark.asyncio
async def test_selective_sharing():
    """
    测试选择性知识分享

    场景：
    - Agent A 只向具有特定能力的智能体分享知识
    - Agent B 有目标能力，应该收到分享
    - Agent C 没有目标能力，不应该收到分享
    """
    logger.info("\n" + "="*80)
    logger.info("测试 7: 选择性分享")
    logger.info("="*80 + "\n")

    # 创建智能体
    agent_a = await create_test_agent("selective-agent-a", "SelectiveAgentA", ["expert"])
    agent_b = await create_test_agent("selective-agent-b", "SelectiveAgentB", ["advanced_learner"])
    agent_c = await create_test_agent("selective-agent-c", "SelectiveAgentC", ["basic_learner"])

    # 测试状态
    test_state = {
        'b_received_share': False,
        'c_received_share': False
    }

    # Agent B 收到分享
    async def handle_b_share(data):
        logger.info(f"📥 Agent B 收到 SHARE: {data['payload']['title']}")
        test_state['b_received_share'] = True

    # Agent C 收到分享（不应该发生）
    async def handle_c_share(data):
        logger.info(f"📥 Agent C 收到 SHARE: {data['payload']['title']}")
        test_state['c_received_share'] = True

    # 注册事件处理器
    agent_b.on('share', handle_b_share)
    agent_c.on('share', handle_c_share)

    try:
        # 等待所有智能体注册完成
        await asyncio.sleep(0.5)

        # Agent A 只向 Agent B 分享（选择性分享）
        logger.info("📤 Agent A 向 Agent B 选择性分享高级知识")
        await agent_a.send_share(
            to_agents=["selective-agent-b"],  # 只发送给 Agent B
            share_type="knowledge",
            title="高级算法优化技巧",
            description="适合高级学习者的算法优化知识",
            content={
                "algorithm": "advanced_optimization",
                "complexity": "O(n log n)",
                "prerequisites": ["data_structures", "algorithms"]
            },
            tags=["advanced", "algorithms", "optimization"]
        )

        # 等待一段时间
        logger.info("⏳ 等待分享传递...")
        await asyncio.sleep(2)

        # 验证结果
        assert test_state['b_received_share'], "Agent B 应该收到知识分享"
        assert not test_state['c_received_share'], "Agent C 不应该收到知识分享"

        logger.info("\n✅ 测试 7 通过: 选择性分享成功\n")

    finally:
        await cleanup_agents(agent_a, agent_b, agent_c)


# ============================================================================
# 测试 8: 错误恢复流程
# ============================================================================

@pytest.mark.asyncio
async def test_agent_failure_recovery():
    """
    测试智能体失败后的恢复

    场景：
    - Agent A 请求 Agent B 完成任务
    - Agent B 接受任务但执行失败
    - Agent B 发送 COMPLETE 消息，状态为 failed
    - Agent A 收到失败通知并处理
    """
    logger.info("\n" + "="*80)
    logger.info("测试 8: 错误恢复流程")
    logger.info("="*80 + "\n")

    # 创建智能体
    agent_a = await create_test_agent("recovery-agent-a", "RecoveryAgentA", ["requester"])
    agent_b = await create_test_agent("recovery-agent-b", "RecoveryAgentB", ["worker"])

    # 测试状态
    test_state = {
        'request_received': False,
        'accept_received': False,
        'complete_received': False,
        'task_failed': False,
        'error_message': None,
        'session_id': None
    }

    # Agent B 的请求处理器
    async def handle_request(data):
        logger.info(f"📥 Agent B 收到 REQUEST")
        test_state['request_received'] = True

        # 接受请求
        await agent_b.send_accept(
            to_agent=data['from_agent'],
            request_id=data['payload']['request_id'],
            estimated_time=5,
            reply_to=data['message_id']
        )
        logger.info(f"✅ Agent B 发送 ACCEPT")

    # Agent A 的接受处理器
    async def handle_accept(data):
        logger.info(f"📥 Agent A 收到 ACCEPT")
        test_state['accept_received'] = True
        test_state['session_id'] = data['payload']['session_id']

        # Agent B 开始工作但会失败
        asyncio.create_task(agent_b_work_and_fail(data['payload']['session_id']))

    # Agent B 工作并失败
    async def agent_b_work_and_fail(session_id: str):
        await asyncio.sleep(0.5)

        # 发送进度
        await agent_b.send_progress(
            to_agent="recovery-agent-a",
            session_id=session_id,
            progress=0.3,
            status="processing",
            message="开始处理任务"
        )
        logger.info("📊 Agent B 发送进度: 30%")

        await asyncio.sleep(0.5)

        # 模拟失败
        logger.warning("⚠️ Agent B 任务执行失败")
        await agent_b.send_complete(
            to_agent="recovery-agent-a",
            session_id=session_id,
            status="failed",
            execution_time=1,
            error="数据处理错误: 输入格式不正确"
        )
        logger.info("❌ Agent B 发送 COMPLETE (失败)")

    # Agent A 的完成处理器
    async def handle_complete(data):
        logger.info(f"📥 Agent A 收到 COMPLETE")
        status = data['payload']['status']
        test_state['complete_received'] = True

        if status == "failed":
            test_state['task_failed'] = True
            test_state['error_message'] = data['payload'].get('error')
            logger.warning(f"⚠️ 任务失败: {test_state['error_message']}")
            logger.info("🔄 Agent A 可以选择重试或请求其他智能体")

    # 注册事件处理器
    agent_b.on('request', handle_request)
    agent_a.on('accept', handle_accept)
    agent_a.on('complete', handle_complete)

    try:
        # 发送请求
        logger.info("📤 Agent A 发送 REQUEST 到 Agent B")
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        await agent_a.send_request(
            to_agent="recovery-agent-b",
            task_id=4001,
            task_type="risky_task",
            description="可能失败的任务",
            required_capability="worker",
            reward_share=0.5,
            deadline=deadline
        )

        # 等待完成（包括失败）
        logger.info("⏳ 等待任务完成...")
        timeout = 10
        start_time = asyncio.get_event_loop().time()

        while not test_state['complete_received']:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("任务超时")
            await asyncio.sleep(0.1)

        # 验证结果
        assert test_state['request_received'], "Agent B 应该收到 REQUEST"
        assert test_state['accept_received'], "Agent A 应该收到 ACCEPT"
        assert test_state['complete_received'], "Agent A 应该收到 COMPLETE"
        assert test_state['task_failed'], "任务应该失败"
        assert test_state['error_message'] is not None, "应该有错误消息"

        logger.info("\n✅ 测试 8 通过: 错误恢复流程成功\n")

    finally:
        await cleanup_agents(agent_a, agent_b)


# ============================================================================
# 主函数 - 运行所有测试
# ============================================================================

if __name__ == "__main__":
    """
    直接运行此文件以执行所有测试

    使用方法:
    python test_workflow_integration.py

    或使用 pytest:
    pytest test_workflow_integration.py -v
    """
    import sys

    async def run_all_tests():
        """运行所有测试"""
        tests = [
            ("测试 1: 完整协作流程", test_full_collaboration_workflow),
            ("测试 2: 拒绝流程", test_rejection_workflow),
            ("测试 3: 多次进度更新", test_multiple_progress_updates),
            ("测试 4: 多智能体协作", test_multi_agent_collaboration),
            ("测试 5: 智能体任务交接", test_agent_handoff),
            ("测试 6: 知识分享流程", test_knowledge_sharing),
            ("测试 7: 选择性分享", test_selective_sharing),
            ("测试 8: 错误恢复流程", test_agent_failure_recovery),
        ]

        passed = 0
        failed = 0

        print("\n" + "="*80)
        print("开始运行工作流集成测试")
        print("="*80 + "\n")

        for test_name, test_func in tests:
            try:
                await test_func()
                passed += 1
            except Exception as e:
                failed += 1
                logger.error(f"\n❌ {test_name} 失败: {e}\n")
                import traceback
                traceback.print_exc()

        print("\n" + "="*80)
        print(f"测试完成: {passed} 通过, {failed} 失败")
        print("="*80 + "\n")

        return failed == 0

    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)



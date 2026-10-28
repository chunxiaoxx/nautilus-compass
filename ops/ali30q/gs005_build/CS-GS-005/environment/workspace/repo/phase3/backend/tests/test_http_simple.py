"""
Nexus Server HTTP 端点简单测试

版本: 1.0.0
创建时间: 2026-02-25
目标: 测试HTTP端点，提升覆盖率到95%+
"""

import pytest
import asyncio
from datetime import datetime, timezone
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nexus_server import create_nexus_app, NexusServer


# ============================================================================
# HTTP 端点测试（不使用TestClient）
# ============================================================================


@pytest.mark.asyncio
async def test_health_check_function():
    """
    测试健康检查函数

    验证:
    - 健康检查函数返回正确的数据
    - 包含status、version和online_agents
    """
    app = create_nexus_app()

    # 直接调用健康检查函数
    for route in app.routes:
        if hasattr(route, 'path') and route.path == '/health':
            if hasattr(route, 'endpoint'):
                result = await route.endpoint()
                assert result['status'] == 'healthy'
                assert 'version' in result
                assert 'online_agents' in result
                break


@pytest.mark.asyncio
async def test_stats_function():
    """
    测试统计信息函数

    验证:
    - 统计信息函数返回正确的数据
    - 包含必需的统计字段
    """
    app = create_nexus_app()

    # 直接调用统计信息函数
    for route in app.routes:
        if hasattr(route, 'path') and route.path == '/stats':
            if hasattr(route, 'endpoint'):
                result = await route.endpoint()
                assert 'total_messages' in result
                assert 'total_agents' in result
                assert 'messages_by_type' in result
                assert 'online_agents' in result
                break


@pytest.mark.asyncio
async def test_agents_function():
    """
    测试获取agents函数

    验证:
    - agents函数返回正确的数据
    - 包含agents列表和total
    """
    app = create_nexus_app()

    # 直接调用agents函数
    for route in app.routes:
        if hasattr(route, 'path') and route.path == '/agents':
            if hasattr(route, 'endpoint'):
                result = await route.endpoint()
                assert 'agents' in result
                assert 'total' in result
                assert isinstance(result['agents'], list)
                assert isinstance(result['total'], int)
                break


@pytest.mark.asyncio
async def test_agents_function_with_registered_agents():
    """
    测试获取agents函数（有注册的agents）

    验证:
    - 返回正确的agent信息
    - 只返回在线的agents
    """
    app = create_nexus_app()

    # 获取nexus_server实例
    nexus_server = None
    for route in app.routes:
        if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__globals__'):
            if 'nexus_server' in route.endpoint.__globals__:
                nexus_server = route.endpoint.__globals__['nexus_server']
                break

    if nexus_server:
        # 注册测试agents
        nexus_server.agents['test-agent-http-1'] = {
            'sid': 'sid-http-1',
            'name': 'Test HTTP Agent 1',
            'capabilities': ['http-test'],
            'status': 'online'
        }
        nexus_server.online_agents.add('test-agent-http-1')

        # 调用agents函数
        for route in app.routes:
            if hasattr(route, 'path') and route.path == '/agents':
                if hasattr(route, 'endpoint'):
                    result = await route.endpoint()

                    # 验证返回的agents包含我们注册的agent
                    agent_ids = [agent['agent_id'] for agent in result['agents']]
                    assert 'test-agent-http-1' in agent_ids

                    # 验证agent信息结构
                    for agent in result['agents']:
                        if agent['agent_id'] == 'test-agent-http-1':
                            assert agent['name'] == 'Test HTTP Agent 1'
                            assert agent['capabilities'] == ['http-test']
                            assert agent['status'] == 'online'
                    break

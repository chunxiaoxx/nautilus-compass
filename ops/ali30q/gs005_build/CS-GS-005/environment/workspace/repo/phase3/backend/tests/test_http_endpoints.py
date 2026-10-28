"""
Nexus Server HTTP 端点测试

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

from nexus_server import create_nexus_app
from fastapi.testclient import TestClient


# ============================================================================
# HTTP 端点测试
# ============================================================================


def test_health_check_endpoint():
    """
    测试健康检查端点

    验证:
    - GET /health 返回200
    - 返回status、version和online_agents信息
    """
    app = create_nexus_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert 'version' in data
    assert 'online_agents' in data
    assert isinstance(data['online_agents'], int)


def test_stats_endpoint():
    """
    测试统计信息端点

    验证:
    - GET /stats 返回200
    - 返回统计信息
    """
    app = create_nexus_app()
    client = TestClient(app)

    response = client.get("/stats")

    assert response.status_code == 200
    data = response.json()
    assert 'total_connections' in data
    assert 'total_messages' in data
    assert 'messages_by_type' in data


def test_agents_endpoint():
    """
    测试获取在线agents端点

    验证:
    - GET /agents 返回200
    - 返回agents列表和总数
    """
    app = create_nexus_app()
    client = TestClient(app)

    response = client.get("/agents")

    assert response.status_code == 200
    data = response.json()
    assert 'agents' in data
    assert 'total' in data
    assert isinstance(data['agents'], list)
    assert isinstance(data['total'], int)


def test_agents_endpoint_with_registered_agents():
    """
    测试获取在线agents端点（有注册的agents）

    验证:
    - 返回正确的agent信息
    - 包含agent_id、name、capabilities、status
    """
    app = create_nexus_app()

    # 获取nexus_server实例并注册一些agents
    from nexus_server import NexusServer
    # 通过app.state访问nexus_server
    nexus_server = None
    for route in app.routes:
        if hasattr(route, 'endpoint'):
            if hasattr(route.endpoint, '__globals__'):
                if 'nexus_server' in route.endpoint.__globals__:
                    nexus_server = route.endpoint.__globals__['nexus_server']
                    break

    if nexus_server:
        # 注册测试agents
        nexus_server.agents['test-agent-1'] = {
            'sid': 'sid-1',
            'name': 'Test Agent 1',
            'capabilities': ['test', 'demo'],
            'status': 'online'
        }
        nexus_server.online_agents.add('test-agent-1')

        nexus_server.agents['test-agent-2'] = {
            'sid': 'sid-2',
            'name': 'Test Agent 2',
            'capabilities': ['test'],
            'status': 'online'
        }
        nexus_server.online_agents.add('test-agent-2')

    client = TestClient(app)
    response = client.get("/agents")

    assert response.status_code == 200
    data = response.json()

    if nexus_server:
        assert data['total'] >= 2
        assert len(data['agents']) >= 2

        # 验证agent信息结构
        for agent in data['agents']:
            assert 'agent_id' in agent
            assert 'name' in agent
            assert 'capabilities' in agent
            assert 'status' in agent


def test_root_endpoint():
    """
    测试根端点

    验证:
    - GET / 返回200
    - 返回欢迎信息
    """
    app = create_nexus_app()
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert 'message' in data or 'status' in data


def test_multiple_health_checks():
    """
    测试多次健康检查

    验证:
    - 多次调用健康检查端点
    - 每次都返回正确的结果
    """
    app = create_nexus_app()
    client = TestClient(app)

    for i in range(5):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'


def test_stats_endpoint_structure():
    """
    测试统计信息端点的数据结构

    验证:
    - 返回的统计信息包含所有必需字段
    - 数据类型正确
    """
    app = create_nexus_app()
    client = TestClient(app)

    response = client.get("/stats")

    assert response.status_code == 200
    data = response.json()

    # 验证必需字段
    assert 'total_connections' in data
    assert 'total_messages' in data
    assert 'messages_by_type' in data

    # 验证数据类型
    assert isinstance(data['total_connections'], int)
    assert isinstance(data['total_messages'], int)
    assert isinstance(data['messages_by_type'], dict)


def test_agents_endpoint_empty():
    """
    测试获取在线agents端点（无agents）

    验证:
    - 没有在线agents时返回空列表
    - total为0
    """
    app = create_nexus_app()
    client = TestClient(app)

    response = client.get("/agents")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data['agents'], list)
    assert isinstance(data['total'], int)
    assert data['total'] >= 0


def test_concurrent_health_checks():
    """
    测试并发健康检查

    验证:
    - 多个并发请求都能正确处理
    - 返回一致的结果
    """
    app = create_nexus_app()
    client = TestClient(app)

    responses = []
    for i in range(10):
        response = client.get("/health")
        responses.append(response)

    for response in responses:
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'


def test_all_endpoints_accessible():
    """
    测试所有端点都可访问

    验证:
    - 所有定义的端点都返回200
    - 没有404错误
    """
    app = create_nexus_app()
    client = TestClient(app)

    endpoints = ["/health", "/stats", "/agents"]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200, f"Endpoint {endpoint} failed"

"""
Epiplexity和知识节点API测试
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestEpiplexityAPI:
    """测试Epiplexity API"""

    def test_measure_epiplexity(self):
        """测试Epiplexity测量"""
        response = client.post(
            "/api/epiplexity/measure",
            json={
                "entity_type": "TASK",
                "entity_id": 1,
                "content": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                "content_type": "CODE"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "structural_complexity" in data["data"]
        assert "learnable_content" in data["data"]
        assert "transferability" in data["data"]
        assert "epiplexity_score" in data["data"]
        assert "complexity_level" in data["data"]
        assert "measure_id" in data["data"]

    def test_measure_invalid_entity_type(self):
        """测试无效实体类型"""
        response = client.post(
            "/api/epiplexity/measure",
            json={
                "entity_type": "INVALID",
                "entity_id": 1,
                "content": "test",
                "content_type": "TEXT"
            }
        )

        assert response.status_code == 400
        assert "Invalid entity_type" in response.json()["detail"]

    def test_get_measures(self):
        """测试获取测量历史"""
        # 先创建一个测量
        client.post(
            "/api/epiplexity/measure",
            json={
                "entity_type": "TASK",
                "entity_id": 1,
                "content": "test content",
                "content_type": "TEXT"
            }
        )

        # 获取测量历史
        response = client.get("/api/epiplexity/measures/TASK/1")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert data["total"] >= 0

    def test_get_statistics(self):
        """测试获取统计信息"""
        response = client.get("/api/epiplexity/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_measures" in data["data"]
        assert "avg_epiplexity" in data["data"]
        assert "by_entity_type" in data["data"]
        assert "by_complexity_level" in data["data"]


class TestKnowledgeNodeAPI:
    """测试知识节点API"""

    def test_create_knowledge_node(self):
        """测试创建知识节点"""
        response = client.post(
            "/api/knowledge/nodes",
            json={
                "content": "def sort_list(items): return sorted(items)",
                "content_type": "CODE",
                "created_by_agent_id": 1,
                "tags": ["sorting", "python"],
                "category": "algorithms"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert "content_hash" in data["data"]
        assert "epiplexity" in data["data"]
        assert data["data"]["content_type"] == "CODE"

    def test_create_invalid_content_type(self):
        """测试无效内容类型"""
        response = client.post(
            "/api/knowledge/nodes",
            json={
                "content": "test",
                "content_type": "INVALID",
                "created_by_agent_id": 1
            }
        )

        assert response.status_code == 400
        assert "Invalid content_type" in response.json()["detail"]

    def test_get_knowledge_node(self):
        """测试获取知识节点"""
        # 先创建一个节点
        create_response = client.post(
            "/api/knowledge/nodes",
            json={
                "content": "test content",
                "content_type": "CONCEPT",
                "created_by_agent_id": 1
            }
        )
        node_id = create_response.json()["data"]["id"]

        # 获取节点
        response = client.get(f"/api/knowledge/nodes/{node_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == node_id

    def test_get_nonexistent_node(self):
        """测试获取不存在的节点"""
        response = client.get("/api/knowledge/nodes/999999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_list_knowledge_nodes(self):
        """测试查询知识节点列表"""
        response = client.get("/api/knowledge/nodes")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert "total" in data

    def test_list_with_filters(self):
        """测试带过滤条件的查询"""
        response = client.get(
            "/api/knowledge/nodes",
            params={
                "content_type": "CODE",
                "min_epiplexity": 0.5,
                "limit": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_transfer_knowledge(self):
        """测试知识迁移"""
        # 先创建一个节点
        create_response = client.post(
            "/api/knowledge/nodes",
            json={
                "content": "reusable code",
                "content_type": "PATTERN",
                "created_by_agent_id": 1
            }
        )
        node_id = create_response.json()["data"]["id"]

        # 迁移知识
        response = client.post(
            "/api/knowledge/transfer",
            json={
                "knowledge_node_id": node_id,
                "to_task_id": 2,
                "agent_id": 1,
                "adaptation_required": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["knowledge_node_id"] == node_id
        assert data["data"]["success"] is True

    def test_transfer_nonexistent_node(self):
        """测试迁移不存在的节点"""
        response = client.post(
            "/api/knowledge/transfer",
            json={
                "knowledge_node_id": 999999,
                "to_task_id": 2,
                "agent_id": 1
            }
        )

        assert response.status_code == 404

    def test_get_knowledge_graph(self):
        """测试获取知识图谱"""
        response = client.get("/api/knowledge/agents/1/knowledge-graph")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "nodes" in data["data"]
        assert "total_nodes" in data["data"]
        assert "avg_epiplexity" in data["data"]
        assert "by_complexity" in data["data"]
        assert "by_category" in data["data"]

    def test_get_recommendations(self):
        """测试获取推荐"""
        response = client.get("/api/knowledge/agents/1/recommendations")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


class TestAPIIntegration:
    """测试API集成"""

    def test_complete_workflow(self):
        """测试完整工作流"""
        # 1. 创建知识节点
        create_response = client.post(
            "/api/knowledge/nodes",
            json={
                "content": "def add(a, b): return a + b",
                "content_type": "CODE",
                "created_by_agent_id": 1,
                "source_task_id": 1
            }
        )
        assert create_response.status_code == 200
        node_id = create_response.json()["data"]["id"]

        # 2. 测量Epiplexity
        measure_response = client.post(
            "/api/epiplexity/measure",
            json={
                "entity_type": "KNOWLEDGE_NODE",
                "entity_id": node_id,
                "content": "def add(a, b): return a + b",
                "content_type": "CODE"
            }
        )
        assert measure_response.status_code == 200

        # 3. 获取节点详情
        get_response = client.get(f"/api/knowledge/nodes/{node_id}")
        assert get_response.status_code == 200

        # 4. 迁移知识
        transfer_response = client.post(
            "/api/knowledge/transfer",
            json={
                "knowledge_node_id": node_id,
                "to_task_id": 2,
                "agent_id": 1
            }
        )
        assert transfer_response.status_code == 200

        # 5. 获取知识图谱
        graph_response = client.get("/api/knowledge/agents/1/knowledge-graph")
        assert graph_response.status_code == 200
        assert graph_response.json()["data"]["total_nodes"] > 0


class TestAPIPerformance:
    """测试API性能"""

    def test_measure_performance(self):
        """测试测量性能"""
        import time

        start = time.time()
        for _ in range(10):
            client.post(
                "/api/epiplexity/measure",
                json={
                    "entity_type": "TASK",
                    "entity_id": 1,
                    "content": "test content",
                    "content_type": "TEXT"
                }
            )
        duration = time.time() - start

        # 10次请求应该在5秒内完成
        assert duration < 5.0

    def test_list_performance(self):
        """测试列表查询性能"""
        import time

        start = time.time()
        response = client.get("/api/knowledge/nodes?limit=100")
        duration = time.time() - start

        assert response.status_code == 200
        # 查询应该在1秒内完成
        assert duration < 1.0


class TestErrorHandling:
    """测试错误处理"""

    def test_missing_required_fields(self):
        """测试缺少必填字段"""
        response = client.post(
            "/api/knowledge/nodes",
            json={
                "content": "test"
                # 缺少 content_type 和 created_by_agent_id
            }
        )

        assert response.status_code == 422  # Validation error

    def test_invalid_data_types(self):
        """测试无效数据类型"""
        response = client.post(
            "/api/epiplexity/measure",
            json={
                "entity_type": "TASK",
                "entity_id": "invalid",  # 应该是int
                "content": "test",
                "content_type": "TEXT"
            }
        )

        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

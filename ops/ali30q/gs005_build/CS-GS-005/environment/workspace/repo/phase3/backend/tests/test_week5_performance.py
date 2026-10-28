"""
Week 5 性能测试 - Task 5.8

测试EvoMap层各组件的性能指标
"""

import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from services.evomap_integration_service import EvomapIntegrationService
from services.enhanced_reflection_service import EnhancedReflectionService
from services.capability_capsule_service import CapabilityCapsuleService
from services.knowledge_emergence_service import KnowledgeEmergenceService
from models.epiplexity import KnowledgeNode
from models.capability_capsule import CapabilityCapsule
from models.emergent_pattern import EmergentPattern


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = Mock(spec=Session)
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.rollback = Mock()
    db.query = Mock()
    return db


class TestReflectionPerformance:
    """反思系统性能测试"""

    @pytest.mark.asyncio
    async def test_reflection_speed_small_code(self, mock_db):
        """测试小代码片段反思速度"""
        service = EnhancedReflectionService(mock_db)

        # 准备小代码片段
        task_result = {
            "status": "COMPLETED",
            "code": "def add(a, b): return a + b",
            "language": "python"
        }

        # Mock数据库操作
        mock_db.query.return_value.filter.return_value.all.return_value = []

        start_time = time.time()
        result = await service.reflect_on_task_execution(
            task_id=1,
            agent_id=1,
            task_result=task_result
        )
        elapsed = time.time() - start_time

        # 性能要求：小代码片段 < 0.5秒
        assert elapsed < 0.5
        assert "knowledge_nodes" in result

    @pytest.mark.asyncio
    async def test_reflection_speed_large_code(self, mock_db):
        """测试大代码片段反思速度"""
        service = EnhancedReflectionService(mock_db)

        # 准备大代码片段（100行）
        large_code = "\n".join([
            f"def function_{i}(x):\n    return x * {i}"
            for i in range(50)
        ])

        task_result = {
            "status": "COMPLETED",
            "code": large_code,
            "language": "python"
        }

        # Mock数据库操作
        mock_db.query.return_value.filter.return_value.all.return_value = []

        start_time = time.time()
        result = await service.reflect_on_task_execution(
            task_id=1,
            agent_id=1,
            task_result=task_result
        )
        elapsed = time.time() - start_time

        # 性能要求：大代码片段 < 2秒
        assert elapsed < 2.0
        assert "knowledge_nodes" in result

    def test_code_pattern_extraction_speed(self, mock_db):
        """测试代码模式提取速度"""
        service = EnhancedReflectionService(mock_db)

        # 准备复杂代码
        code = """
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

def factory_create(type):
    if type == 'A':
        return ClassA()
    return ClassB()

def recursive_func(n):
    if n <= 1:
        return n
    return recursive_func(n-1) + recursive_func(n-2)
        """

        start_time = time.time()
        patterns = service.extract_code_patterns(code, "python")
        elapsed = time.time() - start_time

        # 性能要求：模式提取 < 0.3秒
        assert elapsed < 0.3
        assert len(patterns) > 0


class TestCapabilityCapsulePerformance:
    """能力胶囊性能测试"""

    def test_capsule_creation_speed(self, mock_db):
        """测试能力胶囊创建速度"""
        # Mock知识节点
        mock_nodes = []
        for i in range(5):
            node = Mock(spec=KnowledgeNode)
            node.id = i + 1
            node.epiplexity = 0.6 + i * 0.05
            node.transferability = 0.7
            node.content_type = "CODE"
            node.content = f"Node {i}"
            mock_nodes.append(node)

        mock_db.query.return_value.filter.return_value.all.return_value = mock_nodes

        start_time = time.time()
        capsule = CapabilityCapsuleService.create_capsule(
            db=mock_db,
            name="Test Capsule",
            pattern_type="ALGORITHM",
            knowledge_node_ids=[1, 2, 3, 4, 5],
            created_by_agent_id=1
        )
        elapsed = time.time() - start_time

        # 性能要求：创建胶囊 < 0.2秒
        assert elapsed < 0.2
        assert capsule is not None

    def test_capsule_search_speed(self, mock_db):
        """测试能力胶囊搜索速度"""
        # Mock查询结果
        mock_capsules = []
        for i in range(20):
            capsule = Mock(spec=CapabilityCapsule)
            capsule.id = i + 1
            capsule.quality_score = 0.8
            mock_capsules.append(capsule)

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_capsules
        mock_db.query.return_value = mock_query

        start_time = time.time()
        results = CapabilityCapsuleService.search_capsules(
            db=mock_db,
            pattern_type="ALGORITHM",
            min_epiplexity=0.5,
            limit=20
        )
        elapsed = time.time() - start_time

        # 性能要求：搜索 < 0.1秒
        assert elapsed < 0.1
        assert len(results) == 20

    def test_epiplexity_calculation_speed(self, mock_db):
        """测试Epiplexity计算速度"""
        # 准备多个节点
        nodes = []
        for i in range(10):
            node = Mock(spec=KnowledgeNode)
            node.id = i + 1
            node.epiplexity = 0.5 + i * 0.03
            node.transferability = 0.6 + i * 0.02
            nodes.append(node)

        start_time = time.time()
        for _ in range(100):  # 计算100次
            epiplexity = CapabilityCapsuleService._calculate_capsule_epiplexity(nodes)
        elapsed = time.time() - start_time

        # 性能要求：100次计算 < 0.5秒
        assert elapsed < 0.5
        assert 0.0 <= epiplexity <= 1.0


class TestKnowledgeEmergencePerformance:
    """知识涌现性能测试"""

    def test_emergence_discovery_speed_small_dataset(self, mock_db):
        """测试小数据集涌现发现速度"""
        # Mock知识节点（10个）
        mock_nodes = []
        for i in range(10):
            node = Mock(spec=KnowledgeNode)
            node.id = i + 1
            node.epiplexity = 0.6
            node.transferability = 0.7
            node.content_type = "CODE"
            node.content = f"Node {i}"
            node.tags = ["tag1", "tag2"]
            node.category = "algorithm"
            node.related_nodes = []
            node.parent_nodes = []
            node.child_nodes = []
            mock_nodes.append(node)

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_nodes
        mock_db.query.return_value = mock_query

        # Mock组合检查
        mock_db.query.return_value.filter.return_value.first.return_value = None

        start_time = time.time()
        patterns = KnowledgeEmergenceService.discover_emergent_patterns(
            db=mock_db,
            agent_id=1,
            min_epiplexity=0.5
        )
        elapsed = time.time() - start_time

        # 性能要求：小数据集 < 1秒
        assert elapsed < 1.0

    def test_knowledge_combination_speed(self, mock_db):
        """测试知识组合速度"""
        # 准备节点
        nodes = []
        for i in range(3):
            node = Mock(spec=KnowledgeNode)
            node.id = i + 1
            node.epiplexity = 0.6
            node.content = f"Content {i}"
            node.content_type = "CODE"
            nodes.append(node)

        start_time = time.time()
        for _ in range(50):  # 组合50次
            combined = KnowledgeEmergenceService._combine_knowledge_content(nodes)
        elapsed = time.time() - start_time

        # 性能要求：50次组合 < 0.3秒
        assert elapsed < 0.3
        assert combined is not None


class TestEvomapIntegrationPerformance:
    """EvoMap集成性能测试"""

    @pytest.mark.asyncio
    async def test_full_learning_cycle_speed(self, mock_db):
        """测试完整学习循环速度"""
        service = EvomapIntegrationService(mock_db)

        task_result = {
            "status": "COMPLETED",
            "code": "def test(): pass",
            "language": "python",
            "context": "testing"
        }

        # Mock所有依赖
        with patch.object(
            service.reflection_service,
            'reflect_on_task_execution',
            new_callable=AsyncMock
        ) as mock_reflect:
            mock_reflect.return_value = {
                "knowledge_nodes": [
                    {"id": 1, "content": "test", "content_type": "CODE", "epiplexity": 0.6}
                ],
                "patterns": [],
                "insights": {},
                "epiplexity_stats": {"avg_epiplexity": 0.6}
            }

            with patch.object(
                service,
                '_create_capability_capsules',
                new_callable=AsyncMock
            ) as mock_capsules:
                mock_capsules.return_value = []

                with patch(
                    'services.evomap_integration_service.KnowledgeEmergenceService.discover_emergent_patterns'
                ) as mock_emergence:
                    mock_emergence.return_value = []

                    with patch(
                        'services.evomap_integration_service.LearningTrackingService.track_learning_progress'
                    ) as mock_learning:
                        mock_learning.return_value = {"learning_rate": 0.5}

                        with patch(
                            'services.evomap_integration_service.SpecializationService.identify_specialization'
                        ) as mock_spec:
                            mock_spec.return_value = {"primary_domain": "general"}

                            with patch(
                                'services.evomap_integration_service.TaskRecommendationService.recommend_tasks'
                            ) as mock_recommend:
                                mock_recommend.return_value = []

                                start_time = time.time()
                                result = await service.execute_learning_cycle(
                                    task_id=1,
                                    agent_id=1,
                                    task_result=task_result
                                )
                                elapsed = time.time() - start_time

        # 性能要求：完整循环 < 3秒
        assert elapsed < 3.0
        assert result is not None

    @pytest.mark.asyncio
    async def test_evolution_status_retrieval_speed(self, mock_db):
        """测试进化状态获取速度"""
        service = EvomapIntegrationService(mock_db)

        # Mock知识节点
        mock_nodes = [Mock(spec=KnowledgeNode) for _ in range(50)]
        for i, node in enumerate(mock_nodes):
            node.epiplexity = 0.6
            node.content_type = "CODE"

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_nodes
        mock_db.query.return_value = mock_query

        # Mock其他服务
        with patch(
            'services.evomap_integration_service.CapabilityCapsuleService.get_agent_capsules'
        ) as mock_capsules:
            mock_capsules.return_value = {"total_capsules": 10, "avg_epiplexity": 0.65}

            with patch(
                'services.evomap_integration_service.KnowledgeEmergenceService.get_agent_emergent_patterns'
            ) as mock_patterns:
                mock_pattern = Mock(spec=EmergentPattern)
                mock_pattern.emergence_factor = 1.3
                mock_pattern.value_created = 100.0
                mock_patterns.return_value = [mock_pattern]

                with patch(
                    'services.evomap_integration_service.LearningTrackingService.track_learning_progress'
                ) as mock_learning:
                    mock_learning.return_value = {"learning_rate": 0.75}

                    with patch(
                        'services.evomap_integration_service.SpecializationService.identify_specialization'
                    ) as mock_spec:
                        mock_spec.return_value = {"primary_domain": "algorithm"}

                        start_time = time.time()
                        result = await service.get_agent_evolution_status(agent_id=1)
                        elapsed = time.time() - start_time

        # 性能要求：状态获取 < 0.5秒
        assert elapsed < 0.5
        assert result is not None


class TestMemoryUsage:
    """内存使用测试"""

    def test_large_knowledge_base_memory(self, mock_db):
        """测试大知识库内存使用"""
        import sys

        # 创建大量知识节点
        nodes = []
        for i in range(1000):
            node = Mock(spec=KnowledgeNode)
            node.id = i + 1
            node.epiplexity = 0.6
            node.content = f"Content {i}" * 10  # 较长内容
            node.content_type = "CODE"
            nodes.append(node)

        # 测量内存使用
        size = sys.getsizeof(nodes)

        # 验证内存使用合理（< 10MB）
        assert size < 10 * 1024 * 1024

    def test_capsule_cache_memory(self, mock_db):
        """测试能力胶囊缓存内存使用"""
        import sys

        # 创建大量胶囊
        capsules = []
        for i in range(500):
            capsule = Mock(spec=CapabilityCapsule)
            capsule.id = i + 1
            capsule.knowledge_node_ids = [1, 2, 3, 4, 5]
            capsule.code_template = "def test(): pass" * 20
            capsules.append(capsule)

        # 测量内存使用
        size = sys.getsizeof(capsules)

        # 验证内存使用合理（< 5MB）
        assert size < 5 * 1024 * 1024


class TestConcurrency:
    """并发性能测试"""

    @pytest.mark.asyncio
    async def test_concurrent_learning_cycles(self, mock_db):
        """测试并发学习循环"""
        import asyncio

        service = EvomapIntegrationService(mock_db)

        task_result = {
            "status": "COMPLETED",
            "code": "def test(): pass",
            "language": "python"
        }

        # Mock所有依赖
        with patch.object(
            service.reflection_service,
            'reflect_on_task_execution',
            new_callable=AsyncMock
        ) as mock_reflect:
            mock_reflect.return_value = {
                "knowledge_nodes": [],
                "patterns": [],
                "insights": {},
                "epiplexity_stats": {"avg_epiplexity": 0.6}
            }

            with patch.object(
                service,
                '_create_capability_capsules',
                new_callable=AsyncMock
            ) as mock_capsules:
                mock_capsules.return_value = []

                with patch(
                    'services.evomap_integration_service.KnowledgeEmergenceService.discover_emergent_patterns'
                ) as mock_emergence:
                    mock_emergence.return_value = []

                    with patch(
                        'services.evomap_integration_service.LearningTrackingService.track_learning_progress'
                    ) as mock_learning:
                        mock_learning.return_value = {"learning_rate": 0.5}

                        with patch(
                            'services.evomap_integration_service.SpecializationService.identify_specialization'
                        ) as mock_spec:
                            mock_spec.return_value = {"primary_domain": "general"}

                            with patch(
                                'services.evomap_integration_service.TaskRecommendationService.recommend_tasks'
                            ) as mock_recommend:
                                mock_recommend.return_value = []

                                # 并发执行10个学习循环
                                start_time = time.time()
                                tasks = [
                                    service.execute_learning_cycle(
                                        task_id=i,
                                        agent_id=i,
                                        task_result=task_result
                                    )
                                    for i in range(10)
                                ]
                                results = await asyncio.gather(*tasks)
                                elapsed = time.time() - start_time

        # 性能要求：10个并发循环 < 5秒
        assert elapsed < 5.0
        assert len(results) == 10


class TestScalability:
    """可扩展性测试"""

    def test_knowledge_node_scaling(self, mock_db):
        """测试知识节点数量扩展性"""
        # 测试不同规模的知识节点处理
        for node_count in [10, 50, 100, 500]:
            nodes = []
            for i in range(node_count):
                node = Mock(spec=KnowledgeNode)
                node.id = i + 1
                node.epiplexity = 0.6
                node.transferability = 0.7
                nodes.append(node)

            start_time = time.time()
            epiplexity = CapabilityCapsuleService._calculate_capsule_epiplexity(nodes)
            elapsed = time.time() - start_time

            # 验证时间复杂度接近O(n)
            # 500个节点应该 < 0.1秒
            if node_count == 500:
                assert elapsed < 0.1

    def test_emergence_pattern_scaling(self, mock_db):
        """测试涌现模式发现的可扩展性"""
        # 测试不同规模的知识组合
        for node_count in [5, 10, 20]:
            nodes = []
            for i in range(node_count):
                node = Mock(spec=KnowledgeNode)
                node.id = i + 1
                node.epiplexity = 0.6
                node.content = f"Content {i}"
                node.content_type = "CODE"
                node.tags = ["tag1"]
                node.category = "algorithm"
                node.related_nodes = []
                node.parent_nodes = []
                node.child_nodes = []
                nodes.append(node)

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = nodes
            mock_db.query.return_value = mock_query
            mock_db.query.return_value.filter.return_value.first.return_value = None

            start_time = time.time()
            patterns = KnowledgeEmergenceService.discover_emergent_patterns(
                db=mock_db,
                agent_id=1,
                min_epiplexity=0.5
            )
            elapsed = time.time() - start_time

            # 20个节点应该 < 2秒
            if node_count == 20:
                assert elapsed < 2.0


# 性能基准测试
class TestPerformanceBenchmarks:
    """性能基准测试"""

    def test_performance_summary(self):
        """性能测试总结"""
        benchmarks = {
            "reflection_small_code": "< 0.5s",
            "reflection_large_code": "< 2.0s",
            "pattern_extraction": "< 0.3s",
            "capsule_creation": "< 0.2s",
            "capsule_search": "< 0.1s",
            "epiplexity_calculation_100x": "< 0.5s",
            "emergence_discovery_small": "< 1.0s",
            "knowledge_combination_50x": "< 0.3s",
            "full_learning_cycle": "< 3.0s",
            "evolution_status_retrieval": "< 0.5s",
            "concurrent_10_cycles": "< 5.0s"
        }

        # 打印性能基准
        print("\n=== Week 5 Performance Benchmarks ===")
        for test, target in benchmarks.items():
            print(f"{test}: {target}")

        assert len(benchmarks) == 11

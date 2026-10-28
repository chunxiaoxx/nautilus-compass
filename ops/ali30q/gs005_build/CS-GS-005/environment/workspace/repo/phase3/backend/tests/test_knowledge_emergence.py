"""
测试知识涌现服务
"""
import pytest
from sqlalchemy.orm import Session
from models.epiplexity import KnowledgeNode
from models.emergent_pattern import EmergentPattern, KnowledgeCombination
from models.database import Agent
from services.knowledge_emergence_service import KnowledgeEmergenceService
from services.knowledge_node_service import KnowledgeNodeService


@pytest.fixture
def test_agent(db_session: Session):
    """创建测试Agent"""
    agent = Agent(
        agent_id=9001,
        owner="0x" + "1" * 40,
        name="Test Emergence Agent",
        reputation=100
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


@pytest.fixture
def test_knowledge_nodes(db_session: Session, test_agent: Agent):
    """创建测试知识节点"""
    nodes = []

    # 节点1: 设计模式
    node1 = KnowledgeNodeService.create_knowledge_node(
        db=db_session,
        content="""
        class Singleton:
            _instance = None

            def __new__(cls):
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                return cls._instance
        """,
        content_type="CODE",
        created_by_agent_id=test_agent.agent_id,
        tags=["design_pattern", "singleton"],
        category="DESIGN_PATTERN"
    )
    node1.verified = True
    nodes.append(node1)

    # 节点2: 工厂模式
    node2 = KnowledgeNodeService.create_knowledge_node(
        db=db_session,
        content="""
        class Factory:
            @staticmethod
            def create_product(product_type):
                if product_type == 'A':
                    return ProductA()
                elif product_type == 'B':
                    return ProductB()
        """,
        content_type="CODE",
        created_by_agent_id=test_agent.agent_id,
        tags=["design_pattern", "factory"],
        category="DESIGN_PATTERN"
    )
    node2.verified = True
    nodes.append(node2)

    # 节点3: 观察者模式
    node3 = KnowledgeNodeService.create_knowledge_node(
        db=db_session,
        content="""
        class Observer:
            def update(self, subject):
                pass

        class Subject:
            def __init__(self):
                self._observers = []

            def attach(self, observer):
                self._observers.append(observer)

            def notify(self):
                for observer in self._observers:
                    observer.update(self)
        """,
        content_type="CODE",
        created_by_agent_id=test_agent.agent_id,
        tags=["design_pattern", "observer"],
        category="DESIGN_PATTERN"
    )
    node3.verified = True
    nodes.append(node3)

    # 节点4: 算法模式
    node4 = KnowledgeNodeService.create_knowledge_node(
        db=db_session,
        content="""
        def binary_search(arr, target):
            left, right = 0, len(arr) - 1
            while left <= right:
                mid = (left + right) // 2
                if arr[mid] == target:
                    return mid
                elif arr[mid] < target:
                    left = mid + 1
                else:
                    right = mid - 1
            return -1
        """,
        content_type="CODE",
        created_by_agent_id=test_agent.agent_id,
        tags=["algorithm", "search"],
        category="ALGORITHM"
    )
    node4.verified = True
    nodes.append(node4)

    db_session.commit()
    return nodes


class TestKnowledgeEmergenceService:
    """测试知识涌现服务"""

    def test_analyze_knowledge_relationships(self, db_session: Session, test_knowledge_nodes: list):
        """测试知识关联分析"""
        relationships = KnowledgeEmergenceService._analyze_knowledge_relationships(
            test_knowledge_nodes
        )

        # 验证返回格式
        assert isinstance(relationships, dict)
        assert len(relationships) == len(test_knowledge_nodes)

        # 验证关联关系
        for node in test_knowledge_nodes:
            assert node.id in relationships
            related_ids = relationships[node.id]
            assert isinstance(related_ids, list)

    def test_has_tag_overlap(self, test_knowledge_nodes: list):
        """测试标签重叠检测"""
        node1 = test_knowledge_nodes[0]  # singleton
        node2 = test_knowledge_nodes[1]  # factory

        # 两个都有 design_pattern 标签
        has_overlap = KnowledgeEmergenceService._has_tag_overlap(node1, node2)
        assert has_overlap is True

        # 设计模式和算法模式
        node3 = test_knowledge_nodes[3]  # algorithm
        has_overlap = KnowledgeEmergenceService._has_tag_overlap(node1, node3)
        assert has_overlap is False

    def test_identify_combinable_knowledge(self, db_session: Session, test_knowledge_nodes: list):
        """测试可组合知识识别"""
        relationships = KnowledgeEmergenceService._analyze_knowledge_relationships(
            test_knowledge_nodes
        )

        combinable_groups = KnowledgeEmergenceService._identify_combinable_knowledge(
            test_knowledge_nodes,
            relationships
        )

        # 验证返回格式
        assert isinstance(combinable_groups, list)
        assert len(combinable_groups) > 0

        # 验证每个组合
        for group in combinable_groups:
            assert isinstance(group, list)
            assert len(group) >= KnowledgeEmergenceService.MIN_COMBINATION_SIZE
            assert len(group) <= KnowledgeEmergenceService.MAX_COMBINATION_SIZE

    def test_is_valid_combination(self, test_knowledge_nodes: list):
        """测试组合有效性检查"""
        # 测试节点的Epiplexity总和
        total_2 = sum(n.epiplexity for n in test_knowledge_nodes[:2])
        total_3 = sum(n.epiplexity for n in test_knowledge_nodes[:3])

        # 有效组合：2个节点（如果总和>=1.0）
        valid = KnowledgeEmergenceService._is_valid_combination(
            test_knowledge_nodes[:2]
        )
        # 根据实际Epiplexity判断
        if total_2 >= 1.0:
            assert valid is True
        else:
            assert valid is False

        # 有效组合：3个节点（总和应该>=1.0）
        valid = KnowledgeEmergenceService._is_valid_combination(
            test_knowledge_nodes[:3]
        )
        if total_3 >= 1.0:
            assert valid is True
        else:
            assert valid is False

        # 无效组合：1个节点
        valid = KnowledgeEmergenceService._is_valid_combination(
            test_knowledge_nodes[:1]
        )
        assert valid is False

    def test_combine_knowledge_content(self, test_knowledge_nodes: list):
        """测试知识内容组合"""
        combined = KnowledgeEmergenceService._combine_knowledge_content(
            test_knowledge_nodes[:2]
        )

        # 验证组合内容
        assert isinstance(combined, str)
        assert len(combined) > 0
        assert "Knowledge Component 1" in combined
        assert "Knowledge Component 2" in combined
        assert "Combined Pattern" in combined

    def test_determine_pattern_type(self, test_knowledge_nodes: list):
        """测试模式类型确定"""
        # 相同类型
        pattern_type = KnowledgeEmergenceService._determine_pattern_type(
            test_knowledge_nodes[:2]  # 都是CODE
        )
        assert pattern_type == "CODE"

        # 混合类型
        pattern_type = KnowledgeEmergenceService._determine_pattern_type(
            test_knowledge_nodes[:3]  # 都是CODE，但可能有不同类型
        )
        assert pattern_type in ["CODE", "HYBRID"]

    def test_attempt_combination(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试知识组合尝试"""
        # 尝试组合前2个节点
        pattern = KnowledgeEmergenceService._attempt_combination(
            db=db_session,
            knowledge_group=test_knowledge_nodes[:2],
            agent_id=test_agent.agent_id
        )

        # 验证组合记录
        combination = db_session.query(KnowledgeCombination).filter(
            KnowledgeCombination.attempted_by_agent_id == test_agent.agent_id
        ).first()
        assert combination is not None
        assert combination.combination_size == 2
        assert len(combination.knowledge_node_ids) == 2

        # 如果涌现，验证模式
        if pattern:
            assert isinstance(pattern, EmergentPattern)
            assert pattern.is_emergent is True
            assert pattern.emergence_factor >= KnowledgeEmergenceService.EMERGENCE_THRESHOLD
            assert pattern.combined_epiplexity > pattern.individual_sum
            assert pattern.discovered_by_agent_id == test_agent.agent_id

    def test_discover_emergent_patterns(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试涌现模式发现"""
        patterns = KnowledgeEmergenceService.discover_emergent_patterns(
            db=db_session,
            agent_id=test_agent.agent_id,
            min_epiplexity=0.3
        )

        # 验证返回格式
        assert isinstance(patterns, list)

        # 验证每个模式
        for pattern in patterns:
            assert isinstance(pattern, EmergentPattern)
            assert pattern.is_emergent is True
            assert pattern.emergence_factor >= KnowledgeEmergenceService.EMERGENCE_THRESHOLD
            assert pattern.discovered_by_agent_id == test_agent.agent_id
            assert len(pattern.source_knowledge_ids) >= 2

    def test_get_agent_emergent_patterns(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试获取Agent涌现模式"""
        # 先发现一些模式
        KnowledgeEmergenceService.discover_emergent_patterns(
            db=db_session,
            agent_id=test_agent.agent_id,
            min_epiplexity=0.3
        )

        # 获取模式
        patterns = KnowledgeEmergenceService.get_agent_emergent_patterns(
            db=db_session,
            agent_id=test_agent.agent_id,
            limit=10
        )

        # 验证返回格式
        assert isinstance(patterns, list)

        # 验证排序（按emergence_factor降序）
        if len(patterns) > 1:
            for i in range(len(patterns) - 1):
                assert patterns[i].emergence_factor >= patterns[i + 1].emergence_factor

    def test_apply_emergent_pattern(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试应用涌现模式"""
        # 先发现模式
        patterns = KnowledgeEmergenceService.discover_emergent_patterns(
            db=db_session,
            agent_id=test_agent.agent_id,
            min_epiplexity=0.3
        )

        if not patterns:
            pytest.skip("No emergent patterns discovered")

        pattern = patterns[0]
        initial_applied_count = pattern.applied_count
        initial_success_rate = pattern.success_rate

        # 应用模式（成功）
        KnowledgeEmergenceService.apply_emergent_pattern(
            db=db_session,
            pattern_id=pattern.id,
            task_id=1,
            agent_id=test_agent.agent_id,
            success=True
        )

        # 验证统计更新
        db_session.refresh(pattern)
        assert pattern.applied_count == initial_applied_count + 1
        assert pattern.success_rate >= initial_success_rate
        assert pattern.last_applied_at is not None

        # 应用模式（失败）
        KnowledgeEmergenceService.apply_emergent_pattern(
            db=db_session,
            pattern_id=pattern.id,
            task_id=2,
            agent_id=test_agent.agent_id,
            success=False
        )

        # 验证统计更新
        db_session.refresh(pattern)
        assert pattern.applied_count == initial_applied_count + 2

    def test_emergence_threshold(self, db_session: Session, test_agent: Agent):
        """测试涌现阈值"""
        # 创建低Epiplexity节点
        low_nodes = []
        for i in range(3):
            node = KnowledgeNodeService.create_knowledge_node(
                db=db_session,
                content=f"Simple content {i}",
                content_type="TEXT",
                created_by_agent_id=test_agent.agent_id
            )
            node.verified = True
            node.epiplexity = 0.2  # 低Epiplexity
            low_nodes.append(node)

        db_session.commit()

        # 尝试组合
        pattern = KnowledgeEmergenceService._attempt_combination(
            db=db_session,
            knowledge_group=low_nodes,
            agent_id=test_agent.agent_id
        )

        # 低Epiplexity节点不太可能产生涌现
        # 但我们验证涌现因子的计算
        combination = db_session.query(KnowledgeCombination).filter(
            KnowledgeCombination.attempted_by_agent_id == test_agent.agent_id
        ).order_by(KnowledgeCombination.id.desc()).first()

        assert combination is not None
        if pattern:
            assert pattern.emergence_factor >= KnowledgeEmergenceService.EMERGENCE_THRESHOLD

    def test_check_existing_combination(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试检查已存在的组合"""
        node_ids = [test_knowledge_nodes[0].id, test_knowledge_nodes[1].id]

        # 第一次检查：不存在
        exists = KnowledgeEmergenceService._check_existing_combination(
            db=db_session,
            knowledge_node_ids=node_ids
        )
        assert exists is False

        # 创建组合记录
        combination = KnowledgeCombination(
            knowledge_node_ids=sorted(node_ids),
            combination_size=2,
            success=False,
            attempted_by_agent_id=test_agent.agent_id
        )
        db_session.add(combination)
        db_session.commit()

        # 第二次检查：存在
        exists = KnowledgeEmergenceService._check_existing_combination(
            db=db_session,
            knowledge_node_ids=node_ids
        )
        assert exists is True

    def test_emergence_factor_calculation(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试涌现因子计算"""
        # 组合2个节点
        nodes = test_knowledge_nodes[:2]
        individual_sum = sum(node.epiplexity for node in nodes)

        pattern = KnowledgeEmergenceService._attempt_combination(
            db=db_session,
            knowledge_group=nodes,
            agent_id=test_agent.agent_id
        )

        # 验证涌现因子计算
        if pattern:
            expected_factor = pattern.combined_epiplexity / individual_sum
            assert abs(pattern.emergence_factor - expected_factor) < 0.001

            # 验证涌现条件
            if pattern.is_emergent:
                assert pattern.emergence_factor >= KnowledgeEmergenceService.EMERGENCE_THRESHOLD
                assert pattern.combined_epiplexity > individual_sum * KnowledgeEmergenceService.EMERGENCE_THRESHOLD


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

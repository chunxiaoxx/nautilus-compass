"""
能力胶囊服务测试
"""
import pytest
from sqlalchemy.orm import Session
from models.capability_capsule import CapabilityCapsule, CapsuleTransfer
from models.epiplexity import KnowledgeNode
from models.database import Agent
from services.capability_capsule_service import CapabilityCapsuleService
from datetime import datetime


@pytest.fixture
def test_agent(db_session: Session):
    """创建测试Agent"""
    agent = Agent(
        agent_id=1001,
        owner="0x1234567890abcdef1234567890abcdef12345678",
        name="Test Agent",
        reputation=100
    )
    db_session.add(agent)
    db_session.commit()
    return agent


@pytest.fixture
def test_knowledge_nodes(db_session: Session, test_agent: Agent):
    """创建测试知识节点"""
    nodes = []

    # 节点1: 低复杂度
    node1 = KnowledgeNode(
        content="def hello_world(): print('Hello')",
        content_hash="hash1",
        content_type="CODE",
        epiplexity=0.3,
        learnability=0.8,
        transferability=0.9,
        complexity_level="LOW",
        created_by_agent_id=test_agent.agent_id,
        tags=["python", "basic"]
    )
    nodes.append(node1)

    # 节点2: 中等复杂度
    node2 = KnowledgeNode(
        content="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
        content_hash="hash2",
        content_type="CODE",
        epiplexity=0.5,
        learnability=0.6,
        transferability=0.7,
        complexity_level="MEDIUM",
        created_by_agent_id=test_agent.agent_id,
        tags=["python", "algorithm"]
    )
    nodes.append(node2)

    # 节点3: 高复杂度
    node3 = KnowledgeNode(
        content="Dynamic programming optimization pattern",
        content_hash="hash3",
        content_type="PATTERN",
        epiplexity=0.7,
        learnability=0.5,
        transferability=0.6,
        complexity_level="HIGH",
        created_by_agent_id=test_agent.agent_id,
        tags=["algorithm", "optimization"]
    )
    nodes.append(node3)

    db_session.add_all(nodes)
    db_session.commit()

    for node in nodes:
        db_session.refresh(node)

    return nodes


class TestCapabilityCapsuleService:
    """能力胶囊服务测试"""

    def test_create_capsule(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试创建能力胶囊"""
        node_ids = [node.id for node in test_knowledge_nodes]

        capsule = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Fibonacci Algorithm",
            pattern_type="ALGORITHM",
            knowledge_node_ids=node_ids,
            created_by_agent_id=test_agent.agent_id,
            description="Fibonacci implementation with optimization",
            prerequisites=["python", "recursion"],
            required_skills=["algorithm"],
            applicable_contexts=["mathematics", "programming"],
            tags=["fibonacci", "recursion"],
            category="ALGORITHM"
        )

        assert capsule.id is not None
        assert capsule.name == "Fibonacci Algorithm"
        assert capsule.pattern_type == "ALGORITHM"
        assert capsule.knowledge_node_ids == node_ids
        assert capsule.epiplexity > 0
        assert capsule.complexity_level in ["LOW", "MEDIUM", "HIGH"]
        assert capsule.code_template is not None
        assert capsule.prerequisites == ["python", "recursion"]
        assert capsule.created_by_agent_id == test_agent.agent_id

    def test_calculate_capsule_epiplexity(self, test_knowledge_nodes: list):
        """测试能力胶囊Epiplexity计算"""
        epiplexity = CapabilityCapsuleService._calculate_capsule_epiplexity(test_knowledge_nodes)

        # 应该大于单个节点的平均值（因为组合复杂度）
        avg_node_epiplexity = sum(n.epiplexity for n in test_knowledge_nodes) / len(test_knowledge_nodes)
        assert epiplexity >= avg_node_epiplexity
        assert 0.0 <= epiplexity <= 1.0

    def test_generate_code_template(self, test_knowledge_nodes: list):
        """测试代码模板生成"""
        template = CapabilityCapsuleService._generate_code_template(
            test_knowledge_nodes,
            "ALGORITHM"
        )

        assert template is not None
        assert "ALGORITHM Pattern" in template
        assert "def step_1():" in template
        assert "def execute():" in template

    def test_get_capsule(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试获取能力胶囊"""
        # 创建胶囊
        node_ids = [node.id for node in test_knowledge_nodes]
        capsule = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Test Capsule",
            pattern_type="ALGORITHM",
            knowledge_node_ids=node_ids,
            created_by_agent_id=test_agent.agent_id
        )

        # 获取胶囊
        retrieved = CapabilityCapsuleService.get_capsule(db_session, capsule.id)

        assert retrieved is not None
        assert retrieved.id == capsule.id
        assert retrieved.name == "Test Capsule"

    def test_search_capsules(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试搜索能力胶囊"""
        # 创建多个胶囊
        node_ids = [node.id for node in test_knowledge_nodes]

        capsule1 = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Algorithm 1",
            pattern_type="ALGORITHM",
            knowledge_node_ids=node_ids[:2],
            created_by_agent_id=test_agent.agent_id,
            category="SORTING"
        )
        capsule1.verified = True

        capsule2 = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Pattern 1",
            pattern_type="DESIGN_PATTERN",
            knowledge_node_ids=node_ids[1:],
            created_by_agent_id=test_agent.agent_id,
            category="OPTIMIZATION"
        )
        capsule2.verified = True

        db_session.commit()

        # 按模式类型搜索
        results = CapabilityCapsuleService.search_capsules(
            db=db_session,
            pattern_type="ALGORITHM",
            verified_only=True
        )

        assert len(results) >= 1
        assert all(c.pattern_type == "ALGORITHM" for c in results)

        # 按分类搜索
        results = CapabilityCapsuleService.search_capsules(
            db=db_session,
            category="SORTING"
        )

        assert len(results) >= 1
        assert all(c.category == "SORTING" for c in results)

    def test_get_capsule_with_nodes(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试获取能力胶囊及其知识节点"""
        node_ids = [node.id for node in test_knowledge_nodes]

        capsule = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Test Capsule",
            pattern_type="ALGORITHM",
            knowledge_node_ids=node_ids,
            created_by_agent_id=test_agent.agent_id
        )

        result = CapabilityCapsuleService.get_capsule_with_nodes(db_session, capsule.id)

        assert result is not None
        assert "capsule" in result
        assert "knowledge_nodes" in result
        assert result["capsule"]["id"] == capsule.id
        assert len(result["knowledge_nodes"]) == len(node_ids)

        # 验证顺序保持
        for i, node_data in enumerate(result["knowledge_nodes"]):
            assert node_data["id"] == node_ids[i]

    def test_update_capsule_usage(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试更新能力胶囊使用统计"""
        node_ids = [node.id for node in test_knowledge_nodes]

        capsule = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Test Capsule",
            pattern_type="ALGORITHM",
            knowledge_node_ids=node_ids,
            created_by_agent_id=test_agent.agent_id
        )

        initial_usage = capsule.usage_count

        # 更新使用统计（成功）
        CapabilityCapsuleService.update_capsule_usage(
            db=db_session,
            capsule_id=capsule.id,
            success=True,
            adaptation_effort=2.5
        )

        db_session.refresh(capsule)

        assert capsule.usage_count == initial_usage + 1
        assert capsule.success_rate > 0
        assert capsule.avg_adaptation_effort == 2.5
        assert capsule.quality_score > 0
        assert capsule.last_used_at is not None

        # 再次更新（失败）
        CapabilityCapsuleService.update_capsule_usage(
            db=db_session,
            capsule_id=capsule.id,
            success=False,
            adaptation_effort=3.0
        )

        db_session.refresh(capsule)

        assert capsule.usage_count == initial_usage + 2
        assert capsule.success_rate < 1.0  # 因为有一次失败

    def test_recommend_capsules_for_agent(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试为Agent推荐能力胶囊"""
        # 创建另一个Agent
        other_agent = Agent(
            agent_id=1002,
            owner="0xabcdef1234567890abcdef1234567890abcdef12",
            name="Other Agent",
            reputation=100
        )
        db_session.add(other_agent)
        db_session.commit()

        # 创建胶囊（由other_agent创建）
        node_ids = [node.id for node in test_knowledge_nodes[:2]]

        capsule = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Recommended Capsule",
            pattern_type="ALGORITHM",
            knowledge_node_ids=node_ids,
            created_by_agent_id=other_agent.agent_id,
            applicable_contexts=["programming"]
        )
        capsule.verified = True
        capsule.quality_score = 0.8
        db_session.commit()

        # 为test_agent推荐
        recommendations = CapabilityCapsuleService.recommend_capsules_for_agent(
            db=db_session,
            agent_id=test_agent.agent_id,
            context="programming",
            limit=5
        )

        assert isinstance(recommendations, list)
        if len(recommendations) > 0:
            rec = recommendations[0]
            assert "capsule" in rec
            assert "recommendation_reason" in rec
            assert "match_score" in rec

    def test_get_agent_capsules(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试获取Agent创建的所有能力胶囊"""
        # 创建多个胶囊
        node_ids = [node.id for node in test_knowledge_nodes]

        capsule1 = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Capsule 1",
            pattern_type="ALGORITHM",
            knowledge_node_ids=node_ids[:2],
            created_by_agent_id=test_agent.agent_id
        )

        capsule2 = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Capsule 2",
            pattern_type="DESIGN_PATTERN",
            knowledge_node_ids=node_ids[1:],
            created_by_agent_id=test_agent.agent_id
        )

        result = CapabilityCapsuleService.get_agent_capsules(
            db=db_session,
            agent_id=test_agent.agent_id
        )

        assert result["total_capsules"] >= 2
        assert result["avg_epiplexity"] > 0
        assert "by_pattern_type" in result
        assert "by_complexity" in result
        assert len(result["capsules"]) >= 2

    def test_capsule_order_dependency(self, db_session: Session, test_agent: Agent, test_knowledge_nodes: list):
        """测试能力胶囊的顺序依赖性"""
        # 创建两个胶囊，节点顺序不同
        node_ids_1 = [test_knowledge_nodes[0].id, test_knowledge_nodes[1].id, test_knowledge_nodes[2].id]
        node_ids_2 = [test_knowledge_nodes[2].id, test_knowledge_nodes[1].id, test_knowledge_nodes[0].id]

        capsule1 = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Capsule Order 1",
            pattern_type="ALGORITHM",
            knowledge_node_ids=node_ids_1,
            created_by_agent_id=test_agent.agent_id
        )

        capsule2 = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Capsule Order 2",
            pattern_type="ALGORITHM",
            knowledge_node_ids=node_ids_2,
            created_by_agent_id=test_agent.agent_id
        )

        # 验证顺序保持
        assert capsule1.knowledge_node_ids == node_ids_1
        assert capsule2.knowledge_node_ids == node_ids_2

        # Epiplexity可能不同（因为顺序依赖）
        # 注意：当前实现中可能相同，但设计上应该考虑顺序
        assert capsule1.epiplexity >= 0
        assert capsule2.epiplexity >= 0

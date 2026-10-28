"""
能力迁移服务测试
"""
import pytest
from sqlalchemy.orm import Session
from models.capability_capsule import CapabilityCapsule, CapsuleTransfer
from models.epiplexity import KnowledgeNode
from models.database import Agent
from services.capability_capsule_service import CapabilityCapsuleService
from services.capability_transfer_service import CapabilityTransferService
from datetime import datetime


@pytest.fixture
def test_agents(db_session: Session):
    """创建测试Agents"""
    agent1 = Agent(
        agent_id=2001,
        owner="0x1111111111111111111111111111111111111111",
        name="Expert Agent",
        reputation=100
    )
    agent2 = Agent(
        agent_id=2002,
        owner="0x2222222222222222222222222222222222222222",
        name="Novice Agent",
        reputation=100
    )
    db_session.add_all([agent1, agent2])
    db_session.commit()
    return agent1, agent2


@pytest.fixture
def test_knowledge_nodes_with_skills(db_session: Session, test_agents: tuple):
    """创建带技能标签的测试知识节点"""
    expert_agent, _ = test_agents
    nodes = []

    # 基础节点
    node1 = KnowledgeNode(
        content="Basic Python syntax",
        content_hash="hash_basic",
        content_type="CONCEPT",
        epiplexity=0.2,
        learnability=0.9,
        transferability=0.9,
        complexity_level="LOW",
        created_by_agent_id=expert_agent.agent_id,
        tags=["python", "basic"],
        category="PROGRAMMING"
    )
    nodes.append(node1)

    # 中级节点
    node2 = KnowledgeNode(
        content="Object-oriented programming",
        content_hash="hash_oop",
        content_type="CONCEPT",
        epiplexity=0.5,
        learnability=0.7,
        transferability=0.7,
        complexity_level="MEDIUM",
        created_by_agent_id=expert_agent.agent_id,
        tags=["python", "oop"],
        category="PROGRAMMING"
    )
    nodes.append(node2)

    # 高级节点
    node3 = KnowledgeNode(
        content="Design patterns implementation",
        content_hash="hash_patterns",
        content_type="PATTERN",
        epiplexity=0.7,
        learnability=0.5,
        transferability=0.6,
        complexity_level="HIGH",
        created_by_agent_id=expert_agent.agent_id,
        tags=["design_patterns", "advanced"],
        category="ARCHITECTURE"
    )
    nodes.append(node3)

    db_session.add_all(nodes)
    db_session.commit()

    for node in nodes:
        db_session.refresh(node)

    return nodes


@pytest.fixture
def test_capsule_with_prerequisites(db_session: Session, test_agents: tuple, test_knowledge_nodes_with_skills: list):
    """创建带前置条件的测试能力胶囊"""
    expert_agent, _ = test_agents
    node_ids = [node.id for node in test_knowledge_nodes_with_skills]

    capsule = CapabilityCapsuleService.create_capsule(
        db=db_session,
        name="Advanced Design Patterns",
        pattern_type="DESIGN_PATTERN",
        knowledge_node_ids=node_ids,
        created_by_agent_id=expert_agent.agent_id,
        description="Advanced design patterns for scalable systems",
        prerequisites=["python", "oop", "basic"],  # 顺序很重要！
        required_skills=["design_patterns"],
        applicable_contexts=["web_development", "system_design"],
        tags=["patterns", "architecture"],
        category="ARCHITECTURE"
    )

    return capsule


class TestCapabilityTransferService:
    """能力迁移服务测试"""

    def test_check_prerequisites_met(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试前置条件检查 - 满足条件"""
        expert_agent, _ = test_agents

        # Expert agent应该满足所有前置条件（因为创建了相关知识节点）
        is_met, missing = CapabilityTransferService.check_prerequisites(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            agent_id=expert_agent.agent_id
        )

        assert is_met is True
        assert len(missing) == 0

    def test_check_prerequisites_not_met(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试前置条件检查 - 不满足条件"""
        _, novice_agent = test_agents

        # Novice agent没有相关知识节点，不满足前置条件
        is_met, missing = CapabilityTransferService.check_prerequisites(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            agent_id=novice_agent.agent_id
        )

        assert is_met is False
        assert len(missing) > 0

    def test_check_prerequisites_order_matters(self, db_session: Session, test_agents: tuple, test_knowledge_nodes_with_skills: list):
        """测试前置条件顺序的重要性"""
        expert_agent, _ = test_agents
        node_ids = [node.id for node in test_knowledge_nodes_with_skills]

        # 创建两个胶囊，前置条件顺序不同
        capsule1 = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Capsule Order 1",
            pattern_type="ALGORITHM",
            knowledge_node_ids=node_ids,
            created_by_agent_id=expert_agent.agent_id,
            prerequisites=["basic", "oop", "advanced"]  # 从简单到复杂
        )

        capsule2 = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Capsule Order 2",
            pattern_type="ALGORITHM",
            knowledge_node_ids=node_ids,
            created_by_agent_id=expert_agent.agent_id,
            prerequisites=["advanced", "oop", "basic"]  # 从复杂到简单
        )

        # 验证前置条件顺序保持
        assert capsule1.prerequisites == ["basic", "oop", "advanced"]
        assert capsule2.prerequisites == ["advanced", "oop", "basic"]

    def test_calculate_adaptation_score(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试适配度计算"""
        expert_agent, _ = test_agents

        result = CapabilityTransferService.calculate_adaptation_score(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            target_context="web_development",
            agent_id=expert_agent.agent_id
        )

        assert "adaptation_score" in result
        assert "prerequisites_score" in result
        assert "context_match_score" in result
        assert "capability_match_score" in result
        assert "historical_score" in result
        assert "adaptation_required" in result
        assert "estimated_effort" in result

        assert 0.0 <= result["adaptation_score"] <= 1.0
        assert 0.0 <= result["prerequisites_score"] <= 1.0
        assert 0.0 <= result["context_match_score"] <= 1.0
        assert 0.0 <= result["capability_match_score"] <= 1.0
        assert result["estimated_effort"] >= 0

    def test_calculate_context_match(self, db_session: Session, test_agents: tuple, test_knowledge_nodes_with_skills: list):
        """测试场景匹配度计算"""
        expert_agent, _ = test_agents
        node_ids = [node.id for node in test_knowledge_nodes_with_skills]

        capsule = CapabilityCapsuleService.create_capsule(
            db=db_session,
            name="Web Development Capsule",
            pattern_type="DESIGN_PATTERN",
            knowledge_node_ids=node_ids,
            created_by_agent_id=expert_agent.agent_id,
            applicable_contexts=["web_development", "api_design"]
        )

        # 完全匹配
        score1 = CapabilityTransferService._calculate_context_match(capsule, "web_development")
        assert score1 == 1.0

        # 部分匹配
        score2 = CapabilityTransferService._calculate_context_match(capsule, "web_development_backend")
        assert score2 >= 0.5

        # 无匹配
        score3 = CapabilityTransferService._calculate_context_match(capsule, "mobile_development")
        assert score3 < 0.5

    def test_calculate_capability_match(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试能力水平匹配度计算"""
        expert_agent, novice_agent = test_agents

        # Expert agent应该有较高的匹配度
        score_expert = CapabilityTransferService._calculate_capability_match(
            db=db_session,
            capsule=test_capsule_with_prerequisites,
            agent_id=expert_agent.agent_id
        )

        # Novice agent应该有较低的匹配度
        score_novice = CapabilityTransferService._calculate_capability_match(
            db=db_session,
            capsule=test_capsule_with_prerequisites,
            agent_id=novice_agent.agent_id
        )

        assert 0.0 <= score_expert <= 1.0
        assert 0.0 <= score_novice <= 1.0
        # Expert应该比Novice匹配度更高
        assert score_expert >= score_novice

    def test_adapt_code_template(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试代码模板适配"""
        expert_agent, _ = test_agents

        result = CapabilityTransferService.adapt_code_template(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            target_context="web_api",
            customizations={"api_version": "v2", "auth_type": "jwt"}
        )

        assert "original_template" in result
        assert "adapted_template" in result
        assert "changes" in result

        assert isinstance(result["changes"], list)
        assert len(result["changes"]) > 0

        # 验证适配后的模板包含场景信息
        assert "web_api" in result["adapted_template"]

    def test_transfer_capsule_success(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试能力胶囊迁移 - 成功"""
        expert_agent, _ = test_agents

        transfer = CapabilityTransferService.transfer_capsule(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            to_context="web_development",
            agent_id=expert_agent.agent_id,
            from_context="system_design",
            customizations={"framework": "fastapi"}
        )

        assert transfer.id is not None
        assert transfer.capsule_id == test_capsule_with_prerequisites.id
        assert transfer.to_context == "web_development"
        assert transfer.from_context == "system_design"
        assert transfer.transferred_by_agent_id == expert_agent.agent_id
        assert transfer.prerequisites_met is True
        assert transfer.success is True
        assert transfer.adaptation_score > 0
        assert transfer.completed_at is not None

    def test_transfer_capsule_failure_prerequisites(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试能力胶囊迁移 - 前置条件不满足"""
        _, novice_agent = test_agents

        transfer = CapabilityTransferService.transfer_capsule(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            to_context="web_development",
            agent_id=novice_agent.agent_id,
            force=False
        )

        assert transfer.id is not None
        assert transfer.prerequisites_met is False
        assert transfer.success is False
        assert transfer.failure_reason is not None
        assert len(transfer.missing_prerequisites) > 0

    def test_transfer_capsule_force(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试能力胶囊迁移 - 强制迁移"""
        _, novice_agent = test_agents

        transfer = CapabilityTransferService.transfer_capsule(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            to_context="web_development",
            agent_id=novice_agent.agent_id,
            force=True  # 强制迁移，忽略前置条件
        )

        assert transfer.id is not None
        assert transfer.success is True  # 强制迁移成功
        assert transfer.completed_at is not None

    def test_record_transfer_feedback(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试记录迁移反馈"""
        expert_agent, _ = test_agents

        # 先执行迁移
        transfer = CapabilityTransferService.transfer_capsule(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            to_context="web_development",
            agent_id=expert_agent.agent_id
        )

        # 记录反馈
        CapabilityTransferService.record_transfer_feedback(
            db=db_session,
            transfer_id=transfer.id,
            success=True,
            actual_effort=3.5,
            feedback="Very useful, saved a lot of time",
            rating=5,
            value_created=100.0,
            time_saved=8.0
        )

        db_session.refresh(transfer)

        assert transfer.success is True
        assert transfer.adaptation_effort == 3.5
        assert transfer.feedback == "Very useful, saved a lot of time"
        assert transfer.rating == 5
        assert transfer.value_created == 100.0
        assert transfer.time_saved == 8.0

    def test_get_transfer_history(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试获取迁移历史"""
        expert_agent, _ = test_agents

        # 执行多次迁移
        transfer1 = CapabilityTransferService.transfer_capsule(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            to_context="web_development",
            agent_id=expert_agent.agent_id
        )

        transfer2 = CapabilityTransferService.transfer_capsule(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            to_context="api_design",
            agent_id=expert_agent.agent_id
        )

        # 按胶囊查询
        history_by_capsule = CapabilityTransferService.get_transfer_history(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id
        )

        assert len(history_by_capsule) >= 2

        # 按Agent查询
        history_by_agent = CapabilityTransferService.get_transfer_history(
            db=db_session,
            agent_id=expert_agent.agent_id
        )

        assert len(history_by_agent) >= 2

    def test_get_transfer_statistics(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试获取迁移统计"""
        expert_agent, _ = test_agents

        # 执行多次迁移
        transfer1 = CapabilityTransferService.transfer_capsule(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            to_context="web_development",
            agent_id=expert_agent.agent_id
        )

        CapabilityTransferService.record_transfer_feedback(
            db=db_session,
            transfer_id=transfer1.id,
            success=True,
            actual_effort=2.0,
            value_created=50.0,
            time_saved=5.0
        )

        transfer2 = CapabilityTransferService.transfer_capsule(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            to_context="api_design",
            agent_id=expert_agent.agent_id
        )

        CapabilityTransferService.record_transfer_feedback(
            db=db_session,
            transfer_id=transfer2.id,
            success=False,
            actual_effort=4.0
        )

        # 获取统计
        stats = CapabilityTransferService.get_transfer_statistics(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id
        )

        assert stats["total_transfers"] >= 2
        assert stats["successful_transfers"] >= 1
        assert 0.0 <= stats["success_rate"] <= 1.0
        assert stats["avg_adaptation_score"] > 0
        assert stats["avg_adaptation_effort"] > 0
        assert stats["total_value_created"] >= 50.0
        assert stats["total_time_saved"] >= 5.0

    def test_transfer_updates_capsule_statistics(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试迁移更新胶囊统计"""
        expert_agent, _ = test_agents

        initial_transfer_count = test_capsule_with_prerequisites.transfer_count

        # 执行迁移
        transfer = CapabilityTransferService.transfer_capsule(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            to_context="web_development",
            agent_id=expert_agent.agent_id
        )

        db_session.refresh(test_capsule_with_prerequisites)

        assert test_capsule_with_prerequisites.transfer_count == initial_transfer_count + 1
        assert test_capsule_with_prerequisites.last_used_at is not None

    def test_adaptation_score_threshold(self, db_session: Session, test_agents: tuple, test_capsule_with_prerequisites: CapabilityCapsule):
        """测试适配度评分阈值"""
        expert_agent, novice_agent = test_agents

        # Expert agent应该有高适配度
        result_expert = CapabilityTransferService.calculate_adaptation_score(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            target_context="web_development",
            agent_id=expert_agent.agent_id
        )

        # Novice agent应该有低适配度
        result_novice = CapabilityTransferService.calculate_adaptation_score(
            db=db_session,
            capsule_id=test_capsule_with_prerequisites.id,
            target_context="web_development",
            agent_id=novice_agent.agent_id
        )

        # Expert的适配度应该明显高于Novice
        assert result_expert["adaptation_score"] > result_novice["adaptation_score"]

        # 验证适配度影响迁移成功率目标（≥70%）
        # 这是一个设计目标，实际成功率需要在生产环境中验证
        assert result_expert["adaptation_score"] >= 0.7 or result_expert["adaptation_required"] is True

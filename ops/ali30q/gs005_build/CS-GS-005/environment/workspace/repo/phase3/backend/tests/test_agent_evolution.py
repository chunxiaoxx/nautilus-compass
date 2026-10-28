"""
测试Agent进化服务
"""
import pytest
from sqlalchemy.orm import Session
from models.epiplexity import KnowledgeNode
from models.emergent_pattern import EmergentPattern
from models.database import Agent
from services.agent_evolution_service import AgentEvolutionService
from services.knowledge_node_service import KnowledgeNodeService
from services.knowledge_emergence_service import KnowledgeEmergenceService


@pytest.fixture
def test_agent(db_session: Session):
    """创建测试Agent"""
    agent = Agent(
        agent_id=9002,
        owner="0x" + "2" * 40,
        name="Test Evolution Agent",
        reputation=100
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


@pytest.fixture
def diverse_knowledge_nodes(db_session: Session, test_agent: Agent):
    """创建多样化的知识节点"""
    nodes = []

    # 设计模式类（5个）
    for i in range(5):
        node = KnowledgeNodeService.create_knowledge_node(
            db=db_session,
            content=f"Design pattern {i}: Singleton, Factory, Observer, etc.",
            content_type="CODE",
            created_by_agent_id=test_agent.agent_id,
            tags=["design_pattern"],
            category="DESIGN_PATTERN"
        )
        node.verified = True
        node.epiplexity = 0.7 + (i * 0.05)  # 0.7-0.9
        nodes.append(node)

    # 算法类（3个）
    for i in range(3):
        node = KnowledgeNodeService.create_knowledge_node(
            db=db_session,
            content=f"Algorithm {i}: Binary search, Quick sort, etc.",
            content_type="CODE",
            created_by_agent_id=test_agent.agent_id,
            tags=["algorithm"],
            category="ALGORITHM"
        )
        node.verified = True
        node.epiplexity = 0.6 + (i * 0.05)  # 0.6-0.7
        nodes.append(node)

    # 架构类（2个）
    for i in range(2):
        node = KnowledgeNodeService.create_knowledge_node(
            db=db_session,
            content=f"Architecture {i}: MVC, Microservices, etc.",
            content_type="CONCEPT",
            created_by_agent_id=test_agent.agent_id,
            tags=["architecture"],
            category="ARCHITECTURE"
        )
        node.verified = True
        node.epiplexity = 0.8 + (i * 0.05)  # 0.8-0.85
        nodes.append(node)

    db_session.commit()
    return nodes


class TestAgentEvolutionService:
    """测试Agent进化服务"""

    def test_analyze_knowledge_distribution(self, db_session: Session, test_agent: Agent, diverse_knowledge_nodes: list):
        """测试知识分布分析"""
        distribution = AgentEvolutionService.analyze_knowledge_distribution(
            db=db_session,
            agent_id=test_agent.agent_id
        )

        # 验证返回格式
        assert isinstance(distribution, dict)
        assert "by_category" in distribution
        assert "by_complexity" in distribution
        assert "by_content_type" in distribution
        assert "total_nodes" in distribution
        assert "avg_epiplexity" in distribution

        # 验证统计数据
        assert distribution["total_nodes"] == 10
        assert distribution["avg_epiplexity"] > 0

        # 验证分类统计
        by_category = distribution["by_category"]
        assert "DESIGN_PATTERN" in by_category
        assert "ALGORITHM" in by_category
        assert "ARCHITECTURE" in by_category

        # 验证设计模式类（5个，占50%）
        design_pattern = by_category["DESIGN_PATTERN"]
        assert design_pattern["count"] == 5
        assert design_pattern["percentage"] == 0.5
        assert design_pattern["avg_epiplexity"] > 0

    def test_identify_strength_areas(self, db_session: Session, test_agent: Agent, diverse_knowledge_nodes: list):
        """测试优势领域识别"""
        distribution = AgentEvolutionService.analyze_knowledge_distribution(
            db=db_session,
            agent_id=test_agent.agent_id
        )

        strength_areas = AgentEvolutionService.identify_strength_areas(
            distribution
        )

        # 验证返回格式
        assert isinstance(strength_areas, list)

        # 验证每个优势领域
        for area in strength_areas:
            assert "category" in area
            assert "count" in area
            assert "avg_epiplexity" in area
            assert "percentage" in area
            assert "strength_score" in area

            # 验证优势标准
            assert area["percentage"] >= 0.2
            assert area["avg_epiplexity"] >= AgentEvolutionService.STRENGTH_THRESHOLD

        # 验证排序（按strength_score降序）
        if len(strength_areas) > 1:
            for i in range(len(strength_areas) - 1):
                assert strength_areas[i]["strength_score"] >= strength_areas[i + 1]["strength_score"]

    def test_recommend_specialization_deepen(self, db_session: Session, test_agent: Agent, diverse_knowledge_nodes: list):
        """测试专业化推荐 - 深化方向"""
        distribution = AgentEvolutionService.analyze_knowledge_distribution(
            db=db_session,
            agent_id=test_agent.agent_id
        )

        strength_areas = AgentEvolutionService.identify_strength_areas(
            distribution
        )

        specialization = AgentEvolutionService.recommend_specialization(
            knowledge_distribution=distribution,
            strength_areas=strength_areas,
            emergent_patterns=[]
        )

        # 验证返回格式
        assert isinstance(specialization, dict)
        assert "recommended_direction" in specialization
        assert "target_category" in specialization
        assert "reason" in specialization
        assert "confidence" in specialization

        # 设计模式占50%，应该推荐深化
        assert specialization["recommended_direction"] == "DEEPEN"
        assert specialization["target_category"] == "DESIGN_PATTERN"

    def test_recommend_specialization_explore(self, db_session: Session, test_agent: Agent):
        """测试专业化推荐 - 探索方向"""
        # 创建少量知识节点
        for i in range(2):
            node = KnowledgeNodeService.create_knowledge_node(
                db=db_session,
                content=f"Basic knowledge {i}",
                content_type="TEXT",
                created_by_agent_id=test_agent.agent_id,
                category="BASIC"
            )
            node.verified = True

        db_session.commit()

        distribution = AgentEvolutionService.analyze_knowledge_distribution(
            db=db_session,
            agent_id=test_agent.agent_id
        )

        strength_areas = AgentEvolutionService.identify_strength_areas(
            distribution
        )

        specialization = AgentEvolutionService.recommend_specialization(
            knowledge_distribution=distribution,
            strength_areas=strength_areas,
            emergent_patterns=[]
        )

        # 知识少，应该推荐探索
        assert specialization["recommended_direction"] in ["EXPLORE", "FOCUS"]

    def test_recommend_specialization_with_emergent_patterns(self, db_session: Session, test_agent: Agent, diverse_knowledge_nodes: list):
        """测试专业化推荐 - 有涌现模式"""
        # 创建涌现模式
        emergent_patterns = []
        for i in range(3):
            pattern = EmergentPattern(
                name=f"Emergent Pattern {i}",
                pattern_type="HYBRID",
                source_knowledge_ids=[1, 2, 3],
                knowledge_count=3,
                combined_epiplexity=0.9,
                individual_sum=0.7,
                emergence_factor=1.3,
                is_emergent=True,
                discovered_by_agent_id=test_agent.agent_id
            )
            db_session.add(pattern)
            emergent_patterns.append(pattern)

        db_session.commit()

        distribution = AgentEvolutionService.analyze_knowledge_distribution(
            db=db_session,
            agent_id=test_agent.agent_id
        )

        strength_areas = AgentEvolutionService.identify_strength_areas(
            distribution
        )

        specialization = AgentEvolutionService.recommend_specialization(
            knowledge_distribution=distribution,
            strength_areas=strength_areas,
            emergent_patterns=emergent_patterns
        )

        # 有涌现模式，可能推荐探索
        assert specialization["recommended_direction"] in ["DEEPEN", "EXPLORE"]

    def test_plan_evolution_path_deepen(self, db_session: Session, test_agent: Agent, diverse_knowledge_nodes: list):
        """测试进化路径规划 - 深化"""
        specialization = {
            "recommended_direction": "DEEPEN",
            "target_category": "DESIGN_PATTERN",
            "reason": "Strong expertise",
            "confidence": 0.8
        }

        strength_areas = [
            {
                "category": "DESIGN_PATTERN",
                "count": 5,
                "avg_epiplexity": 0.75,
                "percentage": 0.5,
                "strength_score": 0.375
            }
        ]

        evolution_path = AgentEvolutionService.plan_evolution_path(
            db=db_session,
            agent_id=test_agent.agent_id,
            specialization=specialization,
            strength_areas=strength_areas
        )

        # 验证返回格式
        assert isinstance(evolution_path, list)
        assert len(evolution_path) > 0

        # 验证每个步骤
        for i, step in enumerate(evolution_path):
            assert "step" in step
            assert "action" in step
            assert "target" in step
            assert "estimated_epiplexity" in step
            assert "reason" in step
            assert step["step"] == i + 1

        # 深化路径应该包含 LEARN, APPLY, INNOVATE
        actions = [step["action"] for step in evolution_path]
        assert "LEARN" in actions or "APPLY" in actions or "INNOVATE" in actions

    def test_plan_evolution_path_explore(self, db_session: Session, test_agent: Agent):
        """测试进化路径规划 - 探索"""
        specialization = {
            "recommended_direction": "EXPLORE",
            "target_category": None,
            "reason": "Continue exploring",
            "confidence": 0.5
        }

        evolution_path = AgentEvolutionService.plan_evolution_path(
            db=db_session,
            agent_id=test_agent.agent_id,
            specialization=specialization,
            strength_areas=[]
        )

        # 验证返回格式
        assert isinstance(evolution_path, list)
        assert len(evolution_path) > 0

        # 探索路径应该包含 EXPLORE, COMBINE, EMERGE
        actions = [step["action"] for step in evolution_path]
        assert "EXPLORE" in actions or "COMBINE" in actions or "EMERGE" in actions

    def test_plan_evolution_path_focus(self, db_session: Session, test_agent: Agent):
        """测试进化路径规划 - 聚焦"""
        specialization = {
            "recommended_direction": "FOCUS",
            "target_category": "ALGORITHM",
            "reason": "Knowledge spread",
            "confidence": 0.6
        }

        evolution_path = AgentEvolutionService.plan_evolution_path(
            db=db_session,
            agent_id=test_agent.agent_id,
            specialization=specialization,
            strength_areas=[]
        )

        # 验证返回格式
        assert isinstance(evolution_path, list)
        assert len(evolution_path) > 0

        # 聚焦路径应该包含 FOCUS, MASTER, SPECIALIZE
        actions = [step["action"] for step in evolution_path]
        assert "FOCUS" in actions or "MASTER" in actions or "SPECIALIZE" in actions

    def test_evolve_agent_specialization(self, db_session: Session, test_agent: Agent, diverse_knowledge_nodes: list):
        """测试Agent专业化进化（完整流程）"""
        result = AgentEvolutionService.evolve_agent_specialization(
            db=db_session,
            agent_id=test_agent.agent_id
        )

        # 验证返回格式
        assert isinstance(result, dict)
        assert "current_level" in result
        assert "knowledge_distribution" in result
        assert "strength_areas" in result
        assert "specialization" in result
        assert "emergent_patterns" in result
        assert "evolution_path" in result

        # 验证当前水平
        assert result["current_level"] > 0

        # 验证知识分布
        assert isinstance(result["knowledge_distribution"], dict)

        # 验证优势领域
        assert isinstance(result["strength_areas"], list)

        # 验证专业化推荐
        assert isinstance(result["specialization"], dict)
        assert "recommended_direction" in result["specialization"]

        # 验证进化路径
        assert isinstance(result["evolution_path"], list)
        assert len(result["evolution_path"]) > 0

    def test_get_specialization_level_generalist(self, db_session: Session, test_agent: Agent):
        """测试专业化水平 - 通才"""
        # 创建少量分散的知识
        for i in range(3):
            node = KnowledgeNodeService.create_knowledge_node(
                db=db_session,
                content=f"Knowledge {i}",
                content_type="TEXT",
                created_by_agent_id=test_agent.agent_id,
                category=f"CATEGORY_{i}"
            )
            node.epiplexity = 0.5

        db_session.commit()

        level_info = AgentEvolutionService.get_specialization_level(
            db=db_session,
            agent_id=test_agent.agent_id
        )

        # 验证返回格式
        assert isinstance(level_info, dict)
        assert "level" in level_info
        assert "primary_specialization" in level_info
        assert "specialization_score" in level_info
        assert "knowledge_breadth" in level_info
        assert "knowledge_depth" in level_info

        # 知识分散，应该是通才
        assert level_info["level"] == "GENERALIST"
        assert level_info["knowledge_breadth"] == 3

    def test_get_specialization_level_specialist(self, db_session: Session, test_agent: Agent, diverse_knowledge_nodes: list):
        """测试专业化水平 - 专家"""
        level_info = AgentEvolutionService.get_specialization_level(
            db=db_session,
            agent_id=test_agent.agent_id
        )

        # 设计模式占50%，平均Epiplexity高，应该是专家或专业人士
        assert level_info["level"] in ["SPECIALIST", "EXPERT", "EMERGING_SPECIALIST"]
        assert level_info["primary_specialization"] == "DESIGN_PATTERN"
        assert level_info["specialization_score"] > 0.2

    def test_empty_knowledge_base(self, db_session: Session, test_agent: Agent):
        """测试空知识库"""
        distribution = AgentEvolutionService.analyze_knowledge_distribution(
            db=db_session,
            agent_id=test_agent.agent_id
        )

        assert distribution["total_nodes"] == 0
        assert distribution["avg_epiplexity"] == 0.0

        strength_areas = AgentEvolutionService.identify_strength_areas(
            distribution
        )
        assert len(strength_areas) == 0

        specialization = AgentEvolutionService.recommend_specialization(
            knowledge_distribution=distribution,
            strength_areas=strength_areas,
            emergent_patterns=[]
        )
        assert specialization["recommended_direction"] == "EXPLORE"

    def test_evolution_path_epiplexity_increase(self, db_session: Session, test_agent: Agent, diverse_knowledge_nodes: list):
        """测试进化路径的Epiplexity递增"""
        specialization = {
            "recommended_direction": "DEEPEN",
            "target_category": "DESIGN_PATTERN",
            "reason": "Strong expertise",
            "confidence": 0.8
        }

        evolution_path = AgentEvolutionService.plan_evolution_path(
            db=db_session,
            agent_id=test_agent.agent_id,
            specialization=specialization,
            strength_areas=[]
        )

        # 验证Epiplexity递增
        if len(evolution_path) > 1:
            for i in range(len(evolution_path) - 1):
                assert evolution_path[i + 1]["estimated_epiplexity"] >= evolution_path[i]["estimated_epiplexity"]

    def test_strength_threshold(self, db_session: Session, test_agent: Agent):
        """测试优势阈值"""
        # 创建低Epiplexity的知识节点
        for i in range(5):
            node = KnowledgeNodeService.create_knowledge_node(
                db=db_session,
                content=f"Low quality knowledge {i}",
                content_type="TEXT",
                created_by_agent_id=test_agent.agent_id,
                category="LOW_QUALITY"
            )
            node.verified = True
            node.epiplexity = 0.3  # 低于优势阈值

        db_session.commit()

        distribution = AgentEvolutionService.analyze_knowledge_distribution(
            db=db_session,
            agent_id=test_agent.agent_id
        )

        strength_areas = AgentEvolutionService.identify_strength_areas(
            distribution
        )

        # 低Epiplexity不应该被识别为优势领域
        assert len(strength_areas) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
